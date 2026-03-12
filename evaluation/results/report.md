# CloudGuardAI Evaluation Report

**Generated**: 2026-03-07 18:06:57
**Dataset**: 50 Terraform files (25 vulnerable, 25 clean)
**Scanner**: Rules Engine (29 rules across 5 YAML rule files)

---

## 1. Overall Metrics — Current Ruleset

| Metric | Value |
|--------|-------|
| Precision | 0.9038 (90.4%) |
| Recall | 0.9400 (94.0%) |
| F1 Score | 0.9216 |
| FP Rate (clean files) | 0.0000 (0.0%) |

### Confusion Matrix

| | Predicted Positive | Predicted Negative |
|---|---|---|
| **Actual Positive** | TP = 47 | FN = 3 |
| **Actual Negative** | FP = 5 | — |

- **Total findings produced**: 98
- **True Positives**: 47 (findings matching a real vulnerability)
- **False Positives**: 5 (findings with no corresponding vulnerability)
- **False Negatives**: 3 (real vulnerabilities not detected)
- **Clean files with zero findings**: 25 / 25

---

## 2. Diagnostic: Metrics Excluding `TF_UNENCRYPTED_RDS` (single worst noisy rule)

*This section shows system performance if the single noisiest rule were removed.*
*It is labeled as diagnostic — not a proposal to remove the rule.*

| Metric | Current | Excluding TF_UNENCRYPTED_RDS | Delta |
|--------|---------|------------------------------|-------|
| Precision | 0.9038 | 0.9400 | +0.0362 |
| Recall | 0.9400 | 0.9400 | +0.0000 |
| F1 Score | 0.9216 | 0.9400 | +0.0184 |
| FP Rate | 0.0000 | 0.0000 | +0.0000 |
| Total FP | 5 | 3 | -2 |

---

## 3. Per-Category Recall

| Category | Detected | Total | Recall |
|----------|----------|-------|--------|
| databases | 9 | 9 | 100.0% ██████████ |
| ec2-ebs | 3 | 5 | 60.0% ██████░░░░ |
| iam | 3 | 3 | 100.0% ██████████ |
| s3 | 12 | 13 | 92.3% █████████░ |
| secrets | 13 | 13 | 100.0% ██████████ |
| security-groups | 7 | 7 | 100.0% ██████████ |

---

## 4. Top 5 Rules Hurting Precision (by FP count)

| Rank | Rule ID | FP Count | Notes |
|------|---------|----------|-------|
| 1 | `TF_UNENCRYPTED_RDS` | 2 | terraform_block_match ignores missing_attribute |
| 2 | `TF_HARDCODED_ENV_SECRET` | 1 |  |
| 3 | `AWS_BP_S3_NO_LOGGING` | 1 | not_contains 'logging {' fires on all non-S3 files |
| 4 | `AWS_OWASP_A09_LOGGING` | 1 |  |

---

## 5. Top 5 Missed Vulnerabilities (False Negatives)

| Rank | File | Line | Vulnerability | Severity | Detection Gap? |
|------|------|------|---------------|----------|----------------|
| 1 | `vulnerable/vuln_08_s3_no_encryption.tf` | L1 | s3-no-encryption | HIGH | YES — no rule exists |
| 2 | `vulnerable/vuln_19_ec2_public_unmonitored.tf` | L4 | ec2-public-ip | HIGH | YES — no rule exists |
| 3 | `vulnerable/vuln_23_multi_full_stack.tf` | L24 | ec2-public-ip | HIGH | YES — no rule exists |

---

## 6. All Missed Vulnerabilities (Complete FN List)

Total missed: **3** out of **50** ground truth instances.

| GT ID | File | Line | Vulnerability | Severity | Category | Detection Gap? |
|-------|------|------|---------------|----------|----------|----------------|
| GT-008a | `vulnerable/vuln_08_s3_no_encryption.tf` | L1 | s3-no-encryption | HIGH | s3 | YES |
| GT-019a | `vulnerable/vuln_19_ec2_public_unmonitored.tf` | L4 | ec2-public-ip | HIGH | ec2-ebs | YES |
| GT-023c | `vulnerable/vuln_23_multi_full_stack.tf` | L24 | ec2-public-ip | HIGH | ec2-ebs | YES |

---

## 7. Per-File Summary

### Vulnerable Files

| File | Findings | TP | FP | FN | Status |
|------|----------|----|----|-----|--------|
| `vuln_01_sg_ssh_open.tf` | 2 | 1 | 1 | 0 | ✅ |
| `vuln_02_sg_rdp_open.tf` | 2 | 1 | 1 | 0 | ✅ |
| `vuln_03_sg_all_ports.tf` | 5 | 1 | 4 | 0 | ✅ |
| `vuln_04_sg_egress_all.tf` | 4 | 1 | 3 | 0 | ✅ |
| `vuln_05_s3_public_read.tf` | 3 | 2 | 1 | 0 | ✅ |
| `vuln_06_s3_public_write.tf` | 3 | 2 | 1 | 0 | ✅ |
| `vuln_07_s3_versioning_off.tf` | 1 | 1 | 0 | 0 | ✅ |
| `vuln_08_s3_no_encryption.tf` | 1 | 1 | 0 | 1 | ⚠️ missed 1 |
| `vuln_09_db_public.tf` | 1 | 1 | 0 | 0 | ✅ |
| `vuln_10_db_unencrypted.tf` | 3 | 1 | 2 | 0 | ✅ |
| `vuln_11_db_hardcoded_pw.tf` | 4 | 1 | 3 | 0 | ✅ |
| `vuln_12_db_skip_snapshot.tf` | 2 | 1 | 1 | 0 | ✅ |
| `vuln_13_creds_aws_key.tf` | 4 | 2 | 2 | 0 | ✅ |
| `vuln_14_creds_secret_value.tf` | 5 | 2 | 3 | 0 | ✅ |
| `vuln_15_creds_private_key.tf` | 1 | 1 | 0 | 0 | ✅ |
| `vuln_16_creds_password.tf` | 4 | 1 | 3 | 0 | ✅ |
| `vuln_17_iam_wildcard.tf` | 1 | 1 | 0 | 0 | ✅ |
| `vuln_18_iam_root.tf` | 1 | 1 | 0 | 0 | ✅ |
| `vuln_19_ec2_public_unmonitored.tf` | 1 | 1 | 0 | 1 | ⚠️ missed 1 |
| `vuln_20_ebs_unencrypted.tf` | 1 | 1 | 0 | 0 | ✅ |
| `vuln_21_lambda_secrets.tf` | 3 | 2 | 1 | 0 | ✅ |
| `vuln_22_multi_open_sg_to_db.tf` | 12 | 5 | 7 | 0 | ✅ |
| `vuln_23_multi_full_stack.tf` | 25 | 11 | 14 | 1 | ⚠️ missed 1 |
| `vuln_24_logging_disabled.tf` | 3 | 2 | 1 | 0 | ✅ |
| `vuln_25_s3_multiple_issues.tf` | 4 | 3 | 1 | 0 | ✅ |

### Clean Files

| File | Findings (all FP) | Status |
|------|-------------------|--------|
| `clean_01_sg_ssh_restricted.tf` | 0 | ✅ clean |
| `clean_02_sg_rdp_restricted.tf` | 0 | ✅ clean |
| `clean_03_sg_web_only.tf` | 0 | ✅ clean |
| `clean_04_sg_egress_restricted.tf` | 0 | ✅ clean |
| `clean_05_s3_private.tf` | 0 | ✅ clean |
| `clean_06_s3_encrypted.tf` | 0 | ✅ clean |
| `clean_07_s3_versioned.tf` | 0 | ✅ clean |
| `clean_08_s3_complete.tf` | 0 | ✅ clean |
| `clean_09_db_private_encrypted.tf` | 0 | ✅ clean |
| `clean_10_db_complete.tf` | 0 | ✅ clean |
| `clean_11_iam_minimal.tf` | 0 | ✅ clean |
| `clean_12_iam_scoped.tf` | 0 | ✅ clean |
| `clean_13_ec2_private_monitored.tf` | 0 | ✅ clean |
| `clean_14_ebs_encrypted.tf` | 0 | ✅ clean |
| `clean_15_lambda_ssm.tf` | 0 | ✅ clean |
| `clean_16_provider_no_creds.tf` | 0 | ✅ clean |
| `clean_17_keypair_var.tf` | 0 | ✅ clean |
| `clean_18_secrets_via_vars.tf` | 0 | ✅ clean |
| `clean_19_ec2_bastion_secure.tf` | 0 | ✅ clean |
| `clean_20_logging_enabled.tf` | 0 | ✅ clean |
| `clean_21_full_stack_secure.tf` | 0 | ✅ clean |
| `clean_22_rds_cluster_secure.tf` | 0 | ✅ clean |
| `clean_23_kms_key.tf` | 0 | ✅ clean |
| `clean_24_alb_internal.tf` | 0 | ✅ clean |
| `clean_25_sg_db_restricted.tf` | 0 | ✅ clean |

---

## 8. Methodology

1. **Scanner**: CloudGuardAI rules engine (`rules_engine.engine.scan_single_file`)
2. **Finding matching**: Each actual finding is matched to ground truth using:
   - Rule-to-semantic mapping (RULE_SEMANTIC_MAP) that links rule IDs to vulnerability types
   - Line proximity (±3 lines tolerance) to handle minor line offset differences
   - File-level rules (line=1) are matched more leniently
3. **A finding is TP if**: it matches both a semantic vulnerability type AND a nearby line in ground truth
4. **A finding is FP if**: it does not match any ground truth entry
5. **A GT entry is FN if**: no finding was matched to it
6. **Per-category recall**: ground truth entries grouped by vulnerability category
7. **Diagnostic mode**: same evaluation with the single noisiest rule excluded
