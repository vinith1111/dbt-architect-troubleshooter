"""Deterministic rule engine with explicit unknown-case handling."""
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from .models import DiagnosticFinding, DiagnosticInput

Rule = Callable[[DiagnosticInput], DiagnosticFinding | None]


@dataclass(frozen=True)
class DiagnosticResult:
    findings: tuple[DiagnosticFinding, ...]
    matched_rule_count: int
    needs_more_evidence: bool
    next_checks: tuple[str, ...]


class DiagnosticEngine:
    """Run registered rules in stable order without AI or network access."""

    def __init__(self, rules: Iterable[Rule] = ()) -> None:
        self._rules = tuple(rules)

    def diagnose(self, data: DiagnosticInput) -> DiagnosticResult:
        findings = tuple(
            finding for rule in self._rules
            if (finding := rule(data)) is not None
        )
        if findings:
            return DiagnosticResult(findings, len(findings), False, ())
        return DiagnosticResult((), 0, True, _next_checks_for(data))


def _next_checks_for(data: DiagnosticInput) -> tuple[str, ...]:
    checks: list[str] = []
    if data.message:
        checks.append("Capture the complete error message and relevant stack trace.")
    if data.file_path:
        checks.append(f"Inspect {data.file_path} and its compiled SQL, if available.")
    checks.append("Inspect logs/dbt.log and relevant target artifacts, if available.")
    checks.append("Isolate the failing model or test; record dbt version, adapter, command, and target.")
    checks.append("Do not confirm a root cause until observed evidence supports a matching rule.")
    return tuple(dict.fromkeys(checks))
