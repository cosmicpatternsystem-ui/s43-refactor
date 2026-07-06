# ASO-X Project Charter

## Status

This document is a canonical governance artifact for ASO-X.

## Mission

ASO-X exists to become a durable, enterprise-grade, globally relevant financial intelligence and governance system that can survive long-term technical, organizational, and market change.

The repository must function as the source of truth. No operating decision may depend on chat memory, private assumptions, or undocumented external context.

## 50-Year Thesis

ASO-X is designed for long-horizon durability. The project should remain understandable, auditable, portable, extensible, and commercially useful across changing hardware, software, platforms, teams, and automation agents.

## Non-Negotiables

- The repository is the source of truth.
- Governance must be documented and enforceable.
- Critical decisions must be recorded.
- CI must reject unsafe drift where practical.
- Files must use BOM-free UTF-8 with LF line endings.
- Automation must prefer deterministic, repeatable behavior.
- Writes must be atomic where project tooling modifies files.
- Human and AI contributors must be able to continue work from repository artifacts alone.
- Release and artifact retention rules must remain explicit.
- Commercial viability must be treated as a first-class design constraint.

## Strategic Identity

ASO-X is not only a codebase. It is a long-term operating system for durable financial intelligence, governance, artifact retention, and automation discipline.

## Success Metrics

- A new contributor can understand the current project state from repository files.
- A new automation agent can identify canonical documents without chat history.
- CI detects missing governance artifacts.
- Roadmap, baseline, compatibility, release, and retention artifacts remain aligned.
- The project remains portable and recoverable.
- Enterprise adoption can be supported by clear governance, auditability, and operating controls.

## Anti-Goals

- Hidden decision-making.
- Chat-memory dependency.
- Untracked governance changes.
- Silent roadmap drift.
- Unclear release authority.
- Unbounded dependency sprawl.
- Platform lock-in without documented rationale.
- Commercial ambiguity.

## Protected Invariants

- Governance artifacts must not be removed without replacement and decision-log evidence.
- Canonical source mapping must remain machine-readable.
- Compatibility policy must remain explicit.
- Release governance and artifact retention must remain CI-visible.
- Any major strategic change must update the decision log.

## Continuity Rule

Every future session, contributor, or automation agent must begin from repository state, not conversation memory.