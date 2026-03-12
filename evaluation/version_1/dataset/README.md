# CloudGuardAI Evaluation Dataset

## Purpose

Curated dataset of 50 Terraform files (25 vulnerable, 25 clean) with instance-level vulnerability labels for reproducible evaluation of CloudGuardAI's detection capabilities.

## Structure

```
evaluation/dataset/
├── labels.json                     # Instance-level ground truth + expected findings
├── README.md                       # This file
├── vulnerable/                     # 25 files with known vulnerabilities
│   ├── vuln_01_sg_ssh_open.tf
│   ├── vuln_02_sg_rdp_open.tf
│   ├── ...
│   └── vuln_25_s3_multiple_issues.tf
└── clean/                          # 25 files with no vulnerabilities
    ├── clean_01_sg_ssh_restricted.tf
    ├── clean_02_sg_rdp_restricted.tf
    ├── ...
    └── clean_25_sg_db_restricted.tf
```

## Design Principles

1. **Vulnerability-instance level labels**: Each vulnerability is annotated with exact line number, semantic ID, severity, and CWE reference.
2. **Rule-traceable expected findings**: Every expected rules engine finding was derived by manually tracing each rule's regex pattern against each file line-by-line, matching the exact behavior of `matcher.py`.
3. **Clean files as negative controls**: Clean files are secure counterparts of the same resource types (same resource, properly configured). Ideal scanner output for clean files is zero findings.
4. **Known issues documented**: False positives from broken matchers, dead rules, and detection gaps are explicitly documented.

## Coverage Matrix

### Vulnerability Categories (25 vulnerable files)

| Category | Files | Ground Truth Instances |
|---|---|---|
| Open security groups | vuln_01–04 | 4 |
| Public S3 buckets | vuln_05–06, 25 | 5 |
| S3 versioning/encryption | vuln_07–08, 24 | 5 |
| Public/unencrypted databases | vuln_09–10 | 2 |
| Hardcoded credentials | vuln_11, 13–16 | 7 |
| Data protection gaps | vuln_12 | 1 |
| IAM misconfigurations | vuln_17–18 | 2 |
| EC2 exposure/monitoring | vuln_19 | 2 |
| EBS encryption | vuln_20 | 1 |
| Lambda secrets in env vars | vuln_21 | 2 |
| Multi-resource combinations | vuln_22–23 | 15 |
| **Total** | **25 files** | **46 instances** |

### Clean File Categories (25 clean files)

| Category | Files |
|---|---|
| Restricted security groups | clean_01–04, 25 |
| Private/encrypted S3 | clean_05–08 |
| Hardened RDS instances | clean_09–10, 22, 25 |
| Scoped IAM policies | clean_11–12 |
| Private monitored EC2 | clean_13, 19 |
| Encrypted EBS | clean_14 |
| Lambda with SSM refs | clean_15 |
| Safe provider/key config | clean_16–18 |
| Logging infrastructure | clean_20 |
| Full secure stacks | clean_21 |
| KMS/ALB resources | clean_23–24 |

## Rules Engine Analyzed

All 29 rules across 5 YAML rule files were traced:

- **aws/cis.yaml**: 8 rules (CIS AWS benchmarks)
- **aws/owasp.yaml**: 5 rules (OWASP Top 10 mapped)
- **aws/best_practices.yaml**: 7 rules (AWS security best practices)
- **shared/terraform.yaml**: 8 rules (Terraform-specific patterns)
- **shared/generic.yaml**: 1 rule (generic hardcoded secrets)

### Matcher Types in `matcher.py`

| Matcher | Behavior | Rules Using It |
|---|---|---|
| `regex_match` | Line-by-line `re.search(pattern, line)` | 21 rules |
| `contains_match` | Line-by-line substring check | 2 rules |
| `not_contains_match` | File-level: fires at L1 if string absent | 1 rule |
| `terraform_block_match` | Line-by-line: finds `resource "type"` | 2 rules |
| Missing key / YAML path | Other matchers, not used by active rules | 0 rules in dataset scope |

## Known Issues Discovered

### Critical Bugs

1. **`terraform_block_match` ignores `missing_attribute`**: `TF_UNENCRYPTED_EBS` and `TF_UNENCRYPTED_RDS` are supposed to check for missing `encrypted`/`storage_encrypted` attributes, but the matcher only checks if the resource type string exists. Fires on ALL matching resource blocks regardless of encryption status **→ 8 false positives in this dataset**.

2. **`AWS_CIS_S3_VERSIONING_DISABLED` is dead**: Its multiline regex `versioning\s*\{[^}]*enabled\s*=\s*false` cannot work when applied line-by-line by `regex_match`. **Never fires on standard multi-line Terraform**.

### High-Noise Rules

3. **`AWS_BP_S3_NO_LOGGING`**: `not_contains "logging {"` fires on every `.tf` file that doesn't contain the literal string `logging {`. Produces **41 false positives** across 50 files (fires on SG, EC2, IAM, EBS, Lambda files, not just S3). Alone accounts for ~66% of all expected FPs.

4. **`NO_HARDCODED_SECRET`**: Case-insensitive regex matches attribute names (`password=`, `secret=`, `api_key=`) regardless of whether the value is hardcoded or a variable reference. Fires on `password = var.db_password` as readily as `password = "hardcoded"`. **7 FPs on clean files**.

### Brittle Matching

5. **`TF_SKIP_SNAPSHOT`**: Uses `contains "skip_final_snapshot  = true"` with a **double space**. Only matches files that happen to use 2-space alignment before `=`. Standard single-space Terraform formatting is missed.

### Detection Gaps

6. **No wildcard IAM detection**: `Action="*" Resource="*"` is not caught by any rule (affects vuln_17, vuln_23).
7. **No private key PEM detection**: Rules engine has no regex for `-----BEGIN RSA PRIVATE KEY-----` (affects vuln_15).
8. **No SSM `value=` detection**: Hardcoded plaintext in SSM parameter `value` attribute is missed (affects vuln_14).
9. **No public EC2 IP detection**: `associate_public_ip_address=true` has no rule (affects vuln_19, vuln_23).
10. **Case-sensitive credential rules**: `AWS_BP_HARDCODED_PASSWORD`, `AWS_OWASP_A07_AUTH_FAILURE`, and `TF_HARDCODED_CREDENTIALS` use lowercase-only patterns, missing `DB_PASSWORD=`, `API_KEY=` style env vars (affects vuln_21, vuln_23).

## Expected Performance

Based on manual analysis against the 29 rules engine rules:

| Metric | Value | Notes |
|---|---|---|
| Expected True Positives | 67 | Correct detections across all files |
| Expected False Positives | 62 | Incorrect detections (41 from AWS_BP_S3_NO_LOGGING alone) |
| Ground Truth with Coverage | 38/46 (82.6%) | At least one TP rule fires |
| Detection Gaps | 8/46 (17.4%) | No TP rule fires |
| Estimated Precision | 51.9% | TP / (TP + FP) |
| Precision ex. S3 logging | 76.1% | Excluding AWS_BP_S3_NO_LOGGING FPs |

## Usage

This dataset is designed for:

1. **Automated evaluation**: Run CloudGuardAI's rules engine scanner on all 50 files and compare outputs against `labels.json` expected findings.
2. **Precision/Recall calculation**: Compare actual findings against ground truth to compute detection metrics.
3. **Regression testing**: After fixing known bugs (e.g., `terraform_block_match`), re-run to verify improvement.
4. **Baseline comparison**: Run equivalent Checkov/tfsec rules on the same files for apples-to-apples comparison.

## Label Schema

See `labels.json` for complete annotations. Each file entry contains:

```json
{
  "category": "vulnerable|clean",
  "ground_truth": [
    {
      "id": "GT-NNN",
      "line": 11,
      "vulnerability": "semantic-id",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "cwe": "CWE-XXX",
      "description": "Human-readable description",
      "detection_gap": true  // optional: no TP rule exists
    }
  ],
  "expected_findings": [
    {
      "rule_id": "RULE_ID",
      "line": 11,
      "severity": "SEVERITY",
      "tp": true,       // true = correct detection, false = false positive
      "note": "..."     // optional explanation
    }
  ]
}
```
