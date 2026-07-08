# Agent Entrypoint

This repository must be operated from repository evidence only.

Every new session, human operator, automation agent, or AI assistant must begin here before making project decisions.

## Mandatory Read Order

1. `AGENT_ENTRYPOINT.md`
2. `PROJECT_CHARTER.md`
3. `docs/governance/GOAL_CONSTITUTION.md`
4. `docs/governance/SOURCE_OF_TRUTH_HIERARCHY.md`
5. `repo/contracts/PROJECT_CONSTITUTION.yaml`
6. `repo/contracts/CANONICAL_SOURCES.yaml`
7. `repo/roadmap/roadmap.yaml`
8. `docs/ROADMAP.md`
9. `docs/governance/POLICY_MATRIX.md`
10. `docs/governance/WORK_PROTOCOL.md`
11. `docs/governance/COMPATIBILITY_CONTRACT.md`
12. `docs/OPERATIONS_RUNBOOK.md`
13. `docs/COMMERCIAL_MODEL.md`
14. `docs/governance/DECISION_LOG.md`

## Operating Rule

No project-critical decision may rely on chat memory, private memory, local assumptions, or undocumented intent.

If intent is not present in the repository, the correct action is to preserve safety, add a decision record, and update the canonical contract before implementation.

## Non-Negotiable Project Direction

The project is designed as a long-horizon, commercially serious, globally credible, governance-first operating system for durable financial intelligence and future adaptable systems.

It must remain:

- repository-driven
- source-of-truth governed
- automation-first
- commercially viable
- privacy-capable
- enterprise-capable
- portable
- auditable
- extensible
- anti-drift
- anti-obsolescence
- usable by future agents without chat memory

## Required Behavior for Changes

Every material change must be evaluated against:

- project goals
- roadmap impact
- source-of-truth hierarchy
- compatibility contract
- commercial model
- operational runbook
- policy matrix
- canonical sources
- tests and gates

## Definition of Safe Continuation

A future operator can continue safely only when:

- the working tree is clean before starting
- the current branch is known
- canonical files are read
- changes are made through PRs
- validation passes locally
- CI passes remotely
- roadmap and decision records remain consistent

## Repository System of Record

The repository is the system of record for project goals, governance contracts, roadmap state, validation expectations, and safe continuation instructions. Chat memory is not a source of truth.
