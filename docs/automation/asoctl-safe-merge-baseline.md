# asoctl Safe Merge Baseline

## Objective
Define the baseline command contract for Safe Merge verification in `asoctl.py`.

## Proposed command
- `python asoctl.py safe-merge verify`

## Minimum outputs
- process exit code suitable for CI gating
- machine-readable JSON decision artifact
- deterministic summary for audit capture
- explicit failure reason when verification does not pass

## Minimum inputs
- repository root working tree
- current branch and target branch context
- Safe Merge contract data from `repo/contracts/SAFE_MERGE_AUTOMATION_SPEC.yaml`
- hosted/local checker results when available

## Required artifact expectations
- immutable audit-oriented JSON output
- timestamped execution record
- decision field with pass or fail state
- reason list for every rejection path
- stable schema suitable for long-term retention

## Non-goals for baseline
- merge execution
- branch protection mutation
- approval management
- auto-remediation
- bypassing repository protection rules

## Integration constraints
- preserve PR-only governance
- keep output BOM-free UTF-8
- support deterministic automation and audit retention
- avoid non-deterministic mutation during verification
- make failure states explicit and machine-readable
- keep verification separate from merge execution

## Initial decision schema
```json
{
  "schema": "aso.safe_merge.verify.v1",
  "decision": "pass",
  "reasons": [],
  "checks": [],
  "artifacts": [],
  "repository": {
"branch": "",
"target": "main",
"head": ""
  }
}

## Baseline acceptance criteria
- command contract is documented before implementation
- implementation must not perform a merge
- implementation must not mutate branch protection or repository rulesets
- implementation must return non-zero exit code on failed verification
- implementation must support audit artifact generation in a deterministic path
- implementation must preserve PR-only governance