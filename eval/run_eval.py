"""Full eval runner.

Usage:
    python -m eval.run_eval                 # run eval, gate against baseline.json
    python -m eval.run_eval --write-baseline # run eval, save results as the new baseline

Exits non-zero if any metric regressed beyond tolerance vs baseline.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from eval.metrics import (  # noqa: E402
    faithfulness_proxy,
    keyword_coverage,
    percentile,
    recall_at_k,
)
from src.agent import SupportAgent  # noqa: E402
from src.config import load_config  # noqa: E402
from src.llm import MockLLM  # noqa: E402

EVAL_DIR = ROOT / "eval"
RESULTS_DIR = EVAL_DIR / "results"

# metric -> max allowed drop vs baseline (latency uses max allowed *increase* ratio)
TOLERANCES = {
    "retrieval_recall": 0.05,
    "keyword_coverage": 0.05,
    "faithfulness": 0.05,
    "abstention_accuracy": 0.05,
    "latency_p95_ms": 0.50,  # +50% slower is a regression
}


def load_jsonl(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def run() -> dict:
    config = load_config()
    agent = SupportAgent(config, llm=MockLLM(config.get("mock_max_sentences", 3)))

    golden = load_jsonl(EVAL_DIR / "golden.jsonl")
    unanswerable = load_jsonl(EVAL_DIR / "unanswerable.jsonl")

    recalls, coverages, faithfulnesses, latencies = [], [], [], []
    answered_correctly = 0
    for item in golden:
        res = agent.ask(item["question"])
        latencies.append(res["latency_ms"])
        # retrieval is scored independently of the router's decision
        retrieved_ids = [h["doc_id"] for h in agent.retriever.retrieve(item["question"])]
        recalls.append(recall_at_k(retrieved_ids, item["gold_doc_ids"]))
        if res["escalated"]:
            coverages.append(0.0)
            continue
        answered_correctly += 1
        coverages.append(keyword_coverage(res["answer"], item["expected_keywords"]))
        chunk_texts = [_chunk_text(agent, s) for s in res["sources"]]
        faithfulnesses.append(faithfulness_proxy(res["answer"], [c for c in chunk_texts if c]))

    escalated_correctly = 0
    for item in unanswerable:
        res = agent.ask(item["question"])
        latencies.append(res["latency_ms"])
        escalated_correctly += res["escalated"]

    total = len(golden) + len(unanswerable)
    metrics = {
        "n_answerable": len(golden),
        "n_unanswerable": len(unanswerable),
        "retrieval_recall": round(sum(recalls) / len(recalls), 4) if recalls else 0.0,
        "keyword_coverage": round(sum(coverages) / len(coverages), 4) if coverages else 0.0,
        "faithfulness": round(sum(faithfulnesses) / len(faithfulnesses), 4) if faithfulnesses else 0.0,
        "answer_rate": round(answered_correctly / len(golden), 4),
        "escalation_rate_unanswerable": round(escalated_correctly / len(unanswerable), 4),
        "abstention_accuracy": round(
            (answered_correctly + escalated_correctly) / total, 4
        ),
        "latency_p50_ms": round(percentile(latencies, 50), 1),
        "latency_p95_ms": round(percentile(latencies, 95), 1),
    }
    return metrics


def _chunk_text(agent: SupportAgent, source: dict) -> str:
    for m in agent.retriever.store.metadatas:
        if m["doc_id"] == source["doc_id"] and m["section"] == source["section"]:
            return m["text"]
    for m in agent.retriever.store.metadatas:
        if m["doc_id"] == source["doc_id"]:
            return m["text"]
    return ""


def print_table(metrics: dict) -> None:
    print(f"\n{'metric':<28} {'value':>10}")
    print("-" * 40)
    for k, v in metrics.items():
        if k.startswith("n_"):
            continue
        print(f"{k:<28} {v:>10}")
    print(f"\n(answerable: {metrics['n_answerable']}, unanswerable: {metrics['n_unanswerable']})")


def gate(metrics: dict, baseline: dict) -> list[str]:
    regressions = []
    for metric, tol in TOLERANCES.items():
        old, new = baseline[metric], metrics[metric]
        if metric.startswith("latency"):
            if old > 0 and (new - old) / old > tol:
                regressions.append(f"{metric}: {old} -> {new} (slower than +{tol:.0%})")
        elif new < old - tol:
            regressions.append(f"{metric}: {old} -> {new} (drop > {tol:.0%})")
    return regressions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-baseline", action="store_true")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    metrics = run()
    print_table(metrics)

    latest_path = RESULTS_DIR / "latest.json"
    baseline_path = RESULTS_DIR / "baseline.json"
    with open(latest_path, "w") as f:
        json.dump(metrics, f, indent=2)

    if args.write_baseline:
        with open(baseline_path, "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"\nWrote new baseline to {baseline_path}")
        return

    if not baseline_path.exists():
        print("\nNo baseline.json yet — run with --write-baseline to set one.")
        return

    baseline = json.loads(baseline_path.read_text())
    regressions = gate(metrics, baseline)
    print("\n--- baseline comparison ---")
    for metric in TOLERANCES:
        old, new = baseline[metric], metrics[metric]
        flag = "  <-- REGRESSION" if any(metric in r for r in regressions) else ""
        print(f"{metric:<28} baseline {old:>8}  latest {new:>8}{flag}")
    if regressions:
        print("\nREGRESSIONS DETECTED:")
        for r in regressions:
            print(f"  - {r}")
        sys.exit(1)
    print("\nNo regressions vs baseline.")


if __name__ == "__main__":
    main()
