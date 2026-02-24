from typing import Any, Dict, List, Tuple

import faiss

from llm import DeepSeekClient
from prompt import build_grounded_user_message, default_system_message
from retrieve import retrieve_top_k


def answer_question(
    question: str,
    index: faiss.Index,
    chunks: List[Dict[str, Any]],
    client: DeepSeekClient,
    top_k: int = 4,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    High-level RAG call:
      1) retrieve relevant chunks
      2) build prompt/messages
      3) call DeepSeek
      4) return (answer_text, retrieval_hits)

    Keeping this function makes it easy to:
      - swap LLM providers later
      - add reranking later
      - add evaluation later
    """
    hits = retrieve_top_k(question, index=index, chunks=chunks, top_k=top_k)

    system = default_system_message()
    user = build_grounded_user_message(question, hits)

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    answer = client.chat(messages, temperature=0.2, max_tokens=350)
    return answer, hits