"""Build the search index from data/kb/*.md.

Usage:  python -m src.ingest

Chunks each doc with a sliding word window (with overlap), keeps doc_id and
the current markdown section header in each chunk's metadata, embeds with
sentence-transformers, and saves a numpy index to data/index/.
"""

import re
from pathlib import Path

from sentence_transformers import SentenceTransformer

from src.config import load_config
from src.vector_store import VectorStore


def parse_doc(path: Path) -> tuple[dict, str]:
    """Split off the --- frontmatter block; return (meta, body)."""
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        raise ValueError(f"{path} is missing frontmatter")
    meta = dict(re.findall(r"^(\w+):\s*(.+)$", m.group(1), re.MULTILINE))
    return meta, m.group(2).strip()


def chunk_text(body: str, size: int, overlap: int) -> list[tuple[str, str]]:
    """Sliding window over words; returns (section_header, chunk_text).

    Section headers come from markdown `#` lines: each word remembers the
    most recent header above it, and a chunk takes the header of its first word.
    """
    words, word_headers = [], []
    current = "Overview"
    for line in body.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            current = stripped.lstrip("#").strip() or current
            continue
        for w in stripped.split():
            words.append(w)
            word_headers.append(current)

    chunks: list[tuple[str, str]] = []
    step = max(size - overlap, 1)
    for start in range(0, len(words), step):
        window = words[start : start + size]
        chunks.append((word_headers[start], " ".join(window)))
        if start + size >= len(words):
            break
    return chunks


def build_index(config: dict) -> VectorStore:
    model = SentenceTransformer(config["embedding_model"])
    store = VectorStore()
    texts, metas = [], []
    for path in sorted(Path(config["kb_dir"]).glob("*.md")):
        meta, body = parse_doc(path)
        for i, (section, chunk) in enumerate(
            chunk_text(body, config["chunk_size"], config["chunk_overlap"])
        ):
            texts.append(chunk)
            metas.append(
                {
                    "doc_id": meta["doc_id"],
                    "doc_type": meta.get("doc_type", "guide"),
                    "title": meta.get("title", meta["doc_id"]),
                    "section": section,
                    "chunk_id": f"{meta['doc_id']}:{i}",
                    "text": chunk,
                }
            )
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    store.add(embeddings, metas)
    return store


def main() -> None:
    config = load_config()
    store = build_index(config)
    store.save(Path(config["index_dir"]) / "index")
    print(f"Indexed {len(store)} chunks from {config['kb_dir']}")


if __name__ == "__main__":
    main()
