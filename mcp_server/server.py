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

    # Theme and lightweight custom CSS for a more polished look
    theme = None
    try:
        import gradio.themes as gt  # type: ignore
        theme = gt.Soft() if hasattr(gt, "Soft") else None
    except Exception:
        theme = None
    custom_css = """
    :root { --radius-md: 10px; }
    .gradio-container { max-width: 1100px !important; margin: 0 auto; }
    .gr-button { border-radius: 10px; }
    .gr-textbox textarea {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }
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
# ML Starter MCP

Use semantic search to find the most relevant knowledge base example, then open the code.

Tips:
- After getting a result in Semantic Search, copy the 'path' field and open it in the Get Code tab.
- You can also browse all items on this page below.
"""

    search_article = """
Steps:
1) Describe your task in detail (dataset, modality, goal).
2) Click Submit or choose an example. We will return the best KB match + score.
3) Copy the 'path' and paste it into the Get Code tab to open the file.

Notes:
- Input supports Markdown; feel free to paste bullets or short snippets.
- Scores are cosine similarity on L2-normalized Sentence-Transformer embeddings.
"""
    code_article = """
Paste a valid KB file path (from List Items or Semantic Search) to fetch full source.

Hints:
- Accepts either 'knowledge_base/<category>/<file>.py' or '<category>/<file>.py'
- You can copy directly from the rendered code block.
"""

    list_ui = gr.Interface(
        fn=list_items,
        inputs=None,
        outputs=gr.JSON(label="Items"),
        title="Browse Knowledge Base",
        description="List all KB items with minimal metadata.",
        article=hero_md,
    )

    search_ui = gr.Interface(
        fn=semantic_search,
        inputs=gr.Textbox(
            lines=10,
            label="Describe your problem (Markdown supported)",
            placeholder="E.g., Fine-tune a transformer for sentiment classification on IMDB"
        ),
        outputs=gr.JSON(label="Best match and score"),
        title="Semantic Search",
        description="Return a single best match from the KB and cosine similarity score.",
        examples=search_examples,
        article=search_article,
    )

    code_ui = gr.Interface(
        fn=get_code,
        inputs=gr.Textbox(
            lines=1,
            label="KB file path",
            placeholder="knowledge_base/nlp/text_classification_with_transformer.py"
        ),
        outputs=gr.Code(label="Python source", language="python"),
        title="Open Code",
        description="Fetch the full Python source for a KB file.",
        examples=code_examples,
        article=code_article,
    )

    # Return a single TabbedInterface to avoid duplicate renders
    return gr.TabbedInterface(
        [list_ui, search_ui, code_ui],
        tab_names=["List Items", "Semantic Search", "Get Code"],
    )


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