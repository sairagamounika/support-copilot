# Support Copilot

A customer-support copilot for **ParcelPilot** (a fictional shipping/logistics
SaaS): RAG over the support docs, plus a confidence-based router that answers
with citations when it's sure and escalates to a human with a ticket draft
when it isn't.

The part I'm proudest of isn't the RAG — it's the **evaluation harness**.
`eval/` holds 18 golden Q&As, 8 deliberately unanswerable questions, and a
runner that fails the build (locally and in CI) if any metric regresses.
That's what makes this more than a demo.

Runs **free and offline** after a one-time model download. No Pinecone, no
API keys required.

**Live demo:** [ParcelPilot Support Copilot](https://huggingface.co/spaces/dmounika1103/support-copilot-demo)
— ask a question and see citations, confidence, and latency; try the wifi
question to watch it refuse and draft an escalation ticket instead of guessing.

## Architecture

```
data/kb/*.md ──▶ ingest.py ──▶ chunk (sliding window + overlap)
                                   │ embed (all-MiniLM-L6-v2)
                                   ▼
                          ┌─────────────────┐
                          │  numpy vector    │  cosine index, persisted
                          │  index (.npz)    │  as .npz + .json
                          └────────┬────────┘
                                   │
user question ──▶ retriever ──▶ top-k chunks ──▶ agent.py ──┬──▶ confidence ≥ threshold
   (CLI / API)      (embed + cosine,            (router)    │    → LLM answers with
                     doc_type filter)                       │      [source: doc_id] citations
                                                           └──▶ confidence < threshold
                                                                → escalate: ticket draft
                                                                  {summary, priority,
                                                                   reason, snippet}

eval/run_eval.py ──▶ golden.jsonl (18) + unanswerable.jsonl (8)
                     → metrics → results/latest.json → gate vs baseline.json
```

The `VectorStore` and `LLMClient` are interfaces: the numpy index and the
mock LLM are the offline defaults, swappable for Pinecone / OpenAI without
touching the agent.

## Quickstart

```bash
pip install -r requirements.txt   # first run downloads the embedding model (~90MB)
python -m src.ingest              # chunk + embed + build data/index/
python -m src.cli ask "How many times do webhooks retry?"
python -m src.cli ask "What is the wifi password at the Chicago office?"
python -m eval.run_eval            # full eval + regression gate
pytest -q                         # unit tests
uvicorn src.app:app               # API on localhost:8000
curl -X POST localhost:8000/ask -H 'Content-Type: application/json' \
  -d '{"question":"What uptime does the Growth plan guarantee?"}'
```

To use a real LLM instead of the mock: `cp .env.example .env`, set
`OPENAI_API_KEY`, and `pip install openai`. Everything else is unchanged.

## Config knobs (`config.yaml`)

| Knob | Default | What it does |
|---|---|---|
| `embedding_model` | all-MiniLM-L6-v2 | Sentence-transformers model; swap for a larger one if you have the RAM |
| `chunk_size` / `chunk_overlap` | 120 / 30 words | Sliding window. Bigger chunks = more context per hit but diluted embeddings; smaller = sharper hits but fragmented answers |
| `top_k` | 4 | Chunks passed to the LLM and used for confidence |
| `confidence_threshold` | 0.38 | Below this the agent escalates instead of answering |
| `confidence_*_weight` | 0.4 / 0.3 / 0.5 | Confidence = 0.4·top1 + 0.3·margin(top1−top2) + 0.5·IDF-weighted question/chunk word overlap. The overlap term guards against spuriously high embedding scores; rare terms (error codes, product names) count more than common words |

## Eval results

Measured with the mock LLM on this machine (`python -m eval.run_eval`):

| Metric | Value | What it means |
|---|---|---|
| retrieval_recall | 1.00 | gold doc in top-4 for 18/18 answerable questions |
| keyword_coverage | 0.86 | fraction of expected answer keywords present in answers |
| faithfulness | 1.00 | fraction of answer sentences grounded in retrieved chunks (token-overlap proxy) |
| answer_rate | 1.00 | 18/18 answerable questions answered (not escalated) |
| escalation_rate (unanswerable) | 1.00 | 8/8 out-of-domain questions escalated, none hallucinated |
| abstention_accuracy | 1.00 | correct route (answer vs escalate) on 26/26 eval questions |
| latency p50 / p95 | 14 / 39 ms | per-question end-to-end, mock LLM, local model |

`eval/results/baseline.json` holds these numbers; `eval/run_eval.py` (and
CI) fails if any metric regresses beyond tolerance.

## Trade-offs

- **Numpy index instead of Pinecone/FAISS.** A few hundred chunks:
  brute-force cosine is sub-millisecond and has zero infra. The
  `VectorStore` interface (add/search/save/load) is the seam where Pinecone
  would plug in — I'd make that swap around 100k vectors, where brute force
  stops being funny.
- **Heuristic faithfulness instead of an LLM judge.** The proxy checks that
  each answer sentence shares content words with a retrieved chunk. It's
  free, offline, and deterministic, which keeps evals reproducible. It's
  also blind to subtle errors (a wrong number in the right vocabulary
  scores as grounded). An NLI model or LLM-as-judge is the honest upgrade;
  I say so in the code comments.
- **Mock LLM by default.** Deterministic answers make the eval a pure test
  of retrieval + routing instead of a test of OpenAI's mood that day. The
  `OpenAIAdapter` is one env var away when you want the real thing.

## What didn't work

1. **Thresholding on top-1 score alone let out-of-domain questions
   through.** "What is the wifi password?" still scored ~0.4 on some chunk.
   Adding the margin term (top-1 minus top-2) helped, but "parental leave
   policy" still scored 0.5 on pure embedding noise. The fix was a third
   term: IDF-weighted question/chunk word overlap — if none of the
   question's distinctive terms appear in what was retrieved, the semantic
   score is discounted. That got abstention to 26/26.
2. **Quoting the first sentences of the top chunk missed the point.** The
   first mock LLM stitched the chunk's opening sentences into the answer,
   which often didn't contain what the question asked. Switching to
   question-aware sentence selection (rank sentences by stemmed content-word
   overlap, slight bonus for fact-dense sentences with digits/acronyms)
   fixed keyword coverage without adding hallucination risk — it's still
   purely extractive.
3. **The eval initially conflated retrieval and routing.** My first runner
   scored recall as zero whenever the agent escalated, which punished the
   retriever for the router's decision. Now retrieval_recall is measured
   independently of the answer/escalate decision, and answer_rate covers
   the router. Cleaner attribution, better debugging.
