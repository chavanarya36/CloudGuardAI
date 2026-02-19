from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import yaml

from .schemas import Rule, RuleMatch


RULES_DIR = Path(__file__).resolve().parent / "rules"


def _load_yaml_file(path: Path) -> Dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_rules_from_yaml(path: Path) -> List[Rule]:
    data = _load_yaml_file(path)
    raw_rules = data.get("rules") or []
    rules: List[Rule] = []
    for item in raw_rules:
        match_data = item.get("match", {}) or {}
        match = RuleMatch(
            regex=match_data.get("regex"),
            contains=match_data.get("contains"),
            not_contains=match_data.get("not_contains"),
            missing_key=match_data.get("missing_key"),
            yaml_path=match_data.get("yaml_path"),
            json_path=match_data.get("json_path"),
            equals=match_data.get("equals"),
            terraform_block=match_data.get("terraform_block"),
        )
        rules.append(
            Rule(
                id=str(item.get("id")),
                description=str(item.get("description", "")),
                severity=str(item.get("severity", "LOW")),
                file_types=list(item.get("file_types", [])),
                match=match,
                references=list(item.get("references", []) or []),
            )
        )
    return rules


def load_all_rules() -> List[Rule]:
    """Load all rules from the rules/ tree.

    The loader is intentionally simple: it walks known YAML filenames
    under the rules directory and concatenates them.
    """

    yaml_paths = []
    for sub in [
        "aws/cis.yaml",
        "aws/owasp.yaml",
        "aws/best_practices.yaml",
        "gcp/cis.yaml",
        "gcp/owasp.yaml",
        "gcp/best_practices.yaml",
        "azure/cis.yaml",
        "azure/owasp.yaml",
        "azure/best_practices.yaml",
        "kubernetes/cis.yaml",
        "kubernetes/owasp.yaml",
        "kubernetes/nsa.yaml",
        "shared/generic.yaml",
        "shared/terraform.yaml",
    ]:
        yaml_paths.append(RULES_DIR / sub)

    all_rules: List[Rule] = []
    for path in yaml_paths:
        all_rules.extend(_load_rules_from_yaml(path))
    return all_rules


def get_rule_metadata_map() -> Dict[str, Dict]:
    """Get a flat metadata map keyed by rule_id.
    
    Returns:
        Dict mapping rule_id to metadata dict with:
        - title: rule ID (or explicit title if available)
        - description: rule description
        - severity: severity level
        - references: list of reference URLs
    
    Raises:
        Warning if duplicate rule_ids are found (prints to stderr)
    """
    import sys
    
    rules = load_all_rules()
    meta_map = {}
    duplicates = []
    
    for rule in rules:
        if rule.id in meta_map:
            duplicates.append(rule.id)
            print(
                f"WARNING: Duplicate rule_id '{rule.id}' found in rules. "
                f"Using first occurrence.",
                file=sys.stderr
            )
        else:
            meta_map[rule.id] = {
                "title": rule.id,  # Use ID as title
                "description": rule.description,
                "severity": rule.severity,
                "references": rule.references,
            }
    
    return meta_map

