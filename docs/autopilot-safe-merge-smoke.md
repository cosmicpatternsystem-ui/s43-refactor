# Autopilot Safe Merge Smoke Test

This file records a live smoke test for the Autopilot Safe Merge workflow.

Scope:
- Verify workflow_dispatch availability on main.
- Verify guarded safe merge execution against a real PR.
- Verify audit-friendly repository state after automation.

Expected result:
- PR checks pass.
- Autopilot Safe Merge workflow merges the PR safely.
- main remains clean and autopilot readiness remains ready.