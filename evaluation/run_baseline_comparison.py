#!/usr/bin/env python3
"""Baseline Comparison: CloudGuard vs Checkov vs tfsec

Runs Checkov and tfsec on the same 50-file evaluation dataset,
normalizes their outputs to semantic vulnerability types, and
evaluates them using the same ground truth and matching algorithm
as CloudGuard's own evaluation.

Raw tool outputs are saved for reproducibility.

Usage:
    python evaluation/run_baseline_comparison.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "rules"))

DATASET_DIR = PROJECT_ROOT / "evaluation" / "dataset"
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"
LABELS_PATH = DATASET_DIR / "labels.json"
TFSEC_BIN = PROJECT_ROOT / "evaluation" / "tools" / "tfsec.exe"

# Import shared evaluation functions from the main harness
from run_evaluation import (
    VULNERABILITY_CATEGORIES,
    RULE_SEMANTIC_MAP,
    _candidate_matches,
    _optimal_match,
    load_labels,
    scan_all_files,
)

# ---------------------------------------------------------------------------
# Checkov check_id -> semantic vulnerability type mapping
# ---------------------------------------------------------------------------
CHECKOV_SEMANTIC_MAP: Dict[str, Set[str]] = {
    # Security Groups
    "CKV_AWS_24":  {"ssh-open-to-internet"},
    "CKV_AWS_25":  {"rdp-open-to-internet"},
    "CKV_AWS_260": {"all-ports-open-to-internet", "sg-open-to-internet"},
    "CKV_AWS_277": {"all-ports-open-to-internet", "sg-open-to-internet"},
    "CKV2_AWS_5":  set(),  # SG not attached — not in our GT
    # S3
    "CKV_AWS_18":  {"s3-no-logging"},
    "CKV_AWS_19":  {"s3-no-encryption"},
    "CKV_AWS_20":  {"s3-public-read", "s3-public-write"},
    "CKV_AWS_21":  {"s3-versioning-disabled"},
    "CKV_AWS_53":  {"s3-public-read", "s3-public-write"},
    "CKV_AWS_54":  {"s3-public-read", "s3-public-write"},
    "CKV_AWS_55":  {"s3-public-read", "s3-public-write"},
    "CKV_AWS_57":  {"s3-public-read", "s3-public-write"},
    "CKV_AWS_145": {"s3-no-encryption"},
    "CKV2_AWS_6":  {"s3-public-read", "s3-public-write"},
    "CKV2_AWS_61": {"s3-no-logging"},
    "CKV2_AWS_62": {"s3-no-logging"},
    # Databases
    "CKV_AWS_16":  {"db-unencrypted-storage"},
    "CKV_AWS_17":  {"db-publicly-accessible"},
    "CKV_AWS_23":  {"db-unencrypted-storage"},
    "CKV_AWS_133": {"skip-final-snapshot"},
    "CKV_AWS_226": {"db-unencrypted-storage"},
    "CKV_AWS_293": {"db-publicly-accessible"},
    "CKV_AWS_354": {"db-unencrypted-storage"},
    "CKV2_AWS_30": {"skip-final-snapshot"},
    # Secrets / Credentials
    "CKV_AWS_46":  {"hardcoded-db-password", "hardcoded-connection-password",
                     "hardcoded-env-password"},
    "CKV_SECRET_6": {"hardcoded-aws-access-key", "hardcoded-aws-secret-key"},
    "CKV_SECRET_2": {"hardcoded-db-password", "hardcoded-connection-password",
                      "hardcoded-env-password", "hardcoded-secret-in-userdata"},
    "CKV_SECRET_4": {"hardcoded-env-api-key"},
    "CKV_SECRET_13": {"embedded-private-key"},
    "CKV_SECRET_14": {"hardcoded-env-api-key", "hardcoded-ssm-secret"},
    "CKV_SECRET_19": {"hardcoded-db-password", "hardcoded-env-password"},
    "CKV2_AWS_57":  {"hardcoded-ssm-secret"},
    # IAM
    "CKV_AWS_1":   {"iam-wildcard-policy"},
    "CKV_AWS_49":  {"iam-wildcard-policy"},
    "CKV_AWS_61":  {"iam-wildcard-policy"},
    "CKV_AWS_289": {"iam-wildcard-policy"},
    "CKV_AWS_290": {"iam-wildcard-policy"},
    "CKV_AWS_355": {"iam-wildcard-policy"},
    "CKV_AWS_40":  {"iam-root-account-access"},
    # EC2 / EBS
    "CKV_AWS_3":   {"ebs-unencrypted"},
    "CKV_AWS_8":   {"ebs-unencrypted"},
    "CKV_AWS_88":  {"ec2-public-ip"},
    "CKV_AWS_79":  {"ec2-monitoring-disabled"},
    # Lambda
    "CKV_AWS_45":  {"hardcoded-env-api-key", "hardcoded-env-password",
                     "hardcoded-secret-in-userdata"},
}

# ---------------------------------------------------------------------------
# tfsec (AVD) rule_id -> semantic vulnerability type mapping
# ---------------------------------------------------------------------------
TFSEC_SEMANTIC_MAP: Dict[str, Set[str]] = {
    # Security Groups
    "AVD-AWS-0107": {"ssh-open-to-internet", "rdp-open-to-internet",
                      "all-ports-open-to-internet", "sg-open-to-internet"},
    "AVD-AWS-0104": {"all-ports-open-to-internet", "sg-open-to-internet"},
    "AVD-AWS-0124": set(),  # missing description — not in GT
    # S3
    "AVD-AWS-0086": {"s3-public-read", "s3-public-write"},
    "AVD-AWS-0087": {"s3-no-encryption"},
    "AVD-AWS-0088": {"s3-no-logging"},
    "AVD-AWS-0089": {"s3-versioning-disabled"},
    "AVD-AWS-0090": {"s3-public-read", "s3-public-write"},
    "AVD-AWS-0091": {"s3-no-encryption"},
    "AVD-AWS-0093": {"s3-public-read", "s3-public-write"},
    "AVD-AWS-0094": {"s3-public-read", "s3-public-write"},
    "AVD-AWS-0132": {"s3-public-read", "s3-public-write"},
    # Databases
    "AVD-AWS-0176": {"db-unencrypted-storage"},
    "AVD-AWS-0177": {"db-publicly-accessible"},
    "AVD-AWS-0180": {"skip-final-snapshot"},
    "AVD-AWS-0343": {"db-unencrypted-storage"},
    "AVD-AWS-0080": {"db-unencrypted-storage"},
    "AVD-AWS-0082": {"db-publicly-accessible"},
    "AVD-AWS-0133": {"skip-final-snapshot"},
    # Secrets
    "AVD-AWS-0098": {"hardcoded-db-password", "hardcoded-connection-password",
                      "hardcoded-env-password", "hardcoded-secret-in-userdata"},
    # IAM
    "AVD-AWS-0057": {"iam-wildcard-policy"},
    "AVD-AWS-0053": {"iam-root-account-access"},
    "AVD-AWS-0342": {"iam-wildcard-policy"},
    # EC2 / EBS
    "AVD-AWS-0131": {"ec2-public-ip"},
    "AVD-AWS-0026": {"ebs-unencrypted"},
    "AVD-AWS-0027": {"ebs-unencrypted"},
    # Lambda
    "AVD-AWS-0067": {"hardcoded-env-api-key", "hardcoded-env-password",
                      "hardcoded-secret-in-userdata"},
    # SSM
    "AVD-AWS-0098": {"hardcoded-ssm-secret", "hardcoded-db-password",
                      "hardcoded-env-password", "hardcoded-secret-in-userdata"},
}


# ======================================================================
# Tool runners
# ======================================================================

def run_checkov(dataset_dir: Path) -> List[Dict[str, Any]]:
    """Run Checkov on the full dataset directory and return raw results."""
    print("  Running Checkov ...")
    cmd = [
        sys.executable, "-m", "checkov.main",
        "-d", str(dataset_dir),
        "-o", "json",
        "--quiet",
        "--compact",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                            env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    # Checkov may exit non-zero when findings exist
    raw_text = result.stdout or result.stderr
    # Save raw output
    raw_path = RESULTS_DIR / "checkov_raw.json"
    raw_path.write_text(raw_text, encoding="utf-8")
    print(f"  Saved raw output -> {raw_path}")

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        # Sometimes Checkov returns array of results
        # Try to find JSON array or object in the output
        for line_start in range(len(raw_text)):
            ch = raw_text[line_start]
            if ch in ("{", "["):
                try:
                    data = json.loads(raw_text[line_start:])
                    break
                except json.JSONDecodeError:
                    continue
        else:
            print("  WARNING: Could not parse Checkov JSON output")
            return []

    # Normalize: Checkov may return a single object or array
    if isinstance(data, dict):
        data = [data]

    return data


def run_tfsec(dataset_dir: Path) -> Dict[str, Any]:
    """Run tfsec on the full dataset directory and return raw results."""
    print("  Running tfsec ...")
    cmd = [
        str(TFSEC_BIN),
        str(dataset_dir),
        "-f", "json",
        "--no-color",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    raw_text = result.stdout or result.stderr
    # Save raw output
    raw_path = RESULTS_DIR / "tfsec_raw.json"
    raw_path.write_text(raw_text, encoding="utf-8")
    print(f"  Saved raw output -> {raw_path}")

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        # tfsec stderr sometimes has banner text before JSON
        for line_start in range(len(raw_text)):
            ch = raw_text[line_start]
            if ch in ("{", "["):
                try:
                    data = json.loads(raw_text[line_start:])
                    break
                except json.JSONDecodeError:
                    continue
        else:
            print("  WARNING: Could not parse tfsec JSON output")
            return {}

    return data


# ======================================================================
# Normalizers: tool-specific output -> {file_key: [finding_dicts]}
# ======================================================================

def _file_key_from_abs_path(abs_path: str) -> str | None:
    """Convert an absolute file path to a dataset-relative key like 'vulnerable/vuln_01.tf'.
    
    Returns None if the path doesn't belong to the dataset directory.
    """
    abs_path = abs_path.replace("\\", "/")
    dataset_str = str(DATASET_DIR).replace("\\", "/")
    if dataset_str in abs_path:
        rel = abs_path.split(dataset_str)[-1].lstrip("/")
        return rel
    # Try matching on just the filename
    for subdir in ("vulnerable", "clean"):
        fname = Path(abs_path).name
        candidate = f"{subdir}/{fname}"
        full = DATASET_DIR / subdir / fname
        if full.exists():
            return candidate
    return None


def normalize_checkov(raw_results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Normalize Checkov results to {file_key: [finding_dict, ...]} format."""
    results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    for result_block in raw_results:
        failed_checks = result_block.get("results", {}).get("failed_checks", [])
        for check in failed_checks:
            check_id = check.get("check_id", "")
            check_name = check.get("check_name", "")
            resource = check.get("resource", "")
            severity = check.get("severity") or "MEDIUM"
            
            # File path extraction
            abs_path = check.get("file_abs_path", "")
            if not abs_path:
                abs_path = check.get("repo_file_path", "")
            file_key = _file_key_from_abs_path(abs_path)
            if not file_key:
                continue
            
            # Line number: use start of resource block
            line_range = check.get("file_line_range", [1, 1])
            line = line_range[0] if line_range else 1
            
            results[file_key].append({
                "rule_id": f"CHECKOV_{check_id}",
                "line": line,
                "severity": severity.upper() if isinstance(severity, str) else "MEDIUM",
                "description": check_name,
                "resource": resource,
                "evidence": f"{check_id}: {check_name}",
                "tool": "checkov",
            })
    
    return dict(results)


def normalize_tfsec(raw_result: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Normalize tfsec results to {file_key: [finding_dict, ...]} format."""
    results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    tfsec_results = raw_result.get("results", [])
    if tfsec_results is None:
        tfsec_results = []
    
    for finding in tfsec_results:
        rule_id = finding.get("rule_id", "")
        description = finding.get("rule_description", finding.get("description", ""))
        severity = finding.get("severity", "MEDIUM")
        resource = finding.get("resource", "")
        
        location = finding.get("location", {})
        filename = location.get("filename", "")
        start_line = location.get("start_line", 1)
        
        file_key = _file_key_from_abs_path(filename)
        if not file_key:
            continue
        
        results[file_key].append({
            "rule_id": f"TFSEC_{rule_id}",
            "line": start_line,
            "severity": severity.upper(),
            "description": description,
            "resource": resource,
            "evidence": f"{rule_id}: {description}",
            "tool": "tfsec",
        })
    
    return dict(results)


# ======================================================================
# Evaluation using the same matching algorithm
# ======================================================================

def evaluate_tool(
    tool_name: str,
    scan_results: Dict[str, List[Dict[str, Any]]],
    labels: Dict[str, Any],
    semantic_map: Dict[str, Set[str]],
) -> Dict[str, Any]:
    """Evaluate a tool's results using the same matching logic as CloudGuard.
    
    Temporarily patches RULE_SEMANTIC_MAP to include the tool-specific mapping.
    """
    # Build the tool-specific semantic map (prefixed rule IDs)
    tool_map: Dict[str, Set[str]] = {}
    prefix = "CHECKOV_" if tool_name == "Checkov" else "TFSEC_"
    for check_id, vuln_types in semantic_map.items():
        tool_map[f"{prefix}{check_id}"] = vuln_types
    
    # Temporarily inject tool map into RULE_SEMANTIC_MAP
    original_map = dict(RULE_SEMANTIC_MAP)
    RULE_SEMANTIC_MAP.clear()
    RULE_SEMANTIC_MAP.update(tool_map)
    
    try:
        files_data = labels.get("files", {})
        
        total_tp = 0
        total_fp = 0
        total_fn = 0
        total_tn_files = 0
        
        category_stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"detected": 0, "total": 0}
        )
        fp_by_rule: Dict[str, int] = defaultdict(int)
        tp_by_rule: Dict[str, int] = defaultdict(int)
        missed_vulns: List[Dict[str, Any]] = []
        per_file_results: Dict[str, Dict] = {}
        
        for file_key, file_labels in files_data.items():
            gt_list = file_labels.get("ground_truth", [])
            category = file_labels.get("category", "unknown")
            
            findings = scan_results.get(file_key, [])
            
            # Optimal matching
            gt_matched, finding_matched = _optimal_match(findings, gt_list)
            
            total_tp += len(gt_matched & {gt["id"] for gt in gt_list})
            for i in finding_matched:
                tp_by_rule[findings[i].get("rule_id", "UNKNOWN")] += 1
            
            # Redundancy check
            redundant: Set[int] = set()
            for i, finding in enumerate(findings):
                if i in finding_matched:
                    continue
                candidates = _candidate_matches(finding, gt_list)
                if any(gt_id in gt_matched for gt_id, _dist in candidates):
                    redundant.add(i)
            
            # FPs
            for i, finding in enumerate(findings):
                if i not in finding_matched and i not in redundant:
                    total_fp += 1
                    fp_by_rule[finding.get("rule_id", "UNKNOWN")] += 1
            
            # FNs
            for gt in gt_list:
                if gt["id"] not in gt_matched:
                    total_fn += 1
                    cat = VULNERABILITY_CATEGORIES.get(gt.get("vulnerability", ""), "other")
                    missed_vulns.append({
                        "file": file_key,
                        "gt_id": gt["id"],
                        "vulnerability": gt.get("vulnerability", ""),
                        "severity": gt.get("severity", ""),
                        "category": cat,
                    })
            
            # Per-category recall
            for gt in gt_list:
                vuln_type = gt.get("vulnerability", "")
                cat = VULNERABILITY_CATEGORIES.get(vuln_type, "other")
                category_stats[cat]["total"] += 1
                if gt["id"] in gt_matched:
                    category_stats[cat]["detected"] += 1
            
            if category == "clean" and len(findings) == 0:
                total_tn_files += 1
            
            per_file_results[file_key] = {
                "category": category,
                "total_findings": len(findings),
                "tp": len(gt_matched),
                "fp": sum(1 for i in range(len(findings))
                          if i not in finding_matched and i not in redundant),
                "fn": sum(1 for gt in gt_list if gt["id"] not in gt_matched),
            }
        
        # Compute metrics
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        clean_files = sum(1 for f in files_data.values() if f.get("category") == "clean")
        clean_with_fp = sum(1 for k, v in per_file_results.items()
                            if v["category"] == "clean" and v["fp"] > 0)
        fp_rate = clean_with_fp / clean_files if clean_files > 0 else 0.0
        
        # Category recall
        cat_recall = {}
        for cat in sorted(category_stats.keys()):
            s = category_stats[cat]
            cat_recall[cat] = {
                "detected": s["detected"],
                "total": s["total"],
                "recall": round(s["detected"] / s["total"], 4) if s["total"] > 0 else 0.0,
            }
        
        # Top FP rules
        top_fp = sorted(fp_by_rule.items(), key=lambda x: -x[1])[:5]
        
        total_findings = sum(len(v) for v in scan_results.values())
        
        return {
            "tool": tool_name,
            "total_findings": total_findings,
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
                "false_positive_rate_on_clean_files": round(fp_rate, 4),
            },
            "category_recall": cat_recall,
            "top_fp_rules": [{"rule_id": r, "fp_count": c} for r, c in top_fp],
            "missed_vulnerabilities_count": len(missed_vulns),
            "missed_vulnerabilities": missed_vulns,
            "per_file_results": per_file_results,
        }
    finally:
        # Restore original map
        RULE_SEMANTIC_MAP.clear()
        RULE_SEMANTIC_MAP.update(original_map)


# ======================================================================
# Comparison report generation
# ======================================================================

def generate_comparison_report(
    cloudguard_eval: Dict[str, Any],
    checkov_eval: Dict[str, Any],
    tfsec_eval: Dict[str, Any],
    labels: Dict[str, Any],
) -> str:
    """Generate markdown comparison report."""
    lines: List[str] = []
    
    lines.extend([
        "# Baseline Comparison: CloudGuard vs Checkov vs tfsec",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Dataset**: 50 Terraform files (25 vulnerable, 25 clean)",
        f"**Ground Truth**: {sum(len(f.get('ground_truth', [])) for f in labels.get('files', {}).values())} vulnerability instances",
        "",
        "---",
        "",
        "## 1. Overall Metrics",
        "",
        "| Metric | CloudGuard | Checkov | tfsec |",
        "|--------|-----------|---------|-------|",
    ])
    
    for metric_name, metric_key, fmt in [
        ("Precision", "precision", lambda v: f"{v:.1%}"),
        ("Recall", "recall", lambda v: f"{v:.1%}"),
        ("F1 Score", "f1_score", lambda v: f"{v:.4f}"),
        ("FP Rate (clean)", "false_positive_rate_on_clean_files", lambda v: f"{v:.1%}"),
    ]:
        cg = cloudguard_eval["metrics"][metric_key]
        ck = checkov_eval["metrics"][metric_key]
        tf = tfsec_eval["metrics"][metric_key]
        lines.append(f"| {metric_name} | {fmt(cg)} | {fmt(ck)} | {fmt(tf)} |")
    
    # Confusion matrix counts
    lines.extend([
        "",
        "### Confusion Matrix",
        "",
        "| Metric | CloudGuard | Checkov | tfsec |",
        "|--------|-----------|---------|-------|",
    ])
    for label in ["TP", "FP", "FN", "TN_clean_files"]:
        cg = cloudguard_eval["confusion_matrix"][label]
        ck = checkov_eval["confusion_matrix"][label]
        tf = tfsec_eval["confusion_matrix"][label]
        display = label.replace("TN_clean_files", "Clean files w/0 findings")
        lines.append(f"| {display} | {cg} | {ck} | {tf} |")
    
    cg_total = cloudguard_eval["total_findings"]
    ck_total = checkov_eval["total_findings"]
    tf_total = tfsec_eval["total_findings"]
    lines.append(f"| Total Findings | {cg_total} | {ck_total} | {tf_total} |")
    
    # Per-category recall
    lines.extend([
        "",
        "---",
        "",
        "## 2. Per-Category Recall",
        "",
        "| Category | CloudGuard | Checkov | tfsec |",
        "|----------|-----------|---------|-------|",
    ])
    
    all_cats = sorted(set(
        list(cloudguard_eval.get("category_recall", {}).keys()) +
        list(checkov_eval.get("category_recall", {}).keys()) +
        list(tfsec_eval.get("category_recall", {}).keys())
    ))
    
    for cat in all_cats:
        cg_r = cloudguard_eval.get("category_recall", {}).get(cat, {})
        ck_r = checkov_eval.get("category_recall", {}).get(cat, {})
        tf_r = tfsec_eval.get("category_recall", {}).get(cat, {})
        
        def fmt_cat(r):
            if not r:
                return "—"
            return f"{r['detected']}/{r['total']} ({r['recall']:.0%})"
        
        lines.append(f"| {cat} | {fmt_cat(cg_r)} | {fmt_cat(ck_r)} | {fmt_cat(tf_r)} |")
    
    # Unique detections per tool
    lines.extend([
        "",
        "---",
        "",
        "## 3. Vulnerabilities Uniquely Detected by Each Tool",
        "",
    ])
    
    # Compute which GT instances each tool detected
    cg_detected = {m["gt_id"] for m in cloudguard_eval.get("missed_vulnerabilities", [])}
    ck_detected = {m["gt_id"] for m in checkov_eval.get("missed_vulnerabilities", [])}
    tf_detected = {m["gt_id"] for m in tfsec_eval.get("missed_vulnerabilities", [])}
    
    # These are MISSED by tool, so detected = ALL - missed
    all_gt_ids: Set[str] = set()
    for file_data in labels.get("files", {}).values():
        for gt in file_data.get("ground_truth", []):
            all_gt_ids.add(gt["id"])
    
    cg_found = all_gt_ids - cg_detected
    ck_found = all_gt_ids - ck_detected
    tf_found = all_gt_ids - tf_detected
    
    cg_unique = cg_found - ck_found - tf_found
    ck_unique = ck_found - cg_found - tf_found
    tf_unique = tf_found - cg_found - ck_found
    all_missed = cg_detected & ck_detected & tf_detected  # missed by ALL
    
    # Build GT lookup
    gt_lookup: Dict[str, Dict] = {}
    for file_key, file_data in labels.get("files", {}).items():
        for gt in file_data.get("ground_truth", []):
            gt_lookup[gt["id"]] = {**gt, "file": file_key}
    
    def gt_table(ids: Set[str], header: str):
        lines.append(f"### {header}")
        if not ids:
            lines.append("")
            lines.append("*None*")
            lines.append("")
            return
        lines.append("")
        lines.append("| GT ID | File | Vulnerability | Severity |")
        lines.append("|-------|------|---------------|----------|")
        for gt_id in sorted(ids):
            gt = gt_lookup.get(gt_id, {})
            lines.append(
                f"| {gt_id} | `{gt.get('file', '?')}` "
                f"| {gt.get('vulnerability', '?')} | {gt.get('severity', '?')} |"
            )
        lines.append("")
    
    gt_table(cg_unique, f"Unique to CloudGuard ({len(cg_unique)})")
    gt_table(ck_unique, f"Unique to Checkov ({len(ck_unique)})")
    gt_table(tf_unique, f"Unique to tfsec ({len(tf_unique)})")
    gt_table(all_missed, f"Missed by ALL tools ({len(all_missed)})")
    
    # Top FP sources per tool
    lines.extend([
        "---",
        "",
        "## 4. Top FP Sources by Tool",
        "",
        "### CloudGuard",
        "",
        "| Rule | FP Count |",
        "|------|----------|",
    ])
    for item in cloudguard_eval.get("top_fp_rules", [])[:5]:
        lines.append(f"| `{item['rule_id']}` | {item['fp_count']} |")
    
    lines.extend([
        "",
        "### Checkov",
        "",
        "| Check | FP Count |",
        "|-------|----------|",
    ])
    for item in checkov_eval.get("top_fp_rules", [])[:5]:
        lines.append(f"| `{item['rule_id']}` | {item['fp_count']} |")
    
    lines.extend([
        "",
        "### tfsec",
        "",
        "| Rule | FP Count |",
        "|------|----------|",
    ])
    for item in tfsec_eval.get("top_fp_rules", [])[:5]:
        lines.append(f"| `{item['rule_id']}` | {item['fp_count']} |")
    
    # Methodology
    lines.extend([
        "",
        "---",
        "",
        "## 5. Methodology",
        "",
        "1. All three tools were run on the same 50-file Terraform dataset (25 vulnerable, 25 clean).",
        "2. Tool-specific check IDs were mapped to **semantic vulnerability types** (not CloudGuard rule IDs).",
        "3. The same optimal bipartite matching algorithm was used for all tools.",
        "4. A finding is TP if it matches a ground truth entry by semantic type + line proximity (+-3 lines).",
        "5. Redundant detections (multiple findings for same GT) are not double-counted as TP or FP.",
        "6. Raw tool outputs are saved in `evaluation/results/` for reproducibility.",
        "",
    ])
    
    return "\n".join(lines)


# ======================================================================
# Main
# ======================================================================

def main():
    print("=" * 60)
    print("Baseline Comparison: CloudGuard vs Checkov vs tfsec")
    print("=" * 60)
    
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load labels
    print("\n[1/7] Loading labels ...")
    labels = load_labels()
    gt_count = sum(len(f.get("ground_truth", []))
                   for f in labels.get("files", {}).values())
    print(f"  -> {gt_count} ground truth instances")
    
    # 2. Load CloudGuard results (rerun to get fresh data)
    print("\n[2/7] Running CloudGuard rules engine ...")
    cg_scan = scan_all_files()
    cg_total = sum(len(v) for v in cg_scan.values())
    print(f"  -> {cg_total} findings")
    
    # 3. Run Checkov
    print("\n[3/7] Running Checkov ...")
    checkov_raw = run_checkov(DATASET_DIR)
    checkov_normalized = normalize_checkov(checkov_raw)
    ck_total = sum(len(v) for v in checkov_normalized.values())
    print(f"  -> {ck_total} normalized findings from {len(checkov_normalized)} files")
    
    # 4. Run tfsec
    print("\n[4/7] Running tfsec ...")
    tfsec_raw = run_tfsec(DATASET_DIR)
    tfsec_normalized = normalize_tfsec(tfsec_raw)
    tf_total = sum(len(v) for v in tfsec_normalized.values())
    print(f"  -> {tf_total} normalized findings from {len(tfsec_normalized)} files")
    
    # 5. Evaluate each tool
    print("\n[5/7] Evaluating CloudGuard ...")
    # For CloudGuard we use the main evaluation which has the correct semantic map
    from run_evaluation import evaluate as cg_evaluate
    cg_eval = cg_evaluate(cg_scan, labels)
    cg_m = cg_eval["metrics"]
    print(f"  -> P={cg_m['precision']:.3f} R={cg_m['recall']:.3f} F1={cg_m['f1_score']:.3f}")
    
    print("\n[6/7] Evaluating Checkov ...")
    ck_eval = evaluate_tool("Checkov", checkov_normalized, labels, CHECKOV_SEMANTIC_MAP)
    ck_m = ck_eval["metrics"]
    print(f"  -> P={ck_m['precision']:.3f} R={ck_m['recall']:.3f} F1={ck_m['f1_score']:.3f}")
    
    print("\n[6/7] Evaluating tfsec ...")
    tf_eval = evaluate_tool("tfsec", tfsec_normalized, labels, TFSEC_SEMANTIC_MAP)
    tf_m = tf_eval["metrics"]
    print(f"  -> P={tf_m['precision']:.3f} R={tf_m['recall']:.3f} F1={tf_m['f1_score']:.3f}")
    
    # 7. Generate comparison report
    print("\n[7/7] Generating comparison report ...")
    
    # Add total_findings to CG eval
    cg_eval["total_findings"] = cg_total
    
    report = generate_comparison_report(cg_eval, ck_eval, tf_eval, labels)
    
    report_path = RESULTS_DIR / "baseline_comparison.md"
    report_path.write_text(report, encoding="utf-8")
    
    comparison_data = {
        "generated_at": datetime.now().isoformat(),
        "cloudguard": {
            "metrics": cg_eval["metrics"],
            "confusion_matrix": cg_eval["confusion_matrix"],
            "total_findings": cg_total,
            "category_recall": cg_eval.get("category_recall", {}),
        },
        "checkov": {
            "metrics": ck_eval["metrics"],
            "confusion_matrix": ck_eval["confusion_matrix"],
            "total_findings": ck_total,
            "category_recall": ck_eval.get("category_recall", {}),
        },
        "tfsec": {
            "metrics": tf_eval["metrics"],
            "confusion_matrix": tf_eval["confusion_matrix"],
            "total_findings": tf_total,
            "category_recall": tf_eval.get("category_recall", {}),
        },
    }
    
    metrics_path = RESULTS_DIR / "baseline_comparison.json"
    metrics_path.write_text(json.dumps(comparison_data, indent=2), encoding="utf-8")
    
    print(f"\n  -> {report_path}")
    print(f"  -> {metrics_path}")
    
    print("\n" + "=" * 60)
    print("COMPARISON COMPLETE")
    print("=" * 60)
    print(f"\nCloudGuard:  P={cg_m['precision']:.3f}  R={cg_m['recall']:.3f}  F1={cg_m['f1_score']:.3f}")
    print(f"Checkov:     P={ck_m['precision']:.3f}  R={ck_m['recall']:.3f}  F1={ck_m['f1_score']:.3f}")
    print(f"tfsec:       P={tf_m['precision']:.3f}  R={tf_m['recall']:.3f}  F1={tf_m['f1_score']:.3f}")


if __name__ == "__main__":
    main()
