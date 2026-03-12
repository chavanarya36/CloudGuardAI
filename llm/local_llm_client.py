"""Local LLM client for Ollama-hosted models.

Provides a lightweight HTTP client for the Ollama API. Used by the
explainability pipeline as a free, local alternative to OpenAI when
no API key is configured.
"""
from __future__ import annotations

import json
import logging
import os
import re
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)

# Configurable via environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:0.6b")


def is_ollama_available() -> bool:
    """Check whether the Ollama server is reachable."""
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def call_local_llm(prompt: str, *, system: str = "", timeout: int = 300) -> Optional[str]:
    """Send a chat completion request to the local Ollama server.

    Returns the model's response text, or None if the request fails.
    Qwen3 models emit <think>...</think> blocks; these are stripped
    automatically so only the visible answer is returned.
    """
    url = f"{OLLAMA_BASE_URL}/api/chat"
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    # Append /no_think to disable qwen3 thinking mode for faster inference
    messages.append({"role": "user", "content": prompt + " /no_think"})

    body = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "num_ctx": 2048,
            "num_predict": 1024,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data.get("message", {}).get("content", "")
            # Strip Qwen3 thinking blocks
            clean = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            if clean:
                logger.info("Local LLM (%s) responded: %d chars", OLLAMA_MODEL, len(clean))
                return clean
            logger.warning("Local LLM returned empty response after stripping think tags")
            return None
    except urllib.error.URLError as exc:
        logger.debug("Local LLM unreachable: %s", exc)
        return None
    except Exception as exc:
        logger.warning("Local LLM call failed: %s", exc)
        return None
