"""
Auto-Remediation Engine for CloudGuardAI
==========================================
Generates secure Terraform code fixes for detected vulnerabilities.
Maps scanner findings to concrete, apply-ready IaC patches.

This engine demonstrates practical utility by:
  1. Parsing findings from all scanners (rules, secrets, compliance, GNN, ML)
  2. Matching each finding to a remediation template
  3. Applying regex-based transforms to produce the fixed file
  4. Producing a diff and structured remediation report

Usage:
    from evaluation.case_study.auto_remediation import AutoRemediator
    remediator = AutoRemediator()
    result = remediator.remediate(vulnerable_content, findings)
    print(result['fixed_content'])
    print(result['changes_applied'])
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class RemediationAction:
    """A single remediation change to apply."""
    finding_id: str
    rule_id: str
    severity: str
    description: str
    original_text: str
    fixed_text: str
    line_hint: int = 0
    category: str = ""


# ── Remediation Templates ──────────────────────────────────────────────────

REMEDIATION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    # ─── Hardcoded AWS Credentials ───
    "hardcoded_aws_access_key": {
        "pattern": r'(access_key\s*=\s*)"[A-Z0-9]{20}"',
        "replacement": r'\1var.aws_access_key  # Use variable or IAM role',
        "description": "Replace hardcoded AWS access key with variable reference",
    },
    "hardcoded_aws_secret_key": {
        "pattern": r'(secret_key\s*=\s*)"[A-Za-z0-9/+=]{40}"',
        "replacement": r'\1var.aws_secret_key  # Use variable or IAM role',
        "description": "Replace hardcoded AWS secret key with variable reference",
    },
    # ─── Hardcoded Passwords ───
    "hardcoded_db_password": {
        "pattern": r'(password\s*=\s*)"[^"]{8,}"(\s*#[^\n]*)?',
        "replacement": r'\1var.db_password  # Use AWS Secrets Manager or SSM Parameter Store',
        "description": "Replace hardcoded database password with variable/secrets manager",
    },
    # ─── Hardcoded Env Secrets ───
    "hardcoded_env_secret": {
        "pattern": r'(\b(?:SECRET|PASSWORD|API_KEY|SIGNING_SECRET|CLIENT_SECRET|ENCRYPTION_KEY|PLAID_CLIENT_SECRET|REDIS_PASSWORD|COGNITO_CLIENT_SECRET|JWT_SIGNING_SECRET|JWT_SECRET|STRIPE_SECRET_KEY)\s*=\s*)"[^"]{8,}"',
        "replacement": r'\1data.aws_ssm_parameter.{}.value  # Reference SSM/Secrets Manager',
        "description": "Replace hardcoded environment secret with Secrets Manager reference",
    },
    "hardcoded_env_aws_key": {
        "pattern": r'(export\s+AWS_ACCESS_KEY_ID=)"[^"]+"',
        "replacement": r'# AWS_ACCESS_KEY_ID - use IAM instance profile instead',
        "description": "Remove hardcoded AWS key from user_data, use instance profile",
    },
    "hardcoded_env_aws_secret": {
        "pattern": r'(export\s+AWS_SECRET_ACCESS_KEY=)"[^"]+"',
        "replacement": r'# AWS_SECRET_ACCESS_KEY - use IAM instance profile instead',
        "description": "Remove hardcoded AWS secret from user_data, use instance profile",
    },
    "hardcoded_userdata_db_url": {
        "pattern": r'export\s+DATABASE_URL="[^"]+"',
        "replacement": 'export DATABASE_URL=$(aws ssm get-parameter --name /app/database-url --with-decryption --query Parameter.Value --output text)',
        "description": "Replace hardcoded DATABASE_URL with SSM parameter lookup",
    },
    "hardcoded_userdata_jwt": {
        "pattern": r'export\s+JWT_SECRET="[^"]+"',
        "replacement": 'export JWT_SECRET=$(aws ssm get-parameter --name /app/jwt-secret --with-decryption --query Parameter.Value --output text)',
        "description": "Replace hardcoded JWT_SECRET with SSM parameter lookup",
    },
    # ─── S3 Public Access ───
    "s3_public_acl": {
        "pattern": r'acl\s*=\s*"public-read(?:-write)?"',
        "replacement": 'acl    = "private"  # Restrict bucket access',
        "description": "Change S3 bucket ACL from public to private",
    },
    # ─── S3 Versioning ───
    "s3_versioning_disabled": {
        "pattern": r'(versioning\s*\{[^}]*enabled\s*=\s*)false',
        "replacement": r'\1true   # Enable versioning for data protection',
        "description": "Enable S3 bucket versioning",
    },
    # ─── Security Group: SSH open ───
    "sg_ssh_open": {
        "pattern": r'(ingress\s*\{[^}]*from_port\s*=\s*22[^}]*cidr_blocks\s*=\s*\[)"0\.0\.0\.0/0"(\])',
        "replacement": r'\1"10.0.0.0/8"\2  # Restrict SSH to internal VPN CIDR',
        "description": "Restrict SSH access from 0.0.0.0/0 to internal CIDR",
    },
    # ─── Security Group: RDP open ───
    "sg_rdp_open": {
        "pattern": r'(ingress\s*\{[^}]*from_port\s*=\s*3389[^}]*cidr_blocks\s*=\s*\[)"0\.0\.0\.0/0"(\])',
        "replacement": r'\1"10.0.0.0/8"\2  # Restrict RDP to internal VPN CIDR',
        "description": "Restrict RDP access from 0.0.0.0/0 to internal CIDR",
    },
    # ─── Security Group: All ports open ───
    "sg_all_ports_open": {
        "pattern": r'ingress\s*\{[^}]*from_port\s*=\s*0[^}]*to_port\s*=\s*65535[^}]*cidr_blocks\s*=\s*\["0\.0\.0\.0/0"\][^}]*\}',
        "replacement": 'ingress {\n    from_port   = 443\n    to_port     = 443\n    protocol    = "tcp"\n    cidr_blocks = ["10.0.0.0/8"]  # HTTPS only from internal network\n  }',
        "description": "Replace all-ports-open with HTTPS-only from restricted CIDR",
    },
    # ─── Security Group: 443 open to internet (Kubernetes API) ───
    "sg_k8s_api_open": {
        "pattern": r'(ingress\s*\{[^}]*from_port\s*=\s*443[^}]*to_port\s*=\s*443[^}]*cidr_blocks\s*=\s*\[)"0\.0\.0\.0/0"(\])',
        "replacement": r'\1"10.0.0.0/8"\2  # Restrict K8s API to VPN CIDR',
        "description": "Restrict Kubernetes API access to internal CIDR",
    },
    # ─── Security Group: NodePort range open ───
    "sg_nodeport_open": {
        "pattern": r'(ingress\s*\{[^}]*from_port\s*=\s*30000[^}]*cidr_blocks\s*=\s*\[)"0\.0\.0\.0/0"(\])',
        "replacement": r'\1"10.0.0.0/8"\2  # Restrict NodePorts to internal CIDR',
        "description": "Restrict NodePort range to internal CIDR",
    },
    # ─── Security Group: Database port open ───
    "sg_db_port_open": {
        "pattern": r'(ingress\s*\{[^}]*from_port\s*=\s*(?:5432|3306|1433)[^}]*cidr_blocks\s*=\s*\[)"0\.0\.0\.0/0"(\])',
        "replacement": r'\1"10.0.0.0/8"\2  # Restrict DB access to application subnet',
        "description": "Restrict database port to application subnet CIDR",
    },
    # ─── RDS Public Access ───
    "rds_public": {
        "pattern": r'(publicly_accessible\s*=\s*)true',
        "replacement": r'\1false  # Never expose databases to the internet',
        "description": "Disable public accessibility for RDS instance",
    },
    # ─── RDS Unencrypted ───
    "rds_unencrypted": {
        "pattern": r'(storage_encrypted\s*=\s*)false',
        "replacement": r'\1true   # Enable encryption at rest (AES-256)',
        "description": "Enable storage encryption for RDS instance",
    },
    # ─── RDS Skip Final Snapshot ───
    "rds_skip_snapshot": {
        "pattern": r'(skip_final_snapshot\s*=\s*)true',
        "replacement": r'\1false  # Take final snapshot before deletion',
        "description": "Enable final snapshot on RDS deletion",
    },
    # ─── RDS No Backups ───
    "rds_no_backup": {
        "pattern": r'backup_retention_period\s*=\s*[01]\b',
        "replacement": 'backup_retention_period = 35  # 35 days backup retention (max)',
        "description": "Increase backup retention period to 35 days",
    },
    # ─── EBS Unencrypted ───
    "ebs_unencrypted": {
        "pattern": r'(encrypted\s*=\s*)false(\s*#[^\n]*)?',
        "replacement": r'\1true   # Enable EBS encryption at rest',
        "description": "Enable EBS volume encryption",
    },
    # ─── EC2 Monitoring ───
    "ec2_no_monitoring": {
        "pattern": r'(monitoring\s*=\s*)false',
        "replacement": r'\1true   # Enable detailed CloudWatch monitoring',
        "description": "Enable detailed monitoring for EC2 instance",
    },
    # ─── IAM Wildcard Policy ───
    "iam_wildcard": {
        "pattern": r'(Action\s*=\s*)"(\*)"',
        "replacement": r'\1["sts:AssumeRole", "logs:CreateLogGroup", "logs:PutLogEvents"]  # Least-privilege actions',
        "description": "Replace wildcard IAM Action with least-privilege permissions",
    },
    # ─── CloudWatch Log Retention ───
    "log_short_retention": {
        "pattern": r'retention_in_days\s*=\s*[1-3]\b',
        "replacement": 'retention_in_days = 365  # Retain logs for 1 year (compliance)',
        "description": "Increase CloudWatch log retention to 365 days",
    },
    # ─── Debug Logging in Production ───
    "debug_in_prod": {
        "pattern": r'(LOG_LEVEL\s*=\s*)"DEBUG"',
        "replacement": r'\1"WARN"  # Use WARN or ERROR in production',
        "description": "Change LOG_LEVEL from DEBUG to WARN in production",
    },
    # ─── Egress: Unrestricted outbound ───
    "egress_unrestricted": {
        "pattern": r'(egress\s*\{[^}]*protocol\s*=\s*"-1"[^}]*cidr_blocks\s*=\s*\[)"0\.0\.0\.0/0"(\])',
        "replacement": r'\1"10.0.0.0/8"\2  # Restrict egress to internal network',
        "description": "Restrict unrestricted egress to internal CIDR",
    },
    # ─── CORS Wildcard Origin ───
    "cors_wildcard_origin": {
        "pattern": r'(allowed_origins\s*=\s*\[)"\*"(\])',
        "replacement": r'\1"https://app.acme.com"\2  # Restrict CORS to known origins',
        "description": "Restrict CORS allowed_origins from wildcard to specific domain",
    },
    # ─── CORS Wildcard Headers ───
    "cors_wildcard_headers": {
        "pattern": r'(allowed_headers\s*=\s*\[)"\*"(\])',
        "replacement": r'\1"Content-Type", "Authorization"\2  # Restrict CORS headers',
        "description": "Restrict CORS allowed_headers from wildcard to specific headers",
    },
    # ─── S3 Wildcard IAM Actions ───
    "s3_wildcard_action": {
        "pattern": r'(Action\s*=\s*)"s3:\*"',
        "replacement": r'\1["s3:GetObject", "s3:PutObject", "s3:ListBucket"]  # Least-privilege S3',
        "description": "Replace s3:* wildcard with least-privilege S3 actions",
    },
    # ─── SNS Topic Encryption ───
    "sns_no_encryption": {
        "pattern": r'(resource\s+"aws_sns_topic"\s+"\w+"\s*\{[^}]*name\s*=\s*"[^"]+")',
        "replacement": r'\1\n  kms_master_key_id = "alias/aws/sns"  # Enable SNS encryption',
        "description": "Add KMS encryption to SNS topic",
    },
}


class AutoRemediator:
    """
    Automated IaC remediation engine.
    
    Takes vulnerable Terraform content + scanner findings,
    applies matching remediation templates, and returns
    the fixed content plus a structured change log.
    """

    def __init__(self, custom_templates: Optional[Dict] = None):
        self.templates = {**REMEDIATION_TEMPLATES}
        if custom_templates:
            self.templates.update(custom_templates)
        self._applied: List[RemediationAction] = []

    # ── Public API ──────────────────────────────────────────────────────────

    def remediate(
        self,
        content: str,
        findings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Apply all applicable remediations to *content* based on *findings*.

        Returns dict with:
            fixed_content    – the remediated Terraform code
            changes_applied  – list of RemediationAction dicts
            stats            – summary counts
        """
        self._applied = []
        fixed = content

        # 1. Apply finding-driven remediations (contextual)
        fixed = self._apply_finding_driven(fixed, findings)

        # 2. Apply pattern-scan remediations (catch anything the rules missed)
        fixed = self._apply_pattern_scan(fixed)

        # 3. Add missing security blocks (encryption, versioning, etc.)
        fixed = self._add_missing_blocks(fixed)

        stats = self._compute_stats()

        return {
            "fixed_content": fixed,
            "changes_applied": [
                {
                    "finding_id": a.finding_id,
                    "rule_id": a.rule_id,
                    "severity": a.severity,
                    "description": a.description,
                    "category": a.category,
                }
                for a in self._applied
            ],
            "stats": stats,
        }

    # ── Internal ────────────────────────────────────────────────────────────

    def _apply_finding_driven(
        self, content: str, findings: List[Dict[str, Any]]
    ) -> str:
        """Apply remediations guided by specific scanner findings."""
        for f in findings:
            rule_id = (f.get("rule_id") or f.get("type") or "").upper()
            severity = (f.get("severity") or "MEDIUM").upper()
            title = (f.get("title") or f.get("description") or "").lower()
            category = f.get("category", f.get("scanner", ""))

            # Map finding to template keys
            template_keys = self._map_finding_to_templates(rule_id, title, category)

            for tkey in template_keys:
                tmpl = self.templates.get(tkey)
                if not tmpl:
                    continue
                new_content, count = re.subn(
                    tmpl["pattern"], tmpl["replacement"], content, count=1
                )
                if count > 0 and new_content != content:
                    self._applied.append(
                        RemediationAction(
                            finding_id=f.get("rule_id", tkey),
                            rule_id=rule_id,
                            severity=severity,
                            description=tmpl["description"],
                            original_text="(pattern match)",
                            fixed_text="(template applied)",
                            category=category,
                        )
                    )
                    content = new_content

        return content

    def _apply_pattern_scan(self, content: str) -> str:
        """Sweep all templates across content to catch unreported issues."""
        for tkey, tmpl in self.templates.items():
            # Skip if already applied
            if any(a.finding_id == tkey for a in self._applied):
                continue
            new_content, count = re.subn(
                tmpl["pattern"], tmpl["replacement"], content
            )
            if count > 0 and new_content != content:
                self._applied.append(
                    RemediationAction(
                        finding_id=tkey,
                        rule_id=f"PATTERN_{tkey.upper()}",
                        severity="MEDIUM",
                        description=tmpl["description"],
                        original_text="(pattern scan)",
                        fixed_text="(auto-detected)",
                        category="pattern_scan",
                    )
                )
                content = new_content
        return content

    def _add_missing_blocks(self, content: str) -> str:
        """Add missing security configuration blocks."""
        additions: List[Tuple[str, str, str]] = []

        # Add S3 encryption block if S3 bucket exists but no encryption config
        if "aws_s3_bucket" in content and "server_side_encryption_configuration" not in content:
            # Find bucket resources and add encryption after them
            s3_pattern = r'(resource\s+"aws_s3_bucket"\s+"(\w+)"\s*\{[^}]+\})'
            for match in re.finditer(s3_pattern, content, re.DOTALL):
                bucket_name = match.group(2)
                enc_block = f'''
# Auto-remediation: Add server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "{bucket_name}_encryption" {{
  bucket = aws_s3_bucket.{bucket_name}.id
  rule {{
    apply_server_side_encryption_by_default {{
      sse_algorithm = "aws:kms"
    }}
    bucket_key_enabled = true
  }}
}}
'''
                additions.append(
                    (bucket_name, enc_block, "Add S3 server-side encryption configuration")
                )

        # Add S3 public access block
        if "aws_s3_bucket" in content and "aws_s3_bucket_public_access_block" not in content:
            s3_names = re.findall(
                r'resource\s+"aws_s3_bucket"\s+"(\w+)"', content
            )
            for bname in s3_names:
                pab_block = f'''
# Auto-remediation: Block all public access
resource "aws_s3_bucket_public_access_block" "{bname}_public_access" {{
  bucket                  = aws_s3_bucket.{bname}.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}}
'''
                additions.append(
                    (f"{bname}_pab", pab_block, f"Add public access block for S3 bucket '{bname}'")
                )

        # Add S3 logging block if S3 bucket exists but no logging config
        if "aws_s3_bucket" in content and "aws_s3_bucket_logging" not in content:
            s3_names = re.findall(
                r'resource\s+"aws_s3_bucket"\s+"(\w+)"', content
            )
            if s3_names:
                # Use the first bucket as the logging destination
                log_dest = s3_names[0]
                for bname in s3_names:
                    log_block = f'''
# Auto-remediation: Enable S3 access logging
resource "aws_s3_bucket_logging" "{bname}_logging" {{
  bucket        = aws_s3_bucket.{bname}.id
  target_bucket = aws_s3_bucket.{log_dest}.id
  target_prefix = "access-logs/{bname}/"
}}
'''
                    additions.append(
                        (f"{bname}_logging", log_block, f"Enable access logging for S3 bucket '{bname}'")
                    )

        # Add DynamoDB encryption if table exists but no server_side_encryption
        if "aws_dynamodb_table" in content and "server_side_encryption" not in content:
            ddb_names = re.findall(
                r'resource\s+"aws_dynamodb_table"\s+"(\w+)"', content
            )
            for tname in ddb_names:
                sse_block = f'''
# Auto-remediation: Enable DynamoDB server-side encryption
resource "aws_dynamodb_table" "{tname}" {{
  # Encryption is added inline via SSE block
}}
'''
                # Instead of adding a new resource, inject SSE into existing block
                sse_inject = f'''
  server_side_encryption {{
    enabled     = true
    kms_key_arn = "alias/aws/dynamodb"  # Use AWS managed KMS key
  }}

  point_in_time_recovery {{
    enabled = true  # Enable PITR for data recovery
  }}
'''
                # Find the closing brace of the DynamoDB table
                ddb_pattern = rf'(resource\s+"aws_dynamodb_table"\s+"{tname}"\s*\{{[^}}]+)(tags\s*=)'
                ddb_match = re.search(ddb_pattern, content, re.DOTALL)
                if ddb_match:
                    new_content = content[:ddb_match.start(2)] + sse_inject + "\n  " + content[ddb_match.start(2):]
                    if new_content != content:
                        content = new_content
                        self._applied.append(
                            RemediationAction(
                                finding_id=f"add_{tname}_sse",
                                rule_id="AUTO_ADD_DYNAMODB_SSE",
                                severity="HIGH",
                                description=f"Enable server-side encryption and PITR for DynamoDB table '{tname}'",
                                original_text="(missing block)",
                                fixed_text="(block injected)",
                                category="missing_config",
                            )
                        )

        for name, block, desc in additions:
            if block.strip() not in content:
                content += block
                self._applied.append(
                    RemediationAction(
                        finding_id=f"add_{name}",
                        rule_id="AUTO_ADD_SECURITY_BLOCK",
                        severity="HIGH",
                        description=desc,
                        original_text="(missing block)",
                        fixed_text="(block added)",
                        category="missing_config",
                    )
                )

        return content

    def _map_finding_to_templates(
        self, rule_id: str, title: str, category: str
    ) -> List[str]:
        """Map a finding to one or more template keys."""
        keys: List[str] = []

        # AWS access key
        if any(k in rule_id for k in ["ACCESS_KEY", "AWS_KEY"]) or "aws access key" in title:
            keys.append("hardcoded_aws_access_key")
        if any(k in rule_id for k in ["SECRET_KEY", "AWS_SECRET"]) or "aws secret" in title:
            keys.append("hardcoded_aws_secret_key")

        # Passwords
        if "PASSWORD" in rule_id or "password" in title or "hardcoded password" in title:
            keys.append("hardcoded_db_password")
        if "HARDCODED" in rule_id and ("SECRET" in rule_id or "ENV" in rule_id):
            keys.append("hardcoded_env_secret")
        if "CREDENTIALS" in rule_id or "credential" in title:
            keys.append("hardcoded_db_password")
            keys.append("hardcoded_env_secret")

        # S3
        if "S3_PUBLIC" in rule_id or "public" in title and "s3" in title:
            keys.append("s3_public_acl")
        if "VERSIONING" in rule_id or "versioning" in title:
            keys.append("s3_versioning_disabled")
        if "S3_NO_LOGGING" in rule_id or "logging" in title and "s3" in title:
            pass  # Handled by _add_missing_blocks

        # Security Groups
        if "SG" in rule_id or "security_group" in title or "security group" in title:
            if "ssh" in title or "22" in title:
                keys.append("sg_ssh_open")
            if "rdp" in title or "3389" in title:
                keys.append("sg_rdp_open")
            if "all port" in title or "all_port" in title or "wide" in title:
                keys.append("sg_all_ports_open")
            if not keys or "0.0.0.0" in title:
                keys.append("sg_ssh_open")
                keys.append("sg_all_ports_open")

        # Egress rules
        if "EGRESS" in rule_id or "egress" in title:
            keys.append("egress_unrestricted")

        # CORS
        if "CORS" in rule_id or "cors" in title:
            keys.append("cors_wildcard_origin")
            keys.append("cors_wildcard_headers")

        # RDS/DB
        if "DB_PUBLIC" in rule_id or "publicly accessible" in title:
            keys.append("rds_public")
        if "UNENCRYPTED" in rule_id and ("DB" in rule_id or "RDS" in rule_id or "storage" in title):
            keys.append("rds_unencrypted")
        if "SNAPSHOT" in rule_id or "snapshot" in title:
            keys.append("rds_skip_snapshot")
        if "BACKUP" in rule_id or "backup" in title:
            keys.append("rds_no_backup")

        # EBS
        if "EBS" in rule_id or ("unencrypted" in title and "ebs" in title):
            keys.append("ebs_unencrypted")

        # EC2
        if "MONITORING" in rule_id or "monitoring" in title:
            keys.append("ec2_no_monitoring")

        # IAM
        if "WILDCARD" in rule_id or "wildcard" in title or "iam" in title and "*" in title:
            keys.append("iam_wildcard")
            keys.append("s3_wildcard_action")

        # Crypto / encryption failures
        if "CRYPTO" in rule_id or "encryption" in title or "unencrypted" in title:
            keys.append("rds_unencrypted")
            keys.append("ebs_unencrypted")

        # Debug logging
        if "DEBUG" in rule_id or "debug" in title:
            keys.append("debug_in_prod")

        return keys

    def _compute_stats(self) -> Dict[str, Any]:
        """Compute remediation statistics."""
        by_severity = {}
        by_category = {}
        for a in self._applied:
            by_severity[a.severity] = by_severity.get(a.severity, 0) + 1
            cat = a.category or "other"
            by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "total_remediations": len(self._applied),
            "by_severity": by_severity,
            "by_category": by_category,
            "critical_fixed": by_severity.get("CRITICAL", 0),
            "high_fixed": by_severity.get("HIGH", 0),
        }
