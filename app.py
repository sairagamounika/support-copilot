"""Live demo for the Support Copilot.

Run locally:   python app.py   ->  http://127.0.0.1:7860
On Hugging Face Spaces this file is picked up automatically.

The demo reuses the exact same engine as the CLI/API (src/agent.py) —
nothing is simplified for the demo. First startup downloads the embedding
model once (~90MB) and builds the search index, which takes a few minutes.
"""

from pathlib import Path

import gradio as gr

from src.agent import SupportAgent
from src.config import load_config
from src.ingest import build_index

REPO_URL = "https://github.com/sairagamounika/support-copilot"

print("Loading configuration...")
config = load_config()

if not list(Path(config["index_dir"]).glob("*.npz")):
    print("No search index found — building it now (one-time, a few minutes)...")
    build_index(config)
    print("Index ready.")

print("Loading support agent...")
agent = SupportAgent(config)
print("Ready.")

EXAMPLES = [
    "How do I reset my password?",
    "How many times do webhooks retry?",
    "What is the wifi password at the Chicago office?",
]


def answer_question(question: str):
    """Run one question through the copilot and format the result for the UI."""
    question = (question or "").strip()
    if not question:
        return "Type a question above and press Ask.", "", {"note": "nothing asked yet"}

    result = agent.ask(question)

    answer_md = result["answer"]
    if result["sources"]:
        cites = "\n\n**Sources**\n" + "\n".join(
            f"- `{s['doc_id']}` — {s['title']} / {s['section']} (score {s['score']})"
            for s in result["sources"]
        )
        answer_md += cites

    if result["escalated"]:
        status = (
            f"**Confidence:** {result['confidence']} (below threshold "
            f"{agent.threshold}) &nbsp;|&nbsp; **Latency:** {result['latency_ms']} ms"
            f" &nbsp;|&nbsp; **Escalated:** yes — the bot refused to guess"
        )
        ticket = result["ticket"]
    else:
        status = (
            f"**Confidence:** {result['confidence']} &nbsp;|&nbsp; "
            f"**Latency:** {result['latency_ms']} ms &nbsp;|&nbsp; **Escalated:** no"
        )
        ticket = {"note": "Answered directly from the docs — no ticket needed."}

    return answer_md, status, ticket


with gr.Blocks(title="ParcelPilot Support Copilot") as demo:
    gr.Markdown(
        "# ParcelPilot Support Copilot\n"
        "A RAG support bot that answers from company docs — with citations — "
        "and **refuses to guess** when it doesn't know, escalating to a human "
        "instead. Try an answerable question, then try the wifi one. "
        f"[GitHub repo]({REPO_URL})"
    )
    with gr.Row():
        question_box = gr.Textbox(
            label="Your question",
            placeholder="How do I reset my password?",
            scale=4,
        )
        ask_btn = gr.Button("Ask", variant="primary", scale=1)
    gr.Examples(examples=EXAMPLES, inputs=question_box, label="Try these")
    answer_out = gr.Markdown(label="Answer")
    status_out = gr.Markdown()
    ticket_out = gr.JSON(label="Escalation ticket (appears when the bot refuses to guess)")

    ask_btn.click(
        answer_question,
        inputs=question_box,
        outputs=[answer_out, status_out, ticket_out],
    )
    question_box.submit(
        answer_question,
        inputs=question_box,
        outputs=[answer_out, status_out, ticket_out],
    )

if __name__ == "__main__":
    demo.launch()
