#!/usr/bin/env python3
"""
CloudGuardAI End-to-End Case Study Runner
==========================================
Demonstrates practical utility by running the full pipeline:

  1. SCAN   – Detect vulnerabilities in TerraGoat-style Terraform files
  2. REPORT – Show all findings with severity, type, and context
  3. FIX    – Auto-remediate using the remediation engine
  4. RESCAN – Verify the fixes eliminated the vulnerabilities
  5. DIFF   – Show before/after comparison

Usage:
    cd d:\\CloudGuardAI
    python -m evaluation.case_study.run_case_study
    python evaluation/case_study/run_case_study.py
"""

from __future__ import annotations

import json
import io
import os
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# -- Setup import paths --
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "rules"))
sys.path.insert(0, str(PROJECT_ROOT / "api"))

from rules_engine.engine import scan_single_file  # noqa: E402

# Import integrated scanner for multi-engine scanning
try:
    from scanners.integrated_scanner import IntegratedSecurityScanner
    INTEGRATED_AVAILABLE = True
except ImportError:
    INTEGRATED_AVAILABLE = False

from evaluation.case_study.auto_remediation import AutoRemediator  # noqa: E402

# ── Constants ───────────────────────────────────────────────────────────────
CASE_STUDY_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = CASE_STUDY_DIR / "results"

TERRAGOAT_FILES = [
    "terragoat_s3.tf",
    "terragoat_eks_db.tf",
    "terragoat_lambda.tf",
    "real_world_webapp.tf",
]

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
SEVERITY_EMOJI = {"CRITICAL": "[!]", "HIGH": "[H]", "MEDIUM": "[M]", "LOW": "[L]", "INFO": "[i]"}


# ── Helpers ─────────────────────────────────────────────────────────────────

def _severity_sort(finding: Dict) -> int:
    return SEVERITY_ORDER.get(finding.get("severity", "LOW").upper(), 9)


def _print_header(title: str, char: str = "=", width: int = 90):
    print(f"\n{char * width}")
    print(f"  {title}")
    print(f"{char * width}")


def _print_finding(i: int, f: Dict):
    sev = f.get("severity", "MEDIUM").upper()
    emoji = SEVERITY_EMOJI.get(sev, "⚪")
    rule = f.get("rule_id", f.get("type", "UNKNOWN"))
    title = f.get("title", f.get("description", ""))[:80]
    line = f.get("line", f.get("line_number", ""))
    line_str = f" (line {line})" if line else ""
    print(f"  {emoji} [{sev:8s}] {rule:35s} {title}{line_str}")


def _compute_severity_counts(findings: List[Dict]) -> Dict[str, int]:
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for f in findings:
        sev = f.get("severity", "LOW").upper()
        if sev in counts:
            counts[sev] += 1
    return counts


# ── Core Pipeline ───────────────────────────────────────────────────────────

def scan_file(file_path: Path) -> Tuple[str, List[Dict]]:
    """Scan a single TerraGoat file with rules engine + integrated scanners."""
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    
    # 1. Rules engine scan (always available)
    rules_findings = scan_single_file(file_path, content)
    
    # 2. Integrated scanner (secrets, compliance, CVE, GNN)
    integrated_findings = []
    if INTEGRATED_AVAILABLE:
        try:
            # Quick pre-check: is the ML service reachable?
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            service_up = sock.connect_ex(("localhost", 8001)) == 0
            sock.close()
            
            scanner = IntegratedSecurityScanner()
            if not service_up:
                # Disable remote scanners to avoid timeout delays
                scanner._scan_with_rules = lambda *a, **kw: []
                scanner._scan_with_ml = lambda *a, **kw: []
                scanner._scan_with_llm = lambda *a, **kw: []
            result = scanner.scan_content(content, str(file_path))
            integrated_findings = result.get("findings", [])
        except Exception as e:
            print(f"  [WARN] Integrated scanner skipped: {e}")
    
    # Merge & deduplicate
    all_findings = _merge_findings(rules_findings, integrated_findings)
    all_findings.sort(key=_severity_sort)
    
    return content, all_findings


def _merge_findings(rules: List[Dict], integrated: List[Dict]) -> List[Dict]:
    """Merge findings from rules engine and integrated scanner, deduplicating."""
    seen_keys = set()
    merged = []
    
    for f in rules:
        key = (f.get("rule_id", ""), f.get("line", 0))
        if key not in seen_keys:
            seen_keys.add(key)
            merged.append(f)
    
    for f in integrated:
        rule_id = f.get("rule_id", f.get("type", ""))
        line = f.get("line_number", f.get("line", 0))
        key = (rule_id, line)
        # Only add if not already covered by rules engine
        if key not in seen_keys:
            # Also check by title similarity
            title = f.get("title", "").lower()
            duplicate = False
            for existing in merged:
                et = existing.get("title", "").lower()
                if et and title and (et in title or title in et):
                    duplicate = True
                    break
            if not duplicate:
                seen_keys.add(key)
                merged.append(f)
    
    return merged


def run_single_case_study(file_name: str) -> Dict[str, Any]:
    """Run end-to-end case study for a single file."""
    file_path = CASE_STUDY_DIR / file_name
    if not file_path.exists():
        print(f"  [ERROR] File not found: {file_path}")
        return {}
    
    _print_header(f"CASE STUDY: {file_name}", "-", 90)
    
    # -- Step 1: SCAN --
    print("\n  [SCAN] STEP 1: Scanning for vulnerabilities...")
    original_content, findings = scan_file(file_path)
    before_counts = _compute_severity_counts(findings)
    
    print(f"\n  Found {len(findings)} vulnerabilities:")
    for i, f in enumerate(findings, 1):
        _print_finding(i, f)
    
    print(f"\n  Severity Summary: "
          f"[!] {before_counts['CRITICAL']} CRITICAL  "
          f"[H] {before_counts['HIGH']} HIGH  "
          f"[M] {before_counts['MEDIUM']} MEDIUM  "
          f"[L] {before_counts['LOW']} LOW")
    
    # ── Step 2: REMEDIATE ──
    print("\n  [FIX] STEP 2: Auto-remediating vulnerabilities...")
    remediator = AutoRemediator()
    result = remediator.remediate(original_content, findings)
    fixed_content = result["fixed_content"]
    changes = result["changes_applied"]
    stats = result["stats"]
    
    print(f"\n  Applied {stats['total_remediations']} remediation(s):")
    for c in changes:
        sev = c["severity"]
        emoji = SEVERITY_EMOJI.get(sev, "[?]")
        print(f"    {emoji} [{sev:8s}] {c['description']}")
    
    # ── Step 3: RESCAN ──
    print("\n  [VERIFY] STEP 3: Re-scanning fixed code...")
    
    # Write fixed content to temp path for scanning
    fixed_path = CASE_STUDY_DIR / f"fixed_{file_name}"
    fixed_path.write_text(fixed_content, encoding="utf-8")
    
    _, after_findings = scan_file(fixed_path)
    after_counts = _compute_severity_counts(after_findings)
    
    # ── Step 4: COMPARE ──
    print(f"\n  [COMPARE] STEP 4: Before/After Comparison")
    print(f"  {'':30s} {'BEFORE':>8s}  {'AFTER':>8s}  {'DELTA':>8s}")
    print(f"  {'-' * 58}")
    
    total_before = len(findings)
    total_after = len(after_findings)
    
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        before = before_counts.get(sev, 0)
        after = after_counts.get(sev, 0)
        delta = after - before
        delta_str = f"{delta:+d}" if delta != 0 else "  0"
        emoji = SEVERITY_EMOJI[sev]
        print(f"  {emoji} {sev:28s} {before:8d}  {after:8d}  {delta_str:>8s}")
    
    print(f"  {'-' * 58}")
    total_delta = total_after - total_before
    reduction_pct = ((total_before - total_after) / max(total_before, 1)) * 100
    print(f"  {'TOTAL':30s} {total_before:8d}  {total_after:8d}  {total_delta:+8d}")
    print(f"\n  [OK] Vulnerability Reduction: {reduction_pct:.1f}%")
    
    if after_findings:
        print(f"\n  [WARN] Remaining findings ({len(after_findings)}):")
        for i, f in enumerate(after_findings, 1):
            _print_finding(i, f)
    
    # Clean up temp file
    if fixed_path.exists():
        fixed_path.unlink()
    
    return {
        "file": file_name,
        "before": {
            "total_findings": total_before,
            "by_severity": before_counts,
            "findings": findings,
        },
        "remediation": {
            "changes_applied": len(changes),
            "changes": changes,
            "stats": stats,
        },
        "after": {
            "total_findings": total_after,
            "by_severity": after_counts,
            "findings": [
                {
                    "rule_id": f.get("rule_id", ""),
                    "severity": f.get("severity", ""),
                    "title": f.get("title", ""),
                }
                for f in after_findings
            ],
        },
        "reduction_pct": round(reduction_pct, 1),
    }


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    _print_header("CLOUDGUARD AI - TERRAGOAT CASE STUDY", "=", 90)
    print("  End-to-end: Detect -> Remediate -> Verify")
    print(f"  Timestamp: {datetime.now().isoformat()}")
    print(f"  Files: {len(TERRAGOAT_FILES)} TerraGoat-style vulnerable Terraform configs")
    
    all_results: List[Dict] = []
    
    for file_name in TERRAGOAT_FILES:
        result = run_single_case_study(file_name)
        if result:
            all_results.append(result)
    
    # ── Aggregate Summary ──
    _print_header("AGGREGATE CASE STUDY RESULTS", "=", 90)
    
    total_before = sum(r["before"]["total_findings"] for r in all_results)
    total_after = sum(r["after"]["total_findings"] for r in all_results)
    total_fixes = sum(r["remediation"]["changes_applied"] for r in all_results)
    overall_reduction = ((total_before - total_after) / max(total_before, 1)) * 100
    
    agg_before = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    agg_after = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    
    for r in all_results:
        for sev in agg_before:
            agg_before[sev] += r["before"]["by_severity"].get(sev, 0)
            agg_after[sev] += r["after"]["by_severity"].get(sev, 0)
    
    print(f"\n  Files Analyzed:        {len(all_results)}")
    print(f"  Total Vulnerabilities: {total_before}")
    print(f"  Remediations Applied:  {total_fixes}")
    print(f"  Remaining Issues:      {total_after}")
    print(f"  Reduction Rate:        {overall_reduction:.1f}%")
    
    print(f"\n  {'Severity':20s} {'Before':>8s}  {'After':>8s}  {'Fixed':>8s}")
    print(f"  {'-' * 48}")
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        b = agg_before[sev]
        a = agg_after[sev]
        print(f"  {SEVERITY_EMOJI[sev]} {sev:18s} {b:8d}  {a:8d}  {b - a:8d}")
    print(f"  {'-' * 48}")
    print(f"  {'TOTAL':20s} {total_before:8d}  {total_after:8d}  {total_before - total_after:8d}")
    
    # Per-file summary table
    print(f"\n  {'File':35s} {'Before':>8s} {'After':>8s} {'Reduction':>10s}")
    print(f"  {'-' * 65}")
    for r in all_results:
        fname = r["file"][:34]
        b = r["before"]["total_findings"]
        a = r["after"]["total_findings"]
        red = r["reduction_pct"]
        print(f"  {fname:35s} {b:8d} {a:8d} {red:9.1f}%")
    
    # ── Save Results ──
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # JSON results
    output_path = OUTPUT_DIR / "case_study_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "files_analyzed": len(all_results),
                    "total_before": total_before,
                    "total_after": total_after,
                    "total_fixes": total_fixes,
                    "reduction_pct": round(overall_reduction, 1),
                    "before_by_severity": agg_before,
                    "after_by_severity": agg_after,
                },
                "per_file": all_results,
            },
            f,
            indent=2,
            default=str,
        )
    print(f"\n  [SAVED] Detailed results saved to: {output_path.relative_to(PROJECT_ROOT)}")
    
    # ── Generate Markdown Report ──
    md_path = OUTPUT_DIR / "CASE_STUDY_REPORT.md"
    _generate_markdown_report(md_path, all_results, agg_before, agg_after, total_before, total_after, total_fixes, overall_reduction)
    print(f"  [SAVED] Markdown report saved to:  {md_path.relative_to(PROJECT_ROOT)}")
    
    _print_header("CASE STUDY COMPLETE", "=", 90)
    print(f"  [OK] CloudGuardAI detected {total_before} vulnerabilities across {len(all_results)} TerraGoat files")
    print(f"  [OK] Auto-remediation fixed {total_fixes} issues ({overall_reduction:.1f}% reduction)")
    print(f"  [OK] This demonstrates end-to-end Detect -> Fix -> Verify capability\n")

    return all_results


def _generate_markdown_report(
    path: Path,
    results: List[Dict],
    agg_before: Dict,
    agg_after: Dict,
    total_before: int,
    total_after: int,
    total_fixes: int,
    reduction_pct: float,
):
    """Generate a detailed Markdown case study report."""
    lines = [
        "# CloudGuardAI — TerraGoat Case Study Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Executive Summary",
        "",
        "This case study demonstrates CloudGuardAI's end-to-end security posture management",
        "capability on **TerraGoat-style** intentionally vulnerable Terraform configurations",
        "(inspired by [BridgeCrew/TerraGoat](https://github.com/bridgecrewio/terragoat)).",
        "",
        "The pipeline performs three stages:",
        "1. **Detect** — Multi-engine scanning (rules, secrets, compliance, GNN attack paths)",
        "2. **Remediate** — Automated fix generation with security best practices",
        "3. **Verify** — Re-scan to confirm vulnerability elimination",
        "",
        "## Aggregate Results",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Files Analyzed | {len(results)} |",
        f"| Vulnerabilities Detected | {total_before} |",
        f"| Remediations Applied | {total_fixes} |",
        f"| Remaining Issues | {total_after} |",
        f"| **Reduction Rate** | **{reduction_pct:.1f}%** |",
        "",
        "### By Severity",
        "",
        "| Severity | Before | After | Fixed |",
        "|----------|--------|-------|-------|",
    ]
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        b = agg_before.get(sev, 0)
        a = agg_after.get(sev, 0)
        lines.append(f"| {sev} | {b} | {a} | {b - a} |")
    lines.append(f"| **TOTAL** | **{total_before}** | **{total_after}** | **{total_before - total_after}** |")
    lines.append("")

    # Per-file details
    for r in results:
        fname = r["file"]
        lines.append(f"## Case: `{fname}`")
        lines.append("")
        
        b = r["before"]["total_findings"]
        a = r["after"]["total_findings"]
        red = r["reduction_pct"]
        lines.append(f"**Before:** {b} vulnerabilities → **After:** {a} → **Reduction: {red:.1f}%**")
        lines.append("")
        
        # Findings before
        lines.append("### Vulnerabilities Detected")
        lines.append("")
        lines.append("| # | Severity | Rule ID | Description |")
        lines.append("|---|----------|---------|-------------|")
        for i, f in enumerate(r["before"].get("findings", []), 1):
            sev = f.get("severity", "MEDIUM")
            rule = f.get("rule_id", f.get("type", ""))
            title = f.get("title", f.get("description", ""))[:60]
            lines.append(f"| {i} | {sev} | `{rule}` | {title} |")
        lines.append("")
        
        # Changes applied
        lines.append("### Remediations Applied")
        lines.append("")
        for c in r["remediation"].get("changes", []):
            lines.append(f"- **[{c['severity']}]** {c['description']}")
        lines.append("")
        
        # Remaining
        remaining = r["after"].get("findings", [])
        if remaining:
            lines.append("### Remaining Issues")
            lines.append("")
            for rf in remaining:
                lines.append(f"- [{rf.get('severity', '')}] `{rf.get('rule_id', '')}` — {rf.get('title', '')}")
            lines.append("")
        else:
            lines.append("### ✅ All vulnerabilities remediated!")
            lines.append("")
    
    # Methodology
    lines.extend([
        "## Methodology",
        "",
        "### Vulnerability Sources",
        "- **TerraGoat patterns** — Based on BridgeCrew's intentionally vulnerable Terraform repo",
        "- **Real breach post-mortems** — S3 data leaks, exposed databases, credential exposure",
        "- **CIS AWS Benchmark** — Security group, IAM, encryption, logging controls",
        "",
        "### Scanner Pipeline",
        "1. **Rules Engine** — 40+ pattern-based rules (CIS, OWASP, best practices)",
        "2. **Secrets Scanner** — Regex + entropy-based credential detection",
        "3. **Compliance Scanner** — CIS Benchmark validation",
        "4. **GNN Attack Path Analyzer** — Graph neural network for topology-aware risk",
        "5. **ML Risk Scorer** — Trained classifier for IaC risk prediction",
        "",
        "### Auto-Remediation Engine",
        "- Template-based fix generation with security best practices",
        "- Pattern scanning for unreported issues",
        "- Missing security block injection (encryption, public access blocks)",
        "- Deterministic, auditable changes",
        "",
        "## Limitations & Caveats",
        "",
        "- Remediation templates cover common AWS patterns; custom resources may need manual review",
        "- Some findings require architectural changes beyond simple code fixes",
        "- The auto-remediation engine produces valid HCL but manual review is recommended",
        "- Reduction percentages measure finding count, not risk-weighted reduction",
        "",
        "---",
        f"*Report generated by CloudGuardAI v2.0 — {datetime.now().strftime('%Y-%m-%d')}*",
    ])
    
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
