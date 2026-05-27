"""Gemini API wrapper with JSON-mode helpers and retry."""
from __future__ import annotations

import json
import os
import time
from typing import Any

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

_API_KEY = os.getenv("GEMINI_API_KEY")
_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

if _API_KEY:
    genai.configure(api_key=_API_KEY)


class LLMError(Exception):
    pass


def _model(temperature: float = 0.7, json_mode: bool = False) -> genai.GenerativeModel:
    if not _API_KEY:
        raise LLMError("GEMINI_API_KEY not set. Copy .env.example to .env and add your key.")
    config: dict[str, Any] = {"temperature": temperature}
    if json_mode:
        config["response_mime_type"] = "application/json"
    return genai.GenerativeModel(_MODEL_NAME, generation_config=config)


def generate_text(prompt: str, temperature: float = 0.7, retries: int = 3) -> str:
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            resp = _model(temperature).generate_content(prompt)
            return resp.text or ""
        except Exception as e:
            last_err = e
            time.sleep(2 ** attempt)
    raise LLMError(f"generate_text failed after {retries} retries: {last_err}")


def generate_json(prompt: str, temperature: float = 0.4, retries: int = 3) -> Any:
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            resp = _model(temperature, json_mode=True).generate_content(prompt)
            text = (resp.text or "").strip()
            return json.loads(text)
        except json.JSONDecodeError as e:
            last_err = e
            time.sleep(1 + attempt)
        except Exception as e:
            last_err = e
            time.sleep(2 ** attempt)
    raise LLMError(f"generate_json failed after {retries} retries: {last_err}")
