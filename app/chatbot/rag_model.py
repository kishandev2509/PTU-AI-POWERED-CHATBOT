# app/chatbot/rag_ptu.py
from __future__ import annotations
import os
import json
import argparse
from pathlib import Path
from typing import List, Dict
import pandas as pd
from sentence_transformers import SentenceTransformer
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
import chromadb


# ----------------------------
# Paths
# ----------------------------
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
MODELS_DIR = HERE / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

CSV_CANDIDATES = [
    DATA_DIR / "dataset.csv",
    DATA_DIR / "Structured_Chatbot_Data.csv",
]

INTENTS_JSON = DATA_DIR / "intents.json"
RESPONSES_JSON = DATA_DIR / "responses.json"

# Chroma will persist inside models/ folder
CHROMA_DIR = str(MODELS_DIR / "chroma_db")
EMBEDDER_NAME_PATH = MODELS_DIR / "embedder_name.txt"

# Default embedding + LLM
DEFAULT_EMBEDDER = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_NATURALIZER = os.getenv("HF_NATURALIZER_MODEL", "google/flan-t5-base")


# ----------------------------
# Utilities
# ----------------------------
def log(msg: str) -> None:
    print(f"[RAG] {msg}", flush=True)


def find_existing_csv() -> Path | None:
    for p in CSV_CANDIDATES:
        if p.exists():
            return p
    return None


def load_documents() -> List[Dict[str, str]]:
    """
    Merge your CSV and JSONs into a list of {"question": str, "answer": str}.
    """
    docs: List[Dict[str, str]] = []

    # CSV
    csv_path = find_existing_csv()
    if csv_path:
        log(f"Loading CSV: {csv_path.relative_to(HERE)}")
        df = pd.read_csv(csv_path, encoding="utf-8")

        col_q, col_a = None, None
        for cand in ["User Query (Pattern)", "Pattern", "User Query", "Question"]:
            if cand in df.columns:
                col_q = cand
                break
        for cand in ["Bot Response", "Response", "Answer"]:
            if cand in df.columns:
                col_a = cand
                break
        if not col_q or not col_a:
            raise ValueError(f"CSV missing Q/A columns. Found: {list(df.columns)}")

        df[col_q] = df[col_q].fillna("").astype(str).str.strip()
        df[col_a] = df[col_a].fillna("").astype(str).str.strip()

        for _, row in df.iterrows():
            if row[col_q] and row[col_a]:
                docs.append({"question": row[col_q], "answer": row[col_a]})
        log(f"  -> {len(docs)} rows from CSV")

    # intents.json
    if INTENTS_JSON.exists():
        log(f"Loading intents: {INTENTS_JSON.relative_to(HERE)}")
        intents = json.load(open(INTENTS_JSON, "r", encoding="utf-8")).get("intents", [])
        count = 0
        for intent in intents:
            pats, resps = intent.get("patterns", []), intent.get("responses", [])
            default_resp = resps[0] if resps else ""
            for p in pats:
                if p and default_resp:
                    docs.append({"question": p, "answer": default_resp})
                    count += 1
        log(f"  -> {count} rows from intents.json")

    # responses.json
    if RESPONSES_JSON.exists():
        log(f"Loading responses: {RESPONSES_JSON.relative_to(HERE)}")
        resp_obj = json.load(open(RESPONSES_JSON, "r", encoding="utf-8"))
        if isinstance(resp_obj, dict):
            count = 0
            for q, a in resp_obj.items():
                if q and a:
                    docs.append({"question": q.strip(), "answer": a.strip()})
                    count += 1
            log(f"  -> {count} rows from responses.json")

    if not docs:
        raise FileNotFoundError("No documents found in CSV/JSONs.")
    return docs


# ----------------------------
# ChromaDB Index
# ----------------------------
def build_index(embedder_name: str = DEFAULT_EMBEDDER) -> None:
    log("Building Chroma index from data...")
    docs = load_documents()

    embedder = SentenceTransformer(embedder_name)
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

    # reset old collection
    if "ptu_collection" in [c.name for c in chroma_client.list_collections()]:
        chroma_client.delete_collection("ptu_collection")

    collection = chroma_client.create_collection("ptu_collection")

    questions = [d["question"] for d in docs]
    answers = [d["answer"] for d in docs]
    embeddings = embedder.encode(questions, convert_to_numpy=True).tolist()

    collection.add(
        embeddings=embeddings,
        documents=questions,
        metadatas=[{"answer": a} for a in answers],
        ids=[str(i) for i in range(len(questions))],
    )

    EMBEDDER_NAME_PATH.write_text(embedder_name, encoding="utf-8")
    log("✅ Build complete.")


def load_index_and_models():
    if not EMBEDDER_NAME_PATH.exists():
        build_index()

    embedder_name = EMBEDDER_NAME_PATH.read_text(encoding="utf-8").strip()
    embedder = SentenceTransformer(embedder_name)
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = chroma_client.get_collection("ptu_collection")
    return collection, embedder


def retrieve(user_query: str, k: int = 3) -> List[str]:
    collection, embedder = load_index_and_models()
    q_emb = embedder.encode([user_query], convert_to_numpy=True).tolist()
    results = collection.query(query_embeddings=q_emb, n_results=k)
    answers = [m["answer"] for m in results["metadatas"][0]]
    return answers


# ----------------------------
# Naturalizer (LLM)
# ----------------------------
def init_naturalizer(model_name: str = DEFAULT_NATURALIZER):
    log(f"Initializing naturalizer: {model_name}")
    tok = AutoTokenizer.from_pretrained(model_name)
    mdl = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    return pipeline("text2text-generation", model=mdl, tokenizer=tok)


def answer(user_query: str, use_llm: bool = True, k: int = 3) -> str:
    hits = retrieve(user_query, k=k)
    if not hits:
        return "I’m not sure yet. Please rephrase or provide more details."

    context = "\n".join(f"- {ans}" for ans in hits)

    if not use_llm:
        return f"Here’s what I found:\n{context}"

    naturalizer = init_naturalizer()
    prompt = (
        "You are a helpful assistant for PTU students. "
        # "Use ONLY the context below to answer the student’s question clearly. "
        # "If not in the context, say you don't have that info.\n\n"
        "Give a fformatted response that can be easy to read.\n"
        "You can also search on internet.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {user_query}\n\nAnswer:"
    )
    out = naturalizer(prompt, max_new_tokens=160, num_beams=4)[0]["generated_text"].strip()
    return out

def chat(use_llm: bool = True, k: int = 3):
    naturalizer = init_naturalizer()
    while True:
        try:
            user_query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_query.lower() in {"exit", "quit"}:
            break
        hits = retrieve(user_query, k=k)
        if not hits:
            return "I’m not sure yet. Please rephrase or provide more details."

        context = "\n".join(f"- {ans}" for ans in hits)

        if not use_llm:
            return f"Here’s what I found:\n{context}"

        prompt = (
            "You are a helpful assistant for PTU students. "
            "You h ave answer the queries of students.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {user_query}\n\nAnswer:"
        )
        out = naturalizer(prompt, max_new_tokens=160, num_beams=4)[0]["generated_text"].strip()
        print("Bot:",out)



# ----------------------------
# CLI
# ----------------------------
def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="PTU RAG with ChromaDB")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="Build Chroma index")
    p_build.add_argument("--embedder", default=DEFAULT_EMBEDDER)

    p_ask = sub.add_parser("ask", help="Answer a single question")
    p_ask.add_argument("question")
    p_ask.add_argument("--no-llm", action="store_true")
    p_ask.add_argument("-k", type=int, default=3)

    p_chat = sub.add_parser("chat", help="Interactive chat")
    p_chat.add_argument("--no-llm", action="store_true")
    p_chat.add_argument("-k", type=int, default=3)

    args = parser.parse_args(argv)

    if args.cmd == "build":
        build_index(embedder_name=args.embedder)
    elif args.cmd == "ask":
        print(answer(args.question, use_llm=(not args.no_llm), k=args.k))
    elif args.cmd == "chat":
        log("Entering chat mode. Type 'exit' to quit.")
        while True:
            try:
                user = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if user.lower() in {"exit", "quit"}:
                break
            print("Bot:", answer(user, use_llm=(not args.no_llm), k=args.k))


if __name__ == "__main__":
    main()
