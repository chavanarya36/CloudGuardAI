"""Utility functions for rules engine."""
from __future__ import annotations

from typing import Any, Dict, List, Literal


def dedupe_findings(
    findings: List[Dict[str, Any]], 
    mode: Literal["single", "batch"] = "single"
) -> List[Dict[str, Any]]:
    """Deduplicate findings based on mode.
    
    Args:
        findings: List of finding dictionaries
        mode: 'single' for single-file (dedupe by rule_id only),
              'batch' for batch mode (dedupe by rule_id + file_path + resource)
    
    Returns:
        Deduplicated list of findings
    """
    seen = set()
    deduped = []
    
    for f in findings:
        if mode == "single":
            # Single file: dedupe by rule_id only
            key = f.get("rule_id") or f.get("check_id") or ""
        else:
            # Batch: dedupe by rule_id + file_path + resource
            key = (
                f.get("rule_id") or f.get("check_id") or "",
                f.get("file_path") or f.get("path") or "",
                f.get("resource") or "",
            )
        
        if key not in seen:
            seen.add(key)
            deduped.append(f)
    
    return deduped
