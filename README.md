KB Retrieval MCP Server (Pure Retrieval)
=======================================

Overview
- Purpose: A pure retrieval Model Context Protocol (MCP) server that indexes your local ML knowledge base and exposes three read-only tools:
  - [python.list_items()](mcp_server/tools/list_items.py:11) – list all available KB items with metadata
  - [python.semantic_search()](mcp_server/tools/semantic_search.py:41) – given a markdown problem, return the single most relevant file (path + score)
  - [python.get_code()](mcp_server/tools/get_code.py:9) – fetch full Python source by path

- Scope: No data analysis, no CSV manipulation, no pipeline building, and no code generation. Deterministic, minimal API.

Remote MCP via Gradio (new)
- This project now exposes a remote MCP server over SSE via Gradio, in addition to the existing stdio and FastAPI HTTP surfaces.
- Gradio auto-generates the MCP schema from the function signatures and docstrings defined in [python.create_gradio_blocks()](mcp_server/server.py:80):
  - [python.gr_list_items()](mcp_server/server.py:93)
  - [python.gr_semantic_search()](mcp_server/server.py:107)
  - [python.gr_get_code()](mcp_server/server.py:122)

Run as a remote MCP server (recommended)
1) Install
   - pip install -r requirements.txt
2) Launch Gradio MCP
   - python -m mcp_server.server --mode gradio --host 127.0.0.1 --port 7860
3) Endpoint URL (MCP SSE)
   - http://127.0.0.1:7860/gradio_api/mcp/sse

VS Code Kilo Code MCP settings (remote URL)
Add or update your MCP settings file at:
- /Users/emreatilgan/Library/Application Support/Code/User/globalStorage/kilocode.kilo-code/settings/mcp_settings.json

Example configuration:
{
  "mcpServers": {
    "kb-retrieval-remote": {
      "url": "http://127.0.0.1:7860/gradio_api/mcp/sse",
      "disabled": false,
      "timeout": 60,
      "alwaysAllow": [],
      "disabledTools": []
    }
  }
}

Available tools (same behavior, now remote):
- list_items → lists all KB items
- semantic_search(problem_markdown: str) → returns best_match and score
- get_code(path: str) → returns full Python source

Other run modes
- FastAPI HTTP helpers: python -m mcp_server.server --mode http --host 127.0.0.1 --port 8000
  - App factory: [python.create_app()](mcp_server/server.py:37)
- Legacy local (stdio) MCP: python -m mcp_server.server --mode stdio
  - Stdio server: [python.create_mcp_server()](mcp_server/server.py:168)

Notes
- The SSE endpoint path is managed by Gradio and is fixed at /gradio_api/mcp/sse when launched with mcp_server=True.
- Docstrings drive the MCP tool descriptions. Update the docstrings in [python.create_gradio_blocks()](mcp_server/server.py:80) if you change inputs/outputs.
- This is still a pure-retrieval server; no side-effects or KB writes.
Knowledge Base
- Expected location: [knowledge_base/](knowledge_base/)
- Categories (directories):
  - audio/, generative/, graph/, nlp/, rl/, structured_data/, timeseries/, vision/
- Each subfolder contains many Python files (examples/tutorials)

Semantic Search
- Embedding model: sentence-transformers/all-MiniLM-L6-v2
- Similarity: cosine similarity on L2-normalized vectors (numpy)
- Embedding text per KB file:
  "{category}/{filename}: {docstring or first lines}"
- Returns only the single best match and its score.

Project Layout
- Core modules:
  - [mcp_server/server.py](mcp_server/server.py) – FastAPI entrypoints and MCP stdio server (FastMCP)
  - [mcp_server/loader.py](mcp_server/loader.py) – KB scanning, safe path resolution, code reading, summary extraction
  - [mcp_server/embeddings.py](mcp_server/embeddings.py) – Embedder wrapper and in-memory cosine index
  - Tools:
    - [mcp_server/tools/list_items.py](mcp_server/tools/list_items.py)
    - [mcp_server/tools/semantic_search.py](mcp_server/tools/semantic_search.py)
    - [mcp_server/tools/get_code.py](mcp_server/tools/get_code.py)
- Packaging helpers:
  - [mcp_server/__init__.py](mcp_server/__init__.py)
  - [mcp_server/tools/__init__.py](mcp_server/tools/__init__.py)
- Dependencies:
  - [requirements.txt](requirements.txt)

Install
1) Use Python 3.10+ (recommended 3.11+)
2) Create and activate a virtualenv
   - python3 -m venv .venv
   - source .venv/bin/activate
3) Install dependencies
   - pip install -r requirements.txt

Notes on PyTorch:
- sentence-transformers depends on PyTorch. If you need CPU-only:
  - pip install torch --index-url https://download.pytorch.org/whl/cpu
- Otherwise, the default pip install should fetch an appropriate wheel.

Quick Local HTTP Test (Optional)
This server also provides a minimal HTTP surface via FastAPI for quick manual tests.

Start FastAPI:
- uvicorn mcp_server.server:app --reload

Endpoints:
- GET /health
  - Response: {"status": "ok"}
- GET /list_items
  - Response: list of KB items with id/category/filename/path/summary
- POST /semantic_search
  - Body: {"problem_markdown": "I want to fine-tune a transformer for sentiment classification."}
  - Response example:
    {
      "best_match": "knowledge_base/nlp/text_classification_with_transformer.py",
      "score": 0.89
    }
- POST /get_code
  - Body: {"path": "knowledge_base/nlp/text_classification_with_transformer.py"}
  - Response: {"path": "...", "code": "<full file content>"}

MCP (Stdio) Server
The primary usage is as an MCP server over stdio.

Command:
- python -m mcp_server.server

Exposed Tools
- [python.list_items()](mcp_server/tools/list_items.py:11)
  - Returns:
    [
      {
        "id": "nlp/text_classification_with_transformer.py",
        "category": "nlp",
        "filename": "text_classification_with_transformer.py",
        "path": "knowledge_base/nlp/text_classification_with_transformer.py",
        "summary": "..."
      },
      ...
    ]
- [python.semantic_search()](mcp_server/tools/semantic_search.py:41)
  - Input:
    {
      "problem_markdown": "I want to fine-tune a transformer for sentiment classification."
    }
  - Output:
    {
      "best_match": "knowledge_base/nlp/text_classification_with_transformer.py",
      "score": 0.89
    }
- [python.get_code()](mcp_server/tools/get_code.py:9)
  - Input:
    {
      "path": "knowledge_base/nlp/text_classification_with_transformer.py"
    }
  - Output:
    "<full Python source code>"

Determinism
- Seeded numpy and torch (best-effort)
- TOKENIZERS_PARALLELISM disabled
- Pure retrieval only; no modifications to the knowledge base

KB Scanning and Safety
- Root discovery: project root inferred from [mcp_server/](mcp_server/)
- KB root: [knowledge_base/](knowledge_base/)
- Only .py files are indexed
- Safe path resolution ensures inputs point inside the KB and are Python files

Integrate With VS Code Kilo Code MCP Settings
Add an entry to your MCP settings located at:
- /Users/emreatilgan/Library/Application Support/Code/User/globalStorage/kilocode.kilo-code/settings/mcp_settings.json

Example configuration:
{
  "mcpServers": {
    "kb-retrieval": {
      "command": "python3",
      "args": ["-m", "mcp_server.server"],
      "env": {
      },
      "disabled": false,
      "timeout": 60,
      "alwaysAllow": [],
      "disabledTools": []
    }
  }
}

After saving, the system will detect the new server and expose tools:
- list_items
- semantic_search
- get_code

Usage Notes
- The server returns only existing KB files.
- Input to semantic_search should be a non-empty string; otherwise a 400/validation error is raised.
- get_code accepts both:
  - "knowledge_base/<category>/<file>.py"
  - "<category>/<file>.py"
- list_items returns minimal metadata including summary derived from module docstring or the first non-empty line.

Design Details
- Embedding construction in [mcp_server/embeddings.py](mcp_server/embeddings.py)
- Index build is lazy and cached on first semantic_search call
- Cosine similarity is implemented as dot product on L2-normalized vectors
- No FAISS dependency; numpy is sufficient for MVP

Troubleshooting
- Torch install issues:
  - Try CPU-only wheel: pip install torch --index-url https://download.pytorch.org/whl/cpu
- Permission/path issues:
  - Ensure you run from project root containing [knowledge_base/](knowledge_base/)
- Missing models:
  - First run downloads "sentence-transformers/all-MiniLM-L6-v2"

License
- Internal utility; no external distribution intended.

Attribution
- MCP server powered by Python MCP SDK (FastMCP) and FastAPI for optional HTTP testing surface.