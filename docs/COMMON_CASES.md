# Common-case coverage plan

This inventory distinguishes implemented signal-based diagnostics from cases still planned. A rule is not considered complete without positive, negative, and regression tests.

## Required contract for every rule

Every rule must detect a specific signal, diagnose only from supporting evidence, explain what the evidence does and does not prove, recommend a safe fix, give validation steps, and suggest prevention.

If evidence is missing or ambiguous, request more diagnostic evidence instead of inventing a root cause.

## Prioritized inventory

| Area | Common case | Status |
|---|---|---|
| Project setup | Missing `dbt_project.yml` | Implemented; requires project-root confirmation |
| Configuration | Profile name not found | Implemented |
| Parsing/compilation | Compilation/Jinja/macro-related failure | Implemented as general guidance; exact cause requires log context |
| Dependencies | Missing ref/source target or circular dependency | Implemented as signal-based guidance |
| Data quality | `unique`, `not_null`, `relationships`, `accepted_values` failures | Implemented as general guidance |
| Sources | Source freshness failure | Implemented as general guidance |
| Incremental models | Duplicate rows observed | Implemented; root cause is not assumed |
| Incremental models | Missed updates, late-arriving data, incorrect `unique_key` | Implemented when a recognized structured issue signal is supplied |
| Snapshots | Missing/invalid unique key, missing/null `updated_at`, unexpected history | Implemented when a recognized structured issue signal is supplied |
| Schema evolution | Added column not propagated, removed/renamed column, contract mismatch | Implemented when a recognized structured issue signal is supplied |
| Performance | Runtime regression, join row explosion, unexpectedly large scans | Implemented when a recognized structured issue signal is supplied; root cause is not assumed |
| Sources | Missing source / source definition | Planned |
| Packages/macros | Package resolution/version and specific macro compilation | Planned |
| Execution | Warehouse permission, connection, timeout, resource errors | Planned |
| CI/environment | Local vs CI profile, target, and environment differences | Planned |
| Performance | Spilling and adapter-specific query-profile interpretation | Planned |

## Current implementation boundary

The engine consumes structured evidence supplied by future parsers/adapters. It does not yet scan repositories, parse dbt artifacts, execute dbt commands, connect to Snowflake, or apply fixes. Structured issue labels must be produced from observed evidence by a caller; they must not be guessed from vague text. Do not describe this prototype as a complete troubleshooter.
