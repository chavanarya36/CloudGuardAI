"""Finding deduplication utilities"""
import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime


class FindingDeduplicator:
    """
    Service for deduplicating security findings across scans.
    Uses SHA256 hashing of key finding attributes to identify duplicates.
    """
    
    @staticmethod
    def generate_finding_hash(
        scanner: str,
        severity: str,
        description: str,
        file_path: Optional[str] = None,
        resource: Optional[str] = None,
        cve_id: Optional[str] = None,
        rule_id: Optional[str] = None,
        control_id: Optional[str] = None
    ) -> str:
        """
        Generate a deterministic hash for a finding based on its key attributes.
        
        The hash considers:
        - Scanner type (to differentiate same issue found by different scanners)
        - Severity level
        - Description (core issue description)
        - File path (where applicable)
        - Resource name (for IaC resources)
        - CVE ID (for CVE findings)
        - Rule ID (for rule-based findings)
        - Control ID (for compliance findings)
        
        This allows us to identify when the same finding appears across multiple scans.
        """
        # Build hash components
        hash_components = {
            'scanner': scanner.lower().strip() if scanner else '',
            'severity': severity.upper().strip() if severity else '',
            'description': description.lower().strip() if description else '',
            'file_path': file_path.lower().strip() if file_path else '',
            'resource': resource.lower().strip() if resource else '',
            'cve_id': cve_id.upper().strip() if cve_id else '',
            'rule_id': rule_id.lower().strip() if rule_id else '',
            'control_id': control_id.upper().strip() if control_id else ''
        }
        
        # Create deterministic string representation
        hash_string = json.dumps(hash_components, sort_keys=True)
        
        # Generate SHA256 hash
        return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
    
    @staticmethod
    def should_deduplicate(existing_finding: Dict[str, Any], new_finding: Dict[str, Any]) -> bool:
        """
        Determine if a new finding should be deduplicated with an existing one.
        
        Returns True if findings are duplicates (same hash).
        """
        existing_hash = existing_finding.get('finding_hash')
        
        new_hash = FindingDeduplicator.generate_finding_hash(
            scanner=new_finding.get('scanner'),
            severity=new_finding.get('severity'),
            description=new_finding.get('description'),
            file_path=new_finding.get('file_path'),
            resource=new_finding.get('resource'),
            cve_id=new_finding.get('cve_id'),
            rule_id=new_finding.get('rule_id'),
            control_id=new_finding.get('control_id')
        )
        
        return existing_hash == new_hash if existing_hash else False
    
    @staticmethod
    def merge_duplicate_findings(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge a duplicate finding into an existing one.
        Updates occurrence count and last_seen timestamp.
        """
        return {
            **existing,
            'last_seen': datetime.utcnow(),
            'occurrence_count': existing.get('occurrence_count', 1) + 1,
            # Optionally update severity if new finding is more severe
            'severity': new['severity'] if _is_more_severe(new['severity'], existing['severity']) else existing['severity']
        }


def _is_more_severe(sev1: str, sev2: str) -> bool:
    """Check if sev1 is more severe than sev2"""
    severity_order = {
        'CRITICAL': 4,
        'HIGH': 3,
        'MEDIUM': 2,
        'LOW': 1,
        'INFO': 0
    }
    return severity_order.get(sev1.upper(), 0) > severity_order.get(sev2.upper(), 0)
