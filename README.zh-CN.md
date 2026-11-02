# KnowledgeBase

**与文档对话，追溯回答来源。**

[English](README.md) | **简体中文**

面向个人的知识库，支持 TXT、Markdown 和数字生成的 PDF。上传文档后即可提问，
通过引用查看原文片段或 PDF 原始页面。提供 Web 界面、命令行和 HTTP API。

## 核心功能

- **带来源的回答** — 流式显示回答，点击引用即可查看对应的原文片段。
- **混合检索** — 结合关键词搜索与向量搜索，通过父子分块保留上下文，并支持可选的本地重排序。
- **连续对话** — 支持追问，刷新页面后可恢复已完成的对话。
- **多步检索** — 开启 **Plan complex questions**，将复杂问题拆分为多次搜索，并在需要时补充检索证据。

技术栈：**Python · FastAPI · React · TypeScript · Chroma · SQLite**。

## 快速开始

需要 macOS 或 Linux、Python 3.13+、Node.js 22.13+、[uv](https://docs.astral.sh/uv/getting-started/installation/) 和 Make。

```bash
git clone https://github.com/Shengyuan-Liu/KnowledgeBase.git
cd KnowledgeBase
uv sync --locked --extra pdf
npm --prefix frontend ci
test -f .env || cp .env.example .env
```

**使用 PDF 前**，请先下载一次解析模型：

```bash
uv run --locked --extra pdf docling-tools models download layout tableformer --output-dir data/pdf-models
```

在 `.env` 中设置 `OPENAI_API_KEY`，然后启动应用：

```bash
make app
```

打开 [http://127.0.0.1:8000](http://127.0.0.1:8000)，上传文档，等待状态变为
**Ready** 后即可提问。点击回答中的引用可查看来源。

应用面向本地单用户使用，不含身份认证，数据默认保存在 `data/v1/`。
向量嵌入和回答生成会调用配置的 OpenAI API，并产生服务商费用。
PDF 支持数字生成的文本和可解析的表格结构，暂不支持 OCR、图表解读和数学公式理解。

## 文档

以下详细文档目前为英文：

- [配置说明](docs/configuration.md) · [PDF 设置与限制](docs/pdf-integration.md)
- [项目架构](docs/project-structure.md) · [前端开发](docs/frontend.md)
- [HTTP API](docs/chat-api.md) · [流式 API](docs/chat-streaming.md)
- [评估方法](evals/README.md) · [版本说明](docs/v2/release-summary.md)
- [完整文档](docs/README.md)
