# PROJECT OPERATING DOCTRINE

## Status

- Authority: Active
- Scope: Repository-wide
- Class: Commercial operating doctrine
- Durability target: 50 years
- Enforcement direction: Repository-first, automation-backed, artifact-retained

## Project Identity

- Project: ASO-X
- Standard: Enterprise grade
- Commercial posture: Real-money resilient
- Source of truth: Repository only
- Integration channel: GitHub pull requests
- Primary operational branch: `main`
- Execution spine: Governance, contracts, automation, artifacts, pull requests
- Control surface: `asoctl.py`
- Encoding baseline: UTF-8 without BOM
- Line ending baseline: LF
- Console safety: cp1252-safe stdout
- Write discipline: Atomic writes
- History posture: Immutable Git over informal/manual state

## Prime Directive

ASO-X operates as a repository-declared, automation-verified, artifact-retained commercial system. Policy must be durable. Automation must be explicit. Evidence must be retained. `main` must represent accepted truth.

## Non-Negotiables

- `main` is the protected accepted-truth branch.
- All material changes flow through pull requests.
- Repository content is the only authoritative project source.
- Audit-relevant automation must emit durable artifacts.
- Verification results must be deterministic, structured, and machine-readable where applicable.
- Merge readiness must be verifiable before acceptance.
- Safe concurrent edits must be preserved by design.
- Atomic write discipline is required for generated durable files.
- UTF-8 without BOM and LF are required for durable text artifacts.
- Manual operational knowledge must be converted into repository truth when it becomes repeatable.
- No silent drift is allowed between governance, contracts, automation, artifacts, and `main`.
- Real-money resilience takes priority over convenience.
- Ambiguous policy is not production-grade policy.
- Unretained evidence is not durable evidence.
- Unreviewed branch state is not accepted project truth.

## Decision Authority

- Governance documents define policy truth.
- Contract files define machine-checkable truth.
- `asoctl.py` implements operational truth.
- Retained artifacts provide audit evidence.
- Pull request review finalizes acceptance.
- `main` contains the latest accepted project truth.

## Execution Spine

1. Governance defines the rule.
2. Contracts express the verifiable requirement.
3. Automation checks the requirement.
4. Artifacts retain the evidence.
5. Pull requests integrate accepted change.
6. `main` becomes the accepted sentence of the project.

## Current Safe Merge Baseline

- Safe Merge governance baseline is established.
- Pull request enforcement baseline is established.
- Required check registration baseline is established.
- `asoctl.py safe-merge verify` is the baseline verification command.
- Safe Merge verification emits structured JSON.
- Audit artifacts are retained under `artifacts/audits/safe-merge/`.
- Branch cleanup is part of completion.
- `main` and `origin/main` alignment is part of final acceptance.

## Definition Of Done

A project change is done only when all applicable conditions are true:

- Code or documentation is merged into `main`.
- `main` is synchronized with `origin/main`.
- Working tree is clean.
- Required verification commands pass.
- Required audit artifacts are retained when applicable.
- Feature branches are deleted or pruned after completion.
- Governance state, contract state, automation state, artifact state, and repository state agree.
- The accepted state is reproducible from repository content.

## Repository Unity Rule

The project is one-voice only when:

- Governance says the same thing as contracts.
- Contracts say the same thing as automation.
- Automation says the same thing as retained evidence.
- Retained evidence supports the accepted repository state.
- `main` contains the accepted truth.

If any of these disagree, the project is not unified.

## Commercial Severity Rule

Money is unforgiving. The system must prefer explicit failure over ambiguous success, durable evidence over memory, automation over ritual, and repository truth over conversation.

## Operating Statement

ASO-X operates through repository-declared governance, contract-backed automation, durable audit evidence, and pull-request-controlled integration into `main`.

The repository is the voice.

`main` is the accepted sentence.

Automation is the proof.

Artifacts are the memory.
