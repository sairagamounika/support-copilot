"""FastAPI service: POST /ask, GET /health."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from src.agent import SupportAgent
from src.config import load_config

agent: SupportAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    agent = SupportAgent(load_config())  # loads index once at startup
    yield


app = FastAPI(title="Support Copilot", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok", "llm": type(agent.llm).__name__ if agent else None}


@app.post("/ask")
def ask(req: AskRequest):
    assert agent is not None
    return agent.ask(req.question)
