# Architecture

Current flow: structured evidence -> deterministic Python rules -> findings with evidence and next steps, or a request for more evidence.

## Constraints

- No AI APIs, hosted models, local models, embeddings, or probabilistic inference.
- Identical inputs must produce identical results.
- Findings include evidence and validation steps.
- Unknown or ambiguous cases do not produce a confident diagnosis.
- Initial release is advisory only; it does not modify projects or execute warehouse changes.
- Parsers for project files, dbt artifacts, logs, and adapter-specific evidence are separate layers.

## Planned layers

1. Evidence collectors for project files, manifest.json, run_results.json, compiled SQL, logs, config, and user context.
2. Parsers and normalizers that preserve unknown/missing values.
3. Rule engine evaluating explicit rules against normalized facts.
4. Findings with diagnosis, evidence, fix, validation, and prevention.
5. Test corpus of known incidents, negative cases, and regression examples.
6. CLI/interface only after core rules and coverage contracts are reliable.
