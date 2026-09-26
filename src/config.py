"""Load config.yaml + optional .env into a plain dict of settings."""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


def load_config(path: str | Path | None = None) -> dict:
    load_dotenv(ROOT / ".env")  # no-op if missing
    cfg_path = Path(path) if path else ROOT / "config.yaml"
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)

    cfg["root"] = str(ROOT)
    cfg["kb_dir"] = str(ROOT / cfg["kb_dir"])
    cfg["index_dir"] = str(ROOT / cfg["index_dir"])
    cfg["log_file"] = str(ROOT / cfg["log_file"])
    cfg["openai_api_key"] = os.environ.get("OPENAI_API_KEY", "")
    cfg["openai_model"] = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    return cfg
