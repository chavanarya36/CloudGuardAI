from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .evaluator import evaluate_directory, evaluate_file
from .loader import load_all_rules
from .schemas import Finding, Rule


def get_rules() -> List[Rule]:
    return load_all_rules()


def scan_file(path: Path) -> List[Finding]:
    rules = get_rules()
    content = path.read_text(encoding="utf-8", errors="ignore")
    return evaluate_file(path, content, rules)


def scan_single_file(file_path: Path, content: str) -> List[Dict[str, Any]]:
    """Scan a single in-memory file without touching disk.
    
    Args:
        file_path: Path object (used for file type detection and reporting)
        content: File content as string
    
    Returns:
        List of normalized finding dictionaries with fields:
        rule_id, file_path, resource, severity, title, description, 
        references, code_snippet
    """
    rules = get_rules()
    findings = evaluate_file(file_path, content, rules)
    
    # Normalize findings to dict format with all required fields
    normalized = []
    for f in findings:
        f_dict = f.to_dict() if hasattr(f, "to_dict") else dict(f)
        
        # Ensure all required fields exist
        normalized_finding = {
            "rule_id": f_dict.get("rule_id", "UNKNOWN"),
            "file_path": f_dict.get("file_path", str(file_path)),
            "resource": f_dict.get("resource", ""),
            "severity": f_dict.get("severity", "MEDIUM"),
            "title": f_dict.get("title", f_dict.get("rule_id", "Untitled")),
            "description": f_dict.get("description", "No description available"),
            "references": f_dict.get("references", []),
            "code_snippet": f_dict.get("evidence", ""),
            "line": f_dict.get("line", 0),
        }
        normalized.append(normalized_finding)
    
    return normalized


def scan_directory(path: Path) -> List[Finding]:
    rules = get_rules()
    return evaluate_directory(path, rules)

