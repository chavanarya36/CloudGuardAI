"""
Extended rules engine tests — covers matchers, loader, evaluator, utils, schemas, LLM reasoner.
Pushes rules-engine coverage from ~50% to 80%+.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock


# ═══════════════════════════════════════════════════════════════════════════
# Schemas — dataclasses + file_type_for_path
# ═══════════════════════════════════════════════════════════════════════════
class TestSchemas:
    """Test RuleMatch, Rule, Finding dataclasses and file_type_for_path."""

    def test_file_type_terraform(self):
        from rules.rules_engine.schemas import file_type_for_path
        assert file_type_for_path(Path("main.tf")) == "terraform"

    def test_file_type_yaml(self):
        from rules.rules_engine.schemas import file_type_for_path
        assert file_type_for_path(Path("deploy.yaml")) == "yaml"

    def test_file_type_yml(self):
        from rules.rules_engine.schemas import file_type_for_path
        assert file_type_for_path(Path("values.yml")) == "yaml"

    def test_file_type_json(self):
        from rules.rules_engine.schemas import file_type_for_path
        assert file_type_for_path(Path("config.json")) == "json"

    def test_file_type_bicep(self):
        from rules.rules_engine.schemas import file_type_for_path
        assert file_type_for_path(Path("main.bicep")) == "bicep"

    def test_file_type_other(self):
        from rules.rules_engine.schemas import file_type_for_path
        assert file_type_for_path(Path("readme.md")) == "other"

    def test_finding_to_dict(self):
        from rules.rules_engine.schemas import Finding
        f = Finding(
            rule_id="R001", severity="HIGH", description="desc",
            file_path="main.tf", line=5, evidence="acl=public",
            references=["https://example.com"]
        )
        d = f.to_dict()
        assert d["rule_id"] == "R001"
        assert d["line"] == 5
        assert isinstance(d["references"], list)

    def test_rule_match_defaults(self):
        from rules.rules_engine.schemas import RuleMatch
        m = RuleMatch()
        assert m.regex is None
        assert m.contains is None
        assert m.not_contains is None
        assert m.terraform_block is None

    def test_rule_defaults(self):
        from rules.rules_engine.schemas import Rule, RuleMatch
        r = Rule(id="T1", description="test", severity="LOW")
        assert r.file_types == []
        assert isinstance(r.match, RuleMatch)
        assert r.references == []


# ═══════════════════════════════════════════════════════════════════════════
# Matchers — not_contains, json_path, terraform_block, missing_key
# ═══════════════════════════════════════════════════════════════════════════
class TestMatcherExtended:
    """Test untested matcher functions for 80%+ coverage."""

    def _rule(self, **match_kwargs):
        from rules.rules_engine.schemas import Rule, RuleMatch
        return Rule(
            id="TEST-001", description="Test rule", severity="HIGH",
            match=RuleMatch(**match_kwargs)
        )

    def test_not_contains_missing_string_found(self):
        """If the needle is NOT in content, we get a finding."""
        from rules.rules_engine.matcher import not_contains_match
        rule = self._rule(not_contains="encryption")
        findings = not_contains_match(rule, Path("main.tf"), "resource {}")
        assert len(findings) == 1
        assert "missing" in findings[0].evidence.lower()

    def test_not_contains_string_present(self):
        """If the needle IS in content, no finding."""
        from rules.rules_engine.matcher import not_contains_match
        rule = self._rule(not_contains="encryption")
        findings = not_contains_match(rule, Path("main.tf"), "encryption = true")
        assert len(findings) == 0

    def test_not_contains_no_needle(self):
        from rules.rules_engine.matcher import not_contains_match
        rule = self._rule()  # no not_contains set
        findings = not_contains_match(rule, Path("f.tf"), "anything")
        assert len(findings) == 0

    def test_json_path_match_delegates_to_yaml_path(self):
        """json_path_match is an alias for yaml_path_match."""
        from rules.rules_engine.matcher import json_path_match, yaml_path_match
        content = json.dumps({"spec": {"replicas": 3}})
        rule = self._rule(yaml_path="$.spec.replicas", equals=3)
        jp = json_path_match(rule, Path("f.json"), content)
        yp = yaml_path_match(rule, Path("f.json"), content)
        assert len(jp) == len(yp)

    def test_yaml_path_match_found(self):
        from rules.rules_engine.matcher import yaml_path_match
        content = json.dumps({"spec": {"replicas": 1}})
        rule = self._rule(yaml_path="$.spec.replicas", equals=1)
        findings = yaml_path_match(rule, Path("f.json"), content)
        assert len(findings) == 1

    def test_yaml_path_match_not_found(self):
        from rules.rules_engine.matcher import yaml_path_match
        content = json.dumps({"spec": {"replicas": 3}})
        rule = self._rule(yaml_path="$.spec.replicas", equals=1)
        findings = yaml_path_match(rule, Path("f.json"), content)
        assert len(findings) == 0

    def test_yaml_path_match_invalid_content(self):
        from rules.rules_engine.matcher import yaml_path_match
        rule = self._rule(yaml_path="$.a.b", equals=1)
        findings = yaml_path_match(rule, Path("f.json"), "not valid json {{{")
        assert len(findings) == 0

    def test_yaml_path_with_wildcard(self):
        from rules.rules_engine.matcher import yaml_path_match
        content = json.dumps({"items": [{"name": "a"}, {"name": "b"}]})
        rule = self._rule(yaml_path="$.items[*].name", equals="a")
        findings = yaml_path_match(rule, Path("f.json"), content)
        assert len(findings) == 1

    def test_terraform_block_match_found(self):
        from rules.rules_engine.matcher import terraform_block_match
        rule = self._rule(terraform_block={"type": "aws_s3_bucket"})
        content = 'resource "aws_s3_bucket" "b" {\n  bucket = "test"\n}'
        findings = terraform_block_match(rule, Path("main.tf"), content)
        assert len(findings) == 1

    def test_terraform_block_match_not_found(self):
        from rules.rules_engine.matcher import terraform_block_match
        rule = self._rule(terraform_block={"type": "aws_rds_instance"})
        content = 'resource "aws_s3_bucket" "b" {}'
        findings = terraform_block_match(rule, Path("main.tf"), content)
        assert len(findings) == 0

    def test_terraform_block_no_type(self):
        from rules.rules_engine.matcher import terraform_block_match
        rule = self._rule(terraform_block={})
        findings = terraform_block_match(rule, Path("main.tf"), "anything")
        assert len(findings) == 0

    def test_missing_key_match_found(self):
        from rules.rules_engine.matcher import missing_key_match
        rule = self._rule(missing_key="encryption")
        findings = missing_key_match(rule, Path("main.tf"), "resource {}")
        assert len(findings) == 1

    def test_missing_key_match_present(self):
        from rules.rules_engine.matcher import missing_key_match
        rule = self._rule(missing_key="encryption")
        findings = missing_key_match(rule, Path("main.tf"), "encryption = true")
        assert len(findings) == 0

    def test_contains_match_found(self):
        from rules.rules_engine.matcher import contains_match
        rule = self._rule(contains="public-read")
        content = 'acl = "public-read"\n'
        findings = contains_match(rule, Path("main.tf"), content)
        assert len(findings) == 1
        assert findings[0].line == 1

    def test_regex_match_multiline(self):
        from rules.rules_engine.matcher import regex_match
        rule = self._rule(regex=r"password\s*=")
        content = "line1\npassword = secret\nline3"
        findings = regex_match(rule, Path("f.tf"), content)
        assert len(findings) == 1
        assert findings[0].line == 2


# ═══════════════════════════════════════════════════════════════════════════
# Loader — load_all_rules, get_rule_metadata_map
# ═══════════════════════════════════════════════════════════════════════════
class TestLoaderExtended:
    """Test rule loader edge cases."""

    def test_load_all_rules_returns_list(self):
        from rules.rules_engine.loader import load_all_rules
        rules = load_all_rules()
        assert isinstance(rules, list)
        # Should have at least some rules from the yaml files
        assert len(rules) > 0

    def test_load_all_rules_have_required_fields(self):
        from rules.rules_engine.loader import load_all_rules
        rules = load_all_rules()
        for rule in rules[:5]:  # spot-check first 5
            assert rule.id
            assert rule.severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW")

    def test_get_rule_metadata_map(self):
        from rules.rules_engine.loader import get_rule_metadata_map
        meta = get_rule_metadata_map()
        assert isinstance(meta, dict)
        if meta:
            first_key = next(iter(meta))
            entry = meta[first_key]
            assert "title" in entry
            assert "severity" in entry

    def test_load_yaml_file_missing(self):
        from rules.rules_engine.loader import _load_yaml_file
        result = _load_yaml_file(Path("/nonexistent/path/rules.yaml"))
        assert result == {}

    def test_load_rules_from_yaml_empty(self):
        from rules.rules_engine.loader import _load_rules_from_yaml
        import tempfile, os
        # Create an empty YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("rules: []\n")
            f.flush()
            rules = _load_rules_from_yaml(Path(f.name))
        os.unlink(f.name)
        assert rules == []


# ═══════════════════════════════════════════════════════════════════════════
# Evaluator — evaluate_file
# ═══════════════════════════════════════════════════════════════════════════
class TestEvaluatorExtended:
    """Test evaluator.evaluate_file with custom rules."""

    def test_evaluate_file_matches_rule(self):
        from rules.rules_engine.evaluator import evaluate_file
        from rules.rules_engine.schemas import Rule, RuleMatch
        rule = Rule(
            id="TEST-E1", description="public access", severity="HIGH",
            file_types=["terraform"],
            match=RuleMatch(contains="public-read")
        )
        findings = evaluate_file(
            Path("main.tf"),
            'acl = "public-read"',
            [rule]
        )
        assert len(findings) >= 1
        assert findings[0].rule_id == "TEST-E1"

    def test_evaluate_file_skips_wrong_type(self):
        from rules.rules_engine.evaluator import evaluate_file
        from rules.rules_engine.schemas import Rule, RuleMatch
        rule = Rule(
            id="TEST-E2", description="yaml only", severity="LOW",
            file_types=["yaml"],
            match=RuleMatch(contains="something")
        )
        findings = evaluate_file(
            Path("main.tf"),  # terraform, not yaml
            "something is here",
            [rule]
        )
        assert len(findings) == 0

    def test_evaluate_file_no_file_type_filter(self):
        from rules.rules_engine.evaluator import evaluate_file
        from rules.rules_engine.schemas import Rule, RuleMatch
        rule = Rule(
            id="TEST-E3", description="any file", severity="MEDIUM",
            file_types=[],  # empty = matches all
            match=RuleMatch(contains="keyword")
        )
        findings = evaluate_file(Path("any.txt"), "has keyword here", [rule])
        assert len(findings) >= 1


# ═══════════════════════════════════════════════════════════════════════════
# Utils — dedupe_findings
# ═══════════════════════════════════════════════════════════════════════════
class TestUtilsDedupe:
    """Test dedupe_findings in single and batch modes."""

    def test_single_mode_dedupes_by_rule_id(self):
        from rules.rules_engine.utils import dedupe_findings
        findings = [
            {"rule_id": "R1", "file_path": "a.tf", "resource": "x"},
            {"rule_id": "R1", "file_path": "b.tf", "resource": "y"},
            {"rule_id": "R2", "file_path": "a.tf", "resource": "x"},
        ]
        result = dedupe_findings(findings, mode="single")
        assert len(result) == 2  # R1 + R2

    def test_batch_mode_dedupes_by_rule_path_resource(self):
        from rules.rules_engine.utils import dedupe_findings
        findings = [
            {"rule_id": "R1", "file_path": "a.tf", "resource": "x"},
            {"rule_id": "R1", "file_path": "b.tf", "resource": "y"},
            {"rule_id": "R1", "file_path": "a.tf", "resource": "x"},  # duplicate
        ]
        result = dedupe_findings(findings, mode="batch")
        assert len(result) == 2  # two unique combos

    def test_empty_list(self):
        from rules.rules_engine.utils import dedupe_findings
        assert dedupe_findings([], mode="single") == []

    def test_no_duplicates(self):
        from rules.rules_engine.utils import dedupe_findings
        findings = [
            {"rule_id": "A"}, {"rule_id": "B"}, {"rule_id": "C"}
        ]
        assert len(dedupe_findings(findings)) == 3


# ═══════════════════════════════════════════════════════════════════════════
# Engine — scan_single_file, scan_file
# ═══════════════════════════════════════════════════════════════════════════
class TestEngineExtended:
    """Test engine.scan_single_file and related functions."""

    def test_scan_single_file_returns_list(self):
        from rules.rules_engine.engine import scan_single_file
        result = scan_single_file(
            Path("test.tf"),
            'resource "aws_s3_bucket" "b" { acl = "public-read" }'
        )
        assert isinstance(result, list)

    def test_scan_single_file_findings_have_required_keys(self):
        from rules.rules_engine.engine import scan_single_file
        result = scan_single_file(
            Path("test.tf"),
            'resource "aws_s3_bucket" "b" { acl = "public-read" }'
        )
        for f in result:
            assert "rule_id" in f
            assert "severity" in f
            assert "description" in f

    def test_scan_single_file_safe_content(self):
        from rules.rules_engine.engine import scan_single_file
        result = scan_single_file(Path("safe.tf"), "# just a comment\n")
        assert isinstance(result, list)

    def test_get_rules_returns_list(self):
        from rules.rules_engine.engine import get_rules
        rules = get_rules()
        assert isinstance(rules, list)


# ═══════════════════════════════════════════════════════════════════════════
# LLM Reasoner — deterministic fallback, edge cases
# ═══════════════════════════════════════════════════════════════════════════
class TestLLMReasonerExtended:
    """Test LLM reasoner edge cases for 80%+ coverage."""

    def test_deterministic_fallback_structure(self):
        from rules.rules_engine.llm_reasoner import _deterministic_fallback
        result = _deterministic_fallback(
            {"rule_id": "R1", "description": "test", "severity": "HIGH", "file_path": "f.tf"},
            "some content"
        )
        assert "explanation" in result
        assert "remediation" in result
        assert "certainty" in result
        assert result["certainty"] == 0.6

    def test_deterministic_fallback_missing_fields(self):
        from rules.rules_engine.llm_reasoner import _deterministic_fallback
        result = _deterministic_fallback({}, "")
        assert "explanation" in result
        assert "UNKNOWN_RULE" in result["explanation"]

    @patch.dict('os.environ', {}, clear=True)
    def test_explain_no_api_key_uses_fallback(self):
        from rules.rules_engine.llm_reasoner import explain_and_remediate
        # No OPENAI_API_KEY → deterministic fallback
        result = explain_and_remediate(
            {"rule_id": "R1", "severity": "HIGH", "description": "test"},
            "resource content"
        )
        assert result["certainty"] == 0.6  # deterministic

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('rules.rules_engine.llm_reasoner._call_llm')
    def test_explain_llm_success(self, mock_llm):
        mock_llm.return_value = {
            "message": "This is risky because X.\n1) Fix Y\nCertainty: 0.9"
        }
        from rules.rules_engine.llm_reasoner import explain_and_remediate
        result = explain_and_remediate(
            {"rule_id": "R1", "severity": "HIGH", "description": "test"},
            "resource content"
        )
        assert result["certainty"] == 0.9
        assert "risky" in result["explanation"]

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('rules.rules_engine.llm_reasoner._call_llm')
    def test_explain_llm_exception_falls_back(self, mock_llm):
        mock_llm.side_effect = Exception("API error")
        from rules.rules_engine.llm_reasoner import explain_and_remediate
        result = explain_and_remediate(
            {"rule_id": "R1", "severity": "HIGH", "description": "test"},
            "content"
        )
        assert result["certainty"] == 0.6  # fallback

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('rules.rules_engine.llm_reasoner._call_llm')
    def test_explain_llm_empty_response(self, mock_llm):
        mock_llm.return_value = {"message": ""}
        from rules.rules_engine.llm_reasoner import explain_and_remediate
        result = explain_and_remediate(
            {"rule_id": "R1", "severity": "HIGH", "description": "test"},
            "content"
        )
        assert result["certainty"] == 0.6  # empty → ValueError → fallback

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('rules.rules_engine.llm_reasoner._call_llm')
    def test_explain_certainty_parsing_invalid(self, mock_llm):
        mock_llm.return_value = {
            "message": "Some explanation\nCertainty: not-a-number"
        }
        from rules.rules_engine.llm_reasoner import explain_and_remediate
        result = explain_and_remediate(
            {"rule_id": "R1", "severity": "HIGH", "description": "test"},
            "content"
        )
        # Invalid certainty should default to 0.8
        assert result["certainty"] == 0.8

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('rules.rules_engine.llm_reasoner._call_llm')
    def test_explain_certainty_no_marker(self, mock_llm):
        mock_llm.return_value = {
            "message": "This is the explanation with no certainty marker."
        }
        from rules.rules_engine.llm_reasoner import explain_and_remediate
        result = explain_and_remediate(
            {"rule_id": "R1", "severity": "HIGH", "description": "test"},
            "content"
        )
        # No "Certainty:" marker → default 0.8
        assert result["certainty"] == 0.8
