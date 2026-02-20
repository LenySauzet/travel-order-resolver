"""
This file contains preprocessing utilities for text data.
"""

import spacy
import re
import unicodedata

nlp = spacy.load('fr_core_news_md')

def remove_punctuation(text: str) -> str:
    """
    Removes punctuation from a string.
    """
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


def remove_accents(text: str) -> str:
    """
    Removes accents from a string.
    """
    normalized_text = unicodedata.normalize('NFD', text)
    text_without_accents = ''.join(
        char for char in normalized_text
        if not unicodedata.combining(char)
    )
    return text_without_accents

def normalize_text(text: str) -> str:
    """
    Light text normalization: lowercase, remove accents and punctuation.
    Use this for NER input and dataset generation.
    """
    text = text.lower()
    text = remove_accents(text)
    text = remove_punctuation(text)
    return text

def preprocess_text(text: str) -> str:
    """
    Full text preprocessing pipeline
    """
    text = remove_accents(text)
    text = remove_punctuation(text)
    text = lemmatize(text)
    text = text.lower()
    return text

def unified_to_spacy(data):
    """Convert unified format to spaCy format."""
    return [
        data["text"],
        {"entities": [[e["start"], e["end"], e["label"]] for e in data["entities"]]}
    ]