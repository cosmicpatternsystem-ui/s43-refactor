# Phase 21 Autonomous Operation Governance

Status: DRAFT FOR AUDIT REVIEW
Phase: 21
Scope: Governance for repository-aware autonomous operation
Production Release: BLOCKED WITHOUT APPROVAL
Destructive Automation: BLOCKED
Secrets Handling: DO NOT STORE OR PRINT SECRETS

## Purpose

This artifact defines governance rules for autonomous or AI-assisted repository operations. It applies to local scripts, AI supervisor tooling, dry-run release automation, sync verification, audit artifact generation, and any future workflow that may influence financial-system operations.

## Governance Objectives

1. Keep repository automation non-destructive by default.
2. Require explicit approval before any state-changing or externally visible action.
3. Preserve a reproducible audit trail for every operational decision.
4. Prevent secrets exposure through prompts, logs, generated files, or command output.
5. Detect local and remote synchronization risk before release or closure decisions.
6. Distinguish advisory AI output from reviewed operational authority.
7. Define stop conditions that cause automation to fail closed.

## Authority Model

### Advisory Authority

AI-generated outputs and supervisor reports are advisory. They may identify risks, summarize evidence, draft runbooks, and propose next steps. They do not approve releases, financial changes, production changes, or phase closure.

### Deterministic Tool Authority

Scripts may produce pass/fail results when their checks are deterministic and auditable. A script failure blocks automation until reviewed. A script pass does not replace required human approval.

### Human Approval Authority

Only a designated operator, repository steward, release manager, or compliance owner may approve:

- Commits and pushes.
- Pull requests and merges.
- Releases and tags.
- Production deployments.
- Rollbacks.
- Financial-impacting operations.
- Secrets or access-control changes.
- Phase closure.

## Allowed Phase 21 Autonomous Activities

The following activities are allowed in Phase 21 when they remain local and non-destructive:

1. Read repository files.
2. Read Git metadata.
3. Generate audit documents in approved Phase 21 paths.
4. Run Python syntax checks.
5. Run sync verification that does not fetch, push, checkout, reset, clean, delete, or modify files.
6. Produce dry-run designs and simulated action lists.
7. Report risks, blockers, missing evidence, and stop conditions.

## Forbidden Phase 21 Autonomous Activities

The following activities are forbidden without explicit approval and are not authorized by this artifact:

1. `git add`, `git commit`, `git push`, `git pull`, `git reset`, `git checkout`, `git clean`, branch deletion, or tag creation.
2. Production deploy, package publish, release publish, or artifact upload.
3. Database migration, ledger mutation, balance change, payment action, or account-state change.
4. Secret creation, printing, copying, rotation, storage, or request.
5. Branch protection, CI rule, environment, or access-control modification.
6. Deletion of audit evidence or generated artifacts.
7. Any network action that mutates a remote system.

## Required Preflight For Autonomous Workflows

Before any autonomous workflow writes local audit artifacts or proposes release readiness, it must record:

- Repository path.
- Current branch.
- Current commit.
- Working tree status.
- Upstream branch.
- Ahead and behind counts.
- Remote tracking availability.
- Known untracked files.
- Whether the workflow is read-only, local-write, or external-write.

For Phase 21, external-write workflows are not allowed.

## Working Tree Policy

A clean working tree is required for release, closure, or production-impacting decisions. During artifact drafting, an intentionally dirty working tree may be acceptable only when:

1. The dirty state is limited to known Phase 21 audit or tooling files.
2. The operator has inspected existing untracked files before editing.
3. The final report lists all created or modified paths.
4. No destructive command is used to clean the tree.

## Local and Remote Sync Policy

A workflow must stop if:

- No upstream branch is configured.
- Remote tracking state is unavailable.
- The local branch is behind upstream.
- The local branch is ahead of upstream and the workflow requires published state.
- The local and upstream branch have diverged.
- The working tree is dirty and the workflow does not explicitly allow local dry-run artifacts.

A documented dry-run condition may allow ahead or dirty state only for local artifact generation. That allowance must never imply release readiness or commit readiness.

## AI Prompt and Output Controls

AI-assisted workflows must:

1. Avoid including secrets, tokens, credentials, private keys, or customer-sensitive data in prompts.
2. Redact suspected secret-bearing lines before transmission or storage.
3. State uncertainty when repository context is incomplete.
4. Avoid claiming that checks passed unless command output supports the claim.
5. Save AI outputs as advisory artifacts, not authoritative approvals.
6. Preserve raw enough context for audit without exposing secrets.

## Stop Conditions

Automation must stop and report failure when any of the following are detected:

1. Unexpected branch.
2. Missing upstream.
3. Behind or divergent branch state.
4. Dirty tree outside documented local dry-run scope.
5. Secret-looking material in generated artifacts.
6. Missing required audit artifact for the intended gate.
7. Failed syntax, lint, unit, or policy check relevant to the workflow.
8. Attempt to run a forbidden command.
9. Ambiguous operator instruction that could cause destructive or external mutation.
10. Any uncertainty about whether a command is safe.

## Evidence Requirements

Every governance-relevant run should produce or reference:

- The command or tool name.
- The exact mode or arguments.
- Start condition.
- End condition.
- Pass/fail result.
- Stop condition, if any.
- Files created or modified.
- Human approval record, if required.

## Review Cadence

Governance artifacts should be reviewed when:

- A new autonomous capability is introduced.
- A script gains write capability.
- Release policy changes.
- Branch protection or CI requirements change.
- Financial-system scope changes.
- An incident, rollback, or near miss occurs.

## Phase 21 Implementation Notes

The Phase 21 sync verifier must remain non-destructive and may only inspect local repository metadata. It should fail closed for dirty, missing-upstream, behind, ahead, or divergent state unless a documented dry-run flag explicitly allows the state for local review.

## Final Rule

Autonomy may recommend. Deterministic tooling may block. Humans approve.
