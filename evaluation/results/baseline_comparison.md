# Baseline Comparison: CloudGuard vs Checkov vs tfsec

**Generated**: 2026-02-24 15:45:22
**Dataset**: 50 Terraform files (25 vulnerable, 25 clean)
**Ground Truth**: 50 vulnerability instances

---

## 1. Overall Metrics

| Metric | CloudGuard | Checkov | tfsec |
|--------|-----------|---------|-------|
| Precision | 90.4% | 10.6% | 17.6% |
| Recall | 94.0% | 54.0% | 56.0% |
| F1 Score | 0.9216 | 0.1770 | 0.2679 |
| FP Rate (clean) | 0.0% | 80.0% | 60.0% |

### Confusion Matrix

| Metric | CloudGuard | Checkov | tfsec |
|--------|-----------|---------|-------|
| TP | 47 | 27 | 28 |
| FP | 5 | 228 | 131 |
| FN | 3 | 23 | 22 |
| Clean files w/0 findings | 25 | 5 | 10 |
| Total Findings | 98 | 286 | 193 |

---

## 2. Per-Category Recall

| Category | CloudGuard | Checkov | tfsec |
|----------|-----------|---------|-------|
| databases | 9/9 (100%) | 4/9 (44%) | 7/9 (78%) |
| ec2-ebs | 3/5 (60%) | 4/5 (80%) | 3/5 (60%) |
| iam | 3/3 (100%) | 0/3 (0%) | 1/3 (33%) |
| s3 | 12/13 (92%) | 13/13 (100%) | 11/13 (85%) |
| secrets | 13/13 (100%) | 2/13 (15%) | 1/13 (8%) |
| security-groups | 7/7 (100%) | 4/7 (57%) | 5/7 (71%) |

---

## 3. Vulnerabilities Uniquely Detected by Each Tool

### Unique to CloudGuard (18)

| GT ID | File | Vulnerability | Severity |
|-------|------|---------------|----------|
| GT-004 | `vulnerable/vuln_04_sg_egress_all.tf` | unrestricted-egress | MEDIUM |
| GT-011 | `vulnerable/vuln_11_db_hardcoded_pw.tf` | hardcoded-db-password | CRITICAL |
| GT-013a | `vulnerable/vuln_13_creds_aws_key.tf` | hardcoded-aws-access-key | CRITICAL |
| GT-013b | `vulnerable/vuln_13_creds_aws_key.tf` | hardcoded-aws-secret-key | CRITICAL |
| GT-014b | `vulnerable/vuln_14_creds_secret_value.tf` | hardcoded-password-in-secret | CRITICAL |
| GT-016 | `vulnerable/vuln_16_creds_password.tf` | hardcoded-connection-password | CRITICAL |
| GT-017 | `vulnerable/vuln_17_iam_wildcard.tf` | iam-wildcard-policy | CRITICAL |
| GT-018 | `vulnerable/vuln_18_iam_root.tf` | iam-root-account-access | CRITICAL |
| GT-021a | `vulnerable/vuln_21_lambda_secrets.tf` | hardcoded-env-password | CRITICAL |
| GT-021b | `vulnerable/vuln_21_lambda_secrets.tf` | hardcoded-env-api-key | CRITICAL |
| GT-022d | `vulnerable/vuln_22_multi_open_sg_to_db.tf` | hardcoded-db-password | CRITICAL |
| GT-022e | `vulnerable/vuln_22_multi_open_sg_to_db.tf` | skip-final-snapshot | MEDIUM |
| GT-023b | `vulnerable/vuln_23_multi_full_stack.tf` | unrestricted-egress | MEDIUM |
| GT-023d | `vulnerable/vuln_23_multi_full_stack.tf` | ec2-monitoring-disabled | LOW |
| GT-023e | `vulnerable/vuln_23_multi_full_stack.tf` | hardcoded-secret-in-userdata | CRITICAL |
| GT-023f | `vulnerable/vuln_23_multi_full_stack.tf` | hardcoded-secret-in-userdata | CRITICAL |
| GT-023j | `vulnerable/vuln_23_multi_full_stack.tf` | hardcoded-db-password | CRITICAL |
| GT-023k | `vulnerable/vuln_23_multi_full_stack.tf` | skip-final-snapshot | MEDIUM |

### Unique to Checkov (0)

*None*

### Unique to tfsec (0)

*None*

### Missed by ALL tools (0)

*None*

---

## 4. Top FP Sources by Tool

### CloudGuard

| Rule | FP Count |
|------|----------|
| `TF_UNENCRYPTED_RDS` | 2 |
| `TF_HARDCODED_ENV_SECRET` | 1 |
| `AWS_BP_S3_NO_LOGGING` | 1 |
| `AWS_OWASP_A09_LOGGING` | 1 |

### Checkov

| Check | FP Count |
|-------|----------|
| `CHECKOV_CKV_AWS_129` | 10 |
| `CHECKOV_CKV_AWS_118` | 10 |
| `CHECKOV_CKV_AWS_161` | 10 |
| `CHECKOV_CKV_AWS_353` | 10 |
| `CHECKOV_CKV2_AWS_60` | 10 |

### tfsec

| Rule | FP Count |
|------|----------|
| `TFSEC_AVD-AWS-0087` | 11 |
| `TFSEC_AVD-AWS-0091` | 11 |
| `TFSEC_AVD-AWS-0176` | 9 |
| `TFSEC_AVD-AWS-0133` | 9 |
| `TFSEC_AVD-AWS-0086` | 8 |

---

## 5. Methodology

1. All three tools were run on the same 50-file Terraform dataset (25 vulnerable, 25 clean).
2. Tool-specific check IDs were mapped to **semantic vulnerability types** (not CloudGuard rule IDs).
3. The same optimal bipartite matching algorithm was used for all tools.
4. A finding is TP if it matches a ground truth entry by semantic type + line proximity (+-3 lines).
5. Redundant detections (multiple findings for same GT) are not double-counted as TP or FP.
6. Raw tool outputs are saved in `evaluation/results/` for reproducibility.
