import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def is_duplicate(emb1, emb2, threshold=0.9):
    sim = cosine_similarity([emb1], [emb2])[0][0]
    return sim > threshold, sim