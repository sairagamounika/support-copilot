# Interview Notes — Support Copilot

Read this after you've run the project once. It's the difference between
"here's a repo I built" and "here's a system I can defend."

## 1. The 60-second pitch

"I built a customer-support copilot for a fictional SaaS company. It does
RAG over the support docs, but the interesting part isn't the retrieval —
it's the router. The agent scores its own confidence from the retrieval
scores, and when confidence is low it refuses to answer: it escalates to a
human with a structured ticket draft instead of hallucinating. Everything
is gated by an evaluation harness — 18 golden Q&As, 8 deliberately
unanswerable questions that test abstention, and a CI job that fails the
build if any metric regresses. It runs fully offline with a local embedding
model and a numpy vector index, and the LLM sits behind an interface, so I
can swap in OpenAI without touching the agent logic."

## 2. How to actually learn it (do these in order)

1. **Run the quickstart end to end.** `pip install -r requirements.txt`,
   `python -m src.ingest`, then `python -m src.cli ask "What are the API
   rate limits?"`. See a cited answer. Then ask "What is the wifi password
   at the Chicago office?" and watch it escalate with a ticket draft.
2. **Read the source in this order:** `config.py` → `ingest.py` →
   `vector_store.py` → `retriever.py` → `llm.py` → `agent.py`. It's ~400
   lines total. You should be able to whiteboard the data flow from memory.
3. **Break the threshold.** Set `confidence_threshold: 0.95` in config.yaml
   and run the eval — everything escalates, abstention accuracy collapses
   on the answerable set. Set it to `0.0` — it answers garbage confidently.
   This is how you learn what the threshold *does*.
4. **Break the chunking.** Set `chunk_size: 2000`, re-run ingest and the
   eval, watch recall drop. Then set `chunk_size: 60` and watch faithfulness
   get noisy. Now you have a real opinion on chunking.
5. **Read `eval/metrics.py` twice.** You must be able to explain the
   faithfulness proxy, its limits, and what you'd replace it with (NLI
   model or LLM-as-judge). Interviewers *will* ask.
6. **Add one doc of your own** — pick a domain you know — plus 3 golden
   questions, re-run ingest and eval, and update the baseline. Now it's
   genuinely yours.
7. **Do the 5-minute demo out loud, twice.** See section 4.

## 3. Ten questions you'll get, and how to answer them

**Q: Walk me through the architecture.**
A: "Markdown docs go through ingest: sliding-window chunking with overlap,
embedded with a sentence-transformer, stored in a numpy cosine index with
metadata. At query time the retriever embeds the question, pulls top-k,
and the agent computes confidence as a weighted mix of the top-1 score and
the margin between top-1 and top-2. Above threshold, the LLM answers from
the chunks with citations; below, it escalates with a ticket draft. A
FastAPI service wraps it, and an eval harness gates every change."

**Q: How did you measure groundedness?**
A: "A token-overlap proxy: for each answer sentence, what fraction of its
content words appear in any retrieved chunk. It's honest but limited — it
catches invented content, not wrong numbers in the right vocabulary. The
real upgrade is an NLI model or an LLM judge checking entailment, which I
call out in the code comments."

**Q: Why escalate instead of answering with low confidence?**
A: "In support, a wrong answer is worse than no answer — it creates a
second, angrier ticket. Escalation with a draft summary, priority, and the
retrieved snippet makes the human handoff fast instead of dumping a raw
question in a queue. Abstention is a feature, and the unanswerable set in
the eval proves it works."

**Q: How did you pick the confidence threshold?**
A: "Empirically, against the golden and unanswerable sets. Top-1 score
alone wasn't enough — some out-of-domain questions still scored ~0.4 — so
I added the margin term: in-domain questions have one clear winner,
out-of-domain ones retrieve several equally mediocre chunks. The eval
regression gate locks the threshold in: if someone changes it and
abstention accuracy drops, CI fails."

**Q: Why a numpy index instead of Pinecone?**
A: "This needed to run free and offline so anyone can clone and run it.
Brute-force cosine over a few hundred chunks is milliseconds — no need for
ANN at this scale. The index sits behind a three-method interface (add,
search, save/load), so swapping in Pinecone or FAISS is a one-file change.
I'd never claim numpy scales to millions of vectors."

**Q: How would this scale to 100k docs?**
A: "Four changes: ANN index like FAISS HNSW instead of brute force;
metadata pre-filtering before the vector search; per-doc-type chunking
instead of one global window; and async embedding with caching. The router
and eval logic wouldn't change — that's the point of the interfaces."

**Q: What would you do differently with a real LLM?**
A: "The OpenAI adapter is already stubbed — it activates on
OPENAI_API_KEY. With a real model I'd add a system prompt enforcing
citations, structured JSON output for the ticket draft, and I'd upgrade
the faithfulness proxy to an LLM-as-judge. Trade-off is cost and latency:
that's why the mock exists, so evals stay free and deterministic."

**Q: How do you know the eval isn't gaming itself?**
A: "The golden set was written before I tuned anything, the unanswerable
set tests the opposite behavior — refusing — so you can't win by just
answering everything, and keyword coverage is independent of retrieval
scores. The CI gate compares against a committed baseline, so any tuning
has to hold up on the full set."

**Q: What didn't work?**
A: "Three things. First, 800-word chunks killed recall — the embedding
averaged out the specific facts. Second, thresholding on top-1 score alone
let out-of-domain questions through; the margin term fixed it. Third, my
first mock LLM quoted the first sentences of the top chunk, which missed
the keywords the golden questions asked about — I switched to picking the
sentences with the highest question-word overlap."

**Q: How would you monitor this in production?**
A: "Every decision is already logged to JSONL with confidence, latency,
and escalated flag. In prod I'd dashboard escalation rate, the confidence
distribution, and p95 latency, and I'd sample answers for human review —
feeding the failures back into the golden set. That's the closed loop that
keeps a RAG system honest after launch."

## 4. The 5-minute live demo

1. (30s) "Fictional SaaS, ParcelPilot. Ten support docs in `data/kb`."
2. (60s) Run `python -m src.ingest`. "Chunks, embeds, builds a local
   index — no cloud needed."
3. (60s) `python -m src.cli ask "How many times do webhooks retry?"` —
   point at the citations. Then ask "What is the wifi password at the
   Chicago office?" — point at the escalation and the ticket draft.
4. (90s) `python -m eval.run_eval` — walk the metrics table. "Recall,
   keyword coverage, faithfulness, abstention, latency — and CI fails the
   build if any of these regress."
5. (30s) "The LLM is an interface — mock by default for free offline
   evals, OpenAI when a key is set. The vector store too."

## 5. Make it yours

- **Change the domain.** Rename ParcelPilot to something from your world
  and rewrite 2–3 docs in that domain. Generic SaaS docs are fine, but a
  domain you can speak about is better.
- **Write your own golden questions.** Add 5 questions about things you've
  actually debugged — webhook retries, SSO failures. Interviewers light up
  when the eval set sounds like real incidents.
- **Plug in a real LLM.** Set OPENAI_API_KEY, run the eval, and compare
  faithfulness between the mock and the real model. That's a story: "the
  mock scored X, GPT-4o-mini scored Y, here's why."
- **Add one doc type.** A troubleshooting runbook with different chunking
  would show you thought about heterogeneous content.
- Keep the commit history natural — a few commits ("add eval harness",
  "fix threshold after unanswerable failures"), not one giant dump.
