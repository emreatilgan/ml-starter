from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import List, Sequence, Tuple, Optional

import numpy as np

# Determinism knobs
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

try:
    import torch  # type: ignore
except Exception:  # pragma: no cover
    torch = None  # type: ignore

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "sentence-transformers is required. Add it to requirements.txt and install."
    ) from e


DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _set_deterministic(seed: int = 42) -> None:
    """Best-effort determinism across numpy and torch."""
    np.random.seed(seed)
    if torch is not None:
        try:
            torch.manual_seed(seed)
            torch.use_deterministic_algorithms(True)  # type: ignore[attr-defined]
        except Exception:
            # Older PyTorch or restricted envs
            pass


def _l2_normalize(arr: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms = np.maximum(norms, eps)
    return arr / norms


@dataclass(frozen=True)
class IndexedItem:
    """Holds the minimal info needed by the search index."""
    id: str
    category: str
    filename: str
    path: str  # relative to project root
    summary: str


class Embedder:
    """
    Thin wrapper around SentenceTransformer to produce normalized embeddings.
    Thread-safe, lazily initialized, deterministic.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL, device: Optional[str] = None, seed: int = 42):
        self.model_name = model_name
        self.device = device
        self.seed = seed
        self._model: Optional[SentenceTransformer] = None
        self._lock = threading.Lock()
        _set_deterministic(self.seed)

    def _ensure_model(self) -> SentenceTransformer:
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is None:
                self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model  # type: ignore[return-value]

    def embed(self, texts: Sequence[str], batch_size: int = 64) -> np.ndarray:
        """
        Embed a list of strings into a 2D numpy array (N, D), L2-normalized.
        """
        if not texts:
            return np.zeros((0, 384), dtype=np.float32)  # model dim for MiniLM
        model = self._ensure_model()
        vecs = model.encode(
            list(texts),
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=False,
            show_progress_bar=False,
        )
        if not isinstance(vecs, np.ndarray):
            vecs = np.array(vecs)
        vecs = vecs.astype(np.float32, copy=False)
        return _l2_normalize(vecs)

    def embed_one(self, text: str) -> np.ndarray:
        return self.embed([text])[0:1]


class EmbeddingIndex:
    """
    In-memory embedding index for KB items using cosine similarity.

    - Stores L2-normalized item vectors in a (N, D) float32 matrix.
    - search(query) computes normalized query vector and returns argmax cosine.
    """

    def __init__(self, embedder: Embedder):
        self.embedder = embedder
        self.items: List[IndexedItem] = []
        self.matrix: Optional[np.ndarray] = None  # (N, D), float32, normalized
        self.dim: Optional[int] = None

    def build(self, items: Sequence[IndexedItem], texts: Sequence[str]) -> None:
        if len(items) != len(texts):
            raise ValueError("items and texts must have the same length")
        if not items:
            # Empty index
            self.items = []
            self.matrix = np.zeros((0, 1), dtype=np.float32)
            self.dim = 1
            return
        vecs = self.embedder.embed(texts)
        self.items = list(items)
        self.matrix = vecs  # already L2-normalized
        self.dim = int(vecs.shape[1])

    def is_built(self) -> bool:
        return self.matrix is not None and self.items is not None

    def search_one(self, query_text: str) -> Tuple[IndexedItem, float]:
        """
        Return (best_item, best_score) where score is cosine similarity in [ -1, 1 ].
        """
        if self.matrix is None or len(self.items) == 0:
            raise RuntimeError("Index is empty. Build the index before searching.")
        q = self.embedder.embed_one(query_text)  # (1, D), normalized
        # Cosine for normalized vectors reduces to dot product
        sims = (q @ self.matrix.T).astype(np.float32)  # (1, N)
        best_idx = int(np.argmax(sims, axis=1)[0])
        best_score = float(sims[0, best_idx])
        return self.items[best_idx], best_score

    def search_topk(self, query_text: str, k: int = 5) -> List[Tuple[IndexedItem, float]]:
        if self.matrix is None or len(self.items) == 0:
            raise RuntimeError("Index is empty. Build the index before searching.")
        k = max(1, min(k, len(self.items)))
        q = self.embedder.embed_one(query_text)
        sims = (q @ self.matrix.T).astype(np.float32).ravel()
        topk_idx = np.argpartition(-sims, kth=k - 1)[:k]
        # sort exact top-k
        topk_sorted = sorted(((int(i), float(sims[int(i)])) for i in topk_idx), key=lambda t: -t[1])
        return [(self.items[i], score) for i, score in topk_sorted]