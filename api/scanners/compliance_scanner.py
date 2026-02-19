"""
Compliance Scanner - Validates against CIS Benchmarks
Currently supports AWS CIS Foundations Benchmark
"""

from typing import List, Dict, Optional


class ComplianceScanner:
    """
    Scanner for CIS Benchmark compliance validation
    """
    
    def __init__(self):
        # CIS AWS Foundations Benchmark checks
        self.cis_aws_checks = {
            'cis_1_4': {
                'title': 'CIS 1.4 - Ensure MFA is enabled for IAM users',
                'check': 'iam_mfa_enabled',
                'severity': 'HIGH',
                'description': 'IAM user does not have MFA enabled'
            },
            'cis_2_1_1': {
                'title': 'CIS 2.1.1 - Ensure S3 bucket encryption is enabled',
                'check': 's3_encryption_enabled',
                'severity': 'HIGH',
                'description': 'S3 bucket does not have encryption enabled'
            },
            'cis_2_1_2': {
                'title': 'CIS 2.1.2 - Ensure S3 bucket logging is enabled',
                'check': 's3_logging_enabled',
                'severity': 'MEDIUM',
                'description': 'S3 bucket does not have access logging enabled'
            },
            'cis_4_1': {
                'title': 'CIS 4.1 - Ensure no security groups allow ingress from 0.0.0.0/0 to port 22',
                'check': 'sg_no_ssh_from_world',
                'severity': 'CRITICAL',
                'description': 'Security group allows SSH (port 22) from the internet (0.0.0.0/0)'
            },
            'cis_4_2': {
                'title': 'CIS 4.2 - Ensure no security groups allow ingress from 0.0.0.0/0 to port 3389',
                'check': 'sg_no_rdp_from_world',
                'severity': 'CRITICAL',
                'description': 'Security group allows RDP (port 3389) from the internet (0.0.0.0/0)'
            }
        }
    
    def check_iam_mfa(self, config: Dict) -> List[Dict]:
        """Check if IAM users have MFA enabled"""
        findings = []
        
        iam_config = config.get('iam', {})
        users = iam_config.get('users', [])
        
        for user in users:
            if not user.get('mfa_enabled', False):
                findings.append({
                    'type': 'CIS_1_4',
                    'severity': 'HIGH',
                    'category': 'compliance',
                    'scanner': 'compliance',
                    'title': 'MFA Not Enabled for IAM User',
                    'description': f"IAM user '{user.get('name', 'unknown')}' does not have MFA enabled. CIS Benchmark 1.4 requires MFA for all IAM users.",
                    'resource': user.get('arn', user.get('name', '')),
                    'remediation_steps': [
                        'Enable MFA for the IAM user',
                        'Use virtual MFA device or hardware MFA token',
                        'Configure MFA in AWS IAM console or via CLI',
                        'Enforce MFA through IAM policies'
                    ],
                    'compliance_framework': 'CIS AWS Foundations Benchmark',
                    'control_id': 'CIS 1.4',
                    'references': [
                        'https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa.html'
                    ]
                })
        
        return findings
    
    def check_s3_encryption(self, config: Dict) -> List[Dict]:
        """Check if S3 buckets have encryption enabled"""
        findings = []
        
        s3_config = config.get('s3', {})
        buckets = s3_config.get('buckets', [])
        
        for bucket in buckets:
            if not bucket.get('encryption_enabled', False):
                findings.append({
                    'type': 'CIS_2_1_1',
                    'severity': 'HIGH',
                    'category': 'compliance',
                    'scanner': 'compliance',
                    'title': 'S3 Bucket Encryption Not Enabled',
                    'description': f"S3 bucket '{bucket.get('name', 'unknown')}' does not have server-side encryption enabled. CIS Benchmark 2.1.1 requires encryption at rest.",
                    'resource': bucket.get('arn', bucket.get('name', '')),
                    'remediation_steps': [
                        'Enable S3 bucket encryption',
                        'Use AWS KMS or S3-managed keys (SSE-S3)',
                        'Configure default encryption for the bucket',
                        'Update bucket policy to require encrypted uploads'
                    ],
                    'compliance_framework': 'CIS AWS Foundations Benchmark',
                    'control_id': 'CIS 2.1.1',
                    'references': [
                        'https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-encryption.html'
                    ]
                })
        
        return findings
    
    def check_s3_logging(self, config: Dict) -> List[Dict]:
        """Check if S3 buckets have access logging enabled"""
        findings = []
        
        s3_config = config.get('s3', {})
        buckets = s3_config.get('buckets', [])
        
        for bucket in buckets:
            if not bucket.get('logging_enabled', False):
                findings.append({
                    'type': 'CIS_2_1_2',
                    'severity': 'MEDIUM',
                    'category': 'compliance',
                    'scanner': 'compliance',
                    'title': 'S3 Bucket Logging Not Enabled',
                    'description': f"S3 bucket '{bucket.get('name', 'unknown')}' does not have access logging enabled. CIS Benchmark 2.1.2 requires logging for audit trails.",
                    'resource': bucket.get('arn', bucket.get('name', '')),
                    'remediation_steps': [
                        'Enable S3 bucket access logging',
                        'Configure a target bucket for logs',
                        'Set appropriate log file prefix',
                        'Review logs regularly for security events'
                    ],
                    'compliance_framework': 'CIS AWS Foundations Benchmark',
                    'control_id': 'CIS 2.1.2',
                    'references': [
                        'https://docs.aws.amazon.com/AmazonS3/latest/userguide/ServerLogs.html'
                    ]
                })
        
        return findings
    
    def check_security_group_ssh(self, config: Dict) -> List[Dict]:
        """Check if security groups allow SSH from 0.0.0.0/0"""
        findings = []
        
        security_groups = config.get('security_groups', [])
        
        for sg in security_groups:
            ingress_rules = sg.get('ingress_rules', [])
            
            for rule in ingress_rules:
                from_port = rule.get('from_port', 0)
                to_port = rule.get('to_port', 0)
                cidr_blocks = rule.get('cidr_blocks', [])
                
                # Check if SSH (port 22) is open to the world
                if (from_port <= 22 <= to_port) and ('0.0.0.0/0' in cidr_blocks):
                    findings.append({
                        'type': 'CIS_4_1',
                        'severity': 'CRITICAL',
                        'category': 'compliance',
                        'scanner': 'compliance',
                        'title': 'SSH Open to Internet',
                        'description': f"Security group '{sg.get('name', 'unknown')}' allows SSH access (port 22) from the internet (0.0.0.0/0). CIS Benchmark 4.1 prohibits this.",
                        'resource': sg.get('id', sg.get('name', '')),
                        'remediation_steps': [
                            'Restrict SSH access to specific IP ranges',
                            'Use VPN or bastion host for SSH access',
                            'Remove 0.0.0.0/0 from CIDR blocks',
                            'Implement AWS Systems Manager Session Manager as alternative'
                        ],
                        'compliance_framework': 'CIS AWS Foundations Benchmark',
                        'control_id': 'CIS 4.1',
                        'references': [
                            'https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html'
                        ]
                    })
        
        return findings
    
    def check_security_group_rdp(self, config: Dict) -> List[Dict]:
        """Check if security groups allow RDP from 0.0.0.0/0"""
        findings = []
        
        security_groups = config.get('security_groups', [])
        
        for sg in security_groups:
            ingress_rules = sg.get('ingress_rules', [])
            
            for rule in ingress_rules:
                from_port = rule.get('from_port', 0)
                to_port = rule.get('to_port', 0)
                cidr_blocks = rule.get('cidr_blocks', [])
                
                # Check if RDP (port 3389) is open to the world
                if (from_port <= 3389 <= to_port) and ('0.0.0.0/0' in cidr_blocks):
                    findings.append({
                        'type': 'CIS_4_2',
                        'severity': 'CRITICAL',
                        'category': 'compliance',
                        'scanner': 'compliance',
                        'title': 'RDP Open to Internet',
                        'description': f"Security group '{sg.get('name', 'unknown')}' allows RDP access (port 3389) from the internet (0.0.0.0/0). CIS Benchmark 4.2 prohibits this.",
                        'resource': sg.get('id', sg.get('name', '')),
                        'remediation_steps': [
                            'Restrict RDP access to specific IP ranges',
                            'Use VPN for RDP access',
                            'Remove 0.0.0.0/0 from CIDR blocks',
                            'Consider using AWS Systems Manager Session Manager'
                        ],
                        'compliance_framework': 'CIS AWS Foundations Benchmark',
                        'control_id': 'CIS 4.2',
                        'references': [
                            'https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html'
                        ]
                    })
        
        return findings
    
    def scan_compliance(self, config: Dict) -> List[Dict]:
        """
        Run all compliance checks
        
        Args:
            config: Parsed configuration (from Terraform, CloudFormation, etc.)
        
        Returns:
            List of compliance findings
        """
        all_findings = []
        
        # Run all checks
        all_findings.extend(self.check_iam_mfa(config))
        all_findings.extend(self.check_s3_encryption(config))
        all_findings.extend(self.check_s3_logging(config))
        all_findings.extend(self.check_security_group_ssh(config))
        all_findings.extend(self.check_security_group_rdp(config))
        
        return all_findings


# Example usage
if __name__ == "__main__":
    scanner = ComplianceScanner()
    
    # Test config
    test_config = {
        'iam': {
            'users': [
                {'name': 'admin', 'arn': 'arn:aws:iam::123:user/admin', 'mfa_enabled': False}
            ]
        },
        's3': {
            'buckets': [
                {'name': 'data-bucket', 'arn': 'arn:aws:s3:::data-bucket', 'encryption_enabled': False, 'logging_enabled': False}
            ]
        },
        'security_groups': [
            {
                'name': 'web-sg',
                'id': 'sg-123',
                'ingress_rules': [
                    {'from_port': 22, 'to_port': 22, 'cidr_blocks': ['0.0.0.0/0']},
                    {'from_port': 3389, 'to_port': 3389, 'cidr_blocks': ['0.0.0.0/0']}
                ]
            }
        ]
    }
    
    findings = scanner.scan_compliance(test_config)
    
    for finding in findings:
        print(f"\n{finding['title']} - {finding['severity']}")
        print(f"  {finding['description']}")
