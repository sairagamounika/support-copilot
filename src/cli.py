"""CLI:  python -m src.cli ask "How do I reset my password?" """

import argparse
import json

from src.agent import SupportAgent
from src.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Support Copilot CLI")
    parser.add_argument("command", choices=["ask"])
    parser.add_argument("question")
    args = parser.parse_args()

    agent = SupportAgent(load_config())
    result = agent.ask(args.question)

    print(f"\nQ: {result['question']}\n")
    print(result["answer"])
    print(f"\nconfidence: {result['confidence']}  escalated: {result['escalated']}  "
          f"latency: {result['latency_ms']}ms")
    if result["sources"]:
        print("\nsources:")
        for s in result["sources"]:
            print(f"  - [{s['doc_id']}] {s['title']} / {s['section']} (score {s['score']})")
    if result["ticket"]:
        print("\nticket draft:")
        print(json.dumps(result["ticket"], indent=2))


if __name__ == "__main__":
    main()
