import pytest

from src.agent import SupportAgent
from src.config import load_config
from src.llm import MockLLM


@pytest.fixture(scope="module")
def agent():
    config = load_config()
    return SupportAgent(config, llm=MockLLM())


def test_answerable_question_gets_cited_answer(agent):
    res = agent.ask("What are the API rate limits?")
    assert res["escalated"] is False
    assert "[source:" in res["answer"], "answer must carry citations"
    assert res["sources"], "answer must list sources"
    assert res["confidence"] >= agent.threshold


def test_out_of_domain_question_escalates(agent):
    res = agent.ask("What is the wifi password at the Chicago office?")
    assert res["escalated"] is True
    ticket = res["ticket"]
    assert ticket is not None
    for key in ("summary", "suggested_priority", "reason", "retrieved_context_snippet"):
        assert key in ticket, f"ticket draft missing {key}"


def test_gibberish_escalates(agent):
    res = agent.ask("zxqwv blorpt fnord")
    assert res["escalated"] is True


def test_urgent_language_raises_priority(agent):
    res = agent.ask("Our checkout API is down and we are losing money, wifi password?")
    assert res["escalated"] is True
    assert res["ticket"]["suggested_priority"] == "high"
