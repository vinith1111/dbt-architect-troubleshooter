from dbt_architect_troubleshooter.engine import DiagnosticEngine
from dbt_architect_troubleshooter.models import DiagnosticInput


def test_unknown_case_returns_next_checks_instead_of_guessing():
    result = DiagnosticEngine().diagnose(
        DiagnosticInput(message="Unrecognized failure", file_path="models/orders.sql")
    )
    assert result.findings == ()
    assert result.needs_more_evidence is True
    assert any("compiled SQL" in item for item in result.next_checks)
    assert any("root cause" in item for item in result.next_checks)


def test_empty_input_still_returns_actionable_checks():
    result = DiagnosticEngine().diagnose(DiagnosticInput())
    assert result.needs_more_evidence is True
    assert len(result.next_checks) >= 3
