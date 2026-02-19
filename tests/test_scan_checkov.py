import pytest
from pathlib import Path

try:
    from scanners.scan_checkov import CheckovFinding, normalise_findings, write_results_json
except ImportError:
    pytest.skip("scanners.scan_checkov module not available", allow_module_level=True)


def test_normalise_findings_basic_structure(tmp_path: Path) -> None:
    raw = {
        "results": {
            "failed_checks": [
                {
                    "check_id": "CKV_TEST_1",
                    "check_name": "Test check",
                    "file_path": "main.tf",
                    "resource": "aws_s3_bucket.example",
                    "severity": "HIGH",
                    "bc_category": "TEST_CATEGORY",
                    "code_block": [[1, "resource \"aws_s3_bucket\" \"example\" {}"]],
                }
            ],
            "skipped_checks": [],
            "passed_checks": [],
        }
    }

    findings = normalise_findings(raw)
    assert len(findings) == 1
    f = findings[0]
    assert isinstance(f, CheckovFinding)
    assert f.check_id == "CKV_TEST_1"
    assert f.file_path == "main.tf"
    assert f.resource == "aws_s3_bucket.example"
    assert f.severity == "HIGH"
    assert f.bc_category == "TEST_CATEGORY"
    assert "aws_s3_bucket" in f.checkov_code


def test_write_results_json_roundtrip(tmp_path: Path) -> None:
    raw = {"results": {"failed_checks": []}}
    findings = [
        CheckovFinding(
            check_id="ID1",
            check_name="Name",
            file_path="file.tf",
            resource="res",
            severity="MEDIUM",
            bc_category="CAT",
            checkov_code="code",
        )
    ]

    out_path = tmp_path / "checkov_results.json"
    write_results_json(raw, findings, out_path)

    assert out_path.exists()
    data = out_path.read_text(encoding="utf-8")
    assert "\"findings\"" in data
    assert "ID1" in data
