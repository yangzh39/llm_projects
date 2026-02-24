from typing import Any, Dict, List, Tuple

import faiss
import numpy as np

from embed import embed_texts


def retrieve_top_k(
    query: str,
    index: faiss.Index,
    chunks: List[Dict[str, Any]],
    top_k: int = 4,
    embed_model_name: str = "all-MiniLM-L6-v2",
) -> List[Dict[str, Any]]:
    """
    Retrieve top_k chunks for the given query.

    Steps:
      1) Embed query
      2) Normalize query embedding
      3) FAISS search => scores + ids
      4) Return chunk dicts + score

    Returns:
      list of dicts like:
        {"score": float, "chunk_id": int, "source": str, "text": str}
    """
    q_emb = embed_texts([query], model_name=embed_model_name).astype("float32")
    faiss.normalize_L2(q_emb)

    scores, ids = index.search(q_emb, top_k)

    results: List[Dict[str, Any]] = []
    for score, idx in zip(scores[0], ids[0]):
        if idx == -1:
            continue
        row = chunks[int(idx)]
        results.append(
            {
                "score": float(score),
                "chunk_id": row["chunk_id"],
                "source": row["source"],
                "text": row["text"],
            }
        )

    return results