# Phase 22 Sanitized AI Audit Evidence Policy

Status: DRAFT FOR AUDIT REVIEW
Phase: 22.2
Scope: Repo-safe policy and template for sanitized AI audit evidence
Source Of Truth: Repository files only
Production Release: BLOCKED WITHOUT APPROVAL
Destructive Automation: BLOCKED
Secrets Handling: DO NOT STORE OR PRINT SECRETS

## Purpose

This policy defines how local `AI_AUDIT/` evidence may be converted into commit-ready summaries without committing raw provider output, local private metadata, secrets, or unsafe command examples. Raw `AI_AUDIT/` artifacts remain local evidence unless a sanitized summary is created under `AUDIT/` and reviewed.

## Source Material

Allowed source material for a sanitized summary:

- Local `AI_AUDIT/` file names and high-level categories.
- Roadmap event names and high-level event type.
- Current repository sync state summarized without local absolute paths.
- Classification outcomes from a deferred artifact audit.

Disallowed source material for direct commit:

- Raw `AI_AUDIT/` JSON files.
- Raw `AI_AUDIT/` markdown provider outputs.
- Full prompts or full model responses.
- Unredacted local state snapshots.
- Unredacted roadmap event JSON files.

## Mandatory Exclusions

A sanitized summary must exclude:

1. Local absolute paths, including workstation, mount, home, or drive paths.
2. Raw prompts.
3. Raw provider responses.
4. Provider endpoints or model metadata when sensitive or unnecessary.
5. Token usage metadata, including prompt, completion, cached, input, or output token counts.
6. Bearer tokens, API keys, credentials, passwords, private keys, or authorization headers.
7. Unsafe rollback, destructive, or history-rewriting command examples.
8. File contents from deferred bridge or supervisor tools.
9. Customer, account, ledger, payment, identity, or other regulated data.
10. Any value whose sensitivity is unknown.

## Allowed Sanitized Fields

A commit-ready sanitized summary may include only:

- Phase id.
- Timestamp rounded or normalized to date or minute precision.
- High-level action type, such as status review, release dry-run review, roadmap event, or state snapshot.
- Repo sync state as a non-sensitive summary, such as synced, ahead, behind, or diverged.
- File categories, not raw content.
- Count of files by category, when useful.
- Final decision: `SAFE_TO_COMMIT`, `NEEDS_REDACTION`, or `KEEP_DEFERRED`.
- Review owner or role, if non-sensitive.
- Stop condition category, if any.

## Classification Rules

### SAFE_TO_COMMIT

Use only when the artifact contains no raw prompts, raw responses, local paths, secrets, provider-sensitive metadata, unsafe command examples, or private operational details.

### NEEDS_REDACTION

Use when the artifact could become commit-ready after removing local paths, raw prompt/response fields, provider metadata, token usage, unsafe command examples, or other private data.

### KEEP_DEFERRED

Use when the artifact is raw provider output, requires network/secret context, contains command examples that could be unsafe if copied, or cannot be safely summarized without human review.

## Sanitization Procedure

1. Read the roadmap files before reviewing evidence.
2. Confirm `main` is synchronized with `origin/main`, unless an approved branch workflow is active.
3. Inventory candidate `AI_AUDIT/` files by path, size, and category only.
4. Classify each raw file without copying raw content.
5. Create a new sanitized summary under `AUDIT/` only when the required exclusions can be honored.
6. Validate markdown structure.
7. Stop before staging or committing until explicit approval is provided.

## Sanitized Summary Template

```text
# Sanitized AI Audit Summary

Status: DRAFT FOR AUDIT REVIEW
Phase: <phase-id>
Source Evidence Category: <status-review|release-review|roadmap-event|state-snapshot|other>
Normalized Timestamp: <YYYY-MM-DD or YYYY-MM-DDTHH:MMZ>
Repo Sync Summary: <synced|ahead|behind|diverged|unknown>
Raw Evidence Committed: NO

## Evidence Categories

- <category>: <count or short description without raw content>

## Exclusions Applied

- Local absolute paths removed: YES
- Raw prompts removed: YES
- Raw provider responses removed: YES
- Provider endpoint/model metadata removed or minimized: YES
- Token usage metadata removed: YES
- Credentials and authorization material removed: YES
- Unsafe destructive command examples removed: YES

## Classification

Final Decision: <SAFE_TO_COMMIT|NEEDS_REDACTION|KEEP_DEFERRED>
Reason: <brief audit-safe rationale>

## Review Notes

- <short non-sensitive note>
```

## Commit Readiness Checklist

Before staging a sanitized summary, verify:

1. The raw `AI_AUDIT/` source files are not staged.
2. Deferred bridge/supervisor scripts are not staged unless separately approved.
3. No local absolute paths remain.
4. No raw prompt or response text remains.
5. No token usage fields remain.
6. No provider endpoint, model metadata, or API metadata remains unless explicitly needed and non-sensitive.
7. No unsafe destructive command examples remain.
8. Markdown fences are balanced.
9. The roadmap still authorizes the work.
10. Human approval is recorded before staging and committing.

## Final Rule

Raw AI audit evidence remains local. Only sanitized, reviewable summaries under `AUDIT/` may become commit candidates.
