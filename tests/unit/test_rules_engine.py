from pathlib import Path

from rules_engine.engine import scan_directory
from rules_engine.loader import load_all_rules
from rules_engine.matcher import (
    contains_match,
    missing_key_match,
    regex_match,
    terraform_block_match,
    yaml_path_match,
)
from rules_engine.schemas import Finding, Rule, RuleMatch


def test_load_all_rules_structure() -> None:
    rules = load_all_rules()
    assert any(r.id == "AWS_CIS_SG_0_0_0_0" for r in rules)
    assert any(r.id == "K8S_PRIVILEGED_TRUE" for r in rules)


def test_regex_detection(tmp_path: Path) -> None:
    content = "ingress from 0.0.0.0/0 is bad"
    path = tmp_path / "main.tf"
    path.write_text(content, encoding="utf-8")
    rule = Rule(
        id="TEST_REGEX",
        description="detect 0.0.0.0/0",
        severity="HIGH",
        file_types=["terraform"],
        match=RuleMatch(regex=r"0\.0\.0\.0/0"),
    )
    findings = regex_match(rule, path, content)
    assert findings and isinstance(findings[0], Finding)


def test_contains_detection(tmp_path: Path) -> None:
    content = "privileged: true"
    path = tmp_path / "pod.yaml"
    path.write_text(content, encoding="utf-8")
    rule = Rule(
        id="TEST_CONTAINS",
        description="detect privileged true",
        severity="HIGH",
        file_types=["yaml"],
        match=RuleMatch(contains="privileged: true"),
    )
    findings = contains_match(rule, path, content)
    assert findings and "privileged" in findings[0].evidence


def test_missing_key_detection(tmp_path: Path) -> None:
    content = "resource \"aws_s3_bucket\" \"b\" {}"
    path = tmp_path / "main.tf"
    path.write_text(content, encoding="utf-8")
    rule = Rule(
        id="TEST_MISSING_KEY",
        description="encryption key should be present",
        severity="MEDIUM",
        file_types=["terraform"],
        match=RuleMatch(missing_key="encryption"),
    )
    findings = missing_key_match(rule, path, content)
    assert findings and "missing key" in findings[0].evidence


def test_yaml_path_detection(tmp_path: Path) -> None:
    yaml_content = """
apiVersion: v1
kind: Pod
spec:
  template:
    spec:
      containers:
        - name: app
          securityContext:
            runAsUser: 0
"""
    path = tmp_path / "pod.yaml"
    path.write_text(yaml_content, encoding="utf-8")
    rule = Rule(
        id="TEST_YAML_PATH",
        description="runAsUser 0 should be detected",
        severity="HIGH",
        file_types=["yaml"],
        match=RuleMatch(
            yaml_path="$.spec.template.spec.containers[*].securityContext.runAsUser",
            equals=0,
        ),
    )
    findings = yaml_path_match(rule, path, yaml_content)
    assert findings and "runAsUser" in findings[0].evidence


def test_multi_file_eval(tmp_path: Path) -> None:
    tf = tmp_path / "main.tf"
    tf.write_text("ingress from 0.0.0.0/0", encoding="utf-8")
    pod = tmp_path / "pod.yaml"
    pod.write_text("privileged: true", encoding="utf-8")

    findings = scan_directory(tmp_path)
    assert any("0.0.0.0/0" in f.evidence for f in findings)
    assert any("privileged" in f.evidence for f in findings)


def test_terraform_block_detection(tmp_path: Path) -> None:
    tf = tmp_path / "bucket.tf"
    tf.write_text('resource "aws_s3_bucket" "b" {}', encoding="utf-8")
    rule = Rule(
        id="TEST_TF_BLOCK",
        description="detect aws_s3_bucket block",
        severity="LOW",
        file_types=["terraform"],
        match=RuleMatch(terraform_block={"type": "aws_s3_bucket"}),
    )
    findings = terraform_block_match(rule, tf, tf.read_text(encoding="utf-8"))
    assert findings and "aws_s3_bucket" in findings[0].evidence


def test_severity_and_references_present() -> None:
    rules = load_all_rules()
    for r in rules:
        assert r.severity in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
        assert isinstance(r.references, list)
