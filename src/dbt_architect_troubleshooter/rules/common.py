"""Initial rules for common dbt setup, dependency, and data-test failures."""
from ..models import DiagnosticFinding, DiagnosticInput, Severity


def _finding(rule_id, title, category, diagnosis, explanation, fix, validation, prevention, evidence):
    return DiagnosticFinding(
        rule_id=rule_id, title=title, category=category, severity=Severity.ERROR,
        diagnosis=diagnosis, explanation=explanation, recommended_fix=fix,
        validation_steps=validation, prevention=prevention, evidence=evidence,
    )


def missing_project_file(data: DiagnosticInput) -> DiagnosticFinding | None:
    if "dbt_project.yml" in data.project_files or data.details.get("project_root_checked") is not True:
        return None
    return _finding(
        "DBT-SETUP-001", "dbt project file is missing", "project_setup",
        "The inspected project root does not contain dbt_project.yml.",
        "dbt needs this file to identify and configure a project. This rule only applies after the caller confirms the project root was checked.",
        "Run dbt from the correct directory or restore a valid dbt_project.yml.",
        ("Confirm the file exists in the intended project root.", "Run dbt parse from that directory."),
        "Run commands from the repository root and validate project setup in CI.",
        ("project_root_checked=true", "dbt_project.yml absent from project_files"),
    )


def profile_not_found(data: DiagnosticInput) -> DiagnosticFinding | None:
    if data.error_code != "PROFILE_NOT_FOUND" and "could not find profile named" not in data.message.lower():
        return None
    return _finding(
        "DBT-CONFIG-001", "Configured dbt profile was not found", "configuration",
        "The profile referenced by the project could not be resolved.",
        "The profile name in dbt_project.yml must match a profile available to this dbt process.",
        "Compare the project profile setting with profiles.yml and verify the active profile path and environment.",
        ("Run dbt debug in the same shell or job environment.", "Retry dbt parse after the profile resolves."),
        "Document profile setup and validate environment variables in local runs and CI.",
        (f"error_code={data.error_code}" if data.error_code else "message contains profile-not-found signal",),
    )


def dependency_error(data: DiagnosticInput) -> DiagnosticFinding | None:
    message = data.message.lower()
    if not (data.error_code == "DEPENDENCY_ERROR" or "depends on a node named" in message or "circular dependency" in message):
        return None
    return _finding(
        "DBT-GRAPH-001", "dbt model dependency could not be resolved", "dependencies",
        "dbt reported a missing dependency or circular dependency.",
        "dbt builds a directed graph from ref and source relationships; missing targets or cycles prevent valid graph construction.",
        "Check the referenced model/source name and enabled state. For cycles, redesign dependencies so the graph is acyclic.",
        ("Run dbt parse and confirm graph validation succeeds.", "Run the smallest affected model selection."),
        "Include dbt parse in CI and keep model references under version control.",
        (f"error_code={data.error_code}" if data.error_code else f"message={data.message}",),
    )


def generic_test_failure(data: DiagnosticInput) -> DiagnosticFinding | None:
    name = (data.failed_test_name or "").strip().lower()
    cases = {
        "unique": ("Uniqueness test failed", "The tested column contains repeated values.", "Inspect failing rows and intended grain. Correct upstream joins or duplication; revise the key only if the actual grain differs.", "Document model grain and test the correct business key."),
        "not_null": ("Not-null test failed", "The tested column contains NULL values.", "Inspect failing rows and upstream transformations; correct the source or explicitly model an allowed unknown value.", "Define required fields and add upstream checks."),
        "relationships": ("Relationships test failed", "Some child values lack a matching parent value.", "Inspect unmatched keys and parent coverage; correct key transformations or load order.", "Test parent-key uniqueness and normalize keys consistently."),
        "accepted_values": ("Accepted-values test failed", "The tested column contains values outside the configured accepted set.", "Inspect unexpected values and confirm the business-approved set before changing mappings or the accepted set.", "Maintain accepted values with documented business definitions."),
    }
    if name not in cases:
        return None
    title, diagnosis, fix, prevention = cases[name]
    return _finding(
        f"DBT-TEST-{name.upper()}-001", title, "data_quality", diagnosis,
        "A data test identifies rows that violate its assertion; it does not by itself prove which upstream transformation caused them.",
        fix,
        ("Inspect failing rows using compiled test SQL or the failure relation, if configured.", "Rerun the specific test and then the affected model selection."),
        prevention, (f"failed_test_name={name}",),
    )


COMMON_RULES = (missing_project_file, profile_not_found, dependency_error, generic_test_failure)
