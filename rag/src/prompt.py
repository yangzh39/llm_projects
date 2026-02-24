from typing import Any, Dict, List


def build_grounded_user_message(question: str, hits: List[Dict[str, Any]]) -> str:
    """
    Build the USER message content that includes:
      - The question
      - The retrieved context snippets

    We keep SYSTEM instructions separate in llm.py/app.py.

    The chunk labels [1], [2], ... let you cite in the answer.
    """
    if not hits:
        context = "(no context retrieved)"
    else:
        blocks = []
        for i, h in enumerate(hits, start=1):
            blocks.append(
                f"[{i}] source={h['source']} chunk_id={h['chunk_id']} score={h['score']:.3f}\n"
                f"{h['text']}"
            )
        context = "\n\n".join(blocks)

    return (
        f"Question:\n{question}\n\n"
        f"Context (use ONLY this context to answer):\n{context}\n\n"
        "Answer with citations like [1], [2] where relevant."
    )


def default_system_message() -> str:
    """
    System prompt to reduce hallucinations for a learning RAG setup.
    """
    return (
        "You are a helpful assistant.\n"
        "Answer ONLY using the provided context.\n"
        "If the context does not contain the answer, say: \"I don't know based on the provided context.\""
    )