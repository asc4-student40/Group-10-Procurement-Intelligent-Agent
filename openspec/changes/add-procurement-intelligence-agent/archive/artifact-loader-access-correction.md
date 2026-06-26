# Artifact: Loader Access Correction (AI Oversight)

Date: 2026-06-26
Scope: Replace direct mock_data JSON access with centralized loader usage

## Front 2 Summary
A correction was applied after human feedback: procurement logic should load fixture data via
`data/loader.py` rather than reading `mock_data/*.json` directly in feature code.

## Why This Matters
- Enforces repository convention in .github/copilot-instructions.md
- Centralizes data access, validation boundary, and error handling
- Improves maintainability and test consistency

## Correction Applied
- Tool and agent pathways use loader functions:
  - load_budgets
  - load_vendors
  - load_policies
  - load_requests
- Runner script was updated to remove direct file read and use load_requests.

## Files Reflecting the Correction
- data/loader.py
- tools/budget.py
- tools/vendor_duplication.py
- tools/policy_compliance.py
- tools/risk_assessment.py
- agent.py
- tests/test_agent.py
- tests/test_policy_compliance.py
- run_all_requests.py

## Before vs After (Representative)
Before pattern:
- json.loads(Path("mock_data/requests.json").read_text(...))

After pattern:
- from data.loader import load_requests
- requests_data = load_requests()

## Validation Notes
- Data access is now centralized for core procurement pathways.
- This artifact records a human-guided correction to AI output and the final implementation state.

## AI-Assisted Development Evidence
This document is evidence for Category 5 showcase prompts:
- one Copilot suggestion corrected or redirected
- how generated code was validated against project conventions
