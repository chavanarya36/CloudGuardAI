from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from .matcher import (
    contains_match,
    json_path_match,
    missing_key_match,
    not_contains_match,
    regex_match,
    terraform_block_match,
    yaml_path_match,
)
from .schemas import Finding, Rule, file_type_for_path


def evaluate_file(path: Path, content: str, rules: Iterable[Rule]) -> List[Finding]:
    """Evaluate all rules against a single file content."""

    ftype = file_type_for_path(path)
    findings: List[Finding] = []
    for rule in rules:
        if rule.file_types and ftype not in rule.file_types:
            continue
        findings.extend(regex_match(rule, path, content))
        findings.extend(contains_match(rule, path, content))
        findings.extend(not_contains_match(rule, path, content))
        findings.extend(missing_key_match(rule, path, content))
        findings.extend(yaml_path_match(rule, path, content))
        findings.extend(json_path_match(rule, path, content))
        findings.extend(terraform_block_match(rule, path, content))
    return findings


def evaluate_directory(dir_path: Path, rules: Iterable[Rule]) -> List[Finding]:
    """Recursively evaluate rules against all IaC files in a directory."""

    collected: List[Finding] = []
    for path in dir_path.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".tf", ".yaml", ".yml", ".json", ".bicep"}:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        collected.extend(evaluate_file(path, content, rules))
    return collected

