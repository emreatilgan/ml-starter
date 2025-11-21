from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import gradio as gr

# Tools (pure retrieval only)
from mcp_server.tools.list_items import list_items as tool_list_items
from mcp_server.tools.semantic_search import semantic_search as tool_semantic_search
from mcp_server.tools.get_code import get_code as tool_get_code

# Python MCP SDK (FastMCP) for stdio transport
try:
    from mcp.server.fastmcp import FastMCP
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "The 'mcp' Python package is required. Add it to requirements.txt and install."
    ) from e


# ----------------------------
# FastAPI HTTP surface (minimal)
# ----------------------------

class SearchRequest(BaseModel):
    problem_markdown: str


class CodeRequest(BaseModel):
    path: str


def create_app() -> FastAPI:
    app = FastAPI(title="KB Retrieval MCP (HTTP Surface)", version="0.1.0")

    @app.get("/health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/list_items")
    def http_list_items() -> List[Dict[str, Any]]:
        return tool_list_items()

    @app.post("/semantic_search")
    def http_semantic_search(req: SearchRequest) -> Dict[str, Any]:
        try:
            return tool_semantic_search(req.problem_markdown)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/get_code")
    def http_get_code(req: CodeRequest) -> Dict[str, Any]:
        try:
            code = tool_get_code(req.path)
            return {"path": req.path, "code": code}
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except FileNotFoundError as fe:
            raise HTTPException(status_code=404, detail=str(fe))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


# Expose FastAPI app for uvicorn if needed: `uvicorn mcp_server.server:app`
app = create_app()


# ----------------------------
# Gradio MCP (remote) surface
# ----------------------------

def create_gradio_blocks() -> gr.Blocks:
    """
    Build a Gradio UI that, when launched with mcp_server=True, exposes a remote MCP server
    at: http://<host>:<port>/gradio_api/mcp/sse

    Tools exposed (via function signatures and docstrings):
      - list_items()
      - semantic_search(problem_markdown: str)
      - get_code(path: str)
    """

    # Wrapper functions with rich docstrings for MCP schema generation

    def gr_list_items() -> List[Dict[str, Any]]:
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

    def gr_semantic_search(problem_markdown: str) -> Dict[str, Any]:
        """
        Semantic search over the knowledge base.

        Args:
            problem_markdown: Markdown text describing the task/problem.

        Returns:
            {
              "best_match": "knowledge_base/<category>/<file>.py",
              "score": float  # cosine similarity in [-1, 1]
            }
        """
        return tool_semantic_search(problem_markdown)

    def gr_get_code(path: str) -> str:
        """
        Return the full Python source code for a KB file.

        Args:
            path: Either 'knowledge_base/<category>/<file>.py' or '<category>/<file>.py'

        Returns:
            UTF-8 Python source as a string.
        """
        return tool_get_code(path)

    # Minimal UI surfaces for manual debugging; MCP clients use the SSE endpoint.
    list_ui = gr.Interface(
        fn=gr_list_items,
        inputs=None,
        outputs=gr.JSON(label="items"),
        title="list_items",
        description="List all KB items"
    )

    search_ui = gr.Interface(
        fn=gr_semantic_search,
        inputs=gr.Textbox(lines=8, label="problem_markdown"),
        outputs=gr.JSON(label="result"),
        title="semantic_search",
        description="Return single best match and cosine score"
    )

    code_ui = gr.Interface(
        fn=gr_get_code,
        inputs=gr.Textbox(lines=1, label="path"),
        outputs=gr.Code(label="code", language="python"),
        title="get_code",
        description="Fetch full Python source for a KB file"
    )

    return gr.TabbedInterface(
        [list_ui, search_ui, code_ui],
        tab_names=["list_items", "semantic_search", "get_code"]
    )

# ----------------------------
# MCP (stdio) server definition
# ----------------------------

def create_mcp_server() -> FastMCP:
    """
    Build a stdio-based MCP server exposing three tools:
      - list_items()
      - semantic_search(problem_markdown: str)
      - get_code(path: str)
    """
    mcp = FastMCP("kb-retrieval")

    @mcp.tool()
    def list_items() -> List[Dict[str, Any]]:
        """
        List all knowledge base items.
        Returns:
          [
            {
              "id": "nlp/text_classification_with_transformer.py",
              "category": "nlp",
              "filename": "text_classification_with_transformer.py",
              "path": "knowledge_base/nlp/text_classification_with_transformer.py",
              "summary": "...",
            },
            ...
          ]
        """
        return tool_list_items()

    @mcp.tool()
    def semantic_search(problem_markdown: str) -> Dict[str, Any]:
        """
        Retrieve the most relevant KB file for the given problem description.
        Args:
          problem_markdown: Markdown text describing the task.
        Returns:
          {
            "best_match": "knowledge_base/nlp/text_classification_with_transformer.py",
            "score": 0.89
          }
        """
        return tool_semantic_search(problem_markdown)

    @mcp.tool()
    def get_code(path: str) -> str:
        """
        Return the full Python source for a KB file.
        Args:
          path: Either 'knowledge_base/<cat>/<file>.py' or '<cat>/<file>.py'
        Returns:
          UTF-8 source code string.
        """
        return tool_get_code(path)

    return mcp


def main() -> None:
    """
    Entry point modes (default: Gradio remote MCP):
      - gradio (default): Launch Gradio UI and expose remote MCP over SSE at /gradio_api/mcp/sse
      - http:            Run FastAPI HTTP app (manual testing helpers)
      - stdio:           Run stdio-based MCP (legacy/local)
    """
    parser = argparse.ArgumentParser(description="KB Retrieval MCP Server")
    parser.add_argument(
        "--mode",
        choices=["gradio", "http", "stdio"],
        default="gradio",
        help="Run mode: gradio (remote MCP), http (FastAPI), or stdio (local MCP)"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for Gradio/FastAPI")
    parser.add_argument("--port", type=int, default=7860, help="Port for Gradio/FastAPI")
    args = parser.parse_args()

    if args.mode == "http":
        try:
            import uvicorn  # type: ignore
        except Exception as e:
            raise RuntimeError("uvicorn is required for --mode http. Add it to requirements.txt and install.") from e
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
        return

    if args.mode == "stdio":
        server = create_mcp_server()
        server.run()
        return

    # Gradio remote MCP (default)
    blocks = create_gradio_blocks()
    # Starts an HTTP server and an MCP SSE endpoint at /gradio_api/mcp/sse
    blocks.launch(server_name=args.host, server_port=args.port, mcp_server=True)

if __name__ == "__main__":
    main()