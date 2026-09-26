"""Eval metrics for the support copilot.

Honest note on faithfulness: the proxy below checks that each answer sentence
shares content words with at least one retrieved chunk (token-overlap
heuristic). It catches blatant hallucination but NOT subtle misstatements —
e.g. a wrong number copied in the right vocabulary still scores as grounded.
The stronger upgrade is an NLI model or an LLM-as-judge checking entailment;
the heuristic is here because it's free, offline, and deterministic.
"""

import statistics

from src.text_utils import content_tokens, split_sentences


def recall_at_k(retrieved_doc_ids: list[str], gold_doc_ids: list[str]) -> float:
    """1.0 if any gold doc is in the retrieved set, else 0.0."""
    return 1.0 if set(retrieved_doc_ids) & set(gold_doc_ids) else 0.0


def keyword_coverage(answer: str, expected_keywords: list[str]) -> float:
    """Fraction of expected keywords appearing verbatim (case-insensitive)."""
    if not expected_keywords:
        return 1.0
    lowered = answer.lower()
    return sum(kw.lower() in lowered for kw in expected_keywords) / len(expected_keywords)


def faithfulness_proxy(answer: str, chunk_texts: list[str], threshold: float = 0.35) -> float:
    """Fraction of answer sentences 'grounded' in the retrieved chunks.

    A sentence is grounded if >= `threshold` of its content tokens appear in
    at least one chunk. Proxy only — see module docstring.
    """
    sentences = split_sentences(answer)
    if not sentences:
        return 0.0
    chunk_token_sets = [content_tokens(c) for c in chunk_texts]
    grounded = 0
    for sent in sentences:
        toks = content_tokens(sent)
        if not toks:
            continue
        best = max(len(toks & ct) / len(toks) for ct in chunk_token_sets) if chunk_token_sets else 0.0
        grounded += best >= threshold
    return grounded / len(sentences)


def percentile(values: list[float], pct: float) -> float:
    return statistics.quantiles(sorted(values), n=100)[pct - 1] if values else 0.0
