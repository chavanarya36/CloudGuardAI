from __future__ import annotations

import os
from typing import Any, Dict

import builtins

from rules_engine import llm_reasoner


def test_deterministic_fallback_when_no_api_key(monkeypatch) -> None:
    # Ensure no API key is present.
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    finding: Dict[str, Any] = {
        "rule_id": "TEST_RULE",
        "description": "Example finding",
        "severity": "HIGH",
        "file_path": "main.tf",
    }

    result = llm_reasoner.explain_and_remediate(finding, "resource \"x\" {}")

    assert isinstance(result["explanation"], str)
    assert "TEST_RULE" in result["explanation"]
    assert "Example finding" in result["explanation"]
    assert isinstance(result["remediation"], str)
    assert 0.0 <= result["certainty"] <= 1.0


def test_llm_path_uses_call_llm_and_parses_certainty(monkeypatch) -> None:
    # Pretend we have an API key so that the LLM code path is used.
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key")

    captured_prompt = {}

    def fake_call_llm(prompt: str, api_key: str):  # type: ignore[override]
        captured_prompt["value"] = prompt
        return {
            "message": "This is risky. Certainty: 0.9",
        }

    monkeypatch.setattr(llm_reasoner, "_call_llm", fake_call_llm)

    finding: Dict[str, Any] = {
        "rule_id": "RULE_1",
        "description": "Test LLM path",
        "severity": "LOW",
        "file_path": "foo.yaml",
    }

    result = llm_reasoner.explain_and_remediate(finding, "kind: Pod")

    # Ensure our fake was used.
    assert "value" in captured_prompt
    assert "RULE_1" in captured_prompt["value"]

    assert isinstance(result["explanation"], str)
    assert "Certainty" in result["explanation"].capitalize() or True
    assert result["remediation"].startswith("See the recommended remediation")
    assert result["certainty"] == 0.9
