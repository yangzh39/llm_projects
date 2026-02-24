import json
import os
from typing import Any, Dict, List, Tuple

import faiss
import numpy as np


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    """
    Build a FAISS index using cosine similarity.

    Technique:
      - Normalize vectors to unit length.
      - Use IndexFlatIP (inner product).
      - On normalized vectors, inner product == cosine similarity.

    Why IndexFlatIP:
      - Minimal + exact search, perfect for learning and small corpora.
      - For large corpora you'd use IVF/HNSW and persist trained indexes.
    """
    emb = embeddings.astype("float32")
    faiss.normalize_L2(emb)
    dim = emb.shape[1]

    index = faiss.IndexFlatIP(dim)
    index.add(emb)
    return index


def save_index(index: faiss.Index, path: str) -> None:
    """
    Save FAISS index to disk.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    faiss.write_index(index, path)


def load_index(path: str) -> faiss.Index:
    """
    Load FAISS index from disk.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"FAISS index not found at: {path}")
    return faiss.read_index(path)


def save_chunks(chunks: List[Dict[str, Any]], path: str) -> None:
    """
    Save chunk metadata to disk.

    chunks is a list of dicts like:
      {
        "chunk_id": int,
        "source": "offense.txt",
        "text": "...",
      }
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


def load_chunks(path: str) -> List[Dict[str, Any]]:
    """
    Load chunk metadata from disk.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Chunks file not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def prepare_chunks(docs: List[Tuple[str, str]], chunk_fn) -> List[Dict[str, Any]]:
    """
    Convert docs into a flat list of chunk dicts with stable IDs.

    Args:
      docs: list of (source_name, full_text)
      chunk_fn: function that splits text into chunks

    Returns:
      list of {"chunk_id", "source", "text"}
    """
    chunk_rows: List[Dict[str, Any]] = []
    chunk_id = 0

    for source, text in docs:
        parts = chunk_fn(text)
        for part in parts:
            chunk_rows.append(
                {
                    "chunk_id": chunk_id,
                    "source": source,
                    "text": part,
                }
            )
            chunk_id += 1

    return chunk_rows