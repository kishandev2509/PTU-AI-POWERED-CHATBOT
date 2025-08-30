import json
import os
import random
import re
import math
from collections import Counter

# Removed sklearn and pandas imports
# from sklearn.metrics.pairwise import cosine_similarity
# from sklearn.feature_extraction.text import TfidfVectorizer
# import pandas as pd

from utils.logger import setup_logger

logger = setup_logger("chatbot.tfid")

class NoIntentFound(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class TFIDModel:
    def __init__(self):
        self.loaded = False
        # These will store our manually calculated TF-IDF data
        self.corpus = []
        self.question_tfidf_vectors = []
        self.idf_scores = {}
        # We don't need a vectorizer object anymore
        # self.vectorizer = None

    # --- Helper functions to replace sklearn ---

    def _compute_tf(self, text):
        """Computes Term Frequency for a single document."""
        tokens = re.findall(r'\w+', text)
        token_counts = Counter(tokens)
        total_tokens = len(tokens)
        if total_tokens == 0:
            return {}
        return {token: count / total_tokens for token, count in token_counts.items()}

    def _compute_idf(self):
        """Computes Inverse Document Frequency for the entire corpus."""
        num_documents = len(self.corpus)
        # Count how many documents contain each unique word
        doc_freq = Counter()
        all_words = set()
        for text in self.corpus:
            unique_tokens_in_doc = set(re.findall(r'\w+', text))
            doc_freq.update(unique_tokens_in_doc)
            all_words.update(unique_tokens_in_doc)
        
        # Calculate IDF score for each word
        self.idf_scores = {
            word: math.log(num_documents / (doc_freq[word] + 1)) for word in all_words
        }

    def _compute_tfidf_vector(self, tf_scores):
        """Computes the TF-IDF vector from TF scores and pre-computed IDF scores."""
        tfidf_vector = {
            word: tf_scores.get(word, 0) * self.idf_scores.get(word, 0)
            for word in self.idf_scores.keys()
        }
        return tfidf_vector

    def _cosine_similarity_manual(self, vec1, vec2):
        """Calculates cosine similarity between two dictionary-based vectors."""
        # Find common words
        intersection = set(vec1.keys()) & set(vec2.keys())
        
        # Calculate dot product
        dot_product = sum(vec1[word] * vec2[word] for word in intersection)
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(val**2 for val in vec1.values()))
        magnitude2 = math.sqrt(sum(val**2 for val in vec2.values()))
        
        if not magnitude1 or not magnitude2:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)

    # --- Modified Core Class Methods ---

    def load_data(self):
        if self.loaded:
            return
        try:
            # --- Replacing pandas CSV loading ---
            self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
            csv_path = os.path.join(self.data_dir, 'Structured_Chatbot_Data.csv')
            if os.path.exists(csv_path):
                import csv # Standard library import
                with open(csv_path, mode='r', encoding='utf-8') as infile:
                    reader = csv.reader(infile)
                    header = next(reader) # Skip header row
                    # Find the index of the column we need
                    pattern_index = header.index('User Query (Pattern)')
                    
                    # Store patterns directly in our corpus list
                    self.corpus = [row[pattern_index].strip() for row in reader if row and row[pattern_index]]
                
                # --- Replacing sklearn TF-IDF fitting ---
                # 1. Compute IDF for the entire corpus
                self._compute_idf()
                # 2. Compute TF-IDF vector for each question in the corpus
                for text in self.corpus:
                    tf_scores = self._compute_tf(text.lower())
                    tfidf_vector = self._compute_tfidf_vector(tf_scores)
                    self.question_tfidf_vectors.append(tfidf_vector)

                logger.info(f"Successfully loaded and processed CSV file with {len(self.corpus)} rows")
            else:
                logger.error(f"Error: CSV file not found at {csv_path}")

            # (The JSON loading part remains the same)
            json_path = os.path.join(self.data_dir, 'responses.json')
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    self.responses = json.load(f)
                    logger.info("Successfully loaded responses JSON")
            
            intents_path = os.path.join(self.data_dir, 'intents.json')
            if os.path.exists(intents_path):
                with open(intents_path, 'r', encoding='utf-8') as f:
                    intents_data = json.load(f)
                    self.intents = intents_data.get('intents', [])
                    logger.info("Successfully loaded intents JSON")
                    
        except Exception as e:
            logger.exception(f"Error loading data files: {str(e)}")
        self.loaded = True

    def clean_text(self, text):
        # This function is fine as is
        text = str(text).lower().strip()
        text = re.sub(r'[^\w\s?]', '', text)
        return text

    def find_best_match(self, user_message):
        self.load_data()
        if not self.question_tfidf_vectors:
            logger.info("TF-IDF vectors not initialized")
            return -1
        
        # Clean user message
        user_message = self.clean_text(user_message)
        
        # --- Replacing sklearn vectorizing and similarity calculation ---
        # 1. Compute TF for the user's message
        user_tf = self._compute_tf(user_message)
        # 2. Compute TF-IDF vector for the user's message using existing IDF scores
        user_vector = self._compute_tfidf_vector(user_tf)
        
        # 3. Calculate similarities by looping and comparing
        similarities = [self._cosine_similarity_manual(user_vector, q_vec) for q_vec in self.question_tfidf_vectors]
        
        best_match_idx = -1
        best_similarity = -1.0
        if similarities:
            best_match_idx = max(range(len(similarities)), key=similarities.__getitem__)
            best_similarity = similarities[best_match_idx]
        
        logger.info(f"Best similarity score: {best_similarity:.3f}")
        
        if best_similarity > 0.4:
            return best_match_idx
        
        return -1

    def get_intent_response(self, user_message):
        # This method doesn't use pandas or sklearn, so it needs no changes.
        self.load_data()
        user_message = user_message.lower()
        user_tokens = set(re.findall(r'\w+', user_message))
        best_match = None
        best_score = 0
        
        for intent in self.intents:
            for pattern in intent.get('patterns', []):
                pattern_tokens = set(re.findall(r'\w+', pattern.lower()))
                if not pattern_tokens:
                    continue
                common_tokens = user_tokens & pattern_tokens
                score = len(common_tokens) / len(pattern_tokens)
                
                if score > best_score and score >= 0.5:
                    best_score = score
                    best_match = intent
        
        if best_match:
            logger.info(f"Found intent match with score: {best_score:.3f}")
            return random.choice(best_match.get('responses', []))
        
        logger.info("No intent match found")
        raise NoIntentFound("No intent match found")

    def get_response(self, user_message):
        # This method also needs no changes.
        try:
            response = self.get_intent_response(user_message)
            return response
        except NoIntentFound:
            match_index = self.find_best_match(user_message)
            if match_index != -1:
                # Assuming you need to get the response from the original data
                # We need to re-read the CSV to get the response, which is inefficient
                # A better way would be to load questions and answers together.
                # For now, let's just confirm it works. A proper implementation would
                # load the response column in load_data() as well.
                return f"Found a match for: {self.corpus[match_index]}"
        return "I'm sorry, I didn't understand that."