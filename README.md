# KnowledgeBase

**Chat with your documents, with sources you can inspect.**

**English** | [简体中文](README.zh-CN.md)

A personal knowledge base for TXT, Markdown, and digital PDFs. Upload your files,
ask questions, and follow citations back to the original text or PDF page.
Available through a web interface, CLI, and HTTP API.

## Features

- **Answers with sources** — Stream responses and inspect the excerpts behind each citation.
- **Hybrid search** — Combine keyword and vector search, with parent-child chunks that retain surrounding context and optional local reranking.
- **Follow-up conversations** — Ask follow-up questions and restore completed conversations after a refresh.
- **Multi-step retrieval** — Enable **Plan complex questions** to break a question into searches and retrieve additional evidence when needed.

Built with **Python · FastAPI · React · TypeScript · Chroma · SQLite**.

## Quick start

Requires macOS or Linux, Python 3.13+, Node.js 22.13+, [uv](https://docs.astral.sh/uv/getting-started/installation/), and Make.

```bash
git clone https://github.com/Shengyuan-Liu/KnowledgeBase.git
cd KnowledgeBase
uv sync --locked --extra pdf
npm --prefix frontend ci
test -f .env || cp .env.example .env
```

**For PDFs**, download the parsing models once before uploading:

```bash
uv run --locked --extra pdf docling-tools models download layout tableformer --output-dir data/pdf-models
```

Set `OPENAI_API_KEY` in `.env`, then start the app:

```bash
make app
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000), upload a document, wait for
**Ready**, and ask your first question. Click a citation to view its source.

The app runs locally for a single user, without authentication. Data is saved in
`data/v1/` by default. Embedding and answer generation use the configured OpenAI API
and incur provider charges. PDF support covers digitally generated text and supported
table structures; OCR, chart interpretation, and formula understanding are not included.

## Documentation

- [Configuration](docs/configuration.md) · [PDF setup and limitations](docs/pdf-integration.md)
- [Architecture](docs/project-structure.md) · [Frontend development](docs/frontend.md)
- [HTTP API](docs/chat-api.md) · [Streaming API](docs/chat-streaming.md)
- [Evaluation](evals/README.md) · [Release notes](docs/v2/release-summary.md)
- [All documentation](docs/README.md)
