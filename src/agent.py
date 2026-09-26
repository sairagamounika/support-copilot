"""The copilot router: normalize -> retrieve -> confidence check ->
answer with citations, or escalate with a ticket draft.

Confidence = w1 * top1_score + w2 * margin(top1 - top2) + w3 * question_overlap.

Three signals because no single one was enough on its own:
- top-1 cosine score: raw semantic similarity.
- margin: in-domain questions have one clear winner; out-of-domain questions
  retrieve several equally mediocre chunks.
- IDF-weighted question/chunk word overlap: guards against spuriously high
  embedding scores where none of the question's distinctive terms actually
  appear in the chunks. Rare terms (product names, error codes) count more
  than words like "plan" that appear everywhere.
Weights and threshold were tuned on the eval set (eval/); in production
you'd hold out a separate set for this.
"""

import json
import time
from pathlib import Path

from src.config import load_config
from src.llm import LLMClient, make_llm
from src.retriever import Retriever

URGENT_WORDS = {"outage", "down", "breach", "urgent", "critical", "losing money"}
BILLING_WORDS = {"billing", "invoice", "charge", "refund", "payment"}


class SupportAgent:
    def __init__(self, config: dict | None = None, llm: LLMClient | None = None):
        self.config = config or load_config()
        self.retriever = Retriever(self.config)
        self.llm = llm or make_llm(self.config)
        self.threshold = self.config["confidence_threshold"]
        self.w1 = self.config["confidence_top1_weight"]
        self.w2 = self.config["confidence_margin_weight"]
        self.w3 = self.config["confidence_overlap_weight"]

    # -- pipeline ---------------------------------------------------------
    def ask(self, question: str) -> dict:
        t0 = time.perf_counter()
        question = " ".join(question.strip().split())  # normalize whitespace
        hits = self.retriever.retrieve(question)
        confidence = self._confidence(question, hits)

        if not hits or confidence < self.threshold:
            result = {
                "question": question,
                "answer": (
                    "I couldn't find a reliable answer in the support docs, so I've "
                    "drafted a ticket for a human agent instead of guessing."
                ),
                "sources": [],
                "confidence": round(confidence, 4),
                "escalated": True,
                "ticket": self._draft_ticket(question, hits, confidence),
                "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            }
        else:
            answer = self.llm.generate(question, hits)
            result = {
                "question": question,
                "answer": answer,
                "sources": [
                    {
                        "doc_id": h["doc_id"],
                        "title": h["title"],
                        "section": h["section"],
                        "score": round(h["score"], 4),
                    }
                    for h in hits
                ],
                "confidence": round(confidence, 4),
                "escalated": False,
                "ticket": None,
                "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            }
        self._log_decision(result)
        return result

    # -- internals ----------------------------------------------------------
    def _confidence(self, question: str, hits: list[dict]) -> float:
        if not hits:
            return 0.0
        top1 = hits[0]["score"]
        margin = top1 - hits[1]["score"] if len(hits) > 1 else top1
        overlap = self.retriever.question_overlap(question, hits)
        return self.w1 * top1 + self.w2 * margin + self.w3 * overlap

    def _draft_ticket(self, question: str, hits: list[dict], confidence: float) -> dict:
        lowered = question.lower()
        if any(w in lowered for w in URGENT_WORDS):
            priority = "high"
        elif any(w in lowered for w in BILLING_WORDS):
            priority = "medium"
        else:
            priority = "low"
        snippet = hits[0]["text"][:280] + "..." if hits else "No relevant docs retrieved."
        return {
            "summary": question[:140],
            "suggested_priority": priority,
            "reason": (
                f"Retrieval confidence {confidence:.2f} below threshold {self.threshold}; "
                "answering would risk hallucination."
            ),
            "retrieved_context_snippet": snippet,
        }

    def _log_decision(self, result: dict) -> None:
        path = Path(self.config["log_file"])
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(result) + "\n")
