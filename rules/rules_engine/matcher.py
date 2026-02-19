from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, List

import yaml

from .schemas import Finding, Rule, RuleMatch


def _iter_lines(content: str) -> Iterable[tuple[int, str]]:
    for idx, line in enumerate(content.splitlines(), start=1):
        yield idx, line


def regex_match(rule: Rule, path: Path, content: str) -> List[Finding]:
    pattern = rule.match.regex
    if not pattern:
        return []
    regex = re.compile(pattern)
    findings: List[Finding] = []
    for line_no, line in _iter_lines(content):
        if regex.search(line):
            findings.append(
                Finding(
                    rule_id=rule.id,
                    severity=rule.severity,
                    description=rule.description,
                    file_path=str(path),
                    line=line_no,
                    evidence=line.strip(),
                    references=rule.references,
                )
            )
    return findings


def contains_match(rule: Rule, path: Path, content: str) -> List[Finding]:
    needle = rule.match.contains
    if not needle:
        return []
    findings: List[Finding] = []
    for line_no, line in _iter_lines(content):
        if needle in line:
            findings.append(
                Finding(
                    rule_id=rule.id,
                    severity=rule.severity,
                    description=rule.description,
                    file_path=str(path),
                    line=line_no,
                    evidence=line.strip(),
                    references=rule.references,
                )
            )
    return findings


def not_contains_match(rule: Rule, path: Path, content: str) -> List[Finding]:
    needle = rule.match.not_contains
    if not needle:
        return []
    if needle in content:
        return []
    # Single finding at top of file to indicate violation.
    return [
        Finding(
            rule_id=rule.id,
            severity=rule.severity,
            description=rule.description,
            file_path=str(path),
            line=1,
            evidence=f"missing disallowed string: {needle}",
            references=rule.references,
        )
    ]


def missing_key_match(rule: Rule, path: Path, content: str) -> List[Finding]:
    key = rule.match.missing_key
    if not key:
        return []
    # Heuristic: treat as a simple string search; if absent, flag once.
    if key in content:
        return []
    return [
        Finding(
            rule_id=rule.id,
            severity=rule.severity,
            description=rule.description,
            file_path=str(path),
            line=1,
            evidence=f"missing key: {key}",
            references=rule.references,
        )
    ]


def _load_yaml_or_json(content: str) -> Any:
    try:
        return yaml.safe_load(content)
    except Exception:
        try:
            return json.loads(content)
        except Exception:
            return None


def _simple_path_get(data: Any, path_expr: str) -> List[Any]:
    """Extremely small subset of JSONPath/YAMLPath.

    Supports forms like:
      $.a.b
      $.a[*].b
    """

    if not path_expr.startswith("$."):
        return []
    parts = path_expr[2:].split(".")
    current: List[Any] = [data]
    for part in parts:
        next_items: List[Any] = []
        if part.endswith("[*]"):
            key = part[:-3]
            for obj in current:
                if isinstance(obj, dict) and key in obj and isinstance(obj[key], list):
                    next_items.extend(obj[key])
        else:
            for obj in current:
                if isinstance(obj, dict) and part in obj:
                    next_items.append(obj[part])
        current = next_items
    return current


def yaml_path_match(rule: Rule, path: Path, content: str) -> List[Finding]:
    expr = rule.match.yaml_path
    if not expr:
        return []
    data = _load_yaml_or_json(content)
    if data is None:
        return []
    values = _simple_path_get(data, expr)
    expected = rule.match.equals
    findings: List[Finding] = []
    for value in values:
        if expected is not None and value == expected:
            evidence = f"{expr} == {expected}"
            findings.append(
                Finding(
                    rule_id=rule.id,
                    severity=rule.severity,
                    description=rule.description,
                    file_path=str(path),
                    line=1,
                    evidence=evidence,
                    references=rule.references,
                )
            )
    return findings


def json_path_match(rule: Rule, path: Path, content: str) -> List[Finding]:
    # For now we reuse yaml_path_match semantics for JSON.
    return yaml_path_match(rule, path, content)


def terraform_block_match(rule: Rule, path: Path, content: str) -> List[Finding]:
    """Very small heuristic Terraform block matcher.

    Looks for text patterns like `resource "aws_s3_bucket"` when
    terraform_block contains a `type` key.
    """

    block = rule.match.terraform_block or {}
    block_type = block.get("type")
    if not block_type:
        return []
    pattern = f"resource \"{block_type}\""
    findings: List[Finding] = []
    for line_no, line in _iter_lines(content):
        if pattern in line:
            findings.append(
                Finding(
                    rule_id=rule.id,
                    severity=rule.severity,
                    description=rule.description,
                    file_path=str(path),
                    line=line_no,
                    evidence=line.strip(),
                    references=rule.references,
                )
            )
    return findings

