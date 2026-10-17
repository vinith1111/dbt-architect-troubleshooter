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
