"""Retrieval: embed the query with the same model used at ingest time,
then cosine-search the local index. Supports doc_type metadata filtering."""

from collections import Counter
from math import log
from pathlib import Path

from sentence_transformers import SentenceTransformer

from src.config import load_config
from src.text_utils import content_tokens
from src.vector_store import VectorStore


class Retriever:
    def __init__(self, config: dict | None = None):
        self.config = config or load_config()
        self.model = SentenceTransformer(self.config["embedding_model"])
        self.store = VectorStore.load(Path(self.config["index_dir"]) / "index")
        # IDF table over the indexed chunks, for the lexical grounding signal.
        df = Counter()
        for m in self.store.metadatas:
            df.update(set(content_tokens(m["text"])))
        n = max(len(self.store.metadatas), 1)
        self._idf = {w: log(n / max(c, 1)) for w, c in df.items()}
        self._idf_default = log(n)

    def retrieve(self, query: str, top_k: int | None = None, doc_type: str | None = None) -> list[dict]:
        q = self.model.encode([query.strip()], normalize_embeddings=True)[0]
        return self.store.search(q, top_k=top_k or self.config["top_k"], doc_type=doc_type)

    def question_overlap(self, query: str, hits: list[dict]) -> float:
        """Lexical grounding signal: IDF-weighted fraction of the question's
        content words that appear in the best retrieved chunk.

        Catches spuriously high embedding scores where the question's actual
        terms appear nowhere in what was retrieved. IDF weighting means rare,
        distinctive terms (product names, error codes) count more than words
        like "plan" or "charge" that appear all over the KB.
        """
        q_tokens = content_tokens(query)
        if not q_tokens or not hits:
            return 0.0
        denom = sum(self._idf.get(w, self._idf_default) for w in q_tokens)
        best = 0.0
        for h in hits:
            c_tokens = content_tokens(h["text"])
            num = sum(self._idf.get(w, self._idf_default) for w in q_tokens if w in c_tokens)
            best = max(best, num / denom)
        return best
