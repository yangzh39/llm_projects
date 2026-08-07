# LLM Projects

Independent learning projects for LLM applications, retrieval, agents, and evaluation. Each project contains its own setup instructions, dependencies, environment template, and ignore rules.

## Projects

- [`fraud_block_agent_demo/`](fraud_block_agent_demo/) — an educational agentic-AI workflow with a browser chat interface, fictional banking data, deterministic safety controls, and an evaluation benchmark.

- [`rag/`](rag/) — a minimal retrieval-augmented generation chatbot using local football-rule documents and deterministic keyword retrieval.

Open a project folder and follow its README. No repository-wide Python environment or dependency installation is required.

## Check out one project only

Git normally clones a repository rather than an individual folder. Use sparse checkout when you want only one project in your working tree:

```bash
git clone --filter=blob:none --sparse https://github.com/yangzh39/llm_projects.git
cd llm_projects
git sparse-checkout set fraud_block_agent_demo
```

Replace `fraud_block_agent_demo` with `rag` to check out the RAG project instead.
