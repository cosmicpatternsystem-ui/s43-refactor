# ASO-X Policy Matrix

## Status

This document defines the minimum governance policy matrix for repository changes.

## Policy Principle

Every material change must be understandable, testable, and recoverable from repository state alone.

## Change Classes

| Change Type | Required Evidence | Required Checks | Required Documentation | Blocking Conditions |
|---|---|---|---|---|
| Roadmap change | Rationale and expected impact | Governance hardening check | `docs/ROADMAP.md`, decision log when strategic | Missing roadmap, missing rationale, silent milestone drift |
| Governance baseline change | Baseline state and reason | Governance enforcement tests | `docs/governance/GOVERNANCE_BASELINE.md` | Baseline mismatch, missing lock update |
| Lock schema change | Compatibility impact | Schema/registry validation | `LOCK_SCHEMA.json`, `LOCK_REGISTRY.json` | Schema changed without registry consideration |
| Release governance change | Release safety evidence | Release governance gate | Release governance workflow/docs | Missing release check command |
| Artifact retention change | Retention and restore evidence | Artifact retention gate | Retention workflow/docs | Missing retention class or restore path |
| Compatibility change | Runtime/platform impact | Test suite and hardening check | `COMPATIBILITY_CONTRACT.md` | Runtime drift without documentation |
| Commercial strategy change | Value and customer impact | Documentation review | `COMMERCIAL_MODEL.md`, decision log if strategic | Undefined customer/value change |
| Tooling change | Command behavior evidence | Unit tests | Tool help/docs when applicable | Breaking entrypoint without migration |
| CI workflow change | Local validation output | Targeted workflow tests | Workflow contract docs where applicable | Missing pinned runtime or required command |
| Documentation-only change | Scope statement | Governance hardening check when canonical | Updated canonical docs | Contradiction with canonical sources |

## Merge Discipline

A change should not be merged if it creates contradiction between:

- roadmap and baseline
- lock schema and lock registry
- workflows and documented governance
- compatibility contract and actual runtime usage
- commercial positioning and project charter
- decision log and strategic changes

## Evidence Standard

Evidence should be concrete and reproducible. Preferred evidence includes:

- pytest output
- governance audit output
- exact command lines
- affected file list
- PR checklist
- decision log entry where required

## Future Enforcement

This matrix is intentionally designed to become increasingly machine-enforced by repository tooling.
