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





def compilation_error(data: DiagnosticInput) -> DiagnosticFinding | None:
    message = data.message.lower()
    if data.error_code != "COMPILATION_ERROR" and not any(
        signal in message for signal in (
            "compilation error",
            "jinja error",
            "undefined macro",
            "macro not found",
        )
    ):
        return None
    return _finding(
        "DBT-COMPILE-001", "dbt parsing or compilation failed", "compilation",
        "dbt reported a parsing, Jinja, or compilation failure; the exact cause needs the full error context.",
        "Compilation failures can originate from SQL syntax, Jinja expressions, macro resolution, project configuration, or invalid references. The headline alone does not distinguish these causes.",
        "Use the first actionable error in the full log, inspect the named file and line, and verify referenced macros, variables, and model/source names before changing SQL.",
        ("Run dbt parse to isolate project/Jinja parsing issues.", "Run the smallest affected model selection and inspect compiled SQL when compilation succeeds.", "Add a regression case for the specific failure."),
        "Keep representative dbt parse/build checks in CI and test shared macro changes against dependent models.",
        (f"error_code={data.error_code}" if data.error_code else f"message contains compilation signal: {data.message}",),
    )


def source_freshness_failure(data: DiagnosticInput) -> DiagnosticFinding | None:
    message = data.message.lower()
    if data.error_code != "SOURCE_FRESHNESS_FAILED" and not any(
        signal in message for signal in ("source freshness", "source is stale", "freshness check")
    ):
        return None
    return _finding(
        "DBT-SOURCE-001", "dbt source freshness check failed", "sources",
        "The configured freshness threshold was exceeded or the freshness check reported a failure.",
        "Freshness compares a configured source timestamp with the allowed age. This indicates stale or unverified input, not necessarily a failed downstream transformation.",
        "Inspect the source's configured loaded-at field and freshness thresholds, verify the upstream load completed, and check timezone/timestamp semantics before changing thresholds.",
        ("Run the relevant source freshness command again after verifying the upstream load.", "Inspect the source's loaded-at timestamp and configured warn_after/error_after values."),
        "Monitor upstream ingestion and alert on late loads; keep freshness thresholds aligned with the source's real delivery contract.",
        (f"error_code={data.error_code}" if data.error_code else f"message contains freshness signal: {data.message}",),
    )


def incremental_duplicates(data: DiagnosticInput) -> DiagnosticFinding | None:
    if data.details.get("duplicate_rows_observed") is not True:
        return None
    evidence = ["details.duplicate_rows_observed=true"]
    unique_key_configured = data.details.get("unique_key_configured")
    if unique_key_configured is True:
        evidence.append("details.unique_key_configured=true")
    elif unique_key_configured is False:
        evidence.append("details.unique_key_configured=false")
    return _finding(
        "DBT-INCR-001", "Duplicate rows observed in an incremental model", "incremental",
        "Duplicate rows were explicitly reported, but the root cause is not confirmed by the symptom alone.",
        "Common causes include an incorrect or missing unique_key, source duplicates, a merge key that does not match the model grain, or an incremental predicate that excludes existing rows. The correct cause depends on the model SQL, adapter strategy, and duplicate-key evidence.",
        "Compare the model's intended grain with unique_key, inspect duplicate source keys and compiled incremental SQL, then validate the adapter's incremental strategy. Do not add a key or run a full refresh blindly without checking semantics and data impact.",
        ("Capture duplicate key values and counts before changing the model.", "Inspect compiled SQL and the configured incremental strategy/unique_key.", "Run targeted uniqueness tests and compare row counts after a controlled validation run."),
        "Document model grain, test the intended unique key, and keep a regression fixture for repeated incremental runs.",
        tuple(evidence),
    )



def incremental_behavior_issue(data: DiagnosticInput) -> DiagnosticFinding | None:
    issue = data.details.get("incremental_issue")
    cases = {
        "missed_updates": (
            "Incremental run may be missing updates",
            "Evidence indicates expected updates were not reflected by an incremental run; the exact mechanism is not yet established.",
            "Inspect the incremental filter's time/key boundary, unique_key, strategy, and compiled SQL. Confirm whether updated source rows fall outside the selected window before changing predicates.",
            "Compare a bounded full-source result with the incremental result and test rows updated at the boundary.",
        ),
        "late_arriving_data": (
            "Late-arriving records may be excluded",
            "Evidence indicates late-arriving records are not present after an incremental run; the exact cause is not confirmed.",
            "Check the incremental lookback window, event time versus ingestion time, and source arrival delay. Expand the lookback only after measuring the source's lateness and duplicate impact.",
            "Add boundary fixtures for records arriving late and verify repeated incremental runs remain idempotent.",
        ),
        "wrong_unique_key": (
            "Incremental unique_key may not match model grain",
            "The supplied evidence says the configured unique_key does not represent the intended model grain; validate the grain and adapter behavior before changing it.",
            "Document the intended row grain, compare it with unique_key columns and null/duplicate behavior, then inspect compiled merge SQL for the active adapter.",
            "Add grain-level uniqueness tests and regression fixtures with multiple rows per business entity.",
        ),
    }
    if issue not in cases:
        return None
    title, diagnosis, fix, prevention = cases[issue]
    return _finding(
        "DBT-INCR-002", title, "incremental", diagnosis,
        "Incremental models process a subset of source data. Filters, key definitions, and adapter strategies can affect whether updates and late records are captured; the issue label alone does not prove a single root cause.",
        fix,
        ("Capture the model configuration and compiled SQL for the failing run.", "Compare source rows, incremental selection, and target rows for a small reproducible time/key window.", "Rerun a controlled test and check for missing rows and duplicates."),
        prevention,
        (f"details.incremental_issue={issue}",),
    )


def snapshot_issue(data: DiagnosticInput) -> DiagnosticFinding | None:
    issue = data.details.get("snapshot_issue")
    cases = {
        "missing_unique_key": (
            "Snapshot unique key is missing or invalid",
            "The supplied evidence identifies a missing or invalid snapshot unique key; the affected source grain still needs verification.",
            "Choose a stable, non-null key that uniquely identifies one source entity and validate it against the snapshot input before rerunning the snapshot.",
            "Test snapshot input key uniqueness and non-nullness before snapshot execution.",
        ),
        "updated_at_missing_or_null": (
            "Snapshot updated_at value is missing or null",
            "The snapshot strategy depends on an updated_at value, but evidence indicates the configured value is unavailable or null.",
            "Verify the configured updated_at column exists, is populated, and changes reliably when source rows change. Do not substitute a different column without validating semantics.",
            "Add source-level checks for the updated_at column and test a changed-row scenario.",
        ),
        "unexpected_history": (
            "Snapshot history differs from expectations",
            "Unexpected historical versions were observed; this does not by itself distinguish source changes, key instability, timestamp behavior, or snapshot configuration.",
            "Inspect the entity key, strategy, updated_at/check columns, and the affected rows' validity timestamps. Compare source changes with snapshot history before modifying or deleting history.",
            "Keep a small fixture covering unchanged rows, changed rows, and repeated snapshot runs.",
        ),
    }
    if issue not in cases:
        return None
    title, diagnosis, fix, prevention = cases[issue]
    return _finding(
        "DBT-SNAP-001", title, "snapshots", diagnosis,
        "Snapshot behavior depends on a stable entity key and the selected timestamp- or check-based strategy. The structured issue label is evidence to investigate, not proof of every underlying cause.",
        fix,
        ("Inspect the snapshot configuration and the relevant source rows.", "Run a controlled snapshot against representative unchanged and changed entities.", "Verify validity timestamps and history before considering any repair."),
        prevention,
        (f"details.snapshot_issue={issue}",),
    )


def schema_evolution_issue(data: DiagnosticInput) -> DiagnosticFinding | None:
    change = data.details.get("schema_change")
    cases = {
        "added_column": (
            "A new source column may not be propagated",
            "Evidence indicates a source column was added but is not present downstream; propagation depends on model SQL and materialization behavior.",
            "Compare source schema, model select list, materialization, and adapter-specific schema-change settings. Add the column explicitly where required and validate existing target data.",
            "Test source schema changes in a non-production target and document the intended column propagation policy.",
        ),
        "removed_or_renamed_column": (
            "A removed or renamed column may break downstream models",
            "Evidence indicates a referenced column was removed or renamed; downstream dependencies must be checked before changing models.",
            "Identify all references to the old column, confirm whether this is a rename or removal, and update dependent models in a coordinated change. Avoid assuming a rename is equivalent to a drop-and-add.",
            "Track schema contracts and run parse/build tests for downstream dependents when source schemas change.",
        ),
        "contract_mismatch": (
            "Model contract does not match the produced schema",
            "The supplied evidence indicates a mismatch between the declared contract and the model's produced columns or types.",
            "Compare contract column names and types with the compiled model output, correct the model or contract according to the intended interface, then validate the adapter's enforcement behavior.",
            "Keep contract checks in CI and review schema changes as interface changes.",
        ),
    }
    if change not in cases:
        return None
    title, diagnosis, fix, prevention = cases[change]
    return _finding(
        "DBT-SCHEMA-001", title, "schema_evolution", diagnosis,
        "Schema changes can affect model SQL, materializations, downstream references, and enforced contracts differently. This rule only runs when a recognized schema-change signal is explicitly supplied.",
        fix,
        ("Compare the source schema with the model's compiled output and target schema.", "Inspect dependent models and configured schema-change/contract behavior.", "Run parse and focused tests/builds in a safe target before deployment."),
        prevention,
        (f"details.schema_change={change}",),
    )


COMMON_RULES = (missing_project_file, profile_not_found, dependency_error, generic_test_failure, compilation_error, source_freshness_failure, incremental_duplicates, incremental_behavior_issue, snapshot_issue, schema_evolution_issue)
