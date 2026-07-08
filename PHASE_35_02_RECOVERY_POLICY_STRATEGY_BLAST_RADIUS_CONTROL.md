# Phase 35.02: Autonomous Recovery & Failure Containment - Recovery Policy, Strategy Selection, and Blast-Radius Control

## Metadata
- **Phase ID:** 35.02
- **Parent Phase:** 35 (Autonomous Recovery & Failure Containment)
- **Status:** INITIALIZED
- **Value Proposition:** Standardize the selection logic for recovery strategies and define blast-radius controls to ensure failure containment remains predictable and policy-compliant.

## Objectives
1. **Recovery Policy Schema:** Define how recovery actions are mapped to specific failure modes and criticality levels.
2. **Strategy Selection Logic:** Establish the decision criteria for picking the safest and most effective recovery pathway.
3. **Blast-Radius Isolation:** Define technical and logical boundaries to prevent fault propagation during recovery.
4. **Governed Automation:** Ensure autonomous selection logic is auditable and subject to safety overrides.

## Recovery Policy Schema
- Policies must define a mapping between FailureType, SubsystemSeverity, and ApprovedRecoveryActions.
- Policy must specify MaxRetryCount, BackoffInterval, and EscalationThreshold.
- Recovery policies must be versioned and signed, matching the core Governance Framework.
- Policies must declare IncompatibleActions to prevent conflicting recovery attempts.

## Strategy Selection Criteria
- **Safety First:** Prioritize strategies that result in the smallest possible side-effect, even if recovery is slower.
- **Evidence Availability:** Recovery is only permitted if the pre-failure state and current failure context are backed by immutable evidence.
- **Dependency Awareness:** Selection must account for the health of downstream and upstream dependencies.
- **Success Confidence:** Strategies must have a calculated confidence score based on historical performance and current system telemetry.

## Blast-Radius Control
- **Fault Isolation:** Active containment must lock affected execution contexts and prevent state changes in adjacent domains.
- **Propagation Safeguards:** Define circuit breakers and isolation throttles at domain boundaries.
- **Recovery Bounding:** Recovery actions must be scoped to the minimum set of resources/entities required to restore stability.
- **State Guardrails:** Implement read-only or maintenance-mode states for domains under active recovery.

## Operational Flow
1. Receive failure event and blast-radius assessment from Phase 35.01.
2. Lookup recovery policy matching the failure context and subsystem identity.
3. Filter candidate strategies based on current system health and dependency status.
4. Select high-confidence recovery strategy or escalate to manual review if no safe match is found.
5. Deploy containment isolation to enforce blast-radius boundaries.
6. Hand selected strategy and isolation context to the Recovery Orchestrator (Phase 35.03).

## Exit Criteria
- Recovery policy schema and strategy selection logic are documented.
- Blast-radius isolation mechanisms and propagation safeguards are defined.
- Conflict resolution and escalation triggers for strategy selection are established.
- Roadmap is regenerated and validation passes.
