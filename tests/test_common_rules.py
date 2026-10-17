from dbt_architect_troubleshooter.engine import DiagnosticEngine
from dbt_architect_troubleshooter.models import DiagnosticInput
from dbt_architect_troubleshooter.rules import COMMON_RULES

engine = DiagnosticEngine(COMMON_RULES)


def test_missing_project_file_requires_root_confirmation():
    assert engine.diagnose(DiagnosticInput()).findings == ()
    result = engine.diagnose(DiagnosticInput(details={"project_root_checked": True}))
    assert [f.rule_id for f in result.findings] == ["DBT-SETUP-001"]


def test_profile_not_found_uses_explicit_signal():
    result = engine.diagnose(DiagnosticInput(message="Could not find profile named warehouse_project"))
    assert [f.rule_id for f in result.findings] == ["DBT-CONFIG-001"]
    assert "profiles.yml" in result.findings[0].recommended_fix


def test_unrelated_message_does_not_match_profile_rule():
    result = engine.diagnose(DiagnosticInput(message="Database connection timed out"))
    assert result.findings == ()
    assert result.needs_more_evidence is True


def test_dependency_error_is_diagnosed():
    result = engine.diagnose(DiagnosticInput(error_code="DEPENDENCY_ERROR"))
    assert [f.rule_id for f in result.findings] == ["DBT-GRAPH-001"]


def test_common_data_tests_have_fix_validation_and_prevention():
    for name in ("unique", "not_null", "relationships", "accepted_values"):
        result = engine.diagnose(DiagnosticInput(failed_test_name=name))
        assert len(result.findings) == 1
        finding = result.findings[0]
        assert finding.evidence and finding.recommended_fix
        assert finding.validation_steps and finding.prevention


def test_unknown_test_is_not_misclassified():
    result = engine.diagnose(DiagnosticInput(failed_test_name="custom_business_rule"))
    assert result.findings == ()
    assert result.needs_more_evidence is True



def test_compilation_error_gives_general_steps_without_inventing_exact_cause():
    result = engine.diagnose(DiagnosticInput(error_code="COMPILATION_ERROR"))
    assert [f.rule_id for f in result.findings] == ["DBT-COMPILE-001"]
    finding = result.findings[0]
    assert "exact cause needs" in finding.diagnosis
    assert any("dbt parse" in step for step in finding.validation_steps)


def test_source_freshness_failure_is_detected():
    result = engine.diagnose(DiagnosticInput(error_code="SOURCE_FRESHNESS_FAILED"))
    assert [f.rule_id for f in result.findings] == ["DBT-SOURCE-001"]
    assert "upstream load" in result.findings[0].recommended_fix


def test_incremental_duplicate_rule_requires_observed_evidence():
    no_evidence = engine.diagnose(DiagnosticInput(message="Duplicates might happen"))
    assert no_evidence.findings == ()

    confirmed_symptom = engine.diagnose(
        DiagnosticInput(details={"duplicate_rows_observed": True, "unique_key_configured": False})
    )
    assert [f.rule_id for f in confirmed_symptom.findings] == ["DBT-INCR-001"]
    finding = confirmed_symptom.findings[0]
    assert "root cause is not confirmed" in finding.diagnosis
    assert "details.unique_key_configured=false" in finding.evidence
    assert any("compiled SQL" in step for step in finding.validation_steps)



def test_incremental_missed_updates_requires_explicit_issue_evidence():
    negative = engine.diagnose(DiagnosticInput(details={"incremental_issue": "maybe_missed_updates"}))
    assert negative.findings == ()

    result = engine.diagnose(DiagnosticInput(details={"incremental_issue": "missed_updates"}))
    assert [f.rule_id for f in result.findings] == ["DBT-INCR-002"]
    finding = result.findings[0]
    assert "does not prove" in finding.explanation
    assert any("compiled SQL" in step for step in finding.validation_steps)
    assert finding.prevention


def test_incremental_late_arriving_and_wrong_key_cases_are_distinct():
    late = engine.diagnose(DiagnosticInput(details={"incremental_issue": "late_arriving_data"}))
    wrong_key = engine.diagnose(DiagnosticInput(details={"incremental_issue": "wrong_unique_key"}))
    assert late.findings[0].rule_id == "DBT-INCR-002"
    assert "lookback window" in late.findings[0].recommended_fix
    assert "grain" in wrong_key.findings[0].diagnosis


def test_snapshot_rules_match_only_known_evidence_values():
    assert engine.diagnose(DiagnosticInput(details={"snapshot_issue": "unknown"})).findings == ()

    for issue in ("missing_unique_key", "updated_at_missing_or_null", "unexpected_history"):
        result = engine.diagnose(DiagnosticInput(details={"snapshot_issue": issue}))
        assert [f.rule_id for f in result.findings] == ["DBT-SNAP-001"]
        finding = result.findings[0]
        assert finding.evidence == (f"details.snapshot_issue={issue}",)
        assert finding.recommended_fix and finding.validation_steps and finding.prevention


def test_schema_evolution_rules_are_evidence_gated_and_actionable():
    assert engine.diagnose(DiagnosticInput(message="column was added yesterday")).findings == ()

    for change in ("added_column", "removed_or_renamed_column", "contract_mismatch"):
        result = engine.diagnose(DiagnosticInput(details={"schema_change": change}))
        assert [f.rule_id for f in result.findings] == ["DBT-SCHEMA-001"]
        finding = result.findings[0]
        assert finding.evidence == (f"details.schema_change={change}",)
        assert finding.recommended_fix and finding.validation_steps and finding.prevention


def test_unknown_incremental_snapshot_and_schema_values_do_not_guess():
    for details in (
        {"incremental_issue": "random"},
        {"snapshot_issue": "random"},
        {"schema_change": "random"},
    ):
        result = engine.diagnose(DiagnosticInput(details=details))
        assert result.findings == ()
        assert result.needs_more_evidence is True
