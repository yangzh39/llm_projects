import os
from pathlib import Path

from chunk import chunk_text
from embed import embed_texts
from index import build_faiss_index, prepare_chunks, save_chunks, save_index
from ingest import load_text_files


def main():
    ROOT = Path(__file__).resolve().parents[1]   # .../llm/rag
    data_dir = ROOT / "data"
    storage_dir = ROOT / "storage"
    index_path = storage_dir / "faiss.index"
    chunks_path = storage_dir / "chunks.json"

    docs = load_text_files(data_dir)
    if not docs:
        raise RuntimeError(f"No .txt files found in ./{data_dir}")

    # 1) Chunk docs (and keep metadata)
    chunk_rows = prepare_chunks(docs, chunk_fn=lambda t: chunk_text(t, chunk_size=800, overlap=150))

    # 2) Embed chunk texts
    texts = [r["text"] for r in chunk_rows]
    embeddings = embed_texts(texts)

    # 3) Build index
    index = build_faiss_index(embeddings)

    # 4) Save artifacts
    save_index(index, str(index_path))
    save_chunks(chunk_rows, str(chunks_path))

    print("✅ Built index and saved artifacts:")
    print(f" - {index_path}")
    print(f" - {chunks_path}")
    print(f"Chunks: {len(chunk_rows)}")


if __name__ == "__main__":
    main()