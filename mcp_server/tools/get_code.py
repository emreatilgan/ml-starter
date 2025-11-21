from __future__ import annotations

from mcp_server.loader import read_code


__all__ = ["get_code"]


def get_code(path: str) -> str:
    """
    Return full Python source code for a knowledge base file.

    Args:
        path: Either:
            - "knowledge_base/<category>/<file>.py"
            - "<category>/<file>.py"

    Raises:
        ValueError, FileNotFoundError per validation rules.

    Returns:
        The full UTF-8 text of the Python file.
    """
    return read_code(path)