"""
This file contains preprocessing utilities for text data.
"""

import spacy
import re
from nltk.corpus import stopwords

nlp = spacy.load('fr_core_news_md')
french_stopwords = set(stopwords.words('french'))

def remove_punctuation(text: str) -> str:
    cleaned_text = re.sub(r'[^A-Za-z0-9\s]', ' ', text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    return cleaned_text.strip()

def lemmatize(text: str) -> str:
    """Lemmatization with spaCy - reduces words to their base form (lemma)"""
    doc = nlp(text)
    lemmatized_words = [token.lemma_ for token in doc]
    return " ".join(lemmatized_words)

def return_tokens(text: str) -> list[str]:
    doc = nlp(text)
    return [token.text for token in doc]

def remove_stopwords(text: str) -> str:
    tokens = return_tokens(text)
    return " ".join([token for token in tokens if token not in french_stopwords])

def preprocess_text(text: str) -> str:
    """
    text preprocessing pipeline
    """
    text = remove_punctuation(text)
    text = remove_stopwords(text)
    text = lemmatize(text)
    text = text.lower()
    return text

