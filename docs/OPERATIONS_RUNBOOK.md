# ASO-X Operations Runbook

## Status

Operational continuity guide for humans and automation agents.

## Start Here

A new contributor or automation agent should begin with:

bash
git status --short
git log --oneline -3
python -m pytest
python tools/governance_hardening_check.py

If `asoctl.py` supports equivalent commands, prefer the project entrypoint.

## Clean Sync Procedure

bash
git switch main
git fetch origin
git reset --hard origin/main
git status --short
git log --oneline -3

Expected:

- clean working tree
- HEAD, origin/main, and origin/HEAD aligned when appropriate

## Branch Procedure

bash
git switch main
git fetch origin
git reset --hard origin/main
git switch -c <topic-branch>

Rules:

- Do not push directly to protected main.
- Use PRs.
- Include validation evidence.
- Delete merged topic branches.

## CI Failure Triage

1. Identify failing workflow.
2. Identify contract test or command that failed.
3. Reproduce locally when possible.
4. Patch the smallest safe surface.
5. Run targeted tests.
6. Run full test suite when practical.
7. Record evidence in PR.

## Release Preflight

Minimum expected checks:

bash
git status --short
python -m pytest
python tools/governance_hardening_check.py

Future release tooling should include:

bash
python asoctl.py release preflight

## Rollback Guidance

Rollback should prefer:

- revert commits
- documented recovery commands
- decision log entries for strategic rollback
- preservation of audit trail

Avoid destructive history rewriting on shared branches.

## Artifact Retention

Critical artifacts should have:

- retention class
- provenance
- restore path
- validation evidence
- hash or manifest where practical

## Disaster Recovery

Minimum recovery path:

1. Clone repository from canonical remote.
2. Inspect latest main.
3. Run tests and governance checks.
4. Read project charter, roadmap, governance baseline, decision log, and operations runbook.
5. Restore artifacts according to retention documentation.