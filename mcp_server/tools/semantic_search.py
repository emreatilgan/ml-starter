from __future__ import annotations

from typing import Dict, Tuple, List

from mcp_server.loader import get_items_for_embedding, get_embedding_text
from mcp_server.embeddings import Embedder, EmbeddingIndex, IndexedItem


__all__ = ["semantic_search"]

# Lazy singletons
_embedder: Embedder | None = None
_index: EmbeddingIndex | None = None
_built: bool = False


def _ensure_index() -> EmbeddingIndex:
    global _embedder, _index, _built
    if _embedder is None:
        _embedder = Embedder()
    if _index is None:
        _index = EmbeddingIndex(_embedder)
    if not _built:
        pairs = get_items_for_embedding()  # List[ (KBItem, text) ]
        items: List[IndexedItem] = [
            IndexedItem(
                id=it.id,
                category=it.category,
                filename=it.filename,
                path=it.path,
                summary=it.summary,
            )
            for it, _ in pairs
        ]
        texts: List[str] = [get_embedding_text(it) for it, _ in pairs]
        _index.build(items, texts)
        _built = True
    return _index


def semantic_search(problem_markdown: str) -> Dict:
    """
    Return only the best match and its score.
    {
      "best_match": "knowledge_base/nlp/text_classification_with_transformer.py",
      "score": 0.89
    }
    """
    if not isinstance(problem_markdown, str) or not problem_markdown.strip():
        raise ValueError("problem_markdown must be a non-empty string")
    index = _ensure_index()
    best_item, score = index.search_one(problem_markdown)
    return {
        "best_match": best_item,
        "score": round(float(score), 6),
    }