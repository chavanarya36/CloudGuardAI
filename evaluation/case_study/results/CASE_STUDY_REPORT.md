# CloudGuardAI — TerraGoat Case Study Report

**Generated:** 2026-03-04 23:12:18

## Executive Summary

This case study demonstrates CloudGuardAI's end-to-end security posture management
capability on **TerraGoat-style** intentionally vulnerable Terraform configurations
(inspired by [BridgeCrew/TerraGoat](https://github.com/bridgecrewio/terragoat)).

The pipeline performs three stages:
1. **Detect** — Multi-engine scanning (rules, secrets, compliance, GNN attack paths)
2. **Remediate** — Automated fix generation with security best practices
3. **Verify** — Re-scan to confirm vulnerability elimination

## Aggregate Results

| Metric | Value |
|--------|-------|
| Files Analyzed | 4 |
| Vulnerabilities Detected | 150 |
| Remediations Applied | 83 |
| Remaining Issues | 33 |
| **Reduction Rate** | **78.0%** |

### By Severity

| Severity | Before | After | Fixed |
|----------|--------|-------|-------|
| CRITICAL | 83 | 4 | 79 |
| HIGH | 44 | 15 | 29 |
| MEDIUM | 21 | 14 | 7 |
| LOW | 2 | 0 | 2 |
| INFO | 0 | 0 | 0 |
| **TOTAL** | **150** | **33** | **117** |

## Case: `terragoat_s3.tf`

**Before:** 25 vulnerabilities → **After:** 8 → **Reduction: 68.0%**

### Vulnerabilities Detected

| # | Severity | Rule ID | Description |
|---|----------|---------|-------------|
| 1 | CRITICAL | `AWS_CIS_IAM_WILDCARD_POLICY` | Aws Cis Iam Wildcard Policy |
| 2 | CRITICAL | `AWS_CIS_S3_PUBLIC_ACL` | Aws Cis S3 Public Acl |
| 3 | CRITICAL | `AWS_CIS_S3_PUBLIC_ACL` | Aws Cis S3 Public Acl |
| 4 | CRITICAL | `AWS_CIS_S3_PUBLIC_WRITE` | Aws Cis S3 Public Write |
| 5 | CRITICAL | `AWS_BP_HARDCODED_SECRET` | Aws Bp Hardcoded Secret |
| 6 | CRITICAL | `AWS_BP_HARDCODED_ACCESS_KEY` | Aws Bp Hardcoded Access Key |
| 7 | CRITICAL | `TF_HARDCODED_ENV_SECRET` | Tf Hardcoded Env Secret |
| 8 | CRITICAL | `TF_HARDCODED_CREDENTIALS` | Tf Hardcoded Credentials |
| 9 | CRITICAL | `TF_PUBLIC_S3` | Tf Public S3 |
| 10 | CRITICAL | `TF_PUBLIC_S3` | Tf Public S3 |
| 11 | CRITICAL | `TF_PUBLIC_S3` | Tf Public S3 |
| 12 | CRITICAL | `attack_path` | GNN detected critical risk attack path |
| 13 | CRITICAL | `SECRET_AWS_ACCESS_KEY` | AWS Access Key |
| 14 | CRITICAL | `SECRET_AWS_SECRET_KEY` | AWS Secret Access Key |
| 15 | HIGH | `critical_resource` | Critical infrastructure node: aws_iam_policy.data_engineer_p |
| 16 | HIGH | `CVE` | CVE-2021-3178 in terraform-provider-aws 3.0.0 |
| 17 | HIGH | `CIS_2_1_1` | S3 Bucket Encryption Not Enabled |
| 18 | MEDIUM | `AWS_BP_S3_NO_LOGGING` | Aws Bp S3 No Logging |
| 19 | MEDIUM | `AWS_BP_S3_NO_LOGGING` | Aws Bp S3 No Logging |
| 20 | MEDIUM | `AWS_BP_S3_NO_LOGGING` | Aws Bp S3 No Logging |
| 21 | MEDIUM | `AWS_BP_S3_NO_LOGGING` | Aws Bp S3 No Logging |
| 22 | MEDIUM | `AWS_BP_S3_NO_LOGGING` | Aws Bp S3 No Logging |
| 23 | MEDIUM | `TF_VERSIONING_DISABLED` | Tf Versioning Disabled |
| 24 | MEDIUM | `TF_VERSIONING_DISABLED` | Tf Versioning Disabled |
| 25 | MEDIUM | `CIS_2_1_2` | S3 Bucket Logging Not Enabled |

### Remediations Applied

- **[CRITICAL]** Replace wildcard IAM Action with least-privilege permissions
- **[CRITICAL]** Replace s3:* wildcard with least-privilege S3 actions
- **[CRITICAL]** Change S3 bucket ACL from public to private
- **[CRITICAL]** Change S3 bucket ACL from public to private
- **[CRITICAL]** Change S3 bucket ACL from public to private
- **[CRITICAL]** Replace hardcoded AWS access key with variable reference
- **[CRITICAL]** Replace hardcoded AWS secret key with variable reference
- **[MEDIUM]** Enable S3 bucket versioning
- **[MEDIUM]** Enable S3 bucket versioning
- **[MEDIUM]** Restrict CORS allowed_origins from wildcard to specific domain
- **[MEDIUM]** Restrict CORS allowed_headers from wildcard to specific headers
- **[HIGH]** Add public access block for S3 bucket 'data_lake_raw'
- **[HIGH]** Add public access block for S3 bucket 'data_lake_processed'
- **[HIGH]** Add public access block for S3 bucket 'ml_artifacts'
- **[HIGH]** Add public access block for S3 bucket 'website'
- **[HIGH]** Add public access block for S3 bucket 'backups'
- **[HIGH]** Enable access logging for S3 bucket 'data_lake_raw'
- **[HIGH]** Enable access logging for S3 bucket 'data_lake_processed'
- **[HIGH]** Enable access logging for S3 bucket 'ml_artifacts'
- **[HIGH]** Enable access logging for S3 bucket 'website'
- **[HIGH]** Enable access logging for S3 bucket 'backups'

### Remaining Issues

- [HIGH] `CVE` — CVE-2021-3178 in terraform-provider-aws 3.0.0
- [HIGH] `CIS_2_1_1` — S3 Bucket Encryption Not Enabled
- [MEDIUM] `AWS_BP_S3_NO_LOGGING` — Aws Bp S3 No Logging
- [MEDIUM] `AWS_BP_S3_NO_LOGGING` — Aws Bp S3 No Logging
- [MEDIUM] `AWS_BP_S3_NO_LOGGING` — Aws Bp S3 No Logging
- [MEDIUM] `AWS_BP_S3_NO_LOGGING` — Aws Bp S3 No Logging
- [MEDIUM] `AWS_BP_S3_NO_LOGGING` — Aws Bp S3 No Logging
- [MEDIUM] `CIS_2_1_2` — S3 Bucket Logging Not Enabled

## Case: `terragoat_eks_db.tf`

**Before:** 37 vulnerabilities → **After:** 6 → **Reduction: 83.8%**

### Vulnerabilities Detected

| # | Severity | Rule ID | Description |
|---|----------|---------|-------------|
| 1 | CRITICAL | `AWS_CIS_IAM_WILDCARD_POLICY` | Aws Cis Iam Wildcard Policy |
| 2 | CRITICAL | `AWS_CIS_SG_0_0_0_0` | Aws Cis Sg 0 0 0 0 |
| 3 | CRITICAL | `AWS_CIS_SG_0_0_0_0` | Aws Cis Sg 0 0 0 0 |
| 4 | CRITICAL | `AWS_CIS_SG_0_0_0_0` | Aws Cis Sg 0 0 0 0 |
| 5 | CRITICAL | `AWS_CIS_SG_0_0_0_0` | Aws Cis Sg 0 0 0 0 |
| 6 | CRITICAL | `AWS_CIS_SG_0_0_0_0` | Aws Cis Sg 0 0 0 0 |
| 7 | CRITICAL | `AWS_CIS_SG_0_0_0_0` | Aws Cis Sg 0 0 0 0 |
| 8 | CRITICAL | `AWS_CIS_DB_PUBLIC` | Aws Cis Db Public |
| 9 | CRITICAL | `AWS_OWASP_A05_MISCONFIG_SG` | Aws Owasp A05 Misconfig Sg |
| 10 | CRITICAL | `AWS_OWASP_A05_MISCONFIG_SG` | Aws Owasp A05 Misconfig Sg |
| 11 | CRITICAL | `AWS_OWASP_A07_AUTH_FAILURE` | Aws Owasp A07 Auth Failure |
| 12 | CRITICAL | `AWS_BP_HARDCODED_PASSWORD` | Aws Bp Hardcoded Password |
| 13 | CRITICAL | `TF_HARDCODED_CREDENTIALS` | Tf Hardcoded Credentials |
| 14 | CRITICAL | `TF_OPEN_SECURITY_GROUP` | Tf Open Security Group |
| 15 | CRITICAL | `TF_OPEN_SECURITY_GROUP` | Tf Open Security Group |
| 16 | CRITICAL | `TF_OPEN_SECURITY_GROUP` | Tf Open Security Group |
| 17 | CRITICAL | `TF_OPEN_SECURITY_GROUP` | Tf Open Security Group |
| 18 | CRITICAL | `TF_OPEN_SECURITY_GROUP` | Tf Open Security Group |
| 19 | CRITICAL | `TF_OPEN_SECURITY_GROUP` | Tf Open Security Group |
| 20 | CRITICAL | `attack_path` | GNN detected critical risk attack path |
| 21 | CRITICAL | `SECRET_AWS_ACCESS_KEY` | AWS Access Key |
| 22 | CRITICAL | `SECRET_AWS_SECRET_KEY` | AWS Secret Access Key |
| 23 | CRITICAL | `CIS_4_1` | SSH Open to Internet |
| 24 | HIGH | `AWS_CIS_DB_UNENCRYPTED` | Aws Cis Db Unencrypted |
| 25 | HIGH | `AWS_OWASP_A02_CRYPTO_FAILURE` | Aws Owasp A02 Crypto Failure |
| 26 | HIGH | `AWS_OWASP_A02_CRYPTO_FAILURE` | Aws Owasp A02 Crypto Failure |
| 27 | HIGH | `NO_HARDCODED_SECRET` | No Hardcoded Secret |
| 28 | HIGH | `NO_HARDCODED_SECRET` | No Hardcoded Secret |
| 29 | HIGH | `TF_UNENCRYPTED_EBS` | Tf Unencrypted Ebs |
| 30 | HIGH | `TF_UNENCRYPTED_RDS` | Tf Unencrypted Rds |
| 31 | HIGH | `critical_resource` | Critical infrastructure node: aws_db_instance.platform_db |
| 32 | HIGH | `CVE` | CVE-2021-3178 in terraform-provider-aws 3.0.0 |
| 33 | HIGH | `CIS_1_4` | MFA Not Enabled for IAM User |
| 34 | MEDIUM | `AWS_BP_SKIP_FINAL_SNAPSHOT` | Aws Bp Skip Final Snapshot |
| 35 | MEDIUM | `AWS_BP_EGRESS_ALL` | Aws Bp Egress All |
| 36 | MEDIUM | `AWS_BP_EGRESS_ALL` | Aws Bp Egress All |
| 37 | LOW | `AWS_BP_EC2_NO_MONITORING` | Aws Bp Ec2 No Monitoring |

### Remediations Applied

- **[CRITICAL]** Replace wildcard IAM Action with least-privilege permissions
- **[CRITICAL]** Restrict SSH access from 0.0.0.0/0 to internal CIDR
- **[CRITICAL]** Disable public accessibility for RDS instance
- **[CRITICAL]** Replace hardcoded database password with variable/secrets manager
- **[CRITICAL]** Replace hardcoded environment secret with Secrets Manager reference
- **[HIGH]** Enable storage encryption for RDS instance
- **[HIGH]** Enable EBS volume encryption
- **[MEDIUM]** Enable final snapshot on RDS deletion
- **[MEDIUM]** Restrict unrestricted egress to internal CIDR
- **[MEDIUM]** Restrict unrestricted egress to internal CIDR
- **[LOW]** Enable detailed monitoring for EC2 instance
- **[MEDIUM]** Remove hardcoded AWS key from user_data, use instance profile
- **[MEDIUM]** Remove hardcoded AWS secret from user_data, use instance profile
- **[MEDIUM]** Replace hardcoded DATABASE_URL with SSM parameter lookup
- **[MEDIUM]** Restrict Kubernetes API access to internal CIDR
- **[MEDIUM]** Restrict NodePort range to internal CIDR
- **[MEDIUM]** Restrict database port to application subnet CIDR
- **[MEDIUM]** Increase backup retention period to 35 days
- **[MEDIUM]** Increase CloudWatch log retention to 365 days

### Remaining Issues

- [CRITICAL] `AWS_OWASP_A05_MISCONFIG_SG` — Aws Owasp A05 Misconfig Sg
- [CRITICAL] `AWS_OWASP_A05_MISCONFIG_SG` — Aws Owasp A05 Misconfig Sg
- [HIGH] `CVE` — CVE-2021-3178 in terraform-provider-aws 3.0.0
- [HIGH] `CIS_1_4` — MFA Not Enabled for IAM User
- [MEDIUM] `AWS_BP_EGRESS_ALL` — Aws Bp Egress All
- [MEDIUM] `AWS_BP_EGRESS_ALL` — Aws Bp Egress All

## Case: `terragoat_lambda.tf`

**Before:** 38 vulnerabilities → **After:** 8 → **Reduction: 78.9%**

### Vulnerabilities Detected

| # | Severity | Rule ID | Description |
|---|----------|---------|-------------|
| 1 | CRITICAL | `AWS_CIS_IAM_WILDCARD_POLICY` | Aws Cis Iam Wildcard Policy |
| 2 | CRITICAL | `AWS_CIS_SG_0_0_0_0` | Aws Cis Sg 0 0 0 0 |
| 3 | CRITICAL | `AWS_CIS_SG_0_0_0_0` | Aws Cis Sg 0 0 0 0 |
| 4 | CRITICAL | `AWS_CIS_S3_PUBLIC_ACL` | Aws Cis S3 Public Acl |
| 5 | CRITICAL | `AWS_CIS_SG_ALL_PORTS` | Aws Cis Sg All Ports |
| 6 | CRITICAL | `AWS_CIS_DB_PUBLIC` | Aws Cis Db Public |
| 7 | CRITICAL | `AWS_OWASP_A05_MISCONFIG_SG` | Aws Owasp A05 Misconfig Sg |
| 8 | CRITICAL | `AWS_OWASP_A05_MISCONFIG_SG` | Aws Owasp A05 Misconfig Sg |
| 9 | CRITICAL | `AWS_OWASP_A07_AUTH_FAILURE` | Aws Owasp A07 Auth Failure |
| 10 | CRITICAL | `AWS_BP_HARDCODED_PASSWORD` | Aws Bp Hardcoded Password |
| 11 | CRITICAL | `TF_HARDCODED_ENV_SECRET` | Tf Hardcoded Env Secret |
| 12 | CRITICAL | `TF_HARDCODED_CREDENTIALS` | Tf Hardcoded Credentials |
| 13 | CRITICAL | `TF_OPEN_SECURITY_GROUP` | Tf Open Security Group |
| 14 | CRITICAL | `TF_OPEN_SECURITY_GROUP` | Tf Open Security Group |
| 15 | CRITICAL | `TF_PUBLIC_S3` | Tf Public S3 |
| 16 | CRITICAL | `attack_path` | GNN detected critical risk attack path |
| 17 | CRITICAL | `CIS_4_1` | SSH Open to Internet |
| 18 | CRITICAL | `CIS_4_2` | RDP Open to Internet |
| 19 | HIGH | `AWS_CIS_DB_UNENCRYPTED` | Aws Cis Db Unencrypted |
| 20 | HIGH | `AWS_OWASP_A02_CRYPTO_FAILURE` | Aws Owasp A02 Crypto Failure |
| 21 | HIGH | `NO_HARDCODED_SECRET` | No Hardcoded Secret |
| 22 | HIGH | `NO_HARDCODED_SECRET` | No Hardcoded Secret |
| 23 | HIGH | `NO_HARDCODED_SECRET` | No Hardcoded Secret |
| 24 | HIGH | `NO_HARDCODED_SECRET` | No Hardcoded Secret |
| 25 | HIGH | `NO_HARDCODED_SECRET` | No Hardcoded Secret |
| 26 | HIGH | `NO_HARDCODED_SECRET` | No Hardcoded Secret |
| 27 | HIGH | `NO_HARDCODED_SECRET` | No Hardcoded Secret |
| 28 | HIGH | `TF_UNENCRYPTED_RDS` | Tf Unencrypted Rds |
| 29 | HIGH | `TF_WIDE_PORT_RANGE` | Tf Wide Port Range |
| 30 | HIGH | `critical_resource` | Critical infrastructure node: aws_db_instance.payment_db |
| 31 | HIGH | `SECRET_GENERIC_API_KEY` | API Key |
| 32 | HIGH | `CVE` | CVE-2021-3178 in terraform-provider-aws 3.0.0 |
| 33 | HIGH | `CIS_2_1_1` | S3 Bucket Encryption Not Enabled |
| 34 | MEDIUM | `AWS_BP_S3_NO_LOGGING` | Aws Bp S3 No Logging |
| 35 | MEDIUM | `AWS_BP_SKIP_FINAL_SNAPSHOT` | Aws Bp Skip Final Snapshot |
| 36 | MEDIUM | `AWS_BP_EGRESS_ALL` | Aws Bp Egress All |
| 37 | MEDIUM | `TF_VERSIONING_DISABLED` | Tf Versioning Disabled |
| 38 | MEDIUM | `CIS_2_1_2` | S3 Bucket Logging Not Enabled |

### Remediations Applied

- **[CRITICAL]** Replace wildcard IAM Action with least-privilege permissions
- **[CRITICAL]** Replace all-ports-open with HTTPS-only from restricted CIDR
- **[CRITICAL]** Change S3 bucket ACL from public to private
- **[CRITICAL]** Disable public accessibility for RDS instance
- **[CRITICAL]** Replace hardcoded database password with variable/secrets manager
- **[CRITICAL]** Replace hardcoded environment secret with Secrets Manager reference
- **[CRITICAL]** Replace hardcoded environment secret with Secrets Manager reference
- **[HIGH]** Enable storage encryption for RDS instance
- **[HIGH]** Replace hardcoded environment secret with Secrets Manager reference
- **[HIGH]** Replace hardcoded environment secret with Secrets Manager reference
- **[HIGH]** Replace hardcoded environment secret with Secrets Manager reference
- **[HIGH]** Replace hardcoded environment secret with Secrets Manager reference
- **[HIGH]** Replace hardcoded environment secret with Secrets Manager reference
- **[MEDIUM]** Enable final snapshot on RDS deletion
- **[MEDIUM]** Restrict unrestricted egress to internal CIDR
- **[MEDIUM]** Enable S3 bucket versioning
- **[MEDIUM]** Increase backup retention period to 35 days
- **[MEDIUM]** Increase CloudWatch log retention to 365 days
- **[MEDIUM]** Change LOG_LEVEL from DEBUG to WARN in production
- **[MEDIUM]** Add KMS encryption to SNS topic
- **[HIGH]** Add S3 server-side encryption configuration
- **[HIGH]** Add public access block for S3 bucket 'payment_receipts'
- **[HIGH]** Enable access logging for S3 bucket 'payment_receipts'

### Remaining Issues

- [CRITICAL] `AWS_OWASP_A05_MISCONFIG_SG` — Aws Owasp A05 Misconfig Sg
- [HIGH] `NO_HARDCODED_SECRET` — No Hardcoded Secret
- [HIGH] `SECRET_GENERIC_PASSWORD` — Hardcoded Password
- [HIGH] `CVE` — CVE-2021-3178 in terraform-provider-aws 3.0.0
- [HIGH] `CIS_2_1_1` — S3 Bucket Encryption Not Enabled
- [MEDIUM] `AWS_BP_S3_NO_LOGGING` — Aws Bp S3 No Logging
- [MEDIUM] `AWS_BP_EGRESS_ALL` — Aws Bp Egress All
- [MEDIUM] `CIS_2_1_2` — S3 Bucket Logging Not Enabled

## Case: `real_world_webapp.tf`

**Before:** 50 vulnerabilities → **After:** 11 → **Reduction: 78.0%**

### Vulnerabilities Detected

| # | Severity | Rule ID | Description |
|---|----------|---------|-------------|
| 1 | CRITICAL | `AWS_CIS_IAM_WILDCARD_POLICY` | Aws Cis Iam Wildcard Policy |
| 2 | CRITICAL | `AWS_CIS_SG_0_0_0_0` | Aws Cis Sg 0 0 0 0 |
| 3 | CRITICAL | `AWS_CIS_SG_0_0_0_0` | Aws Cis Sg 0 0 0 0 |
| 4 | CRITICAL | `AWS_CIS_SG_0_0_0_0` | Aws Cis Sg 0 0 0 0 |
| 5 | CRITICAL | `AWS_CIS_SG_0_0_0_0` | Aws Cis Sg 0 0 0 0 |
| 6 | CRITICAL | `AWS_CIS_S3_PUBLIC_ACL` | Aws Cis S3 Public Acl |
| 7 | CRITICAL | `AWS_CIS_SG_ALL_PORTS` | Aws Cis Sg All Ports |
| 8 | CRITICAL | `AWS_CIS_DB_PUBLIC` | Aws Cis Db Public |
| 9 | CRITICAL | `AWS_OWASP_A05_MISCONFIG_SG` | Aws Owasp A05 Misconfig Sg |
| 10 | CRITICAL | `AWS_OWASP_A05_MISCONFIG_SG` | Aws Owasp A05 Misconfig Sg |
| 11 | CRITICAL | `AWS_OWASP_A07_AUTH_FAILURE` | Aws Owasp A07 Auth Failure |
| 12 | CRITICAL | `AWS_BP_HARDCODED_PASSWORD` | Aws Bp Hardcoded Password |
| 13 | CRITICAL | `AWS_BP_HARDCODED_SECRET` | Aws Bp Hardcoded Secret |
| 14 | CRITICAL | `AWS_BP_HARDCODED_ACCESS_KEY` | Aws Bp Hardcoded Access Key |
| 15 | CRITICAL | `TF_HARDCODED_ENV_SECRET` | Tf Hardcoded Env Secret |
| 16 | CRITICAL | `TF_HARDCODED_ENV_SECRET` | Tf Hardcoded Env Secret |
| 17 | CRITICAL | `TF_HARDCODED_CREDENTIALS` | Tf Hardcoded Credentials |
| 18 | CRITICAL | `TF_HARDCODED_CREDENTIALS` | Tf Hardcoded Credentials |
| 19 | CRITICAL | `TF_OPEN_SECURITY_GROUP` | Tf Open Security Group |
| 20 | CRITICAL | `TF_OPEN_SECURITY_GROUP` | Tf Open Security Group |
| 21 | CRITICAL | `TF_OPEN_SECURITY_GROUP` | Tf Open Security Group |
| 22 | CRITICAL | `TF_OPEN_SECURITY_GROUP` | Tf Open Security Group |
| 23 | CRITICAL | `TF_PUBLIC_S3` | Tf Public S3 |
| 24 | CRITICAL | `attack_path` | GNN detected critical risk attack path |
| 25 | CRITICAL | `SECRET_AWS_ACCESS_KEY` | AWS Access Key |
| 26 | CRITICAL | `SECRET_AWS_SECRET_KEY` | AWS Secret Access Key |
| 27 | CRITICAL | `CIS_4_1` | SSH Open to Internet |
| 28 | CRITICAL | `CIS_4_2` | RDP Open to Internet |
| 29 | HIGH | `AWS_CIS_DB_UNENCRYPTED` | Aws Cis Db Unencrypted |
| 30 | HIGH | `AWS_OWASP_A02_CRYPTO_FAILURE` | Aws Owasp A02 Crypto Failure |
| 31 | HIGH | `AWS_OWASP_A02_CRYPTO_FAILURE` | Aws Owasp A02 Crypto Failure |
| 32 | HIGH | `NO_HARDCODED_SECRET` | No Hardcoded Secret |
| 33 | HIGH | `NO_HARDCODED_SECRET` | No Hardcoded Secret |
| 34 | HIGH | `NO_HARDCODED_SECRET` | No Hardcoded Secret |
| 35 | HIGH | `NO_HARDCODED_SECRET` | No Hardcoded Secret |
| 36 | HIGH | `NO_HARDCODED_SECRET` | No Hardcoded Secret |
| 37 | HIGH | `TF_UNENCRYPTED_EBS` | Tf Unencrypted Ebs |
| 38 | HIGH | `TF_UNENCRYPTED_RDS` | Tf Unencrypted Rds |
| 39 | HIGH | `TF_WIDE_PORT_RANGE` | Tf Wide Port Range |
| 40 | HIGH | `critical_resource` | Critical infrastructure node: aws_db_instance.main_db |
| 41 | HIGH | `SECRET_GENERIC_API_KEY` | API Key |
| 42 | HIGH | `CVE` | CVE-2021-3178 in terraform-provider-aws 3.0.0 |
| 43 | HIGH | `CIS_1_4` | MFA Not Enabled for IAM User |
| 44 | HIGH | `CIS_2_1_1` | S3 Bucket Encryption Not Enabled |
| 45 | MEDIUM | `AWS_BP_S3_NO_LOGGING` | Aws Bp S3 No Logging |
| 46 | MEDIUM | `AWS_BP_SKIP_FINAL_SNAPSHOT` | Aws Bp Skip Final Snapshot |
| 47 | MEDIUM | `AWS_BP_EGRESS_ALL` | Aws Bp Egress All |
| 48 | MEDIUM | `TF_VERSIONING_DISABLED` | Tf Versioning Disabled |
| 49 | MEDIUM | `CIS_2_1_2` | S3 Bucket Logging Not Enabled |
| 50 | LOW | `AWS_BP_EC2_NO_MONITORING` | Aws Bp Ec2 No Monitoring |

### Remediations Applied

- **[CRITICAL]** Replace wildcard IAM Action with least-privilege permissions
- **[CRITICAL]** Restrict SSH access from 0.0.0.0/0 to internal CIDR
- **[CRITICAL]** Replace all-ports-open with HTTPS-only from restricted CIDR
- **[CRITICAL]** Change S3 bucket ACL from public to private
- **[CRITICAL]** Disable public accessibility for RDS instance
- **[CRITICAL]** Replace hardcoded database password with variable/secrets manager
- **[CRITICAL]** Replace hardcoded environment secret with Secrets Manager reference
- **[CRITICAL]** Replace hardcoded AWS access key with variable reference
- **[CRITICAL]** Replace hardcoded AWS secret key with variable reference
- **[HIGH]** Enable storage encryption for RDS instance
- **[HIGH]** Enable EBS volume encryption
- **[MEDIUM]** Enable final snapshot on RDS deletion
- **[MEDIUM]** Restrict unrestricted egress to internal CIDR
- **[MEDIUM]** Enable S3 bucket versioning
- **[LOW]** Enable detailed monitoring for EC2 instance
- **[MEDIUM]** Restrict RDP access from 0.0.0.0/0 to internal CIDR
- **[MEDIUM]** Increase backup retention period to 35 days
- **[HIGH]** Add S3 server-side encryption configuration
- **[HIGH]** Add public access block for S3 bucket 'app_data'
- **[HIGH]** Enable access logging for S3 bucket 'app_data'

### Remaining Issues

- [CRITICAL] `AWS_OWASP_A05_MISCONFIG_SG` — Aws Owasp A05 Misconfig Sg
- [HIGH] `NO_HARDCODED_SECRET` — No Hardcoded Secret
- [HIGH] `NO_HARDCODED_SECRET` — No Hardcoded Secret
- [HIGH] `NO_HARDCODED_SECRET` — No Hardcoded Secret
- [HIGH] `SECRET_GENERIC_PASSWORD` — Hardcoded Password
- [HIGH] `CVE` — CVE-2021-3178 in terraform-provider-aws 3.0.0
- [HIGH] `CIS_1_4` — MFA Not Enabled for IAM User
- [HIGH] `CIS_2_1_1` — S3 Bucket Encryption Not Enabled
- [MEDIUM] `AWS_BP_S3_NO_LOGGING` — Aws Bp S3 No Logging
- [MEDIUM] `AWS_BP_EGRESS_ALL` — Aws Bp Egress All
- [MEDIUM] `CIS_2_1_2` — S3 Bucket Logging Not Enabled

## Methodology

### Vulnerability Sources
- **TerraGoat patterns** — Based on BridgeCrew's intentionally vulnerable Terraform repo
- **Real breach post-mortems** — S3 data leaks, exposed databases, credential exposure
- **CIS AWS Benchmark** — Security group, IAM, encryption, logging controls

### Scanner Pipeline
1. **Rules Engine** — 40+ pattern-based rules (CIS, OWASP, best practices)
2. **Secrets Scanner** — Regex + entropy-based credential detection
3. **Compliance Scanner** — CIS Benchmark validation
4. **GNN Attack Path Analyzer** — Graph neural network for topology-aware risk
5. **ML Risk Scorer** — Trained classifier for IaC risk prediction

### Auto-Remediation Engine
- Template-based fix generation with security best practices
- Pattern scanning for unreported issues
- Missing security block injection (encryption, public access blocks)
- Deterministic, auditable changes

## Limitations & Caveats

- Remediation templates cover common AWS patterns; custom resources may need manual review
- Some findings require architectural changes beyond simple code fixes
- The auto-remediation engine produces valid HCL but manual review is recommended
- Reduction percentages measure finding count, not risk-weighted reduction

---
*Report generated by CloudGuardAI v2.0 — 2026-03-04*