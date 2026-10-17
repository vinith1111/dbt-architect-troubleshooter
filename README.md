# dbt Architect Troubleshooter

A deterministic, no-AI diagnostic tool for common dbt engineering problems.

## Principles

- No AI APIs or models.
- Evidence-based diagnosis. Never claim a root cause without supporting evidence.
- Prioritize common, recurring dbt problems before rare edge cases.
- Every diagnostic should aim to Detect, Diagnose, Explain, Fix, Validate, and Prevent.
- Keep changes on feature branches and validate with automated tests before opening a pull request.

## Initial milestone

Build a Python rule engine and automated tests for common dbt project issues. Start with a small, testable diagnostic framework, then expand coverage for compilation/configuration, dependencies, tests/data quality, incremental models, snapshots, and execution failures.

## Status

Project bootstrap. Implementation begins on a feature branch; this README commit exists on `main` because the repository was empty and needed an initial commit before a branch could be created.

## Scope boundaries

The tool can only diagnose cases for which it has rules and sufficient evidence. When evidence is missing or ambiguous, it must say so and return follow-up checks rather than inventing a root cause. It must not automatically apply production changes.


## Browser UI

A static, deterministic diagnostic interface lives in `docs/index.html`. It lets a user paste a dbt error, optionally select a known category, and review a diagnosis, recommended next steps, validation, and prevention guidance. The browser UI uses local JavaScript rules only: it does not send pasted text to a server or call AI APIs/models. The Python engine remains a separate implementation today; keeping the UI rule coverage aligned with the Python engine is a follow-up integration task.

### GitHub Pages

The `.github/workflows/pages.yml` workflow deploys `docs/` to GitHub Pages when changes are pushed to `main`. After merging the UI PR, if Pages is not already enabled, open **Settings → Pages** and set the build/deployment source to **GitHub Actions**. For private repositories, Pages availability depends on the GitHub plan and repository settings.
