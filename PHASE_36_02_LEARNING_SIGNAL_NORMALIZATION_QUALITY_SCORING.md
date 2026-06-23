# Phase 36.02: Adaptive Learning & Continuous Improvement - Learning Signal Normalization and Quality Scoring

## Metadata
- **Phase ID:** 36.02
- **Parent Phase:** 36 (Adaptive Learning & Continuous Improvement)
- **Status:** INITIALIZED
- **Value Proposition:** Define how operational feedback signals are normalized, scored, filtered, and prepared for safe continuous-improvement workflows.

## Objectives
1. **Signal Normalization:** Convert heterogeneous runtime, decision, execution, recovery, and governance evidence into a consistent learning-signal format.
2. **Quality Scoring:** Assign confidence, completeness, reliability, and relevance scores to each learning signal.
3. **Noise Filtering:** Reject low-quality, ambiguous, duplicate, or unsafe signals before they can influence improvement logic.
4. **Learning Eligibility:** Establish clear criteria for deciding whether a signal may be used for observation, recommendation, or bounded adjustment.

## Learning Signal Contract
- Every learning signal must include LearningSignalID, source phase, source evidence reference, timestamp, signal type, and operational context.
- Accepted signal types include DECISION_OUTCOME, EXECUTION_RESULT, RECOVERY_RESULT, DEGRADATION_EVENT, ESCALATION_EVENT, OPERATOR_FEEDBACK, and REPLAY_VERIFICATION.
- Signals must retain linkage to the immutable evidence chain defined in Phase 32.
- Signals without verified provenance must be marked UNTRUSTED and excluded from autonomous learning.

## Quality Scoring Dimensions
- Completeness: Whether required evidence fields and source references are present.
- Reliability: Whether the source system and evidence lineage are verified.
- Relevance: Whether the signal applies to an active decision, execution, recovery, or governance domain.
- Freshness: Whether the signal is recent enough to influence current behavior safely.
- Conflict Status: Whether the signal contradicts other verified evidence.

## Filtering and Rejection Rules
- Duplicate signals must be collapsed into a single canonical signal with linked references.
- Contradictory signals must be routed to governance review instead of autonomous learning.
- Signals with incomplete evidence, missing lineage, or failed verification must be rejected.
- Rejected signals must be retained with a rejection reason for audit and future replay analysis.

## Operational Flow
1. Receive raw feedback from approved runtime and governance sources.
2. Normalize raw input into the learning-signal schema.
3. Validate provenance against the evidence chain.
4. Score signal quality across completeness, reliability, relevance, freshness, and conflict dimensions.
5. Assign a learning eligibility classification: OBSERVABLE, RECOMMENDABLE, BOUNDED_UPDATE_ELIGIBLE, or REJECTED.
6. Forward eligible signals to the learning loop defined in Phase 36.01.

## Exit Criteria
- Learning signal schema and accepted signal types are documented.
- Quality scoring dimensions and eligibility classes are defined.
- Filtering, rejection, and duplicate-handling rules are established.
- Provenance and audit-retention requirements are documented.
- Roadmap is regenerated and validation passes.
