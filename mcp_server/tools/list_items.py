from __future__ import annotations

from typing import List, Dict

from mcp_server.loader import list_items_dict


__all__ = ["list_items"]


def list_items() -> List[Dict]:
    """
    Return all KB items with minimal metadata:
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
    return list_items_dict()