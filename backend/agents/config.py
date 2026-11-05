"""Portkey model and prompt files for every Campus Customs agent."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

BACKEND = Path(__file__).resolve().parent.parent
ROOT = BACKEND.parent
PROMPTS = BACKEND / "prompts"

load_dotenv(ROOT / ".env")

# Every agent uses this model. No other model name belongs in this homework.
MODEL_NAME = "gpt-6-luna"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"

_model: OpenAIResponsesModel | None = None


def require_api_key() -> str:
    key = os.getenv("PORTKEY_API_KEY", "").strip()
    if not key:
        raise RuntimeError("PORTKEY_API_KEY is not set. Put it in .env.")
    return key


def build_model() -> OpenAIResponsesModel:
    """One Portkey model shared by Boss and every specialist."""
    global _model
    if _model is None:
        key = require_api_key()
        client = AsyncOpenAI(
            api_key=key,
            base_url=PORTKEY_BASE_URL,
            default_headers={"x-portkey-api-key": key},
        )
        _model = OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))
    return _model


def load_prompt(name: str) -> str:
    return (PROMPTS / name).read_text(encoding="utf-8")
