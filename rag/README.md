# Simple RAG Chatbot

This folder keeps only the source docs in `rag/data` and one minimal chatbot entrypoint.

## Run

From the repo root:

```bash
python3 rag/chat.py
```

The script:

- loads `.txt` files from `rag/data`
- splits them into simple text chunks
- retrieves the most relevant chunks with keyword overlap
- sends the retrieved context to DeepSeek using your existing `DEEPSEEK_API_KEY`

If the answer is not supported by the docs, it will say so.
