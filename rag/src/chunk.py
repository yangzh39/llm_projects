from typing import List


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
    """
    Split text into overlapping chunks (character-based).

    Why chunking:
      - Retrieval works better with smaller passages than whole documents.
      - LLM context is limited; chunking allows selecting only relevant parts.

    Args:
      chunk_size: max characters per chunk (simple and predictable)
      overlap: repeated characters between chunks to reduce boundary information loss

    Returns:
      List[str] chunks
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be < chunk_size")

    chunks: List[str] = []
    start = 0
    n = len(text)

    while start < n:
        end = min(n, start + chunk_size)
        chunks.append(text[start:end])

        if end == n:
            break

        start = end - overlap

    return chunks