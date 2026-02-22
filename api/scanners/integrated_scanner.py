"""
Integrated Scanner - Combines all 6 security scanners
Provides comprehensive security analysis using:
1. SecretsScanner - Hardcoded credentials detection
2. CVEScanner - Known vulnerability detection
3. ComplianceScanner - CIS Benchmark validation
4. RulesScanner - Pattern-based security rules
5. MLScanner - Machine learning predictions
6. LLMScanner - AI-powered reasoning

"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging
import requests

logger = logging.getLogger(__name__)

# Add parent directory to path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from .secrets_scanner import SecretsScanner
from .compliance_scanner import ComplianceScanner
from .cve_scanner import CVEScanner

# Try to import GNN scanner (may not be available if PyTorch Geometric not installed)
try:
    from .gnn_scanner import GNNScanner
    GNN_AVAILABLE = True
except ImportError:
    GNN_AVAILABLE = False


class IntegratedSecurityScanner:
    """
    Unified security scanner that orchestrates all scanning engines
    """
    
    def __init__(self, ml_service_url: str = "http://localhost:8001"):
        # Initialize all scanners
        self.secrets_scanner = SecretsScanner()
        self.compliance_scanner = ComplianceScanner()
        self.cve_scanner = CVEScanner()
        
        # Initialize GNN scanner if available
        self.gnn_scanner = None
        if GNN_AVAILABLE:
            try:
                self.gnn_scanner = GNNScanner()
                logger.info("GNN Attack Path Detector initialized")
            except Exception as e:
                logger.warning("GNN scanner initialization failed: %s", e)
        
        # ML service URL for external scanners
        self.ml_service_url = ml_service_url
        
        # Scanner execution order (fastest to slowest, most critical first)
        self.scanner_order = [
            'gnn',          # Novel AI: Graph Neural Network attack paths
            'secrets',      # Fastest, most critical
            'cve',          # API calls, cacheable
            'compliance',   # Config-based checks
            'rules',        # Pattern-based (external)
            'ml',           # Model-based (external)
            'llm'           # Slowest (external)
        ]
        
        # Severity weights for risk scoring
        self.severity_weights = {
            'CRITICAL': 10,
            'HIGH': 5,
            'MEDIUM': 2,
            'LOW': 1,
            'INFO': 0.5
        }
    
    def parse_config_from_content(self, content: str, file_path: str) -> Dict:
        """
        Parse configuration from file content
        Used for compliance scanning
        """
        config = {}
        
        try:
            # Try to parse as JSON (CloudFormation, etc.)
            if file_path.endswith('.json'):
                config = json.loads(content)
            
            # For Terraform files, extract resource blocks
            elif file_path.endswith('.tf'):
                config = self._parse_terraform_config(content)
            
            # For YAML files
            elif file_path.endswith(('.yaml', '.yml')):
                try:
                    import yaml
                    config = yaml.safe_load(content)
                except:
                    pass
        
        except Exception as e:
            logger.warning("Config parsing error: %s", e)
        
        return config
    
    def _parse_terraform_config(self, content: str) -> Dict:
        """
        Parse Terraform HCL content for compliance checking.
        Extracts resource blocks and also performs direct content analysis
        for common compliance violations.
        """
        import re
        config = {
            'security_groups': [],
            's3': {'buckets': []},
            'iam': {'users': []}
        }
        
        # ── Extract security group blocks ─────────────────────────
        # More lenient regex: stop at the next top-level resource or end
        sg_pattern = r'resource\s+"aws_security_group"\s+"([^"]+)"\s*\{(.*?)(?=\nresource\s|\Z)'
        for match in re.finditer(sg_pattern, content, re.DOTALL):
            sg_name = match.group(1)
            sg_content = match.group(2)
            
            ingress_rules = []
            ingress_pattern = r'ingress\s*\{([^}]*?)\}'
            ingress_blocks = re.findall(ingress_pattern, sg_content, re.DOTALL)
            
            for rule_content in ingress_blocks:
                port_match = re.search(r'from_port\s*=\s*(\d+)', rule_content)
                to_port_match = re.search(r'to_port\s*=\s*(\d+)', rule_content)
                cidr_match = re.search(r'cidr_blocks\s*=\s*\[([^\]]+)\]', rule_content)
                
                rule = {}
                if port_match:
                    rule['from_port'] = int(port_match.group(1))
                if to_port_match:
                    rule['to_port'] = int(to_port_match.group(1))
                if cidr_match:
                    cidrs = [c.strip(' "\'\n') for c in cidr_match.group(1).split(',')]
                    rule['cidr_blocks'] = cidrs
                
                if rule:
                    ingress_rules.append(rule)
            
            config['security_groups'].append({
                'name': sg_name,
                'id': sg_name,
                'ingress_rules': ingress_rules
            })

        # ── Fallback: detect inline SG-like patterns even without
        #    a proper "resource" block – e.g. ingress { ... 0.0.0.0/0 }
        if not config['security_groups']:
            # Look for any ingress block with 0.0.0.0/0
            inline_ingress = re.findall(
                r'ingress\s*\{([^}]+)\}', content, re.DOTALL
            )
            for rule_content in inline_ingress:
                if '0.0.0.0/0' in rule_content:
                    port_match = re.search(r'from_port\s*=\s*(\d+)', rule_content)
                    to_port_match = re.search(r'to_port\s*=\s*(\d+)', rule_content)
                    cidr_match = re.search(r'cidr_blocks\s*=\s*\[([^\]]+)\]', rule_content)

                    rule = {}
                    if port_match:
                        rule['from_port'] = int(port_match.group(1))
                    if to_port_match:
                        rule['to_port'] = int(to_port_match.group(1))
                    if cidr_match:
                        cidrs = [c.strip(' "\'\n') for c in cidr_match.group(1).split(',')]
                        rule['cidr_blocks'] = cidrs

                    if rule:
                        config['security_groups'].append({
                            'name': 'inline_sg',
                            'id': 'inline_sg',
                            'ingress_rules': [rule]
                        })
        
        # ── Extract S3 bucket blocks ──────────────────────────────
        s3_pattern = r'resource\s+"aws_s3_bucket"\s+"([^"]+)"\s*\{(.*?)(?=\nresource\s|\Z)'
        for match in re.finditer(s3_pattern, content, re.DOTALL):
            bucket_name = match.group(1)
            bucket_content = match.group(2)
            
            encryption_enabled = 'server_side_encryption_configuration' in bucket_content or 'encryption' in bucket_content
            logging_enabled = 'logging' in bucket_content
            
            config['s3']['buckets'].append({
                'name': bucket_name,
                'arn': f'arn:aws:s3:::{bucket_name}',
                'encryption_enabled': encryption_enabled,
                'logging_enabled': logging_enabled
            })

        # Fallback: detect S3 bucket resources even with alternate naming
        if not config['s3']['buckets'] and 'aws_s3_bucket' in content:
            # If there are S3 buckets but parser missed them
            has_encryption = 'server_side_encryption' in content or 'sse_algorithm' in content
            has_logging = 'logging' in content and 'target_bucket' in content
            config['s3']['buckets'].append({
                'name': 'detected_bucket',
                'arn': 'arn:aws:s3:::detected_bucket',
                'encryption_enabled': has_encryption,
                'logging_enabled': has_logging
            })
        
        # ── Extract IAM users ─────────────────────────────────────
        iam_pattern = r'resource\s+"aws_iam_user"\s+"([^"]+)"\s*\{(.*?)(?=\nresource\s|\Z)'
        for match in re.finditer(iam_pattern, content, re.DOTALL):
            user_name = match.group(1)
            user_content = match.group(2)
            
            mfa_enabled = 'mfa_device' in user_content or 'virtual_mfa' in user_content
            
            config['iam']['users'].append({
                'name': user_name,
                'arn': f'arn:aws:iam::123456789012:user/{user_name}',
                'mfa_enabled': mfa_enabled
            })
        
        return config
    
    def scan_with_secrets_scanner(self, content: str, file_path: str) -> List[Dict]:
        """Run secrets scanner"""
        try:
            return self.secrets_scanner.scan_content(content, file_path)
        except Exception as e:
            return [{
                'type': 'SCAN_ERROR',
                'severity': 'LOW',
                'category': 'error',
                'scanner': 'secrets',
                'title': 'Secrets Scanner Error',
                'description': f'Error in secrets scanner: {str(e)}'
            }]
    
    def scan_with_cve_scanner(self, content: str, file_path: str) -> List[Dict]:
        """Run CVE scanner"""
        try:
            return self.cve_scanner.scan_content(content, file_path)
        except Exception as e:
            return [{
                'type': 'SCAN_ERROR',
                'severity': 'LOW',
                'category': 'error',
                'scanner': 'cve',
                'title': 'CVE Scanner Error',
                'description': f'Error in CVE scanner: {str(e)}'
            }]
    
    def scan_with_compliance_scanner(self, content: str, file_path: str) -> List[Dict]:
        """Run compliance scanner"""
        try:
            config = self.parse_config_from_content(content, file_path)
            if config:
                return self.compliance_scanner.scan_compliance(config)
            return []
        except Exception as e:
            return [{
                'type': 'SCAN_ERROR',
                'severity': 'LOW',
                'category': 'error',
                'scanner': 'compliance',
                'title': 'Compliance Scanner Error',
                'description': f'Error in compliance scanner: {str(e)}'
            }]
    
    def scan_with_rules_scanner(self, content: str, file_path: str) -> List[Dict]:
        """Run rules scanner via ML service API"""
        try:
            response = requests.post(
                f"{self.ml_service_url}/rules-scan",
                json={"file_path": file_path, "file_content": content},
                timeout=5.0
            )
            
            if response.status_code == 200:
                result = response.json()
                findings = result.get('findings', [])
                
                # Convert to standard format
                return [{
                    'type': f.get('rule_id', 'UNKNOWN'),
                    'severity': f.get('severity', 'LOW').upper(),
                    'category': 'rules',
                    'scanner': 'rules',
                    'title': f.get('title', 'Security Rule Violation'),
                    'description': f.get('description', ''),
                    'line_number': f.get('line_number'),
                    'code_snippet': f.get('code_snippet', ''),
                    'remediation': f.get('remediation', '')
                } for f in findings]
            else:
                logger.warning("Rules scanner returned status %s", response.status_code)
                return []
                
        except requests.exceptions.ConnectionError:
            logger.warning("Rules scanner service not reachable at %s — rules findings will be missing", self.ml_service_url)
            return []
        except requests.exceptions.Timeout:
            logger.warning("Rules scanner timed out — rules findings will be missing")
            return []
        except Exception as e:
            logger.error("Rules scanner error: %s", e)
            return []
    
    def scan_with_ml_scanner(self, content: str, file_path: str) -> List[Dict]:
        """Run ML scanner via ML service API"""
        try:
            response = requests.post(
                f"{self.ml_service_url}/predict",
                json={"file_path": file_path, "file_content": content},
                timeout=5.0
            )
            
            if response.status_code == 200:
                result = response.json()
                risk_score = result.get('risk_score', 0.0)
                prediction = result.get('prediction', 'low')
                confidence = result.get('confidence', 0.0)
                
                # Only create finding if risk is detected
                if risk_score > 0.4:  # Threshold for reporting
                    severity_map = {
                        'critical': 'CRITICAL',
                        'high': 'HIGH',
                        'medium': 'MEDIUM',
                        'low': 'LOW'
                    }
                    
                    return [{
                        'type': 'ML_PREDICTION',
                        'severity': severity_map.get(prediction, 'MEDIUM'),
                        'category': 'ml',
                        'scanner': 'ml',
                        'title': f'ML-Detected Security Risk ({prediction.upper()})',
                        'description': f'Machine learning model detected potential security issues with {risk_score:.1%} risk score and {confidence:.1%} confidence.',
                        'risk_score': risk_score,
                        'confidence': confidence,
                        'remediation': 'Review file for security misconfigurations flagged by ML analysis.'
                    }]
                return []
            else:
                logger.warning("ML scanner returned status %s", response.status_code)
                return []
                
        except requests.exceptions.ConnectionError:
            logger.warning("ML scanner service not reachable at %s — ML findings will be missing from this scan", self.ml_service_url)
            return []
        except requests.exceptions.Timeout:
            logger.warning("ML scanner timed out — ML findings will be missing from this scan")
            return []
        except Exception as e:
            logger.error("ML scanner error: %s", e)
            return []
    
    def scan_with_llm_scanner(self, content: str, file_path: str, existing_findings: List[Dict] = None) -> List[Dict]:
        """Run LLM scanner via ML service API for enhanced explanations"""
        try:
            # Only call LLM if we have existing findings to explain
            if not existing_findings or len(existing_findings) == 0:
                return []
            
            # Take up to 5 most critical findings for LLM analysis
            findings_to_explain = sorted(
                existing_findings,
                key=lambda x: self.severity_weights.get(x.get('severity', 'LOW'), 0),
                reverse=True
            )[:5]
            
            response = requests.post(
                f"{self.ml_service_url}/explain",
                json={
                    "file_path": file_path,
                    "file_content": content,
                    "findings": findings_to_explain
                },
                timeout=10.0  # LLM inference needs more time
            )
            
            if response.status_code == 200:
                result = response.json()
                explained = result.get('findings', [])
                
                # Convert to standard format - these are enhanced findings
                llm_findings = []
                for finding in explained:
                    llm_findings.append({
                        'type': finding.get('rule_id', 'LLM_ENHANCED'),
                        'severity': finding.get('severity', 'MEDIUM'),
                        'category': 'llm',
                        'scanner': 'llm',
                        'title': f"LLM: {finding.get('title', 'Enhanced Security Analysis')}",
                        'description': finding.get('llm_explanation', finding.get('description', '')),
                        'remediation': finding.get('llm_remediation', ''),
                        'original_finding': finding
                    })
                return llm_findings
            elif response.status_code == 500:
                # LLM service error (likely missing API keys) - skip gracefully
                logger.warning("LLM scanner service error (may need API keys configured)")
                return []
            else:
                logger.warning("LLM scanner returned status %s", response.status_code)
                return []
                
        except requests.exceptions.ConnectionError:
            logger.debug("LLM scanner service not available")
            return []
        except requests.exceptions.Timeout:
            logger.warning("LLM scanner timeout")
            return []
        except Exception as e:
            logger.error("LLM scanner error: %s", e)
            return []
    
    def calculate_risk_score(self, all_findings: List[Dict]) -> float:
        """
        Calculate unified risk score based on all findings
        Uses weighted severity scoring
        """
        if not all_findings:
            return 0.0
        
        total_weighted_score = 0
        max_possible_score = len(all_findings) * self.severity_weights['CRITICAL']
        
        for finding in all_findings:
            severity = finding.get('severity', 'LOW').upper()
            weight = self.severity_weights.get(severity, 1)
            total_weighted_score += weight
        
        # Normalize to 0-100 scale
        if max_possible_score > 0:
            risk_score = (total_weighted_score / max_possible_score) * 100
        else:
            risk_score = 0
        
        return round(min(risk_score, 100), 2)
    
    def calculate_compliance_score(self, compliance_findings: List[Dict]) -> float:
        """
        Calculate compliance score (0-100)
        100 = fully compliant, 0 = non-compliant
        Uses severity-weighted penalties
        """
        if not compliance_findings:
            return 100.0  # No violations = fully compliant
        
        # Severity-based penalties
        severity_penalties = {
            'CRITICAL': 25,  # Critical violations heavily impact score
            'HIGH': 15,
            'MEDIUM': 8,
            'LOW': 3,
            'INFO': 1
        }
        
        total_penalty = 0
        for finding in compliance_findings:
            severity = finding.get('severity', 'MEDIUM').upper()
            penalty = severity_penalties.get(severity, 8)
            total_penalty += penalty
        
        # Calculate score (can't go below 0)
        score = max(0, 100 - total_penalty)
        
        return round(score, 2)
    
    def aggregate_findings_by_scanner(self, findings_dict: Dict[str, List[Dict]]) -> Dict:
        """
        Aggregate findings and generate statistics by scanner
        """
        aggregated = {}
        
        for scanner_name, findings in findings_dict.items():
            by_severity = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0}
            by_type = {}
            
            for finding in findings:
                severity = finding.get('severity', 'LOW').upper()
                finding_type = finding.get('type', 'UNKNOWN')
                
                if severity in by_severity:
                    by_severity[severity] += 1
                
                by_type[finding_type] = by_type.get(finding_type, 0) + 1
            
            aggregated[scanner_name] = {
                'total_findings': len(findings),
                'by_severity': by_severity,
                'by_type': by_type,
                'findings': findings
            }
        
        return aggregated
    
    def scan_file_integrated(
        self, 
        file_path: str, 
        content: str,
        rules_findings: Optional[List[Dict]] = None,
        ml_score: Optional[float] = None,
        llm_findings: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Perform integrated security scan using all available scanners
        
        Args:
            file_path: Path to the file being scanned
            content: File content as string
            rules_findings: Findings from rules scanner (external)
            ml_score: ML risk score (external)
            llm_findings: LLM-enhanced findings (external)
        
        Returns:
            Comprehensive scan results with all findings aggregated
        """
        scan_start_time = datetime.now()
        
        # Results container
        findings = {
            'gnn': [],  # NEW: Graph Neural Network attack paths
            'secrets': [],
            'cve': [],
            'compliance': [],
            'rules': rules_findings or [],
            'ml': [],
            'llm': llm_findings or []
        }
        
        scanner_timings = {}
        
        # Run internal scanners
        logger.info("Starting integrated scan for: %s", file_path)
        
        # 0. GNN Scanner (NEW: Novel AI feature)
        start = datetime.now()
        if self.gnn_scanner and self.gnn_scanner.available:
            findings['gnn'] = self.gnn_scanner.scan_file(file_path)
            scanner_timings['gnn'] = (datetime.now() - start).total_seconds()
            logger.info("GNN scanner: %d findings in %.2fs", len(findings['gnn']), scanner_timings['gnn'])
        else:
            scanner_timings['gnn'] = 0
            logger.warning("GNN scanner: SKIPPED — install torch-geometric to enable attack path detection")
        
        # 1. Secrets Scanner (fastest, most critical)
        start = datetime.now()
        findings['secrets'] = self.scan_with_secrets_scanner(content, file_path)
        scanner_timings['secrets'] = (datetime.now() - start).total_seconds()
        logger.info("Secrets scanner: %d findings in %.2fs", len(findings['secrets']), scanner_timings['secrets'])
        
        # 2. CVE Scanner
        start = datetime.now()
        findings['cve'] = self.scan_with_cve_scanner(content, file_path)
        scanner_timings['cve'] = (datetime.now() - start).total_seconds()
        logger.info("CVE scanner: %d findings in %.2fs", len(findings['cve']), scanner_timings['cve'])
        
        # 3. Compliance Scanner
        start = datetime.now()
        findings['compliance'] = self.scan_with_compliance_scanner(content, file_path)
        scanner_timings['compliance'] = (datetime.now() - start).total_seconds()
        logger.info("Compliance scanner: %d findings in %.2fs", len(findings['compliance']), scanner_timings['compliance'])
        
        # 4. Rules Scanner (external via ML service)
        start = datetime.now()
        findings['rules'] = rules_findings or self.scan_with_rules_scanner(content, file_path)
        scanner_timings['rules'] = (datetime.now() - start).total_seconds()
        logger.info("Rules scanner: %d findings in %.2fs", len(findings['rules']), scanner_timings['rules'])
        
        # 5. ML Scanner (external via ML service)
        start = datetime.now()
        findings['ml'] = self.scan_with_ml_scanner(content, file_path)
        scanner_timings['ml'] = (datetime.now() - start).total_seconds()
        logger.info("ML scanner: %d findings in %.2fs", len(findings['ml']), scanner_timings['ml'])
        
        # 6. LLM Scanner (external via ML service) - analyzes existing findings
        start = datetime.now()
        all_existing_findings = []
        for scanner_findings in [findings['secrets'], findings['cve'], findings['compliance'], findings['rules']]:
            all_existing_findings.extend(scanner_findings)
        findings['llm'] = llm_findings or self.scan_with_llm_scanner(content, file_path, all_existing_findings)
        scanner_timings['llm'] = (datetime.now() - start).total_seconds()
        logger.info("LLM scanner: %d findings in %.2fs", len(findings['llm']), scanner_timings['llm'])
        
        # Aggregate all findings
        all_findings = []
        for scanner_name, scanner_findings in findings.items():
            all_findings.extend(scanner_findings)
        
        # Calculate scores
        risk_score = self.calculate_risk_score(all_findings)
        compliance_score = self.calculate_compliance_score(findings['compliance'])
        
        # Aggregate by scanner
        aggregated = self.aggregate_findings_by_scanner(findings)
        
        # Count by severity across all scanners
        total_by_severity = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0}
        for finding in all_findings:
            severity = finding.get('severity', 'LOW').upper()
            if severity in total_by_severity:
                total_by_severity[severity] += 1
        
        # Build final result
        scan_duration = (datetime.now() - scan_start_time).total_seconds()
        
        result = {
            'scan_id': f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'file_path': file_path,
            'scan_timestamp': scan_start_time.isoformat(),
            'scan_duration_seconds': round(scan_duration, 2),
            
            # Findings by scanner
            'findings': findings,
            
            # Aggregated statistics
            'summary': {
                'total_findings': len(all_findings),
                'by_severity': total_by_severity,
                'by_scanner': {
                    scanner: stats['total_findings'] 
                    for scanner, stats in aggregated.items()
                },
                'scanner_details': aggregated
            },
            
            # Scores
            'scores': {
                'unified_risk_score': risk_score,
                'compliance_score': compliance_score,
                'ml_score': ml_score or 0.0,
                'secrets_risk': self.calculate_risk_score(findings['secrets']),
                'cve_risk': self.calculate_risk_score(findings['cve']),
                'compliance_risk': 100 - compliance_score
            },
            
            # Performance metrics
            'performance': {
                'scanner_timings': scanner_timings,
                'total_scan_time': scan_duration
            },
            
            # Metadata
            'metadata': {
                'scanners_used': list(findings.keys()),
                'file_size_bytes': len(content),
                'scan_version': '2.0.0'
            }
        }
        
        return result
    
    def generate_scan_summary(self, scan_result: Dict) -> str:
        """
        Generate human-readable summary of scan results
        """
        summary = scan_result.get('summary', {})
        scores = scan_result.get('scores', {})
        
        total_findings = summary.get('total_findings', 0)
        by_severity = summary.get('by_severity', {})
        
        lines = [
            "=" * 80,
            "CLOUDGUARD AI - INTEGRATED SECURITY SCAN REPORT",
            "=" * 80,
            f"File: {scan_result.get('file_path', 'Unknown')}",
            f"Scan Time: {scan_result.get('scan_timestamp', 'Unknown')}",
            f"Duration: {scan_result.get('scan_duration_seconds', 0)}s",
            "",
            "RISK SCORES:",
            f"  Unified Risk Score: {scores.get('unified_risk_score', 0):.2f}/100",
            f"  Compliance Score: {scores.get('compliance_score', 100):.2f}/100",
            f"  Secrets Risk: {scores.get('secrets_risk', 0):.2f}/100",
            f"  CVE Risk: {scores.get('cve_risk', 0):.2f}/100",
            "",
            "FINDINGS SUMMARY:",
            f"  Total Findings: {total_findings}",
            f"  CRITICAL: {by_severity.get('CRITICAL', 0)}",
            f"  HIGH: {by_severity.get('HIGH', 0)}",
            f"  MEDIUM: {by_severity.get('MEDIUM', 0)}",
            f"  LOW: {by_severity.get('LOW', 0)}",
            "",
            "FINDINGS BY SCANNER:",
        ]
        
        by_scanner = summary.get('by_scanner', {})
        for scanner, count in by_scanner.items():
            lines.append(f"  {scanner.upper()}: {count} findings")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def scan_content(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Scan content and return results in the format expected by the API endpoint.
        This is a simplified wrapper around scan_file_integrated.
        
        Args:
            content: File content as string
            file_path: File name/path
        
        Returns:
            Dict with findings, risk_score, severity_counts, scanners_used
        """
        # Run the full integrated scan
        result = self.scan_file_integrated(file_path, content)
        
        # Flatten all findings into a single list for the API
        all_findings = []
        findings_by_scanner = result.get('findings', {})
        
        for scanner_name, scanner_findings in findings_by_scanner.items():
            for finding in scanner_findings:
                # Normalize finding format for API
                all_findings.append({
                    'rule_id': finding.get('type', finding.get('rule_id', f'{scanner_name.upper()}_FINDING')),
                    'check_id': finding.get('type', finding.get('check_id', '')),
                    'severity': finding.get('severity', 'MEDIUM').upper(),
                    'title': finding.get('title', finding.get('description', '')[:100]),
                    'description': finding.get('description', ''),
                    'category': finding.get('category', scanner_name),
                    'scanner': scanner_name,
                    'line_number': finding.get('line_number', finding.get('line')),
                    'code_snippet': finding.get('code_snippet', finding.get('evidence', '')),
                    'resource': finding.get('resource', ''),
                    'remediation': finding.get('remediation', ''),
                    'confidence': finding.get('confidence', finding.get('certainty', 0.8))
                })
        
        # --- Apply adaptive rule weights (lower confidence of noisy rules) ---
        try:
            from app.adaptive_learning import learning_engine
            for finding in all_findings:
                rule_id = finding.get("rule_id", "")
                weight = learning_engine.rule_weights.get_weight(rule_id)
                finding["confidence"] = round(finding.get("confidence", 0.8) * weight, 3)
                finding["adaptive_weight"] = weight
        except Exception:
            pass  # adaptive learning not available (e.g. in tests)

        # Get summary data
        summary = result.get('summary', {})
        by_severity = summary.get('by_severity', {})
        scores = result.get('scores', {})
        
        # Return in the format expected by the API
        return {
            'findings': all_findings,
            'total_findings': len(all_findings),
            'risk_score': scores.get('unified_risk_score', 0.0) / 100.0,  # Normalize to 0-1
            'critical_count': by_severity.get('CRITICAL', 0),
            'high_count': by_severity.get('HIGH', 0),
            'medium_count': by_severity.get('MEDIUM', 0),
            'low_count': by_severity.get('LOW', 0),
            'severity_counts': {
                'critical': by_severity.get('CRITICAL', 0),
                'high': by_severity.get('HIGH', 0),
                'medium': by_severity.get('MEDIUM', 0),
                'low': by_severity.get('LOW', 0),
                'info': by_severity.get('INFO', 0)
            },
            'scanners_used': result.get('metadata', {}).get('scanners_used', []),
            'scan_duration': result.get('scan_duration_seconds', 0)
        }


# Singleton instance
_integrated_scanner = None

def get_integrated_scanner() -> IntegratedSecurityScanner:
    """Get singleton instance of integrated scanner"""
    global _integrated_scanner
    if _integrated_scanner is None:
        _integrated_scanner = IntegratedSecurityScanner()
    return _integrated_scanner
