# Work Protocol

This document defines the mandatory operating protocol for professional continuation.

## Start Protocol

Before work starts:

1. ensure clean working tree
2. switch to the intended base branch
3. pull with fast-forward only
4. create a focused branch
5. read canonical governance files
6. identify roadmap impact
7. identify contract impact

## Change Protocol

Every material change must answer:

- What goal does this serve?
- Which roadmap item does this affect?
- Which contract does this change?
- Which validation proves it?
- Which documentation must remain synchronized?
- Is there compatibility risk?
- Is there commercial or operational impact?

## Validation Protocol

At minimum, governance changes must run:

- `python tools/governance_hardening_check.py`
- `python tools/project_constitution_check.py`
- `python -m pytest tests/test_governance_hardening_pack.py tests/test_project_constitution_pack.py -q`

## PR Protocol

Every PR should be focused, reviewable, and reversible.

A PR should not mix unrelated governance, product, commercial, and refactor changes unless the roadmap explicitly requires a coordinated change.

## Merge Protocol

Before merge:

- local validation must pass
- CI must pass
- roadmap and docs must be synchronized
- source-of-truth conflicts must be absent
- branch must be mergeable

After merge:

- switch to `main`
- pull with `--ff-only`
- verify clean status
- delete completed branches when appropriate

## Agent Protocol

Any agent must operate from repository state, not assumptions.

If a required rule is missing, the agent should propose adding the rule before making broad changes.

## Failure Protocol

If validation fails, fix the validator-reported cause before proceeding.

Do not bypass governance gates unless a documented emergency protocol exists.

## Work Protocol Compliance Terms

- Required governance phrase: pull request
