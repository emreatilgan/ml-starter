from __future__ import annotations

import ast
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Tuple

KB_DIRNAME = "knowledge_base"

@dataclass(frozen=True)
class KBItem:
    id: str
    category: str
    filename: str
    path: str
    summary: str

def project_root() -> Path:
    """Return project root (folder containing 'mcp_server' and 'knowledge_base')."""
    return Path(__file__).resolve().parent.parent

def kb_root() -> Path:
    """Return absolute path to knowledge_base directory."""
    return project_root() / KB_DIRNAME

def extract_docstring(p: Path) -> str:
    """Extract module docstring; fallback to first non-empty line if absent."""
    try:
        src = p.read_text(encoding="utf-8")
    except Exception:
        return ""
    try:
        module = ast.parse(src)
        doc = ast.get_docstring(module) or ""
        if doc:
            return " ".join(doc.strip().split())
        # fallback: first non-empty non-comment line
        for ln in src.splitlines():
            s = ln.strip()
            if s:
                return s[:300]
        return ""
    except Exception:
        return ""

def to_rel_path(p: Path) -> str:
    """Return path relative to project root for stable IDs."""
    try:
        return str(p.relative_to(project_root()))
    except Exception:
        return str(p)

def scan_knowledge_base() -> List[KBItem]:
    """Scan knowledge_base for Python examples and return KBItem list."""
    root = kb_root()
    if not root.exists():
        raise FileNotFoundError(f"Knowledge base folder not found: {root}")
    items: List[KBItem] = []
    for category_dir in sorted([d for d in root.iterdir() if d.is_dir()]):
        category = category_dir.name
        for py in sorted(category_dir.rglob("*.py")):
            filename = py.name
            rel_path = to_rel_path(py)
            summary = extract_docstring(py) or filename
            item_id = f"{category}/{filename}"
            items.append(
                KBItem(
                    id=item_id,
                    category=category,
                    filename=filename,
                    path=rel_path,
                    summary=summary,
                )
            )
    return items

# Simple in-process cache. Re-scan lazily on first access.
_ITEMS_CACHE: Optional[List[KBItem]] = None

def list_items_dict() -> List[dict]:
    """Return KB items as plain dicts suitable for JSON serialization."""
    global _ITEMS_CACHE
    if _ITEMS_CACHE is None:
        _ITEMS_CACHE = scan_knowledge_base()
    return [asdict(item) for item in _ITEMS_CACHE]

def get_embedding_text(item: KBItem) -> str:
    """Canonical string used for embedding a KB item."""
    head = (item.summary or "").strip()
    return f"{item.category}/{item.filename}: {head}"

def ensure_kb_path(path_str: str) -> Path:
    """
    Validate and resolve a path under knowledge_base.
    Accepts either:
      - 'knowledge_base/<category>/<file>.py'
      - '<category>/<file>.py'
    Raises if outside KB or not a Python file.
    """
    base = kb_root().resolve()
    # Normalize input
    candidate = Path(path_str)
    if not candidate.is_absolute():
        # Allow either direct rel to project root or category/file
        p1 = (project_root() / candidate).resolve()
        p2 = (base / candidate).resolve()
        # Prefer inside KB
        p = p1 if str(p1).startswith(str(base)) and p1.exists() else p2
    else:
        p = candidate.resolve()
    try:
        p.relative_to(base)
    except Exception:
        raise ValueError(f"Path is outside knowledge base: {path_str}")
    if not p.exists() or not p.is_file() or p.suffix != ".py":
        raise FileNotFoundError(f"KB file not found: {p}")
    return p

def read_code(path_str: str) -> str:
    """Read and return full source code of a KB file."""
    p = ensure_kb_path(path_str)
    return p.read_text(encoding="utf-8")

def get_items_for_embedding() -> List[Tuple[KBItem, str]]:
    """Return list of (KBItem, text) pairs for embedding."""
    global _ITEMS_CACHE
    if _ITEMS_CACHE is None:
        _ITEMS_CACHE = scan_knowledge_base()
    return [(it, get_embedding_text(it)) for it in _ITEMS_CACHE]