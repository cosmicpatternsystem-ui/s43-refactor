# Phase 17 Quality Gate Emergency Fix - 20260614

## Reason

The enterprise quality gate failed with:

A parameter cannot be found that matches parameter name 'or'.

Root cause: PowerShell syntax error in the rebase-state check. The expression used Test-Path ... -or Test-Path ... without wrapping each Test-Path call in parentheses.

## Correct Syntax

if ((Test-Path ".git\rebase-merge") -or (Test-Path ".git\rebase-apply")) { ... }

## Runtime Race Observation

A validated auto snapshot commit appeared after the gate failure:

8bc5d3c Auto snapshot phase 17 validated work 20260614-092532
.auto_snapshot.lock
.gitignore
AUDIT/PHASE17_ENTERPRISE_AUTO_SNAPSHOT_HARDENING_20260614.md
ROADMAP_CANONICAL.md
tools/enterprise_quality_gate_phase17.ps1
tools/safe_auto_snapshot_phase17.ps1

This patch stops all auto snapshot workers, fixes the quality gate, validates the gate, commits only after PASS, and restarts a single hardened worker.

## Operational Rule

If the quality gate fails, auto snapshot must remain stopped until manual correction.
