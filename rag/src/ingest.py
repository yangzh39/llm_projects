import glob
import os
from typing import List, Tuple


def load_text_files(data_dir: str) -> List[Tuple[str, str]]:
    """
    Load all .txt files in data_dir.

    Returns:
        List of tuples: (source_name, full_text)

    Notes:
        - "source_name" is usually the filename. We keep it for citations/debugging.
        - This is the ingestion stage of RAG.
    """
    pattern = os.path.join(data_dir, "*.txt")
    paths = sorted(glob.glob(pattern))

    docs: List[Tuple[str, str]] = []
    for p in paths:
        with open(p, "r", encoding="utf-8") as f:
            text = f.read()
        source_name = os.path.basename(p)
        docs.append((source_name, text))

    return docs