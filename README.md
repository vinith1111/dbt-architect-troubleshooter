# dbt Architect Troubleshooter

A deterministic, no-AI diagnostic tool and learning site for common dbt engineering problems.

## What is included

- A Python rule engine with structured diagnostic inputs and findings.
- Signal-based guidance for common project setup, configuration, compilation, dependencies, data quality, incremental model, snapshot, schema evolution, and performance problems.
- A static browser interface for guided troubleshooting, plus SQL, Python, Snowflake, dbt, and AWS learning roadmaps.
- 29 dbt lessons with Beginner, Intermediate, and Advanced levels, English/Tinglish explanations, examples, and practice.
- Automated Python tests and Playwright browser smoke tests.

## Design principles

- No AI APIs, model APIs, or network calls in the diagnostic engine.
- Evidence before diagnosis. A symptom or label alone must not be presented as a confirmed root cause.
- Every diagnostic should Detect, Diagnose, Explain, Fix, Validate, and Prevent.
- Prioritize common, recurring dbt problems before rare edge cases.
- Work on feature branches and validate changes before opening a pull request.

## Current limitations

This is a prototype, not yet a fully automated production troubleshooter.

- The Python engine consumes structured evidence supplied by a caller. It does not automatically scan a dbt repository or parse dbt logs/artifacts.
- It does not execute dbt commands, connect to Snowflake, or apply production fixes.
- Browser-side rules and the Python engine are separate implementations; their coverage is not yet generated from a shared rule catalog.
- Some diagnostic areas provide general guidance rather than identifying a precise cause from parsed logs.

For performance diagnostics, provide the recognized performance_issue plus the measurements required by that case. Runtime comparisons also require comparable_input_volume: true. A finding means the measurements support the reported regression, not that the tool has proven the root cause.

## Local development

Requires Python 3.10 or newer. The CI currently tests with Python 3.12 and Node.js 22.

```bash
python -m pip install -e ".[dev]"
python -m pytest
npm install --no-save playwright
npx playwright install chromium
node tests/browser-smoke.mjs
```

The browser smoke test opens local HTML files and does not require a running web server.

## Browser UI and GitHub Pages

The static site is in docs/. The GitHub Pages workflow is .github/workflows/pages.yml and deploys the site from GitHub Actions when changes are pushed to main. If deployment is not enabled, configure Settings → Pages → GitHub Actions. Pages availability for private repositories depends on the GitHub plan and repository settings.

## Contributing safely

1. Create a feature branch from main.
2. Add positive, negative, and regression tests for each new rule.
3. Run the Python and browser smoke tests.
4. Open a pull request and merge only after reviewing the diff and checks.
