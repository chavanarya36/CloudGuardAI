from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional


Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]


@dataclass
class RuleMatch:
    """Definition of how a rule matches content or structure."""

    regex: Optional[str] = None
    contains: Optional[str] = None
    not_contains: Optional[str] = None
    missing_key: Optional[str] = None
    yaml_path: Optional[str] = None
    json_path: Optional[str] = None
    equals: Optional[Any] = None
    terraform_block: Optional[Dict[str, Any]] = None


@dataclass
class Rule:
    """In-memory representation of a single static rule."""

    id: str
    description: str
    severity: Severity
    file_types: List[str] = field(default_factory=list)
    match: RuleMatch = field(default_factory=RuleMatch)
    references: List[str] = field(default_factory=list)


@dataclass
class Finding:
    """Result of evaluating a rule against a file."""

    rule_id: str
    severity: Severity
    description: str
    file_path: str
    line: int
    evidence: str
    references: List[str]
    title: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "title": self.title or self.rule_id.replace("_", " ").title(),
            "description": self.description,
            "file_path": self.file_path,
            "line": self.line,
            "line_number": self.line,
            "code_snippet": self.evidence,
            "evidence": self.evidence,
            "references": list(self.references),
            "scanner": "rules",
            "category": "rules",
        }


def file_type_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".tf":
        return "terraform"
    if suffix in {".yaml", ".yml"}:
        return "yaml"
    if suffix == ".json":
        return "json"
    if suffix == ".bicep":
        return "bicep"
    return "other"

