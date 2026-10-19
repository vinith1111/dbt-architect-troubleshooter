"""Evidence-gated rules for common dbt performance regressions."""
from ..models import DiagnosticFinding, DiagnosticInput, Severity


_CASES = {
    "runtime_regression": (
        "dbt model runtime regressed",
        "A runtime regression was observed, but the cause is not established by duration alone.",
        "Compare runs with similar input volume. Inspect compiled SQL, query profile, scan volume, join cardinality, warehouse/resource settings, and recent code changes. Change one evidence-backed bottleneck at a time.",
        "Track representative runtimes and input volumes; investigate changes against a known-good baseline.",
    ),
    "join_row_explosion": (
        "Join cardinality may be increasing row volume",
        "Evidence indicates an unexpectedly large intermediate or final row count; a join fan-out is a candidate cause, not yet proven.",
        "Compare row counts before and after each join, check key uniqueness on both sides, and inspect the intended grain. Fix the specific many-to-many relationship only after confirming the business logic.",
        "Add key uniqueness and row-count regression checks around joins where the intended relationship is one-to-one or many-to-one.",
    ),
    "poor_pruning_or_large_scan": (
        "Query scans more data than expected",
        "Evidence indicates a larger-than-expected scan; pruning, filter selectivity, or source volume may contribute.",
        "Use the warehouse query profile to verify bytes/partitions scanned, inspect predicates and casts on filtered columns, and compare source volume with a known-good run. Do not assume clustering or a larger warehouse is the answer without profile evidence.",
        "Keep representative query-profile baselines and validate filter changes against both performance and result correctness.",
    ),
}


def performance_issue(data: DiagnosticInput) -> DiagnosticFinding | None:
    """Return a performance finding only when a recognized observation is supplied."""
    issue = data.details.get("performance_issue")
    if issue not in _CASES:
        return None

    title, diagnosis, fix, prevention = _CASES[issue]
    return DiagnosticFinding(
        rule_id="DBT-PERF-001",
        title=title,
        category="performance",
        severity=Severity.WARNING,
        diagnosis=diagnosis,
        explanation=(
            "Runtime symptoms can have different causes, including larger inputs, query-plan changes, "
            "join fan-out, reduced pruning, or resource constraints. This rule requires an explicit "
            "structured observation and does not claim a confirmed root cause."
        ),
        recommended_fix=fix,
        validation_steps=(
            "Capture the model, adapter, command, runtime, and comparable input-volume details.",
            "Inspect compiled SQL and the warehouse query profile before changing configuration.",
            "Benchmark the proposed change against a comparable baseline and verify output correctness.",
        ),
        prevention=prevention,
        evidence=(f"details.performance_issue={issue}",),
        confidence="medium",
    )
