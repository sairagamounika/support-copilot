"""Tiny local vector index: cosine similarity over L2-normalized embeddings.

Persisted as <prefix>.npz (embeddings) + <prefix>.json (chunk metadata).
In production this class would be swapped for Pinecone/Weaviate behind the
same three methods: add, search, save/load.
"""

import json
from pathlib import Path

import numpy as np


class VectorStore:
    def __init__(self):
        self.embeddings = np.zeros((0, 0), dtype=np.float32)
        self.metadatas: list[dict] = []

    def add(self, embeddings: np.ndarray, metadatas: list[dict]) -> None:
        vecs = np.asarray(embeddings, dtype=np.float32)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        vecs = vecs / norms  # normalize once so search is a dot product
        self.embeddings = vecs if len(self.metadatas) == 0 else np.vstack([self.embeddings, vecs])
        self.metadatas.extend(metadatas)

    def search(self, query_vec: np.ndarray, top_k: int = 4, doc_type: str | None = None) -> list[dict]:
        """Return top_k hits as {score, **metadata}, optionally filtered by doc_type."""
        if len(self.metadatas) == 0:
            return []
        q = np.asarray(query_vec, dtype=np.float32)
        q = q / (np.linalg.norm(q) or 1.0)
        scores = self.embeddings @ q

        idx = np.arange(len(self.metadatas))
        if doc_type is not None:
            idx = np.array([i for i in idx if self.metadatas[i].get("doc_type") == doc_type])
            if len(idx) == 0:
                return []

        order = idx[np.argsort(scores[idx])[::-1][:top_k]]
        return [{"score": float(scores[i]), **self.metadatas[i]} for i in order]

    def save(self, prefix: str | Path) -> None:
        prefix = Path(prefix)
        prefix.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(prefix.with_suffix(".npz"), embeddings=self.embeddings)
        with open(prefix.with_suffix(".json"), "w") as f:
            json.dump(self.metadatas, f)

    @classmethod
    def load(cls, prefix: str | Path) -> "VectorStore":
        prefix = Path(prefix)
        store = cls()
        data = np.load(prefix.with_suffix(".npz"))
        store.embeddings = data["embeddings"]
        with open(prefix.with_suffix(".json")) as f:
            store.metadatas = json.load(f)
        return store

    def __len__(self):
        return len(self.metadatas)
