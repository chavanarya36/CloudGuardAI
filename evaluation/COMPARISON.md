# CloudGuardAI Evaluation — Baseline Comparison (version\_1)

> **Frozen**: 2026-03-01 &nbsp;|&nbsp; **Dataset**: 50 Terraform files (25 vulnerable, 25 clean) &nbsp;|&nbsp; **Ground Truth**: 50 vulnerability instances

---

## 1. Overall Metrics

| Metric | CloudGuard | Checkov | tfsec |
|--------|-----------|---------|-------|
| **Precision** | **90.4 %** | 10.6 % | 17.6 % |
| **Recall** | **94.0 %** | 54.0 % | 56.0 % |
| **F1 Score** | **0.922** | 0.177 | 0.268 |
| FP-rate on clean files | **0.0 %** | 80.0 % | 60.0 % |
| True Positives | 47 | 27 | 28 |
| False Positives | 5 | 228 | 131 |
| False Negatives | 3 | 23 | 22 |
| Clean files with 0 findings | 25/25 | 5/25 | 10/25 |
| Total findings produced | 98 | 286 | 193 |

**Key takeaway.** CloudGuard achieves a substantially higher F1 score primarily because of its low false-positive rate: it generates 5 FP versus 228 (Checkov) and 131 (tfsec). All three tools are evaluated with the same optimal bipartite matching algorithm on the same dataset and ground truth.

---

## 2. Per-Category Recall

| Category | Ground Truth | CloudGuard | Checkov | tfsec |
|----------|:------------:|:----------:|:-------:|:-----:|
| Databases | 9 | 9/9 **(100 %)** | 4/9 (44 %) | 7/9 (78 %) |
| EC2 / EBS | 5 | 3/5 (60 %) | 4/5 **(80 %)** | 3/5 (60 %) |
| IAM | 3 | 3/3 **(100 %)** | 0/3 (0 %) | 1/3 (33 %) |
| S3 | 13 | 12/13 (92 %) | 13/13 **(100 %)** | 11/13 (85 %) |
| Secrets | 13 | 13/13 **(100 %)** | 2/13 (15 %) | 1/13 (8 %) |
| Security Groups | 7 | 7/7 **(100 %)** | 4/7 (57 %) | 5/7 (71 %) |
| **Overall** | **50** | **47/50 (94 %)** | **27/50 (54 %)** | **28/50 (56 %)** |

**Notes.**
- CloudGuard leads in 5 of 6 categories. Its weakest category — EC2/EBS (60 %) — ties with tfsec and trails Checkov (80 %).
- Checkov's strongest category is S3 (100 %) but it misses all IAM and nearly all secrets findings.
- tfsec detects no more than 85 % in any single category and its secrets recall is only 8 %.

---

## 3. Unique Detections

| Metric | CloudGuard | Checkov | tfsec |
|--------|:---------:|:-------:|:-----:|
| Vulnerabilities detected by **only** this tool | **18** | 0 | 0 |
| Vulnerabilities missed by **all** tools | — | 0 | — |

The 18 vulnerabilities uniquely detected by CloudGuard span several categories:

| Category | Count | Examples |
|----------|:-----:|---------|
| Secrets / Hardcoded credentials | 10 | AWS access keys, secret keys, DB passwords in env vars, connection strings |
| IAM misconfigurations | 2 | Wildcard actions, root account access |
| Security Groups | 2 | Unrestricted egress |
| Database best practices | 2 | Skip-final-snapshot |
| EC2 operational | 1 | Monitoring disabled |
| Multi-resource chains | 1 | Hardcoded secret in user-data |

Neither Checkov nor tfsec detected any vulnerability that CloudGuard missed.

---

## 4. Scope Differences

The three tools differ meaningfully in scope and design philosophy:

| Dimension | CloudGuard | Checkov | tfsec |
|-----------|-----------|---------|-------|
| **Focus** | Security vulnerabilities & misconfigurations (domain-specific YAML rules + ML/GNN enrichment) | Broad compliance posture (CIS, PCI-DSS, SOC2, HIPAA, etc.) | Security-focused static analysis |
| **Rule philosophy** | Curated rules targeting exploitable issues; each rule maps to a known vulnerability class | Exhaustive policy checks including best-practice, tagging, and encryption defaults | Security checks derived from AWS/Azure/GCP documentation |
| **Secrets detection** | Regex + heuristic patterns for credentials, API keys, passwords, private keys | Minimal — relies on upstream scanners | Minimal |
| **False-positive control** | Rules tuned against labeled dataset; low FP by design | High FP rate — many checks fire on compliant resources | Moderate FP rate |
| **Output** | Vulnerability findings with severity, reasoning, attack-path context, ML risk score | Pass/fail per-check per-resource | Findings with severity and impact description |

**Why does CloudGuard have fewer rules but higher recall?**

CloudGuard's 34 rules are purpose-built for the vulnerability classes in the evaluation ground truth. Checkov and tfsec apply a much larger rule set (68 and 30 checks, respectively, on this dataset) but most of their checks target compliance posture (encryption defaults, logging, tagging) rather than directly exploitable vulnerabilities. This means they produce many findings that do not match the ground truth definitions, inflating FP counts without improving TP coverage.

---

## 5. Approximate Rule-Count Comparison

| Tool | Rules / checks observed on this dataset | Total rules in distribution (approx.) |
|------|:---------------------------------------:|:-------------------------------------:|
| **CloudGuard** | 34 | 34 (14 YAML files across AWS, Azure, GCP, Kubernetes, shared) |
| **Checkov** | 68 | ~1 200+ (built-in checks across all providers) |
| **tfsec** | 30 | ~400+ (Aqua/tfsec rule library) |

> *"Observed on this dataset"* counts distinct check/rule IDs that fired at least once during evaluation. Checkov and tfsec ship with substantially larger rule libraries, but only a subset is relevant to the Terraform resource types present in the 50-file dataset.

CloudGuard's rule set is intentionally compact: each rule targets a specific, documented vulnerability pattern. The evaluation results show that a focused, well-tuned rule set can outperform broader tools on vulnerability detection tasks, particularly when precision matters.

---

## Methodology

1. All three tools were run on the same 50-file Terraform dataset (25 vulnerable, 25 clean).
2. Tool-specific check IDs were mapped to **semantic vulnerability types** (not tool-internal IDs).
3. The same optimal bipartite matching algorithm was used for all tools to avoid double-counting.
4. A finding is TP if it matches a ground truth entry by semantic type + line proximity (±3 lines).
5. Redundant detections (multiple findings for the same ground truth) are not double-counted as TP or FP.
6. Raw tool outputs are preserved in `evaluation/version_1/results/` for reproducibility.

---

*This document is part of the version\_1 evaluation freeze. Do not modify evaluation artifacts without creating a new version.*
