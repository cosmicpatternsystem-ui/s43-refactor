# Phase 36.03: Model and Strategy Update Governance

## Purpose
Define the governance contract for how learned signals, candidate model updates, and strategy changes are reviewed, approved, versioned, and promoted into active system behavior without violating safety, evidence, or operational control boundaries.

## Scope
This phase documents:
- governance boundaries for model and strategy updates
- approval and review workflow for candidate changes
- versioning and promotion rules across staging and production states
- rollback and freeze controls for unsafe or low-confidence updates
- evidence and audit requirements for every approved change

This phase does not implement live retraining, autonomous self-modification, or direct production mutation.

## Governance Objectives
1. Ensure no adaptive improvement bypasses explicit safety and approval gates.
2. Maintain full evidence continuity from learning signal to approved change.
3. Prevent unreviewed model or strategy drift in runtime execution.
4. Support reversible, auditable, staged rollout of approved updates.
5. Separate observation, recommendation, approval, and activation responsibilities.

## Update Classes
### 1. Model Updates
Changes affecting:
- model weights
- prompts or system instruction layers
- feature mappings
- inference calibration parameters
- confidence thresholds tied to learned behavior

### 2. Strategy Updates
Changes affecting:
- decision policies
- routing logic
- recovery preferences
- execution heuristics
- safety guard tuning
- escalation thresholds

### 3. Configuration-Only Governance Updates
Changes affecting:
- metadata
- rollout windows
- reviewer assignment
- activation scheduling
without changing core decision logic.

## Governance Flow
1. Learning systems produce a candidate update package.
2. Candidate update is normalized into a reviewable artifact.
3. Safety and policy validation are executed before human or policy approval.
4. Approval authority evaluates evidence, blast radius, reversibility, and expected benefit.
5. Approved updates are versioned and staged.
6. Activation occurs only through controlled promotion.
7. Post-activation monitoring verifies expected behavior.
8. Failed or risky updates are rolled back, frozen, or escalated.

## Mandatory Approval Gates
No model or strategy update may activate unless all of the following are satisfied:
- provenance is known
- training or learning inputs are attributable
- quality score passes minimum threshold
- safety review status is pass
- rollback plan exists
- blast-radius classification is assigned
- activation scope is explicit
- evidence package is complete
- approver identity is recorded
- target environment is declared

## Evidence Contract
Each candidate update must include:
- candidate update ID
- source learning window or evidence interval
- affected component list
- expected behavioral delta
- risk assessment
- validation summary
- approval decision
- approved scope
- activation timestamp
- rollback reference
- post-deployment verification result

## Promotion Policy
Candidate updates move through the following states:
- observed
- proposed
- validated
- approved
- staged
- active
- frozen
- rolled_back
- retired

State transitions must be monotonic, recorded, and attributable.

## Safety Boundary
The adaptive learning loop may recommend updates, but it may not:
- directly self-activate new runtime behavior
- alter safety-critical policy without governance approval
- suppress evidence required for audit
- overwrite rollback baselines
- expand blast radius beyond approved scope

## Rollback and Freeze Controls
Governance must support:
- immediate rollback to last-known-good version
- emergency freeze on a candidate family
- scoped disablement by environment or tenant
- temporary approval suspension during anomaly conditions
- re-verification before reactivation

## Audit and Compliance Requirements
Every approved or rejected change must preserve:
- reviewer identity
- approval rationale
- decision timestamp
- evidence references
- target scope
- activation result
- rollback outcome if triggered

## Acceptance Criteria
- Governance boundaries for model and strategy updates are explicitly documented.
- Candidate update lifecycle states are defined from proposal through retirement.
- Mandatory approval gates are enumerated and cannot be bypassed conceptually.
- Evidence requirements are defined for every approved change.
- Rollback, freeze, and staged promotion expectations are documented.
- Separation between recommendation, approval, and activation is clear.

## Exit Condition
This phase is complete when model and strategy update governance is documented as a non-bypassable control layer for adaptive system improvement.
