from __future__ import annotations

import argparse
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

    list_ui = gr.Interface(
        fn=list_items,
        inputs=None,
        outputs=gr.JSON(label="items"),
        title="list_items",
        description="List all KB items"
    )

    search_ui = gr.Interface(
        fn=semantic_search,
        inputs=gr.Textbox(lines=8, label="problem_markdown"),
        outputs=gr.JSON(label="result"),
        title="semantic_search",
        description="Return single best match and cosine score"
    )

    code_ui = gr.Interface(
        fn=get_code,
        inputs=gr.Textbox(lines=1, label="path"),
        outputs=gr.Code(label="code", language="python"),
        title="get_code",
        description="Fetch full Python source for a KB file"
    )

    return gr.TabbedInterface(
        [list_ui, search_ui, code_ui],
        tab_names=["list_items", "semantic_search", "get_code"]
    )


def main() -> None:
    """
    Entry point: Launch Gradio UI and expose remote MCP over SSE at /gradio_api/mcp/sse
    """
    parser = argparse.ArgumentParser(description="KB Retrieval MCP Server (Gradio Remote Only)")
    parser.add_argument("--host", default="127.0.0.1", help="Host for Gradio")
    parser.add_argument("--port", type=int, default=7860, help="Port for Gradio")
    args = parser.parse_args()

    blocks = create_gradio_blocks()
    blocks.launch(server_name=args.host, server_port=args.port, mcp_server=True)


if __name__ == "__main__":
    main()