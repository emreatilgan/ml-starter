from __future__ import annotations

import argparse
import os
from typing import Any, Dict, List

import gradio as gr

from mcp_server.tools.list_items import list_items as tool_list_items
from mcp_server.tools.semantic_search import semantic_search as tool_semantic_search
from mcp_server.tools.get_code import get_code as tool_get_code

def create_gradio_blocks() -> gr.Blocks:
    """
    Build a Gradio UI that, when launched with mcp_server=True, exposes a remote MCP server
    at: http://<host>:<port>/gradio_api/mcp/sse

    Tools exposed (via function signatures and docstrings):
      - list_items()
      - semantic_search(problem_markdown: str)
      - get_code(path: str)

    Polished UI/UX:
      - Themed interfaces, custom CSS, clear titles and descriptions
      - Curated examples for Semantic Search and Get Code
      - Helpful hero/guide text on the List Items tab
    """

    # Lightweight custom CSS for a more polished look
    custom_css = """
    :root {
        --radius-md: 12px;
        --shadow-md: 0 6px 24px rgba(0,0,0,.08);
        --color-accent: #3B82F6; /* Blue 500 */
        --color-accent-hover: #2563EB; /* Blue 600 */
        --color-accent-soft: rgba(59,130,246,.15);
        --link-text-color: #3B82F6;
    }
    .gradio-container { max-width: 1120px !important; margin: 0 auto; }

    /* Buttons and controls -> blue accent */
    .gr-button {
        border-radius: 12px;
        box-shadow: var(--shadow-md);
        background: var(--color-accent) !important;
        color: #fff !important;
        border: 1px solid transparent !important;
    }
    .gr-button:hover { background: var(--color-accent-hover) !important; }
    .gr-button:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }

    /* Tabs -> blue accent on active/hover */
    .gr-tabs .tab-nav button[aria-selected="true"] {
        border-bottom: 2px solid var(--color-accent) !important;
        color: var(--color-accent) !important;
    }
    .gr-tabs .tab-nav button:hover { color: var(--color-accent) !important; }

    /* Examples (chips/buttons) */
    .gr-examples button, .examples button {
        border-color: var(--color-accent) !important;
        color: var(--color-accent) !important;
        background: transparent !important;
    }
    .gr-examples button:hover, .examples button:hover {
        background: var(--color-accent-soft) !important;
    }

    .gr-textbox textarea {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }
    h1, .prose h1 {
        background: linear-gradient(90deg, #60A5FA, #22D3EE, #1D4ED8);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    a, .prose a { color: var(--link-text-color) !important; }
    .prose p, .prose li { font-size: 15px; line-height: 1.65; }
    """

    def list_items() -> List[Dict[str, Any]]:
        """
        List all knowledge base items.

        Returns:
            A JSON-serializable list of items, each with:
              id (str): '<category>/<filename>.py'
              category (str)
              filename (str)
              path (str): 'knowledge_base/<category>/<filename>.py'
              summary (str): Docstring or first non-empty line
        """
        return tool_list_items()

    def semantic_search(problem_markdown: str) -> Dict[str, Any]:
        """
        Semantic search over the knowledge base.

        Args:
            problem_markdown: Markdown text describing the task/problem.

        Returns:
            {
              "best_match": {
                  "id": str,
                  "category": str,
                  "filename": str,
                  "path": str,
                  "summary": str
                },
              "score": float  # cosine similarity in [-1, 1]
            }
        """
        return tool_semantic_search(problem_markdown)

    def get_code(path: str) -> str:
        """
        Return the full Python source code for a KB file.

        Args:
            path: Either 'knowledge_base/<category>/<file>.py' or '<category>/<file>.py'

        Returns:
            UTF-8 Python source as a string.
        """
        return tool_get_code(path)

    # Curated examples for a smoother first-run UX
    search_examples = [
        "I want to fine-tune a transformer for sentiment classification.",
        "Train a GNN on citation networks for node classification.",
        "Image generation with GANs; how to stabilize training?",
    ]
    code_examples = [
        "knowledge_base/nlp/text_classification_with_transformer.py",
        "knowledge_base/graph/gnn_citations.py",
        "knowledge_base/generative/dcgan_overriding_train_step.py",
    ]

    hero_md = """
# 🚀 ML Starter MCP Server & UI

Meet your AI knowledge base copilot. This app does two things:
1) A visual UI to explore the ML knowledge base.
2) A remote MCP server that lets any MCP-compatible client call the same tools programmatically.

What is MCP?
- The Model Context Protocol (MCP) is an open standard for tools your AI can call. This server exposes three tools over SSE so IDEs/agents can use them as if they were built-ins.

What you can do here:
- 📚 Browse Items — see everything in the knowledge base with quick summaries.
- 🔎 Semantic Search — paste your problem; get the best matching recipe + similarity score.
- 💻 Get Code — fetch the exact Python file so you can copy/paste or adapt it.

How it works under the hood:
- We build sentence-embedding vectors for every item and do cosine similarity search.
- Each item includes id, category, path, and a summary derived from docstrings or first lines.
- The remote endpoint is available at /gradio_api/mcp/sse when this app is running.

Quickstart:
1) Go to “🔎 Semantic Search”, describe your task, and submit.
2) Copy the returned path.
3) Open “💻 Get Code”, paste the path, and retrieve the full source.
4) If you want to see all options first, try “📚 List Items”.

Tip: You can run this UI locally or on Spaces. Clients can connect to the MCP endpoint to call list_items(), semantic_search(), and get_code().
"""

    search_article = """
🧭 How to use
1) Describe your task with as much signal as possible (dataset, modality, constraints, target metric).
2) Click Submit or pick an example. We compute embeddings and retrieve the closest KB match.
3) Copy the 'path' value and open it in the “💻 Get Code” tab to view the full source.

🧠 Notes
- Markdown is supported. Bullet points and short snippets help a lot.
- Similarity uses cosine distance on L2‑normalized sentence-transformer embeddings.
    """
    code_article = """
Paste a valid knowledge base path to fetch the full Python source.

📌 Examples
- knowledge_base/nlp/text_classification_with_transformer.py
- nlp/text_classification_with_transformer.py

💡 Tips
- Accepts both absolute KB paths and '<category>/<file>.py'.
- The code block is copy-friendly for quick reuse.
    """

    list_ui = gr.Interface(
        fn=list_items,
        inputs=None,
        outputs=gr.JSON(label="📦 Items (JSON)"),
        title="📚 Machine Learning Starter",
        description="Explore every ML Starter KB entry — id, category, path, and summary.",
        article="",
    )

    search_ui = gr.Interface(
        fn=semantic_search,
        inputs=gr.Textbox(
            lines=10,
            label="✍️ Describe your problem (Markdown supported)",
            placeholder="e.g., Fine-tune a transformer for sentiment classification on IMDB (dataset, goal, constraints)"
        ),
        outputs=gr.JSON(label="🏆 Best match + similarity score"),
        title="🔎 Semantic Search",
        description="Paste your task. We compute embeddings and return the closest KB recipe with a score.",
        examples=search_examples,
        article=search_article,
    )

    code_ui = gr.Interface(
        fn=get_code,
        inputs=gr.Textbox(
            lines=1,
            label="📄 KB file path",
            placeholder="knowledge_base/nlp/text_classification_with_transformer.py"
        ),
        outputs=gr.Code(label="🧩 Python source", language="python"),
        title="💻 Get Code",
        description="Paste a KB path and copy the exact source into your project.",
        examples=code_examples,
        article=code_article,
    )

    # Compose top-level layout: explanation on top, tabs below
    with gr.Blocks() as blocks:
        gr.HTML(f"<style>{custom_css}</style>")
        gr.Markdown(hero_md)
        with gr.Tabs():
            with gr.Tab("📚 List Items"):
                list_ui.render()
            with gr.Tab("🔎 Semantic Search"):
                search_ui.render()
            with gr.Tab("💻 Get Code"):
                code_ui.render()
    return blocks


def main() -> None:
    """
    Entry point: Launch Gradio UI and expose remote MCP over SSE at /gradio_api/mcp/sse
    """
    parser = argparse.ArgumentParser(description="ML Starter MCP Server (Gradio Remote Only)")
    parser.add_argument("--host", default="127.0.0.1", help="Host for Gradio")
    parser.add_argument("--port", type=int, default=7860, help="Port for Gradio")
    args = parser.parse_args()

    # Derive host/port from environment for Hugging Face Spaces and containers
    env_host = os.getenv("GRADIO_SERVER_NAME") or os.getenv("HOST") or args.host
    env_port_str = os.getenv("GRADIO_SERVER_PORT") or os.getenv("PORT")
    env_port = int(env_port_str) if env_port_str and env_port_str.isdigit() else args.port

    # If running on HF Spaces, bind to 0.0.0.0 unless explicitly overridden
    if os.getenv("SPACE_ID") and env_host in ("127.0.0.1", "localhost"):
        env_host = "0.0.0.0"

    blocks = create_gradio_blocks()
    blocks.launch(server_name=env_host, server_port=env_port, mcp_server=True)


if __name__ == "__main__":
    main()