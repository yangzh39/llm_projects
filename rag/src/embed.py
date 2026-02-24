from functools import lru_cache
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def get_embedder(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Load embedding model once and cache it.

    Why:
      - Embedding model load can be slow; caching avoids repeated initialization.
      - SentenceTransformers runs locally (free).

    Default model:
      - all-MiniLM-L6-v2 is fast and good enough for learning RAG.
    """
    return SentenceTransformer(model_name)


def embed_texts(texts: List[str], model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    """
    Convert list of texts into embeddings.

    Returns:
      np.ndarray of shape (len(texts), embedding_dim), dtype float32-ish.
    """
    embedder = get_embedder(model_name)
    emb = embedder.encode(texts, convert_to_numpy=True)
    return emb