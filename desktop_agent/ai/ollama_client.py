"""Optional local AI summarizer using Ollama.

This is not required for version 0.1. If Ollama is not running, the app should
still work normally.
"""

from __future__ import annotations

from typing import Any

import requests


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self.base_url = base_url.rstrip("/")

    def summarize(self, payload: dict[str, Any], model: str = "llama3.2") -> str:
        prompt = (
            "You are a careful desktop systems assistant. "
            "Summarize the system status in plain English, rank the top issues, "
            "and only make claims supported by the input.\n\n"
            f"Input:\n{payload}"
        )
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return str(data.get("response", "")).strip()
