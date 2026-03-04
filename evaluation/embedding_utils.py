"""
Hilfsmodul für semantische Ähnlichkeit mit sentence-transformers
"""
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Modell einmalig laden (kleines Modell für Geschwindigkeit)
_model = SentenceTransformer('all-MiniLM-L6-v2')

def embedding_similarity(text1: str, text2: str) -> float:
    if not text1 or not text2:
        return 0.0
    emb1 = _model.encode([text1], convert_to_numpy=True)
    emb2 = _model.encode([text2], convert_to_numpy=True)
    sim = cosine_similarity(emb1, emb2)[0, 0]
    return float(sim)
