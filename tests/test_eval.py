from eval.metrics import (
    faithfulness_proxy,
    keyword_coverage,
    percentile,
    recall_at_k,
)


def test_recall_at_k_hit():
    assert recall_at_k(["a", "b", "c"], ["b"]) == 1.0


def test_recall_at_k_miss():
    assert recall_at_k(["a", "b"], ["z"]) == 0.0


def test_keyword_coverage_case_insensitive():
    assert keyword_coverage("The LIMIT is 429 per minute", ["limit", "429"]) == 1.0
    assert keyword_coverage("The limit is high", ["limit", "429"]) == 0.5


def test_faithfulness_verbatim_sentence():
    chunk = "Webhooks retry 5 times with exponential backoff before dead-lettering."
    answer = "Webhooks retry 5 times with exponential backoff before dead-lettering. [source: webhooks]"
    assert faithfulness_proxy(answer, [chunk]) == 1.0


def test_faithfulness_hallucinated_sentence():
    chunk = "Webhooks retry 5 times with exponential backoff before dead-lettering."
    answer = "Our CEO was born in 1975 and loves sailing."
    assert faithfulness_proxy(answer, [chunk]) == 0.0


def test_percentile():
    assert percentile([1, 2, 3, 4], 50) == 2.5
    assert percentile([], 95) == 0.0
