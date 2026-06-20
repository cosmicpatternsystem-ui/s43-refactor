# Phase 22 Deferred Files Manifest

Status: DRAFT FOR AUDIT REVIEW
Phase: 22.5
Scope: Commit-safe manifest for deferred local artifacts and tools
Source Of Truth: Repository files only
Production Release: BLOCKED WITHOUT APPROVAL
Destructive Automation: BLOCKED
Secrets Handling: DO NOT STORE OR PRINT SECRETS

## Purpose

This manifest records deferred local artifacts using sanitized metadata only. It does not include raw file contents, prompts, responses, credentials, local absolute paths, provider metadata, token metadata, or executable remediation commands.

## Manifest Rules

- Do not read or copy raw sensitive content from deferred files.
- Do not stage deferred files through directory-level staging.
- Do not commit raw `AI_AUDIT/` artifacts.
- Do not execute deferred bridge or supervisor tools.
- Do not infer approval from chat history.
- Keep disposition changes approval-gated and repo-recorded.

## Deferred File Manifest

| File/Path Identifier | Current Disposition | Reason Category | Required Approval Gate | Commit Policy |
| --- | --- | --- | --- | --- |
| `AI_AUDIT/` | KEEP_DEFERRED | Raw local AI evidence and state events | Sanitized evidence policy plus human review | Do not commit raw directory; commit only sanitized summaries under `AUDIT/` |
| `tools/ai/bridge_claude.py` | KEEP_DEFERRED | Network bridge, environment credential use, raw provider output risk | Network approval, secret-handling approval, redaction approval, safety-policy review | Do not commit until tool defaults to no network/no artifact write and approval artifact exists |
| `tools/ai/bridge_claude_repo.py` | KEEP_DEFERRED | Repo-context network bridge, subprocess inspection, prompt construction risk | Network approval, repository-context sharing approval, secret-handling approval, redaction approval | Do not commit until prompt construction and redaction are deterministic and approval-gated |
| `tools/ai/s43_supervisor.py` | KEEP_DEFERRED | Supervisor workflow, network call capability, artifact-writing capability | Network approval, artifact-writing approval, secret-handling approval, no-save/default-safe review | Do not commit until artifact writing and network behavior are disabled by default or explicitly approved |

## Allowed Sanitized Metadata

The manifest may include only:

- File or path identifier.
- Current disposition.
- Reason category.
- Required approval gate.
- Commit policy.
- High-level tool category.
- Non-sensitive review status.

## Prohibited Manifest Content

The manifest must not include:

- Raw prompts.
- Raw model responses.
- API keys, tokens, bearer material, credentials, or authorization values.
- Local absolute paths.
- Provider endpoints or sensitive model metadata.
- Token usage metadata.
- Full environment data.
- File contents from deferred tools or raw evidence.
- Unsafe destructive command examples.

## Disposition Definitions

### SAFE_TO_COMMIT

The file is commit-ready after review and contains no prohibited content.

### NEEDS_REDACTION

The file may become commit-ready after removing prohibited content and passing leak checks.

### KEEP_DEFERRED

The file remains local and untracked until a separate approval gate and safety review authorize a change in disposition.

## Approval Gate Summary

Before any deferred file changes disposition:

1. The roadmap must authorize the review.
2. `main` must be synchronized with `origin/main`, unless an approved branch workflow is active.
3. A commit-safe approval artifact must describe the exact file path and approval scope.
4. Network, secret, subprocess, artifact-writing, and repository-context-sharing risks must be classified.
5. Sanitized summaries must pass leak checks.
6. Raw evidence must remain excluded unless explicitly sanitized.
7. Human approval must be recorded before staging.

## Current Recommendation

All listed deferred files remain `KEEP_DEFERRED`. The next safe objective is to design approval-gated hardening for AI bridge/supervisor tools or enforce sanitized evidence generation as the only commit path for local AI audit evidence.
