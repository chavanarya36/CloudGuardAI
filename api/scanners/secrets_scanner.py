"""
Secrets Scanner - Detects hardcoded credentials and secrets in IaC files
Supports AWS, Azure, GCP, GitHub, GitLab and generic secrets
"""

import re
import math
from typing import List, Dict, Optional


class SecretsScanner:
    """
    Scanner for detecting hardcoded credentials and sensitive information
    """
    
    def __init__(self):
        # Secret patterns with descriptions
        self.patterns = {
            'aws_access_key': {
                'pattern': r'(?:AKIA|ASIA)[A-Z0-9]{16}',
                'title': 'AWS Access Key',
                'description': 'Hardcoded AWS Access Key ID detected',
                'severity': 'CRITICAL'
            },
            'aws_secret_key': {
                'pattern': r'(?:aws.{0,20})?["\']?([A-Za-z0-9/+=]{40})["\']?',
                'title': 'AWS Secret Access Key',
                'description': 'Potential AWS Secret Access Key detected',
                'severity': 'CRITICAL'
            },
            'azure_client_secret': {
                'pattern': r'(?:azure|az).{0,20}["\']?([A-Za-z0-9~._-]{34})["\']?',
                'title': 'Azure Client Secret',
                'description': 'Azure client secret detected',
                'severity': 'CRITICAL'
            },
            'gcp_api_key': {
                'pattern': r'AIza[0-9A-Za-z\\-_]{35}',
                'title': 'GCP API Key',
                'description': 'Google Cloud Platform API key detected',
                'severity': 'CRITICAL'
            },
            'github_token': {
                'pattern': r'gh[pousr]_[A-Za-z0-9_]{36,255}',
                'title': 'GitHub Token',
                'description': 'GitHub personal access token detected',
                'severity': 'HIGH'
            },
            'gitlab_token': {
                'pattern': r'glpat-[A-Za-z0-9\-_]{20}',
                'title': 'GitLab Token',
                'description': 'GitLab personal access token detected',
                'severity': 'HIGH'
            },
            'private_key': {
                'pattern': r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
                'title': 'Private Key',
                'description': 'Private key detected in plaintext',
                'severity': 'CRITICAL'
            },
            'generic_password': {
                'pattern': r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([^\s"\']{8,})["\']?',
                'title': 'Hardcoded Password',
                'description': 'Potential hardcoded password detected',
                'severity': 'HIGH'
            },
            'generic_api_key': {
                'pattern': r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([A-Za-z0-9_\-]{20,})["\']?',
                'title': 'API Key',
                'description': 'Potential API key detected',
                'severity': 'HIGH'
            }
        }
        
        # Lines to skip (common false positives)
        self.skip_patterns = [
            r'example',
            r'sample',
            r'<.*>',  # Placeholders
            r'\$\{',   # Variable references
            r'xxx',
            r'test'
        ]
    
    def calculate_entropy(self, text: str) -> float:
        """
        Calculate Shannon entropy of a string
        High entropy suggests randomness (like a secret)
        """
        if not text:
            return 0.0
        
        # Count character frequencies
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Calculate entropy
        entropy = 0.0
        text_len = len(text)
        
        for count in char_counts.values():
            probability = count / text_len
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def is_false_positive(self, match_text: str, line: str) -> bool:
        """
        Check if this is likely a false positive
        """
        combined = (match_text + line).lower()
        
        # Skip only obvious placeholders
        skip_words = ['example.com', 'your-', 'my-', '<', '>', '${', 'xxx', 'test@test']
        
        for skip_word in skip_words:
            if skip_word in combined:
                return True
        
        return False
    
    def scan_content(self, content: str, file_path: str) -> List[Dict]:
        """
        Scan content for secrets and credentials
        
        Returns:
            List of findings with type, severity, description, remediation
        """
        findings = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith('#'):
                continue
            
            # Check each pattern
            for secret_type, info in self.patterns.items():
                pattern = info['pattern']
                matches = re.finditer(pattern, line, re.IGNORECASE)
                
                for match in matches:
                    match_text = match.group(0)
                    
                    # Skip false positives
                    if self.is_false_positive(match_text, line):
                        continue
                    
                    # Check entropy for high-entropy strings
                    entropy = self.calculate_entropy(match_text)
                    
                    # Only report if entropy is high enough (> 3.5) or it matches specific patterns
                    if secret_type in ['aws_access_key', 'github_token', 'gitlab_token', 'private_key', 'gcp_api_key']:
                        # These have specific formats, report immediately
                        pass
                    elif entropy < 3.5:
                        # Low entropy, likely not a real secret
                        continue
                    
                    # Redact the actual secret value from evidence to prevent leaking
                    redacted_line = line.strip()[:100]
                    # Mask the matched secret value
                    if match_text and len(match_text) > 4:
                        visible_prefix = match_text[:4]
                        redacted_value = visible_prefix + '*' * min(len(match_text) - 4, 20)
                        redacted_line = redacted_line.replace(match_text, redacted_value)
                    
                    finding = {
                        'type': f'SECRET_{secret_type.upper()}',
                        'severity': info['severity'],
                        'category': 'secrets',
                        'scanner': 'secrets',
                        'title': info['title'],
                        'description': f"{info['description']}. This poses a critical security risk as credentials should never be hardcoded.",
                        'line_number': line_num,
                        'code_snippet': redacted_line,
                        'file_path': file_path,
                        'entropy': round(entropy, 2),
                        'remediation_steps': [
                            'Remove the hardcoded credential from the code',
                            'Use environment variables or a secrets management service (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault)',
                            'Rotate the exposed credential immediately',
                            'Implement pre-commit hooks to prevent future credential commits',
                            'Review Git history and remove credential if committed'
                        ],
                        'references': [
                            'https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_password',
                            'https://cwe.mitre.org/data/definitions/798.html'
                        ]
                    }
                    
                    findings.append(finding)
        
        return findings


# Example usage
if __name__ == "__main__":
    scanner = SecretsScanner()
    
    test_content = '''
    provider "aws" {
      access_key = "AKIAEXAMPLEKEYDONOTUSE"
      secret_key = "EXAMPLESECRETKEY/DO/NOT/USE/EXAMPLE"
    }
    
    password = "SuperSecret123!"
    api_key = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
    '''
    
    findings = scanner.scan_content(test_content, "test.tf")
    
    for finding in findings:
        print(f"\n{finding['title']} - {finding['severity']}")
        print(f"  Line {finding['line_number']}: {finding['description']}")
        print(f"  Entropy: {finding['entropy']}")


