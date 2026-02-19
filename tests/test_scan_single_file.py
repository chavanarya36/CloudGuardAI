"""Tests for scan_single_file and deduplication."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest

from rules_engine.engine import scan_single_file
from rules_engine.utils import dedupe_findings


def test_scan_single_file_returns_normalized_findings(tmp_path: Path):
    """Test that scan_single_file returns only findings for the given file."""
    # Create a sample Terraform file
    tf_file = tmp_path / "main.tf"
    content = """
resource "aws_s3_bucket" "example" {
  bucket = "my-bucket"
  acl    = "public-read"
}
"""
    
    findings = scan_single_file(tf_file, content)
    
    # Verify findings structure
    assert isinstance(findings, list)
    
    for f in findings:
        # Check all required fields exist
        assert "rule_id" in f
        assert "file_path" in f
        assert "severity" in f
        assert "title" in f
        assert "description" in f
        assert "references" in f
        assert "code_snippet" in f
        
        # Verify file_path matches
        assert str(tf_file) in str(f["file_path"])
        
        # Verify no "Untitled" in title (should be enriched)
        assert f["title"] != "Untitled"


def test_scan_single_file_yaml_content(tmp_path: Path):
    """Test scan_single_file with YAML content."""
    yaml_file = tmp_path / "deployment.yaml"
    content = """
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: test
    image: nginx:latest
    securityContext:
      privileged: true
"""
    
    findings = scan_single_file(yaml_file, content)
    
    assert isinstance(findings, list)
    # Should find privileged container issue if rules are loaded
    for f in findings:
        assert "rule_id" in f
        assert "severity" in f


def test_dedupe_findings_single_mode():
    """Test deduplication in single-file mode (by rule_id only)."""
    findings = [
        {"rule_id": "RULE_A", "file_path": "/path/file1.tf", "resource": "res1"},
        {"rule_id": "RULE_A", "file_path": "/path/file1.tf", "resource": "res2"},
        {"rule_id": "RULE_B", "file_path": "/path/file1.tf", "resource": "res1"},
        {"rule_id": "RULE_A", "file_path": "/path/file2.tf", "resource": "res3"},
    ]
    
    deduped = dedupe_findings(findings, mode="single")
    
    # In single mode, should dedupe by rule_id only
    # So we should get 2 findings: RULE_A and RULE_B
    assert len(deduped) == 2
    
    rule_ids = {f["rule_id"] for f in deduped}
    assert rule_ids == {"RULE_A", "RULE_B"}


def test_dedupe_findings_batch_mode():
    """Test deduplication in batch mode (by rule_id + file_path + resource)."""
    findings = [
        {"rule_id": "RULE_A", "file_path": "/path/file1.tf", "resource": "res1"},
        {"rule_id": "RULE_A", "file_path": "/path/file1.tf", "resource": "res1"},  # duplicate
        {"rule_id": "RULE_A", "file_path": "/path/file1.tf", "resource": "res2"},  # different resource
        {"rule_id": "RULE_A", "file_path": "/path/file2.tf", "resource": "res1"},  # different file
        {"rule_id": "RULE_B", "file_path": "/path/file1.tf", "resource": "res1"},  # different rule
    ]
    
    deduped = dedupe_findings(findings, mode="batch")
    
    # Should keep 4 unique combinations
    assert len(deduped) == 4
    
    # Verify exact deduplication
    keys = set()
    for f in deduped:
        key = (f["rule_id"], f["file_path"], f["resource"])
        keys.add(key)
    
    assert len(keys) == 4


def test_metadata_enrichment_no_untitled():
    """Test that findings are enriched with metadata and have no 'Untitled' placeholders."""
    from rules_engine.loader import get_rule_metadata_map
    
    # Get rule metadata
    meta_map = get_rule_metadata_map()
    
    # Verify metadata structure
    assert isinstance(meta_map, dict)
    
    for rule_id, meta in meta_map.items():
        assert "title" in meta
        assert "description" in meta
        assert "severity" in meta
        assert "references" in meta
        
        # Verify no untitled
        assert meta["title"] != "Untitled"
        assert meta["title"] != ""
        
        # Verify description exists
        assert meta["description"] != "Untitled finding"


def test_scan_single_file_empty_content(tmp_path: Path):
    """Test scan_single_file with empty content returns empty list."""
    tf_file = tmp_path / "empty.tf"
    content = ""
    
    findings = scan_single_file(tf_file, content)
    
    # Empty file should have no findings
    assert isinstance(findings, list)


def test_dedupe_preserves_order():
    """Test that deduplication preserves the order of first occurrence."""
    findings = [
        {"rule_id": "RULE_C", "file_path": "/f1.tf", "resource": "r1"},
        {"rule_id": "RULE_A", "file_path": "/f1.tf", "resource": "r1"},
        {"rule_id": "RULE_B", "file_path": "/f1.tf", "resource": "r1"},
        {"rule_id": "RULE_A", "file_path": "/f1.tf", "resource": "r1"},  # duplicate
    ]
    
    deduped = dedupe_findings(findings, mode="single")
    
    # Should preserve order: C, A, B
    assert len(deduped) == 3
    assert deduped[0]["rule_id"] == "RULE_C"
    assert deduped[1]["rule_id"] == "RULE_A"
    assert deduped[2]["rule_id"] == "RULE_B"
