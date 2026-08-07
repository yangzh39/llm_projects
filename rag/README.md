# Simple RAG Chatbot

A self-contained educational retrieval-augmented generation project. It retrieves relevant passages from local football-rule documents and asks DeepSeek to answer using only that context.

## Setup

From the repository root, create an isolated environment for this project:

```bash
python3 -m venv rag/.venv
source rag/.venv/bin/activate
python -m pip install -r rag/requirements.txt
```

On Windows, activate the environment with `rag\.venv\Scripts\activate`.

Copy the safe configuration template and add your API key:

```bash
cp rag/.env.example rag/.env
```

```text
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

The private `rag/.env`, virtual environment, Python caches, and generated storage are excluded from Git.

## Run

```bash
python rag/chat.py
```

The script:

- loads `.txt` files from `rag/data`;
- splits them into paragraph-sized chunks;
- retrieves the most relevant chunks with deterministic keyword overlap;
- sends only the retrieved context and question to the configured DeepSeek model;
- cites the source filenames in the answer.

If the answer is not supported by the local documents, it says so.

## Project structure

```text
rag/
├── .env.example       # safe local configuration template
├── .gitignore         # project-specific secrets and generated files
├── requirements.txt   # minimal project dependencies
├── chat.py            # retrieval and model-calling entrypoint
└── data/               # local source documents
```
