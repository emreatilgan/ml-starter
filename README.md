---
title: ML Starter MCP Server
emoji: 🧠
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: "5.49.1"
app_file: app.py
license: apache-2.0
pinned: true
short_description: Pure-retrieval MCP server that indexes the ML Starter knowledge base with deterministic semantics search.
tags:
  - building-mcp-track-enterprise
  - gradio
  - mcp
  - retrieval
  - embeddings
  - python
  - knowledge-base
  - semantic-search
  - sentence-transformers
  - huggingface
---

# ML Starter MCP Server
<p align="center">
  <img src="https://dummyimage.com/1000x180/020617/ffffff&text=ML+Starter+MCP+Server" height="90px" alt="ML Starter Banner">
</p>

Gradio-powered **remote-only** MCP server that exposes a curated ML knowledge base through deterministic, read-only tooling. Ideal for editors like Claude Desktop, VS Code (Kilo Code), or Cursor that want a trustworthy retrieval endpoint with **no side-effects**.

![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![License](https://img.shields.io/badge/license-Apache%202.0-green) ![Status](https://img.shields.io/badge/Status-Active-success) ![MCP](https://img.shields.io/badge/MCP-enabled-brightgreen) ![Retrieval](https://img.shields.io/badge/Retrieval-pure-lightgrey) ![SentenceTransformers](https://img.shields.io/badge/Embeddings-all--MiniLM--L6--v2-6f42c1)

---

## 🧩 Overview

The **ML Starter MCP Server** indexes the entire `knowledge_base/` tree (audio, vision, NLP, RL, etc.) and makes it searchable through:

* `list_items` – enumerate every tutorial/script with metadata.
* `semantic_search` – vector search over docstrings and lead context to find the single best code example for a natural-language brief.
* `get_code` – return the full Python source for a safe, validated path.

The server is deterministic (seeded numpy/torch), write-protected, and designed to run as a **Gradio MCP SSE endpoint** suitable for Hugging Face Spaces or on-prem deployments.

---

## 📚 ML Starter Knowledge Base

* Root: `knowledge_base/`
* Domains:
  * `audio/`
  * `generative/`
  * `graph/`
  * `nlp/`
  * `rl/`
  * `structured_data/`
  * `timeseries/`
  * `vision/`
* Each file stores a complete, runnable ML example with docstring summaries leveraged during indexing.

### Features exposed via MCP

* ✅ Vector search via `sentence-transformers/all-MiniLM-L6-v2` with cosine similarity.
* ⚙️ Safe path resolution ensures only in-repo `.py` files can be fetched.
* 🧮 Metadata-first outputs (category, filename, semantic score) for quick triage.
* 🛡️ Read-only contract; zero KB mutations, uploads, or side effects.
* 🌐 Spaces-ready networking with auto `0.0.0.0` binding when environment variables are provided by the platform.

---

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Running the MCP Server

```bash
python -m mcp_server.server --host 127.0.0.1 --port 7860
```

* **SSE Endpoint:** `http://127.0.0.1:7860/gradio_api/mcp/sse`
* Launch with `mcp_server=True` (handled by `mcp_server/server.py`).

### VS Code Kilo Code Settings

```json
{
  "mcpServers": {
    "ml-starter-kb": {
      "url": "http://127.0.0.1:7860/gradio_api/mcp/sse",
      "disabled": false,
      "timeout": 60,
      "alwaysAllow": [],
      "disabledTools": []
    }
  }
}
```

### Environment Variables

```bash
export TOKENIZERS_PARALLELISM=false
export PYTORCH_ENABLE_MPS_FALLBACK=1  # optional, improves macOS stability
```

---

## 🧠 MCP Usage

Any MCP-capable client can connect to the SSE endpoint to:

* Browse the full inventory of ML tutorials.
* Submit a markdown problem statement and receive the best-matching file path plus relevance score.
* Fetch the code immediately and render it inline (clients typically syntax-highlight the response).

The Gradio UI mirrors these capabilities via three tabs (List Items, Semantic Search, Get Code) for manual exploration.

---

## 🔤 Supported Embeddings

* `sentence-transformers/all-MiniLM-L6-v2`

### Configuration Example

```yaml
embedding_model: sentence-transformers/all-MiniLM-L6-v2
batch_size: 32
similarity: cosine
```

---

## 🔍 Retrieval Strategy

| Component            | Description                                                  |
|----------------------|--------------------------------------------------------------|
| Index Type           | In-memory cosine index backed by numpy vectors               |
| Chunking             | File-level (docstring + prefix)                              |
| Similarity Function  | Dot product on L2-normalized vectors                         |
| Results Returned     | Top-1 match (deterministic)                                  |
| Rerankers            | Not applicable (pure retrieval)                              |

### Configuration Example

```yaml
retriever: cosine
max_results: 1
```

---

## 🧩 Folder Structure

```
ml-starter/
├── app.py                  # Optional Gradio hook
├── mcp_server/
│   ├── server.py           # Remote MCP entrypoint & UI builder
│   ├── loader.py           # KB scanning + safe path resolution
│   ├── embeddings.py       # MiniLM wrapper + cosine index
│   └── tools/
│       ├── list_items.py   # list_items()
│       ├── semantic_search.py  # semantic_search()
│       └── get_code.py     # get_code()
├── knowledge_base/         # ML examples grouped by domain
├── requirements.txt
└── README.md
```

---

## 🔧 MCP Tools (`mcp_server/server.py`)

| MCP Tool       | Python Function                    | Description                                                                             |
|----------------|------------------------------------|-----------------------------------------------------------------------------------------|
| `list_items`   | `list_items()`                      | Enumerates every KB entry with category, filename, absolute path, and summary metadata. |
| `semantic_search` | `semantic_search(problem_markdown: str)` | Embeds the prompt and returns the single best match plus cosine score.                  |
| `get_code`     | `get_code(path: str)`              | Streams back the full Python source for a validated KB path.                            |

`server.py` registers these functions with Gradio's MCP adapter, wires docstrings into tool descriptions, and ensures the SSE endpoint stays read-only.

---

## 🎬 Demo

* Walk through the three tabs in Gradio (List Items → Semantic Search → Get Code).
* Copy the SSE URL into your MCP client and trigger each tool from within the editor.
* Optional: record a quick clip showing semantic query → best match → code inspection.

---

## 📥 Inputs

### 1. `list_items`

No input parameters; returns the entire catalog.

### 2. `semantic_search`

<details>
<summary>Input Model</summary>

| Field            | Type   | Description                                             | Example                                                         |
|------------------|--------|---------------------------------------------------------|-----------------------------------------------------------------|
| problem_markdown | str    | Natural-language description of the ML task or need.    | "I need a transformer example for multilingual NER."           |
</details>

### 3. `get_code`

<details>
<summary>Input Model</summary>

| Field | Type | Description                                   | Example                                              |
|-------|------|-----------------------------------------------|------------------------------------------------------|
| path  | str  | KB-relative or absolute path to a `.py` file. | "knowledge_base/nlp/text_classification_from_scratch.py" |
</details>

---

## 📤 Outputs

### 1. `list_items`

<details>
<summary>Response Example</summary>

```json
[
  {
    "id": "nlp/text_classification_with_transformer.py",
    "category": "nlp",
    "filename": "text_classification_with_transformer.py",
    "path": "knowledge_base/nlp/text_classification_with_transformer.py",
    "summary": "Fine-tune a Transformer for sentiment classification."
  }
]
```
</details>

### 2. `semantic_search`

<details>
<summary>Response Example</summary>

```json
{
  "best_match": "knowledge_base/nlp/text_classification_with_transformer.py",
  "score": 0.89
}
```
</details>

### 3. `get_code`

<details>
<summary>Response Example</summary>

```json
{
  "path": "knowledge_base/vision/grad_cam.py",
  "source": "<full Python source>"
}
```
</details>

Each response is deterministic for the same corpus and embeddings, allowing MCP clients to trust caching and diffing workflows.

---

## 🛠️ Next Steps

Today the knowledge base focuses on curated **Keras** walkthroughs. Upcoming updates will expand coverage to include:

* TensorFlow
* PyTorch 
* scikit-learn
* ...

These additions will land in the same deterministic retrieval flow, making mixed-framework discovery as seamless as the current experience.

---

## 📘 License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for full terms.

---

<p align="center">
  <sub>Built with ❤️ for the ML Starter knowledge base • Apache 2.0</sub>
</p>
