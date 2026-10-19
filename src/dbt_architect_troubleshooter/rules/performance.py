"""Evidence-gated rules for common dbt performance regressions."""
from collections.abc import Mapping
from math import isfinite

from ..models import DiagnosticFinding, DiagnosticInput, Severity


_CASES = {
    "runtime_regression": (
        "dbt model runtime regressed",
        "Comparable runs show a longer runtime; the underlying cause is not established by duration alone.",
        "Compare compiled SQL, query profile, scan volume, join cardinality, warehouse/resource settings, and recent code changes. Change one evidence-backed bottleneck at a time.",
        "Track representative runtimes and input volumes; investigate changes against a known-good baseline.",
        ("baseline_runtime_seconds", "current_runtime_seconds"),
    ),
    "join_row_explosion": (
        "Join cardinality may be increasing row volume",
        "Observed row counts increased across a join; fan-out is a candidate explanation, not yet proven to be incorrect.",
        "Compare row counts before and after each join, check key uniqueness on both sides, and inspect the intended grain. Fix a many-to-many relationship only after confirming the business logic.",
        "Add key uniqueness and row-count regression checks around joins expected to be one-to-one or many-to-one.",
        ("rows_before_join", "rows_after_join"),
    ),
    "poor_pruning_or_large_scan": (
        "Query scans more data than expected",
        "Measured scan volume is higher than the supplied baseline; pruning, filter selectivity, or source volume may contribute.",
        "Use the warehouse query profile to verify bytes or partitions scanned, inspect predicates and casts on filtered columns, and compare source volume with a known-good run. Do not assume clustering or a larger warehouse is the answer without profile evidence.",
        "Keep representative query-profile baselines and validate filter changes against performance and result correctness.",
        ("baseline_bytes_scanned", "current_bytes_scanned"),
    ),
}


def _finite_number(value: object) -> bool:
    """Accept finite non-negative numeric measurements, excluding booleans."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and isfinite(value)
        and value >= 0
    )


def _evidence_for(issue: str, details: Mapping[str, object]) -> tuple[str, ...] | None:
    """Require measurements that demonstrate the reported regression."""
    case = _CASES.get(issue)
    if case is None:
        return None

    keys = case[4]
    values = [details.get(key) for key in keys]
    if not all(_finite_number(value) for value in values):
        return None

    baseline, current = values
    if current <= baseline:
        return None

    if issue == "runtime_regression" and details.get("comparable_input_volume") is not True:
        return None

    evidence = [f"details.performance_issue={issue}"]
    evidence.extend(f"details.{key}={details[key]}" for key in keys)
    if issue == "runtime_regression":
        evidence.append("details.comparable_input_volume=True")
    return tuple(evidence)


def performance_issue(data: DiagnosticInput) -> DiagnosticFinding | None:
    """Return a finding only when the symptom and supporting measurements agree."""
    details = data.details
    issue = details.get("performance_issue")
    if not isinstance(issue, str) or issue not in _CASES:
        return None

    evidence = _evidence_for(issue, details)
    if evidence is None:
        return None

    title, diagnosis, fix, prevention, _ = _CASES[issue]
    return DiagnosticFinding(
        rule_id="DBT-PERF-001",
        title=title,
        category="performance",
        severity=Severity.WARNING,
        diagnosis=diagnosis,
        explanation=(
            "The supplied measurements support the reported regression, but they do not identify its root cause. "
            "Input volume, query-plan changes, join fan-out, pruning, and resource constraints are possible contributors."
        ),
        recommended_fix=fix,
        validation_steps=(
            "Confirm the model, adapter, command, measurement units, and comparability of the baseline.",
            "Inspect compiled SQL and the warehouse query profile before changing configuration.",
            "Benchmark the proposed change against a comparable baseline and verify output correctness.",
        ),
        prevention=prevention,
        evidence=evidence,
        confidence="medium",
    )
