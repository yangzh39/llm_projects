import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import requests
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
SYSTEM_PROMPT = (
    "You answer questions using only the provided context from the local football policy notes. "
    "If the answer is not supported by the context, say you do not know based on the docs."
)


@dataclass
class Chunk:
    source: str
    text: str
    tokens: Counter[str]


def load_env() -> tuple[str, str, str]:
    # Prefer this project's private configuration. The repository-root file is
    # retained only as a backward-compatible fallback for existing local users.
    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT.parent / ".env")
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip().rstrip("/")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is missing. Add it to rag/.env.")
    return api_key, base_url, model


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def split_into_chunks(text: str) -> Iterable[str]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    for block in blocks:
        yield block


def load_chunks() -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(DATA_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()
        for block in split_into_chunks(text):
            chunks.append(
                Chunk(
                    source=path.name,
                    text=block,
                    tokens=Counter(tokenize(block)),
                )
            )
    if not chunks:
        raise RuntimeError(f"No .txt files found in {DATA_DIR}")
    return chunks


def score_chunk(query_tokens: list[str], chunk: Chunk) -> tuple[int, int]:
    overlap = sum(min(chunk.tokens[token], 1) for token in query_tokens if token in chunk.tokens)
    return overlap, len(chunk.text)


def retrieve(query: str, chunks: list[Chunk], top_k: int = 3) -> list[Chunk]:
    query_tokens = tokenize(query)
    ranked = sorted(chunks, key=lambda chunk: score_chunk(query_tokens, chunk), reverse=True)
    return [chunk for chunk in ranked[:top_k] if score_chunk(query_tokens, chunk)[0] > 0]


def build_user_prompt(question: str, matches: list[Chunk]) -> str:
    context = "\n\n".join(f"[Source: {chunk.source}]\n{chunk.text}" for chunk in matches)
    return (
        f"Question:\n{question}\n\n"
        f"Context:\n{context}\n\n"
        "Answer the question using only the context above. Cite the source file names you used."
    )


def ask_deepseek(
    question: str,
    matches: list[Chunk],
    api_key: str,
    base_url: str,
    model: str,
) -> str:
    if not matches:
        return "I do not know based on the docs in rag/data."

    response = requests.post(
        f"{base_url}/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(question, matches)},
            ],
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["choices"][0]["message"]["content"].strip()


def main() -> None:
    api_key, base_url, model = load_env()
    chunks = load_chunks()

    print("Simple RAG chat ready. Ask a question about the docs in rag/data.")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("You: ").strip()
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            break

        matches = retrieve(question, chunks)
        answer = ask_deepseek(question, matches, api_key, base_url, model)

        print(f"\nAssistant:\n{answer}\n")
        print("Retrieved:")
        if not matches:
            print("  No matching docs found.\n")
            continue

        for index, chunk in enumerate(matches, start=1):
            preview = " ".join(chunk.text.split())
            if len(preview) > 120:
                preview = preview[:117] + "..."
            print(f"  [{index}] {chunk.source}: {preview}")
        print("")


if __name__ == "__main__":
    main()
