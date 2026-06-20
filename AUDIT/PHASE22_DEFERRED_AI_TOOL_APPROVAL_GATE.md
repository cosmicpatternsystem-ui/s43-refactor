# Phase 22 Deferred AI Tool Approval Gate

Status: DRAFT FOR AUDIT REVIEW
Phase: 22.4
Scope: Approval gate for deferred AI bridge and supervisor tooling
Source Of Truth: Repository files only
Production Release: BLOCKED WITHOUT APPROVAL
Destructive Automation: BLOCKED
Secrets Handling: DO NOT STORE OR PRINT SECRETS

## Purpose

This policy defines the approval gate required before deferred AI bridge or supervisor tools can be committed, executed, or adopted into the repository control plane. It is commit-safe documentation only. It does not approve execution of deferred tools, network calls, artifact writes, secret use, staging, commits, pushes, or production actions.

## Deferred Tool Categories

### Network Bridge Tools

Tools that can call an external AI or API service, transmit prompts, or use credentials from environment variables.

Current deferred examples:

```text
tools/ai/bridge_claude.py
tools/ai/bridge_claude_repo.py
```

### Supervisor Tools

Tools that can collect repository context, call an external AI or API service, and write local audit artifacts.

Current deferred example:

```text
tools/ai/s43_supervisor.py
```

### Raw AI Audit Artifacts

Local evidence files that may contain prompts, provider responses, local paths, provider metadata, or token metadata.

Current deferred category:

```text
AI_AUDIT/
```

## Approval Requirements

Before any deferred AI tool can be committed or executed, the following approvals are required:

1. Network approval for any external request.
2. Secret-handling approval for any environment variable, credential, token, or authorization header usage.
3. Data-sharing approval for any repository context sent to an external service.
4. Artifact-writing approval for any tool that writes under `AI_AUDIT/`, `AUDIT/`, or other repository paths.
5. Redaction approval confirming raw prompts, raw responses, provider metadata, token metadata, and local paths are not committed.
6. Safety-policy approval confirming the tool cannot stage, commit, push, reset, clean, delete branches, force push, or mutate production systems.
7. Human review approval before staging or committing the tool.

Approval must be explicit, task-scoped, and recorded in a commit-safe audit artifact. Approval must not be inferred from prior chat context.

## Prohibited Contents

Deferred tools and related artifacts must not be committed if they contain or emit:

- Raw prompts.
- Raw provider responses.
- API keys, bearer tokens, credentials, passwords, private keys, authorization headers, or secret values.
- Local absolute paths.
- Provider endpoints or model metadata when unnecessary or sensitive.
- Token usage metadata.
- Full environment dumps.
- File contents from private or sensitive repository files.
- Unsafe rollback, destructive, history-rewriting, branch deletion, or force-push command examples.
- Production deployment, release, migration, payment, ledger, account, identity, or infrastructure mutation instructions.

## Allowed Sanitized Metadata

A commit-ready approval artifact may include only:

- Tool path.
- Tool category.
- High-level purpose.
- Whether network access is required.
- Whether secrets are required.
- Whether artifact writing is required.
- Whether subprocesses are used.
- Whether repository mutation is possible.
- Required approval gates.
- Final classification: `SAFE_TO_COMMIT`, `NEEDS_REDACTION`, or `KEEP_DEFERRED`.
- Reviewer role and approval timestamp, if non-sensitive.

## Pre-Commit Checklist

Before staging any deferred AI tool, verify:

1. The roadmap authorizes the review.
2. `main` is synchronized with `origin/main`, unless an approved branch workflow is active.
3. The raw `AI_AUDIT/` directory is not staged.
4. No deferred tool is staged accidentally as part of a directory add.
5. No local absolute paths are present in committed content.
6. No raw prompts or provider responses are present in committed content.
7. No credentials, tokens, bearer material, or authorization values are present.
8. No token usage metadata is present.
9. No unsafe destructive command examples are present.
10. Any network, secret, subprocess, and artifact-writing behavior is explicitly documented.
11. The tool defaults to safe behavior: no network call and no artifact write unless explicitly approved.
12. Syntax validation uses no-artifact `ast.parse`, not bytecode-producing validation.
13. Generated summaries are sanitized and pass leak checks.
14. Human approval is recorded before staging and committing.

## Post-Approval Adoption Workflow

If a deferred AI tool receives approval, adoption proceeds in this order:

1. Create or update a commit-safe approval artifact under `AUDIT/`.
2. Refactor the tool, if needed, so network calls and artifact writes are disabled by default.
3. Add explicit dry-run, no-save, or show-context modes where applicable.
4. Add deterministic redaction before any prompt construction or artifact write.
5. Add safety-policy checks for blocked repository mutation commands.
6. Validate with `ast.parse` and no cache artifacts.
7. Generate sanitized evidence only, never raw provider output.
8. Stage exact file paths only after approval.
9. Commit through a protected PR workflow.
10. Keep raw local evidence deferred unless separately sanitized.

## Stop Conditions

Stop and keep the tool deferred if:

- Approval is missing or ambiguous.
- Any raw prompt or raw provider response would be committed.
- Any credential-like value is present.
- Any local absolute path remains.
- The tool requires network access without an approval model.
- The tool writes artifacts by default.
- The tool can mutate Git, production systems, releases, secrets, or financial state.
- Validation creates cache or bytecode artifacts.

## Final Rule

Deferred AI tools remain local and uncommitted until a documented approval gate proves they are safe, sanitized, non-destructive by default, and compatible with the repository living roadmap.
