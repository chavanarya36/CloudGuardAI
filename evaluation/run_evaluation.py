#!/usr/bin/env python3
"""CloudGuardAI Evaluation Harness

Runs the rules engine on all 50 evaluation dataset files, matches findings
against labels.json ground truth / expected findings, and computes metrics.

Usage:
    python -m evaluation.run_evaluation          # from project root
    python evaluation/run_evaluation.py          # from project root

Output:
    evaluation/results/metrics.json   - machine-readable metrics
    evaluation/results/report.md      - human-readable report
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# ---------------------------------------------------------------------------
# Setup import path so rules_engine is importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "rules"))

from rules_engine.engine import scan_single_file  # noqa: E402

DATASET_DIR = PROJECT_ROOT / "evaluation" / "dataset"
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"
LABELS_PATH = DATASET_DIR / "labels.json"

# ---------------------------------------------------------------------------
# Semantic category mapping: maps vulnerability type strings from
# ground_truth labels to broad categories for per-category recall.
# ---------------------------------------------------------------------------
VULNERABILITY_CATEGORIES: Dict[str, str] = {
    "ssh-open-to-internet": "security-groups",
    "rdp-open-to-internet": "security-groups",
    "all-ports-open-to-internet": "security-groups",
    "unrestricted-egress": "security-groups",
    "sg-open-to-internet": "security-groups",
    "s3-public-read": "s3",
    "s3-public-write": "s3",
    "s3-versioning-disabled": "s3",
    "s3-no-encryption": "s3",
    "s3-no-logging": "s3",
    "db-publicly-accessible": "databases",
    "db-unencrypted-storage": "databases",
    "skip-final-snapshot": "databases",
    "hardcoded-db-password": "secrets",
    "hardcoded-aws-access-key": "secrets",
    "hardcoded-aws-secret-key": "secrets",
    "hardcoded-ssm-secret": "secrets",
    "hardcoded-password-in-secret": "secrets",
    "embedded-private-key": "secrets",
    "hardcoded-connection-password": "secrets",
    "hardcoded-env-password": "secrets",
    "hardcoded-env-api-key": "secrets",
    "hardcoded-secret-in-userdata": "secrets",
    "iam-wildcard-policy": "iam",
    "iam-root-account-access": "iam",
    "ec2-public-ip": "ec2-ebs",
    "ec2-monitoring-disabled": "ec2-ebs",
    "ebs-unencrypted": "ec2-ebs",
}

# ---------------------------------------------------------------------------
# Rule-to-vulnerability mapping: maps rule IDs to the semantic vulnerability
# types they are capable of detecting.  Used for matching actual scanner
# findings to ground truth when multiple rules cover the same bug.
# ---------------------------------------------------------------------------
RULE_SEMANTIC_MAP: Dict[str, Set[str]] = {
    # Security group rules
    "AWS_CIS_SG_0_0_0_0": {"ssh-open-to-internet", "rdp-open-to-internet",
                            "all-ports-open-to-internet", "unrestricted-egress",
                            "sg-open-to-internet"},
    "TF_OPEN_SECURITY_GROUP": {"ssh-open-to-internet", "rdp-open-to-internet",
                                "all-ports-open-to-internet", "unrestricted-egress",
                                "sg-open-to-internet"},
    "AWS_CIS_SG_ALL_PORTS": {"all-ports-open-to-internet"},
    "AWS_OWASP_A05_MISCONFIG_SG": {"all-ports-open-to-internet", "unrestricted-egress"},
    "TF_WIDE_PORT_RANGE": {"all-ports-open-to-internet"},
    "AWS_BP_EGRESS_ALL": {"unrestricted-egress"},
    # S3 rules
    "AWS_CIS_S3_PUBLIC_ACL": {"s3-public-read", "s3-public-write"},
    "AWS_CIS_S3_PUBLIC_WRITE": {"s3-public-write"},
    "TF_PUBLIC_S3": {"s3-public-read", "s3-public-write"},
    "AWS_CIS_S3_VERSIONING_DISABLED": {"s3-versioning-disabled"},
    "TF_VERSIONING_DISABLED": {"s3-versioning-disabled"},
    "AWS_BP_S3_NO_LOGGING": {"s3-no-logging"},
    # DB rules
    "AWS_CIS_DB_PUBLIC": {"db-publicly-accessible"},
    "AWS_CIS_DB_UNENCRYPTED": {"db-unencrypted-storage"},
    "AWS_OWASP_A02_CRYPTO_FAILURE": {"db-unencrypted-storage", "ebs-unencrypted"},
    "AWS_BP_SKIP_FINAL_SNAPSHOT": {"skip-final-snapshot"},
    "TF_SKIP_SNAPSHOT": {"skip-final-snapshot"},
    "TF_UNENCRYPTED_RDS": {"db-unencrypted-storage"},
    "TF_UNENCRYPTED_EBS": {"ebs-unencrypted"},
    # Secrets rules
    "AWS_BP_HARDCODED_PASSWORD": {"hardcoded-db-password", "hardcoded-connection-password",
                                   "hardcoded-password-in-secret", "hardcoded-secret-in-userdata"},
    "AWS_OWASP_A07_AUTH_FAILURE": {"hardcoded-db-password", "hardcoded-connection-password",
                                    "hardcoded-password-in-secret", "hardcoded-secret-in-userdata"},
    "TF_HARDCODED_CREDENTIALS": {"hardcoded-db-password", "hardcoded-connection-password",
                                   "hardcoded-aws-access-key", "hardcoded-aws-secret-key",
                                   "hardcoded-password-in-secret", "hardcoded-secret-in-userdata",
                                   "hardcoded-env-password", "hardcoded-env-api-key"},
    "AWS_BP_HARDCODED_SECRET": {"hardcoded-aws-secret-key"},
    "AWS_BP_HARDCODED_ACCESS_KEY": {"hardcoded-aws-access-key"},
    "NO_HARDCODED_SECRET": {"hardcoded-db-password", "hardcoded-connection-password",
                             "hardcoded-password-in-secret", "hardcoded-secret-in-userdata",
                             "hardcoded-env-password", "hardcoded-env-api-key",
                             "hardcoded-ssm-secret"},
    # IAM rules
    "AWS_CIS_IAM_WILDCARD_POLICY": {"iam-wildcard-policy"},
    "AWS_CIS_IAM_ROOT_ACCESS": {"iam-root-account-access"},
    "AWS_BP_SSM_PLAINTEXT_SECRET": {"hardcoded-ssm-secret"},
    "TF_EMBEDDED_PRIVATE_KEY": {"embedded-private-key"},
    "TF_HARDCODED_ENV_SECRET": {"hardcoded-env-api-key", "hardcoded-secret-in-userdata"},
    # EC2/EBS rules
    "AWS_BP_EC2_NO_MONITORING": {"ec2-monitoring-disabled"},
    # Logging
    "AWS_OWASP_A09_LOGGING": set(),  # Too imprecise to map to a semantic vuln
}


# ---------------------------------------------------------------------------
# Core evaluation functions
# ---------------------------------------------------------------------------

def load_labels() -> Dict[str, Any]:
    """Load labels.json."""
    with open(LABELS_PATH, encoding="utf-8") as f:
        return json.load(f)


def scan_all_files() -> Dict[str, List[Dict[str, Any]]]:
    """Run the rules engine on every .tf file in the dataset.
    
    Returns dict mapping relative file path (e.g. 'vulnerable/vuln_01_sg_ssh_open.tf')
    to a list of finding dicts.
    """
    results: Dict[str, List[Dict[str, Any]]] = {}
    for subdir in ["vulnerable", "clean"]:
        folder = DATASET_DIR / subdir
        if not folder.exists():
            continue
        for tf_file in sorted(folder.glob("*.tf")):
            content = tf_file.read_text(encoding="utf-8", errors="ignore")
            findings = scan_single_file(tf_file, content)
            rel_key = f"{subdir}/{tf_file.name}"
            results[rel_key] = findings
    return results


def _candidate_matches(
    finding: Dict[str, Any],
    ground_truths: List[Dict[str, Any]],
    line_tolerance: int = 3,
) -> List[tuple[str, int]]:
    """Return all valid (gt_id, distance) pairs for a single finding.

    A candidate is valid if:
      1. The rule's semantic set includes the GT vulnerability type AND
         the finding line is within *line_tolerance* of the GT line
         (or the finding is file-level at line 1), OR
      2. The finding line exactly equals the GT line and the rule has
         no semantic mapping (fallback for unmapped rules).

    Returns a list of (gt_id, line_distance) tuples sorted by distance.
    """
    rule_id = finding.get("rule_id", "")
    finding_line = finding.get("line", 0)
    semantic_types = RULE_SEMANTIC_MAP.get(rule_id, set())

    candidates: List[tuple[str, int]] = []

    for gt in ground_truths:
        gt_vuln = gt.get("vulnerability", "")
        gt_line = gt.get("line", 0)

        # Strategy 1: semantic match + line proximity
        if gt_vuln in semantic_types:
            dist = abs(finding_line - gt_line)
            if dist <= line_tolerance:
                candidates.append((gt["id"], dist))
            elif finding_line == 1:
                # File-level rules — lenient match, large distance so
                # a line-precise match is preferred when available.
                candidates.append((gt["id"], 1000))

        # Strategy 2: fallback for unmapped rules on exact line
        elif finding_line == gt_line and rule_id not in RULE_SEMANTIC_MAP:
            candidates.append((gt["id"], 0))

    candidates.sort(key=lambda c: c[1])
    return candidates


def _optimal_match(
    findings: List[Dict[str, Any]],
    gt_list: List[Dict[str, Any]],
    line_tolerance: int = 3,
) -> tuple[Set[str], Set[int]]:
    """Compute an optimal 1-to-1 matching between findings and ground truth.

    Uses a greedy closest-first strategy over **all** (finding, GT) candidate
    pairs sorted by line distance.  This avoids the previous sequential bias
    where the iteration order of findings could shadow an adjacent GT entry.

    Returns:
        gt_matched:      set of GT ids that were successfully matched
        finding_matched: set of finding indices that were successfully matched
    """
    # Build all candidate edges: (distance, finding_idx, gt_id)
    edges: List[tuple[int, int, str]] = []
    for i, finding in enumerate(findings):
        for gt_id, dist in _candidate_matches(finding, gt_list, line_tolerance):
            edges.append((dist, i, gt_id))

    # Sort by distance — ties broken by finding index (stable)
    edges.sort(key=lambda e: (e[0], e[1]))

    gt_matched: Set[str] = set()
    finding_matched: Set[int] = set()

    for _dist, f_idx, gt_id in edges:
        if f_idx in finding_matched or gt_id in gt_matched:
            continue
        gt_matched.add(gt_id)
        finding_matched.add(f_idx)

    return gt_matched, finding_matched


def evaluate(
    scan_results: Dict[str, List[Dict[str, Any]]],
    labels: Dict[str, Any],
    exclude_rules: Set[str] | None = None,
) -> Dict[str, Any]:
    """Evaluate scan results against labels.
    
    Args:
        scan_results: actual findings per file
        labels: loaded labels.json
        exclude_rules: set of rule_ids to exclude from analysis (diagnostic mode)
    
    Returns:
        Dict with all computed metrics.
    """
    exclude_rules = exclude_rules or set()
    files_data = labels.get("files", {})
    
    # Accumulators
    total_tp = 0
    total_fp = 0
    total_fn = 0
    total_tn_files = 0  # clean files with zero findings
    
    # Per-file details
    per_file_results: Dict[str, Dict] = {}
    
    # Per-category tracking: category -> {detected, total}
    category_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"detected": 0, "total": 0})
    
    # FP tracking: rule_id -> count
    fp_by_rule: Dict[str, int] = defaultdict(int)
    
    # Missed vulnerabilities (FN)
    missed_vulns: List[Dict[str, Any]] = []
    
    # Actual finding tracking per rule
    findings_by_rule: Dict[str, int] = defaultdict(int)
    tp_by_rule: Dict[str, int] = defaultdict(int)
    
    for file_key, file_labels in files_data.items():
        gt_list = file_labels.get("ground_truth", [])
        category = file_labels.get("category", "unknown")
        
        # Get actual findings for this file, with exclusions applied
        raw_findings = scan_results.get(file_key, [])
        findings = [f for f in raw_findings if f.get("rule_id") not in exclude_rules]
        
        # Track all findings by rule
        for f in findings:
            findings_by_rule[f.get("rule_id", "UNKNOWN")] += 1
        
        # --- Optimal 1-to-1 matching between findings and ground truth ---
        gt_matched, finding_matched = _optimal_match(findings, gt_list)

        total_tp += len(gt_matched & {gt["id"] for gt in gt_list})
        for i in finding_matched:
            tp_by_rule[findings[i].get("rule_id", "UNKNOWN")] += 1

        # For unmatched findings, check if they are redundant detections
        # of an already-matched GT.  Redundant findings are neither TP nor FP.
        redundant: Set[int] = set()
        for i, finding in enumerate(findings):
            if i in finding_matched:
                continue
            candidates = _candidate_matches(finding, gt_list)
            if any(gt_id in gt_matched for gt_id, _dist in candidates):
                redundant.add(i)

        # Unmatched findings that are NOT redundant are false positives
        for i, finding in enumerate(findings):
            if i not in finding_matched and i not in redundant:
                total_fp += 1
                fp_by_rule[finding.get("rule_id", "UNKNOWN")] += 1
        
        # Unmatched ground truth entries are false negatives
        file_fn = []
        for gt in gt_list:
            if gt["id"] not in gt_matched:
                total_fn += 1
                cat = VULNERABILITY_CATEGORIES.get(gt.get("vulnerability", ""), "other")
                missed_vulns.append({
                    "file": file_key,
                    "gt_id": gt["id"],
                    "line": gt.get("line", 0),
                    "vulnerability": gt.get("vulnerability", ""),
                    "severity": gt.get("severity", ""),
                    "description": gt.get("description", ""),
                    "category": cat,
                    "detection_gap": gt.get("detection_gap", False),
                })
                file_fn.append(gt["id"])
        
        # Per-category recall tracking
        for gt in gt_list:
            vuln_type = gt.get("vulnerability", "")
            cat = VULNERABILITY_CATEGORIES.get(vuln_type, "other")
            category_stats[cat]["total"] += 1
            if gt["id"] in gt_matched:
                category_stats[cat]["detected"] += 1
        
        # Clean file with no findings = true negative
        if category == "clean" and len(findings) == 0:
            total_tn_files += 1
        
        per_file_results[file_key] = {
            "category": category,
            "total_findings": len(findings),
            "tp": len(gt_matched),
            "fp": len(findings) - len(finding_matched),
            "fn": len(file_fn),
            "matched_gt": sorted(gt_matched),
            "missed_gt": file_fn,
        }
    
    # --- Compute overall metrics ---
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    # Count clean files total and those with FP findings
    clean_files_total = sum(1 for f in files_data.values() if f.get("category") == "clean")
    clean_files_with_fp = sum(
        1 for k, v in per_file_results.items()
        if files_data[k].get("category") == "clean" and v["fp"] > 0
    )
    false_positive_rate = clean_files_with_fp / clean_files_total if clean_files_total > 0 else 0.0
    
    # Per-category recall
    category_recall = {}
    for cat, stats in sorted(category_stats.items()):
        r = stats["detected"] / stats["total"] if stats["total"] > 0 else 0.0
        category_recall[cat] = {
            "detected": stats["detected"],
            "total": stats["total"],
            "recall": round(r, 4),
        }
    
    # Top FP rules
    top_fp_rules = sorted(fp_by_rule.items(), key=lambda x: x[1], reverse=True)
    
    # Total findings
    total_findings = sum(len(f) for f in scan_results.values())
    total_findings_filtered = sum(
        len([f for f in findings if f.get("rule_id") not in exclude_rules])
        for findings in scan_results.values()
    )
    
    return {
        "confusion_matrix": {
            "TP": total_tp,
            "FP": total_fp,
            "FN": total_fn,
            "TN_clean_files": total_tn_files,
        },
        "metrics": {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "false_positive_rate_on_clean_files": round(false_positive_rate, 4),
        },
        "total_findings_produced": total_findings_filtered,
        "category_recall": category_recall,
        "top_fp_rules": [{"rule_id": r, "fp_count": c} for r, c in top_fp_rules[:10]],
        "top_tp_rules": [
            {"rule_id": r, "tp_count": c}
            for r, c in sorted(tp_by_rule.items(), key=lambda x: x[1], reverse=True)[:10]
        ],
        "missed_vulnerabilities": missed_vulns,
        "per_file": per_file_results,
        "excluded_rules": sorted(exclude_rules),
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(
    baseline_eval: Dict[str, Any],
    diagnostic_eval: Dict[str, Any],
    worst_rule: str,
    scan_results: Dict[str, List[Dict[str, Any]]],
) -> str:
    """Generate a markdown evaluation report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines = [
        "# CloudGuardAI Evaluation Report",
        "",
        f"**Generated**: {now}",
        f"**Dataset**: 50 Terraform files (25 vulnerable, 25 clean)",
        f"**Scanner**: Rules Engine (29 rules across 5 YAML rule files)",
        "",
        "---",
        "",
        "## 1. Overall Metrics — Current Ruleset",
        "",
        "| Metric | Value |",
        "|--------|-------|",
    ]
    
    bm = baseline_eval["metrics"]
    bc = baseline_eval["confusion_matrix"]
    lines.extend([
        f"| Precision | {bm['precision']:.4f} ({bm['precision']*100:.1f}%) |",
        f"| Recall | {bm['recall']:.4f} ({bm['recall']*100:.1f}%) |",
        f"| F1 Score | {bm['f1_score']:.4f} |",
        f"| FP Rate (clean files) | {bm['false_positive_rate_on_clean_files']:.4f} ({bm['false_positive_rate_on_clean_files']*100:.1f}%) |",
        "",
        "### Confusion Matrix",
        "",
        "| | Predicted Positive | Predicted Negative |",
        "|---|---|---|",
        f"| **Actual Positive** | TP = {bc['TP']} | FN = {bc['FN']} |",
        f"| **Actual Negative** | FP = {bc['FP']} | — |",
        "",
        f"- **Total findings produced**: {baseline_eval['total_findings_produced']}",
        f"- **True Positives**: {bc['TP']} (findings matching a real vulnerability)",
        f"- **False Positives**: {bc['FP']} (findings with no corresponding vulnerability)",
        f"- **False Negatives**: {bc['FN']} (real vulnerabilities not detected)",
        f"- **Clean files with zero findings**: {bc['TN_clean_files']} / 25",
        "",
        "---",
        "",
        f"## 2. Diagnostic: Metrics Excluding `{worst_rule}` (single worst noisy rule)",
        "",
        "*This section shows system performance if the single noisiest rule were removed.*",
        "*It is labeled as diagnostic — not a proposal to remove the rule.*",
        "",
        "| Metric | Current | Excluding {0} | Delta |".format(worst_rule),
        "|--------|---------|{0}|-------|".format("-" * (len(worst_rule) + 12)),
    ])
    
    dm = diagnostic_eval["metrics"]
    dc = diagnostic_eval["confusion_matrix"]
    lines.extend([
        f"| Precision | {bm['precision']:.4f} | {dm['precision']:.4f} | {dm['precision']-bm['precision']:+.4f} |",
        f"| Recall | {bm['recall']:.4f} | {dm['recall']:.4f} | {dm['recall']-bm['recall']:+.4f} |",
        f"| F1 Score | {bm['f1_score']:.4f} | {dm['f1_score']:.4f} | {dm['f1_score']-bm['f1_score']:+.4f} |",
        f"| FP Rate | {bm['false_positive_rate_on_clean_files']:.4f} | {dm['false_positive_rate_on_clean_files']:.4f} | {dm['false_positive_rate_on_clean_files']-bm['false_positive_rate_on_clean_files']:+.4f} |",
        f"| Total FP | {bc['FP']} | {dc['FP']} | {dc['FP']-bc['FP']:+d} |",
        "",
        "---",
        "",
        "## 3. Per-Category Recall",
        "",
        "| Category | Detected | Total | Recall |",
        "|----------|----------|-------|--------|",
    ])
    
    for cat, stats in sorted(baseline_eval["category_recall"].items()):
        r = stats["recall"]
        bar = "█" * int(r * 10) + "░" * (10 - int(r * 10))
        lines.append(
            f"| {cat} | {stats['detected']} | {stats['total']} | {r:.1%} {bar} |"
        )
    
    lines.extend([
        "",
        "---",
        "",
        "## 4. Top 5 Rules Hurting Precision (by FP count)",
        "",
        "| Rank | Rule ID | FP Count | Notes |",
        "|------|---------|----------|-------|",
    ])
    
    for i, item in enumerate(baseline_eval["top_fp_rules"][:5], 1):
        rid = item["rule_id"]
        # Add the known issue notes
        note = ""
        if rid == "AWS_BP_S3_NO_LOGGING":
            note = "not_contains 'logging {' fires on all non-S3 files"
        elif rid == "NO_HARDCODED_SECRET":
            note = "Case-insensitive regex matches attribute names, not values"
        elif rid == "TF_UNENCRYPTED_RDS":
            note = "terraform_block_match ignores missing_attribute"
        elif rid == "TF_UNENCRYPTED_EBS":
            note = "terraform_block_match ignores missing_attribute"
        elif rid == "AWS_OWASP_A05_MISCONFIG_SG":
            note = "from_port=0 matches egress rules too"
        lines.append(f"| {i} | `{rid}` | {item['fp_count']} | {note} |")
    
    lines.extend([
        "",
        "---",
        "",
        "## 5. Top 5 Missed Vulnerabilities (False Negatives)",
        "",
        "| Rank | File | Line | Vulnerability | Severity | Detection Gap? |",
        "|------|------|------|---------------|----------|----------------|",
    ])
    
    # Sort by severity (CRITICAL first), then by detection_gap
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    sorted_missed = sorted(
        baseline_eval["missed_vulnerabilities"],
        key=lambda x: (severity_order.get(x["severity"], 9), not x.get("detection_gap", False)),
    )
    
    for i, mv in enumerate(sorted_missed[:5], 1):
        gap = "YES — no rule exists" if mv.get("detection_gap") else "no"
        lines.append(
            f"| {i} | `{mv['file']}` | L{mv['line']} | {mv['vulnerability']} | {mv['severity']} | {gap} |"
        )
    
    lines.extend([
        "",
        "---",
        "",
        "## 6. All Missed Vulnerabilities (Complete FN List)",
        "",
        f"Total missed: **{len(baseline_eval['missed_vulnerabilities'])}** out of "
        f"**{bc['TP'] + len(baseline_eval['missed_vulnerabilities'])}** ground truth instances.",
        "",
        "| GT ID | File | Line | Vulnerability | Severity | Category | Detection Gap? |",
        "|-------|------|------|---------------|----------|----------|----------------|",
    ])
    for mv in sorted_missed:
        gap = "YES" if mv.get("detection_gap") else "" 
        lines.append(
            f"| {mv['gt_id']} | `{mv['file']}` | L{mv['line']} | {mv['vulnerability']} "
            f"| {mv['severity']} | {mv['category']} | {gap} |"
        )
    
    lines.extend([
        "",
        "---",
        "",
        "## 7. Per-File Summary",
        "",
        "### Vulnerable Files",
        "",
        "| File | Findings | TP | FP | FN | Status |",
        "|------|----------|----|----|-----|--------|",
    ])
    
    for fk in sorted(baseline_eval["per_file"].keys()):
        pf = baseline_eval["per_file"][fk]
        if pf["category"] != "vulnerable":
            continue
        status = "✅" if pf["fn"] == 0 else f"⚠️ missed {pf['fn']}"
        short_name = fk.split("/")[-1]
        lines.append(
            f"| `{short_name}` | {pf['total_findings']} | {pf['tp']} | {pf['fp']} | {pf['fn']} | {status} |"
        )
    
    lines.extend([
        "",
        "### Clean Files",
        "",
        "| File | Findings (all FP) | Status |",
        "|------|-------------------|--------|",
    ])
    
    for fk in sorted(baseline_eval["per_file"].keys()):
        pf = baseline_eval["per_file"][fk]
        if pf["category"] != "clean":
            continue
        status = "✅ clean" if pf["total_findings"] == 0 else f"⚠️ {pf['fp']} FP"
        short_name = fk.split("/")[-1]
        lines.append(
            f"| `{short_name}` | {pf['total_findings']} | {status} |"
        )
    
    lines.extend([
        "",
        "---",
        "",
        "## 8. Methodology",
        "",
        "1. **Scanner**: CloudGuardAI rules engine (`rules_engine.engine.scan_single_file`)",
        "2. **Finding matching**: Each actual finding is matched to ground truth using:",
        "   - Rule-to-semantic mapping (RULE_SEMANTIC_MAP) that links rule IDs to vulnerability types",
        "   - Line proximity (±3 lines tolerance) to handle minor line offset differences",
        "   - File-level rules (line=1) are matched more leniently",
        "3. **A finding is TP if**: it matches both a semantic vulnerability type AND a nearby line in ground truth",
        "4. **A finding is FP if**: it does not match any ground truth entry",
        "5. **A GT entry is FN if**: no finding was matched to it",
        "6. **Per-category recall**: ground truth entries grouped by vulnerability category",
        "7. **Diagnostic mode**: same evaluation with the single noisiest rule excluded",
        "",
    ])
    
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("CloudGuardAI Evaluation Harness")
    print("=" * 60)
    
    # 1. Load labels
    print("\n[1/5] Loading labels.json ...")
    labels = load_labels()
    file_count = len(labels.get("files", {}))
    gt_count = sum(
        len(f.get("ground_truth", []))
        for f in labels.get("files", {}).values()
    )
    print(f"  → {file_count} files, {gt_count} ground truth instances")
    
    # 2. Scan all files
    print("\n[2/5] Scanning all dataset files with rules engine ...")
    scan_results = scan_all_files()
    total_findings = sum(len(v) for v in scan_results.values())
    print(f"  → Scanned {len(scan_results)} files")
    print(f"  → Total findings produced: {total_findings}")
    
    # 3. Evaluate — baseline (all rules)
    print("\n[3/5] Evaluating findings against ground truth (baseline) ...")
    baseline_eval = evaluate(scan_results, labels, exclude_rules=set())
    bm = baseline_eval["metrics"]
    bc = baseline_eval["confusion_matrix"]
    print(f"  → TP={bc['TP']}  FP={bc['FP']}  FN={bc['FN']}")
    print(f"  → Precision={bm['precision']:.4f}  Recall={bm['recall']:.4f}  F1={bm['f1_score']:.4f}")
    
    # 4. Find worst rule, evaluate diagnostic
    if baseline_eval["top_fp_rules"]:
        worst_rule = baseline_eval["top_fp_rules"][0]["rule_id"]
    else:
        worst_rule = "NONE"
    print(f"\n[4/5] Diagnostic: re-evaluating excluding '{worst_rule}' ...")
    diagnostic_eval = evaluate(scan_results, labels, exclude_rules={worst_rule})
    dm = diagnostic_eval["metrics"]
    dc = diagnostic_eval["confusion_matrix"]
    print(f"  → TP={dc['TP']}  FP={dc['FP']}  FN={dc['FN']}")
    print(f"  → Precision={dm['precision']:.4f}  Recall={dm['recall']:.4f}  F1={dm['f1_score']:.4f}")
    
    # 5. Write results
    print("\n[5/5] Writing results ...")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # metrics.json
    metrics_data = {
        "generated_at": datetime.now().isoformat(),
        "dataset": {
            "total_files": file_count,
            "ground_truth_instances": gt_count,
            "total_findings_produced": total_findings,
        },
        "baseline": {
            "confusion_matrix": baseline_eval["confusion_matrix"],
            "metrics": baseline_eval["metrics"],
            "category_recall": baseline_eval["category_recall"],
            "top_fp_rules": baseline_eval["top_fp_rules"][:5],
            "top_tp_rules": baseline_eval["top_tp_rules"][:5],
            "missed_vulnerabilities_count": len(baseline_eval["missed_vulnerabilities"]),
            "missed_vulnerabilities": baseline_eval["missed_vulnerabilities"],
        },
        "diagnostic": {
            "excluded_rule": worst_rule,
            "confusion_matrix": diagnostic_eval["confusion_matrix"],
            "metrics": diagnostic_eval["metrics"],
            "category_recall": diagnostic_eval["category_recall"],
        },
    }
    
    metrics_path = RESULTS_DIR / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2, ensure_ascii=False)
    print(f"  → {metrics_path}")
    
    # report.md
    report = generate_report(baseline_eval, diagnostic_eval, worst_rule, scan_results)
    report_path = RESULTS_DIR / "report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  → {report_path}")
    
    print("\n" + "=" * 60)
    print("EVALUATION COMPLETE")
    print("=" * 60)
    print(f"\nBaseline:    P={bm['precision']:.3f}  R={bm['recall']:.3f}  F1={bm['f1_score']:.3f}")
    print(f"Diagnostic:  P={dm['precision']:.3f}  R={dm['recall']:.3f}  F1={dm['f1_score']:.3f}  (excl. {worst_rule})")


if __name__ == "__main__":
    main()
