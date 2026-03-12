"""
Unified Findings Integration Layer
===================================
Merges rule-engine findings with GNN attack-path analysis and ML risk scores
into a single enriched output.  Adds three optional fields to each finding
(``part_of_attack_path``, ``attack_path_context``, ``ranking_score``,
``reasoning_summary``) without modifying any existing field.

Returns a ``recommended_order`` list (indices sorted by descending
``ranking_score``) so consumers can display ranked results without the
original list order being mutated.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

# Bonus added to ranking_score when a finding's resource sits on an attack path.
_ATTACK_PATH_BONUS = 0.15
# Weight applied to the GNN scan-level risk score in ranking formula.
_GNN_WEIGHT = 0.25
# Base severity weights for ranking formula.
_SEV_WEIGHT = {"CRITICAL": 1.0, "HIGH": 0.75, "MEDIUM": 0.5, "LOW": 0.25, "INFO": 0.1}


# ── helpers ────────────────────────────────────────────────────────────────

def _resources_on_paths(
    attack_paths: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Build a map:  resource_full_name  →  [concise path summaries it appears in].

    Each summary contains only lightweight, serialisable fields:
      path_id, path_string, entry_point, target, hops, severity, role
    """
    resource_map: Dict[str, List[Dict[str, Any]]] = {}

    for path in attack_paths:
        chain = path.get("chain", [])
        entry = path.get("entry_point", "")
        target = path.get("target", "")
        path_info_base = {
            "path_id": path.get("path_id", ""),
            "path_string": path.get("path_string", ""),
            "entry_point": entry,
            "target": target,
            "hops": path.get("hops", 0),
            "severity": path.get("severity", ""),
        }

        # Collect all resource names in chain with their role
        chain_resources: List[str] = [n.get("resource", "") for n in chain]
        upstream_downstream: Dict[str, Tuple[List[str], List[str]]] = {}

        for idx, node in enumerate(chain):
            res = node.get("resource", "")
            if not res:
                continue

            # Determine role
            if node.get("is_entry") or idx == 0:
                role = "entry_point"
            elif node.get("is_target") or idx == len(chain) - 1:
                role = "target"
            else:
                role = "intermediate"

            upstream = [chain_resources[i] for i in range(idx) if chain_resources[i] != res]
            downstream = [chain_resources[i] for i in range(idx + 1, len(chain)) if chain_resources[i] != res]
            upstream_downstream[res] = (upstream, downstream)

            path_info = {**path_info_base, "role": role}
            resource_map.setdefault(res, []).append(path_info)
            # Store upstream/downstream on the path_info so the caller can read it
            path_info["upstream_resources"] = upstream
            path_info["downstream_resources"] = downstream

    return resource_map


def _build_reasoning(
    finding: Dict[str, Any],
    on_path: bool,
    path_context: Optional[Dict[str, Any]],
) -> str:
    """Return a single-sentence deterministic reasoning string."""
    scanner = (finding.get("scanner") or finding.get("category") or "Scanner").capitalize()
    title = finding.get("title") or finding.get("description") or finding.get("rule_id") or ""
    finding_type = finding.get("type", "")

    # Template C – GNN attack-path finding
    if finding_type == "attack_path":
        meta = finding.get("metadata") or {}
        path_string = meta.get("path_string") or (path_context or {}).get("path_string", "")
        hops = meta.get("hops") or (path_context or {}).get("hops", "?")
        severity = finding.get("severity", "")
        entry = meta.get("entry_point", "")
        target = meta.get("target", "")
        if not path_string:
            path_string = f"{entry} -> {target}"
        return (
            f"Attack path detected: {path_string} "
            f"({hops} hops, {severity}). "
            f"Entry: {entry} -> Target: {target}."
        )

    # Template D – GNN critical-resource or ML prediction
    if finding_type in ("critical_resource", "ML_PREDICTION"):
        return f"{scanner} analysis: {title}."

    # Template B – any finding whose resource sits on an attack path
    if on_path and path_context:
        role_display = (
            path_context.get("role_in_path")
            or path_context.get("role")
            or "node"
        ).replace("_", " ")
        path_id = path_context.get("path_id", "")
        path_string = (
            path_context.get("path_description")
            or path_context.get("path_string")
            or ""
        )
        target = path_context.get("target", "")
        # Derive target from downstream_resources if not directly available
        if not target:
            downstream = path_context.get("downstream_resources") or []
            target = downstream[-1] if downstream else "high-value target"
        return (
            f"{scanner} finding: {title}. "
            f"This resource is the {role_display} of attack path {path_id} "
            f"({path_string}), enabling lateral movement toward {target}."
        )

    # Template A – regular finding, not on path
    return f"{scanner} finding: {title}."


# ── public API ─────────────────────────────────────────────────────────────

def unify_findings(
    findings: List[Dict[str, Any]],
    attack_paths: List[Dict[str, Any]],
    ml_risk_score: float,
) -> List[int]:
    """Enrich *findings* **in-place** with integration fields and return
    ``recommended_order`` (indices sorted by descending ``ranking_score``).

    Parameters
    ----------
    findings:
        The mutable ``all_findings`` list already populated by all scanners.
        Each dict receives three new keys: ``part_of_attack_path``,
        ``attack_path_context``, ``ranking_score``, ``reasoning_summary``.
    attack_paths:
        The ``_gnn_attack_paths`` list produced by ``analyze_attack_paths``.
    ml_risk_score:
        File-level ML risk score (0.0–1.0).  Falls back to 0.0 if unavailable.

    Returns
    -------
    recommended_order:
        List of integer indices into *findings*, sorted by descending
        ``ranking_score``.  The original list order is **not** mutated.
    """
    ml_score = max(0.0, min(float(ml_risk_score or 0.0), 1.0))
    resource_path_map = _resources_on_paths(attack_paths)

    for finding in findings:
        resource = finding.get("resource") or ""
        path_entries = resource_path_map.get(resource)
        severity = (finding.get("severity") or "MEDIUM").upper()
        sev_weight = _SEV_WEIGHT.get(severity, 0.25)
        gnn_bonus = ml_score * _GNN_WEIGHT

        if path_entries:
            # Pick the highest-severity path this resource participates in
            best = max(path_entries, key=lambda p: p.get("hops", 0))
            finding["part_of_attack_path"] = True
            finding["attack_path_context"] = {
                "path_id": best["path_id"],
                "path_description": best["path_string"],
                "upstream_resources": best.get("upstream_resources", []),
                "downstream_resources": best.get("downstream_resources", []),
                "role_in_path": best.get("role", "intermediate"),
            }
            finding["ranking_score"] = round(
                min(sev_weight + gnn_bonus + _ATTACK_PATH_BONUS, 1.0), 4
            )
        else:
            finding["part_of_attack_path"] = False
            finding["attack_path_context"] = None
            finding["ranking_score"] = round(
                min(sev_weight + gnn_bonus, 1.0), 4
            )

        finding["reasoning_summary"] = _build_reasoning(
            finding,
            finding["part_of_attack_path"],
            finding.get("attack_path_context"),
        )

    # Build recommended_order: indices sorted by ranking_score desc,
    # with original index as tiebreaker (stable).
    recommended_order = sorted(
        range(len(findings)),
        key=lambda i: (-findings[i].get("ranking_score", 0.0), i),
    )

    return recommended_order
