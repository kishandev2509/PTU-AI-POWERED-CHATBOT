import os
from dotenv import load_dotenv
from groq import Groq
import markdown

load_dotenv()

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),  # This is the default and can be omitted
)


def answer(query:str, intent) -> str:
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role":'system',
                "content":'You are a PTU SUPPORT webpage assitant that helps students to get anaswer from the knowlwdge you have with intent provided before the query. PTU stands for Punjab Technical University and also reffered as IKGPTU (Inder Kumar Gujral Punjab Techincal Unversity). Don\'t let user know about intent and always answer in a friendly manner. If you are not sure about the answer, politely let the user know that you are unable to provide the information they are looking for. Always keep your answers short and precise. If the user query is not related to PTU, politely let them know that you can only assist with PTU related queries and suggest them to contact support for further assistance.'
            },
            {
                "role": "user",
                "content":f",'intent': {intent},'query': {query},"
                
            }
        ],
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
    )
    response = chat_completion.choices[0].message.content
    result = markdown.markdown(response)
    return result
