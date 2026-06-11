# Phase 9 Evidence Template

## Status
This template is for validation planning and evidence capture design only.
It does not authorize runtime activation, recovery enablement, or live trading.

## Usage Instructions
Use one copy of this template per validation area, per review item, or per planned validation execution record.
The goal is to make evidence expectations explicit before any execution-oriented work is approved.

## Global Safety Conditions
The following must remain true whenever this template is prepared or used:
- `SAFE-NO-TRADE` remains in effect
- no silent runtime activation is introduced
- no live trading enablement is introduced
- validation work remains explicitly scoped and reviewer-visible

---

## Evidence Record Header

### Record ID
- ID:
- Date:
- Author:
- Reviewer:
- Phase:
- Validation Area:

### Scope Reference
- Related phase document:
- Related checklist item:
- Related touchpoint(s):
- Related commit(s):
- Related test file(s):
- Related script(s):

### Validation Intent
- Objective:
- Why this validation matters:
- Risk being evaluated:
- Out-of-scope items:
- Blocked actions confirmed:

---

## Preconditions
Document the required preconditions before the evidence is considered valid.

- Safety posture confirmed:
- Working tree clean:
- Runtime activation absent:
- Recovery activation absent:
- Reviewer visibility preserved:
- Required environment assumptions:
- Required fixtures or mocks:
- Required logs or outputs available:

---

## Validation Method
Describe how evidence is expected to be collected.

- Validation type: [ ] documentation review  [ ] test execution  [ ] static inspection  [ ] observability review  [ ] failure-path analysis  [ ] other
- Planned steps:
  1.
  2.
  3.
- Expected system posture during validation:
- Expected operator-visible outputs:
- Expected blocked behaviors:

---

## Expected Result
Define success criteria before collecting evidence.

- Expected safe behavior:
- Expected failure handling behavior:
- Expected observability/reporting behavior:
- Expected non-goal preservation:
- Expected abort trigger(s), if any:

---

## Observed Result
Capture what was actually observed.

- Actual behavior observed:
- Actual logs/messages observed:
- Actual state behavior observed:
- Actual operator-visible result:
- Unexpected behavior observed:
- Ambiguities observed:

---

## Evidence Artifacts
List concrete artifacts supporting the record.

- [ ] document reference
- [ ] test output
- [ ] command output
- [ ] log snippet
- [ ] screenshot or terminal capture
- [ ] reviewer note
- [ ] commit reference
- [ ] other

Artifact details:
- Artifact 1:
- Artifact 2:
- Artifact 3:

---

## Failure / Risk Classification
If anything deviates from expectation, classify it here.

- Classification: [ ] none  [ ] minor documentation gap  [ ] review blocker  [ ] safety concern  [ ] runtime concern  [ ] unclear
- Severity: [ ] low  [ ] medium  [ ] high
- Description:
- Is execution blocked by this finding?: [ ] yes  [ ] no
- Immediate safe response:
- Follow-up required:

---

## Abort Condition Check
Document whether any abort condition was triggered or would have been triggered.

- Abort condition defined in advance?: [ ] yes  [ ] no
- Abort condition triggered?: [ ] yes  [ ] no
- Trigger details:
- Safe-stop behavior confirmed:
- Additional containment needed:

---

## Reviewer Assessment
This section should be completed by a reviewer or approver.

- Evidence completeness: [ ] insufficient  [ ] partial  [ ] adequate  [ ] strong
- Scope discipline preserved: [ ] yes  [ ] no
- Non-goals preserved: [ ] yes  [ ] no
- `SAFE-NO-TRADE` preserved: [ ] yes  [ ] no
- Runtime activation introduced: [ ] yes  [ ] no
- Reviewer comments:
- Required follow-up actions:

---

## Signoff Status
- Status: [ ] not reviewed  [ ] review in progress  [ ] accepted for planning  [ ] blocked  [ ] requires follow-up
- Reviewer name:
- Review date:
- Final note:

---

## Completion Reminder
Evidence is only useful if it is:
- explicit
- reviewable
- safety-preserving
- tied to scope
- clear about what was and was not validated

This template must not be used to imply live-trading approval, recovery activation approval, or production-readiness signoff by itself.
