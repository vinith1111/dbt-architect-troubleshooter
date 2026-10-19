from dbt_architect_troubleshooter.engine import DiagnosticEngine
from dbt_architect_troubleshooter.models import DiagnosticInput
from dbt_architect_troubleshooter.rules import COMMON_RULES

engine = DiagnosticEngine(COMMON_RULES)


def diagnose(details):
    return engine.diagnose(DiagnosticInput(details=details))


def test_performance_rule_requires_recognized_issue_and_measurements():
    incomplete_cases = (
        {},
        {"performance_issue": "maybe_slow"},
        {"performance_issue": "runtime_regression"},
        {"performance_issue": "join_row_explosion", "rows_before_join": 10},
        {"performance_issue": "poor_pruning_or_large_scan", "baseline_bytes_scanned": 100},
    )
    for details in incomplete_cases:
        result = diagnose(details)
        assert not any(f.rule_id == "DBT-PERF-001" for f in result.findings)
        assert result.needs_more_evidence is True


def test_runtime_regression_requires_comparable_runs_and_increased_runtime():
    details = {
        "performance_issue": "runtime_regression",
        "baseline_runtime_seconds": 60,
        "current_runtime_seconds": 90,
        "comparable_input_volume": True,
    }
    result = diagnose(details)
    findings = [f for f in result.findings if f.rule_id == "DBT-PERF-001"]
    assert len(findings) == 1
    finding = findings[0]
    assert finding.severity.value == "warning"
    assert finding.confidence == "medium"
    assert "not established" in finding.diagnosis
    assert "details.baseline_runtime_seconds=60" in finding.evidence
    assert "details.comparable_input_volume=True" in finding.evidence
    assert any("query profile" in step.lower() for step in finding.validation_steps)
    assert finding.recommended_fix and finding.prevention


def test_runtime_regression_rejects_non_comparable_or_non_regressed_measurements():
    cases = (
        {"performance_issue": "runtime_regression", "baseline_runtime_seconds": 60, "current_runtime_seconds": 90, "comparable_input_volume": False},
        {"performance_issue": "runtime_regression", "baseline_runtime_seconds": 90, "current_runtime_seconds": 60, "comparable_input_volume": True},
    )
    for details in cases:
        result = diagnose(details)
        assert not any(f.rule_id == "DBT-PERF-001" for f in result.findings)


def test_join_and_scan_cases_require_increased_measurements_and_stay_distinct():
    join = diagnose({"performance_issue": "join_row_explosion", "rows_before_join": 100, "rows_after_join": 500})
    scan = diagnose({"performance_issue": "poor_pruning_or_large_scan", "baseline_bytes_scanned": 1024, "current_bytes_scanned": 4096})
    assert "Join cardinality" in join.findings[0].title
    assert "scans more data" in scan.findings[0].title
    assert join.findings[0].rule_id == scan.findings[0].rule_id == "DBT-PERF-001"


def test_performance_rule_rejects_invalid_or_non_regressed_measurements():
    cases = (
        {"performance_issue": "join_row_explosion", "rows_before_join": -1, "rows_after_join": 5},
        {"performance_issue": "join_row_explosion", "rows_before_join": 5, "rows_after_join": 5},
        {"performance_issue": "poor_pruning_or_large_scan", "baseline_bytes_scanned": True, "current_bytes_scanned": 5},
        {"performance_issue": "poor_pruning_or_large_scan", "baseline_bytes_scanned": 5, "current_bytes_scanned": float("nan")},
    )
    for details in cases:
        result = diagnose(details)
        assert not any(f.rule_id == "DBT-PERF-001" for f in result.findings)
