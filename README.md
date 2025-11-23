ML Starter MCP Server (Gradio Remote Only)
===========================================

Overview
- Purpose: A pure retrieval Model Context Protocol (MCP) server that indexes your local ML knowledge base and exposes three read-only tools:
  - list_items – list all available KB items with metadata
  - semantic_search – given a markdown problem, return the single most relevant file (path + score)
  - get_code – fetch full Python source by path
- Scope: No data analysis, no CSV manipulation, no pipeline building, and no code generation. Deterministic, minimal API.

Run as a remote MCP server (only mode)
1) Install
   - pip install -r requirements.txt
2) Launch Gradio MCP
   - python -m mcp_server.server --host 127.0.0.1 --port 7860
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

Available tools
- list_items → lists all KB items
- semantic_search(problem_markdown: str) → returns best_match and score
- get_code(path: str) → returns full Python source

Notes
- The SSE endpoint path is managed by Gradio and is fixed at /gradio_api/mcp/sse when launched with mcp_server=True.
- Docstrings drive the MCP tool descriptions. Update the docstrings in create_gradio_blocks() if you change inputs/outputs.
- This is still a pure-retrieval server; no side-effects or KB writes.

Knowledge Base
- Expected location: knowledge_base/
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
  - mcp_server/server.py – Gradio remote MCP entrypoint and minimal UI wrappers
  - mcp_server/loader.py – KB scanning, safe path resolution, code reading, summary extraction
  - mcp_server/embeddings.py – Embedder wrapper and in-memory cosine index
  - Tools:
    - mcp_server/tools/list_items.py
    - mcp_server/tools/semantic_search.py
    - mcp_server/tools/get_code.py
- Packaging helpers:
  - mcp_server/__init__.py
  - mcp_server/tools/__init__.py
- Dependencies:
  - requirements.txt

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

Exposed Tools (MCP via SSE)
- list_items
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
- semantic_search
  - Input:
    {
      "problem_markdown": "I want to fine-tune a transformer for sentiment classification."
    }
  - Output:
    {
      "best_match": "knowledge_base/nlp/text_classification_with_transformer.py",
      "score": 0.89
    }
- get_code
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
- Root discovery: project root inferred from mcp_server/
- KB root: knowledge_base/
- Only .py files are indexed
- Safe path resolution ensures inputs point inside the KB and are Python files

Usage Notes
- The server returns only existing KB files.
- Input to semantic_search should be a non-empty string; otherwise validation error is raised.
- get_code accepts both:
  - "knowledge_base/<category>/<file>.py"
  - "<category>/<file>.py"
- list_items returns minimal metadata including summary derived from module docstring or the first non-empty line.

Design Details
- Embedding construction in mcp_server/embeddings.py
- Index build is lazy and cached on first semantic_search call
- Cosine similarity is implemented as dot product on L2-normalized vectors
- No FAISS dependency; numpy is sufficient for MVP

Troubleshooting
- Torch install issues:
  - Try CPU-only wheel: pip install torch --index-url https://download.pytorch.org/whl/cpu
- Permission/path issues:
  - Ensure you run from project root containing knowledge_base/
- Missing models:
  - First run downloads "sentence-transformers/all-MiniLM-L6-v2"

License
- Internal utility; no external distribution intended.

Attribution
- MCP server powered by Gradio’s MCP support and Sentence-Transformers for embeddings.

UI/UX polish (what you get out-of-the-box)
- Theming + CSS: Soft theme fallback with custom CSS for tighter visuals. See [python.create_gradio_blocks()](mcp_server/server.py:13) near the "Theme and lightweight custom CSS" section.
- Curated examples: Quick-start examples are prefilled for both Semantic Search and Get Code tabs to reduce first-run friction.
- Guided articles per tab:
  - Browse Knowledge Base includes a hero guide with tips.
  - Semantic Search and Open Code include mini “How-to” sections for clarity.
- Clear labeling, spacing, and consistent tone across tabs.
- Spaces-ready networking: The server auto-binds to 0.0.0.0 on Hugging Face Spaces to ensure external access. See [python.main()](mcp_server/server.py:159).

How the polished UI is structured
- Tabs (via [python.create_gradio_blocks()](mcp_server/server.py:13)):
  - "List Items" (Browse Knowledge Base)
    - Output: JSON list of items (id, category, filename, path, summary).
    - Article: Hero guide with tips for using the app end-to-end.
  - "Semantic Search"
    - Input: Markdown textbox (with examples).
    - Output: JSON containing the best match object and cosine score.
    - Article: Step-by-step instructions to go from query → code.
  - "Get Code"
    - Input: KB path textbox (with examples).
    - Output: Syntax-highlighted Python source.
    - Article: Path formatting hints and usage notes.

Hugging Face Spaces setup (recommended)
- Space type: Gradio (Python).
- Python version: 3.10+ (3.11 recommended).
- Hardware: CPU is sufficient (MiniLM model). For faster cold starts, consider persistent storage.
- requirements.txt already includes:
  - gradio[mcp]
  - sentence-transformers, numpy, torch, huggingface_hub
- Entry options:
  1) Minimal change (use your current entrypoint):
     - Spaces defaults require an app object (e.g., demo) in app.py.
     - To keep your CLI entrypoint, set a Custom Command in Space Settings to:
       - python -m mcp_server.server
  2) Conventional Gradio app.py (recommended for Spaces auto-discovery):
     - Create an app.py that exposes a demo object:
       - [python.create_gradio_blocks()](mcp_server/server.py:13) can be imported and used as:
         - demo = create_gradio_blocks()
- Environment variables (auto-handled but documented):
  - SPACE_ID: detected to bind 0.0.0.0 for external access.
  - PORT/GRADIO_SERVER_PORT: used if provided by Spaces.
  - HOST/GRADIO_SERVER_NAME: fallback to 0.0.0.0 on Spaces.
- Launch behavior:
  - [python.main()](mcp_server/server.py:159) reads environment and launches Gradio with mcp_server=True, exposing SSE at /gradio_api/mcp/sse.

Judging checklist (mapped to criteria)
- Completeness
  - Space: Deployed as Gradio app (via app.py or custom command).
  - Documentation: This README plus in-app articles on each tab.
  - Demo video: Record a short walkthrough showing:
    - Semantic search query → best match → path copied
    - Get Code → paste path → view code
    - Optional: Show MCP SSE URL in VS Code Kilo Code settings
  - Social post: See template below.
- Design / Polished UI-UX
  - Themed UI, curated examples, helpful articles, consistent labels, and spacing.
- Functionality (Gradio 6 + MCP)
  - Remote MCP server via SSE using Gradio’s mcp_server=True.
  - Three read-only tools exposed: list_items, semantic_search, get_code.
- Creativity
  - Focused retrieval assistant tailored for ML example discovery.
- Documentation
  - Clear instructions here and inline in the app.
- Real-world impact
  - Quickly locate canonical ML examples from a curated KB for faster prototyping.

Demo video storyboard (quick script)
- 1) Open the Space and explain the three tabs (10s).
- 2) On Semantic Search, select an example → show best match + score (20s).
- 3) Copy the path → switch to Get Code → paste → show source (20s).
- 4) Show List Items tab to demonstrate KB breadth (10s).
- 5) Mention SSE endpoint for MCP in VS Code Kilo Code and how to configure it (10s).

Social post template (edit to your tone)
- Title: "ML Starter MCP Server: Pure Retrieval over ML Examples via Gradio 6 + MCP"
- Body:
  - "Just shipped a pure-retrieval MCP server with Gradio 6. Browse a local ML knowledge base, semantic-search with MiniLM, and fetch code fast. Remote MCP exposed via SSE. Try the Space: <Space URL>"
  - Hashtags: #Gradio #MCP #AI #ML #NLP #ComputerVision #HuggingFace
- Media: Attach a 30–60s demo clip or GIF showing query → result → code.

Roadmap ideas (post-hackathon)
- List tab enhancements: add interactive filters and a table view.
- Search tab: optionally show top-k matches (UI only; keep public tool best-1 for scope).
- Code tab: add “Copy Path” and “Copy Code” buttons and basic syntax-aware formatting.
- Light/dark theme toggle with persisted preference.