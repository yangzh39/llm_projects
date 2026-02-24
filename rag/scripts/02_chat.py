import os
from pathlib import Path

from app import answer_question
from index import load_chunks, load_index
from llm import DeepSeekClient


def main():
    ROOT = Path(__file__).resolve().parents[1]  # .../llm/rag
    storage_dir = ROOT / "storage"
    index_path = storage_dir / "faiss.index"
    chunks_path = storage_dir / "chunks.json"

    index = load_index(str(index_path))
    chunks = load_chunks(str(chunks_path))

    client = DeepSeekClient()

    print("RAG chat ready. Type a question (or 'exit').\n")

    while True:
        q = input("You: ").strip()
        if not q:
            continue
        if q.lower() in {"exit", "quit"}:
            break

        answer, hits = answer_question(q, index=index, chunks=chunks, client=client, top_k=4)

        print("\nAssistant:\n", answer, "\n", sep="")

        # Show retrieval hits for learning/debugging
        print("Retrieved:")
        for i, h in enumerate(hits, start=1):
            print(f"  [{i}] {h['source']} (chunk_id={h['chunk_id']}, score={h['score']:.3f})")
        print("")


if __name__ == "__main__":
    main()