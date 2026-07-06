# Autonomy Model

This document defines how the project moves toward low-human-dependency operation.

## Autonomy Principles

The project should automate repeatable governance work while keeping strategic authority explicit and auditable.

Automation must be deterministic where practical.

Automation must prefer repository evidence over external memory.

Automation must fail closed when required governance artifacts are missing.

## Autonomy Levels

### Level 0: Manual

Humans manually inspect all project state.

### Level 1: Assisted

Scripts validate known rules.

### Level 2: Governed

CI blocks changes that violate declared contracts.

### Level 3: Coordinated

Roadmap, contracts, docs, and tests are checked for drift together.

### Level 4: Advisory Autonomous

Automation proposes roadmap and decision updates from repository changes.

### Level 5: Self-Maintaining

The project can detect stale plans, missing decisions, and inconsistent documentation with minimal human prompting.

## Current Target

The current target is Level 3 with a clear path to Level 4.

## Required Autonomy Capabilities

- new-agent onboarding
- source-of-truth validation
- roadmap synchronization
- drift detection
- governance health scoring
- compatibility awareness
- release readiness awareness
- commercial posture awareness
- operational safety awareness
