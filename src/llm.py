"""LLM layer: one interface, two backends.

MockLLM is the default — deterministic, builds answers only from retrieved
chunks, never invents. OpenAIAdapter activates when OPENAI_API_KEY is set.
"""

import re
from abc import ABC, abstractmethod

from src.text_utils import content_tokens

# Sentences with digits or acronyms tend to carry the concrete facts
# (limits, time windows, header names) that support answers need, so the
# mock prefers them slightly when ranking. Pure heuristic, no semantics.
FACT_DENSE_RE = re.compile(r"\d|[A-Z]{2,}")


class LLMClient(ABC):
    @abstractmethod
    def generate(self, question: str, chunks: list[dict]) -> str:
        """Answer `question` using only `chunks`. Each chunk has text, doc_id, title."""


class MockLLM(LLMClient):
    """Deterministic extractive stand-in: picks the retrieved sentences with the
    highest content-word overlap with the question and stitches them together
    with [source: doc_id] citations. It only reorders chunk text, so it cannot
    hallucinate beyond what's retrieved — which is exactly what the
    faithfulness eval measures."""

    def __init__(self, max_sentences: int = 3):
        self.max_sentences = max_sentences

    def generate(self, question: str, chunks: list[dict]) -> str:
        if not chunks:
            return "I don't have information about that in the support docs."
        q_words = content_tokens(question)
        scored = []
        for rank, chunk in enumerate(chunks):
            for sent in chunk["text"].replace("\n", " ").split(". "):
                sent = sent.strip().rstrip(".")
                if len(sent) < 20:
                    continue
                overlap = len(q_words & content_tokens(sent))
                bonus = 0.5 if FACT_DENSE_RE.search(sent) else 0.0
                scored.append((overlap + bonus, rank, sent, chunk["doc_id"]))
        # highest overlap first; ties prefer higher-ranked chunks, keep stable
        scored.sort(key=lambda t: (-t[0], t[1]))

        picked, cited = [], []
        for _, _, sent, doc_id in scored:
            if sent not in picked:
                picked.append(sent)
                if doc_id not in cited:
                    cited.append(doc_id)
            if len(picked) >= self.max_sentences:
                break
        body = ". ".join(picked) + "."
        cites = " ".join(f"[source: {d}]" for d in cited)
        return f"{body} {cites}"


class OpenAIAdapter(LLMClient):
    """Real LLM backend. Only constructed when OPENAI_API_KEY is present."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        try:
            from openai import OpenAI
        except ImportError as e:
            raise RuntimeError("pip install openai to use the OpenAI adapter") from e
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, question: str, chunks: list[dict]) -> str:
        context = "\n\n".join(f"[{c['doc_id']}] {c['title']}: {c['text']}" for c in chunks)
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a support copilot. Answer ONLY from the provided "
                        "context. Cite sources as [source: doc_id]. If the context "
                        "doesn't contain the answer, say you don't know."
                    ),
                },
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
            temperature=0,
        )
        return resp.choices[0].message.content.strip()


def make_llm(config: dict) -> LLMClient:
    if config.get("openai_api_key"):
        return OpenAIAdapter(config["openai_api_key"], config["openai_model"])
    return MockLLM(max_sentences=config.get("mock_max_sentences", 3))
