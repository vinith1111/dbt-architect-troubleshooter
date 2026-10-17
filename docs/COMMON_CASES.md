# Common-case coverage plan

This is an inventory, not a claim that every case is implemented. Add positive, negative, and regression tests before marking any case covered.

## Required contract for every rule

Every implemented rule must Detect a specific signal, Diagnose only from supporting evidence, Explain what the evidence proves and does not prove, recommend a safe Fix, give steps to Validate the fix, and suggest how to Prevent recurrence.

If evidence is missing or ambiguous, ask for more diagnostic evidence instead of inventing a root cause.

## Prioritized inventory

| Area | Common case | Initial status |
|---|---|---|
| Project setup | Missing dbt_project.yml | Implemented with project-root confirmation |
| Configuration | Profile name not found | Implemented |
| Parsing/compilation | Compilation/Jinja/macro-related failure signal | Implemented as general guidance; exact cause still needs evidence |
| Dependencies | Missing ref/source target or circular dependency | Initial signal-based rule implemented |
| Data quality | unique, not_null, relationships, accepted_values failures | Implemented as general guidance |\n| Sources | Source freshness failure | Implemented as general guidance |\n| Incremental models | Duplicate rows observed | Implemented as evidence-gated diagnostic; root cause not auto-assumed |
| Sources | Source missing | Planned |
| Incremental models | Wrong unique_key, missed updates, late-arriving data | Planned |
| Snapshots | Unique-key, strategy, updated_at, unexpected history | Planned |
| Schema evolution | Added, removed, renamed columns and contract mismatch | Planned |
| Packages/macros | Package resolution/version and macro compilation | Planned |
| Execution | Warehouse permission, connection, timeout, resource errors | Planned |
| CI/environment | Local vs CI profile, target, and environment differences | Planned |
| Performance | Expensive scans, joins, spilling, warehouse sizing | Planned |

## Current implementation boundary

The engine consumes structured evidence supplied by future parsers/adapters. It does not yet scan repositories, parse dbt artifacts, execute dbt commands, connect to Snowflake, or apply fixes. Do not describe this prototype as a complete troubleshooter.
