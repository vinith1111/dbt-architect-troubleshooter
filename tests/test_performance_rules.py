from dbt_architect_troubleshooter.engine import DiagnosticEngine
from dbt_architect_troubleshooter.models import DiagnosticInput
from dbt_architect_troubleshooter.rules import COMMON_RULES

engine = DiagnosticEngine(COMMON_RULES)


def test_performance_rule_requires_recognized_structured_evidence():
    for details in ({}, {"performance_issue": "maybe_slow"}, {"performance_issue": "unknown"}):
        result = engine.diagnose(DiagnosticInput(details=details))
        assert result.findings == ()
        assert result.needs_more_evidence is True


def test_runtime_regression_does_not_claim_a_confirmed_root_cause():
    result = engine.diagnose(DiagnosticInput(details={"performance_issue": "runtime_regression"}))
    assert [finding.rule_id for finding in result.findings] == ["DBT-PERF-001"]
    finding = result.findings[0]
    assert finding.severity.value == "warning"
    assert finding.confidence == "medium"
    assert "not established" in finding.diagnosis
    assert finding.evidence == ("details.performance_issue=runtime_regression",)
    assert any("query profile" in step.lower() for step in finding.validation_steps)
    assert finding.recommended_fix and finding.prevention


def test_join_and_scan_performance_cases_are_distinct():
    join = engine.diagnose(DiagnosticInput(details={"performance_issue": "join_row_explosion"}))
    scan = engine.diagnose(DiagnosticInput(details={"performance_issue": "poor_pruning_or_large_scan"}))
    assert "Join cardinality" in join.findings[0].title
    assert "scans more data" in scan.findings[0].title
    assert join.findings[0].rule_id == scan.findings[0].rule_id == "DBT-PERF-001"
