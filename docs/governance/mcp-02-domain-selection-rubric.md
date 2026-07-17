# MCP-02 Domain Selection Rubric

## Status
Governance companion artifact for MCP-02 domain lock evaluation.

## Authority
This artifact is subordinate to repository governance policy, the governance manifest, and `ROADMAP_CANONICAL.md`.

This artifact defines the enforced evaluation rubric for selecting and locking the final MCP-02 domain. It does not override canonical roadmap intent, manifest authority, schema rules, or validator policy.

## Scope
This rubric applies only to:
- evaluation of MCP-02 domain candidates
- comparison of MCP-02 domain candidates
- recommendation of a single MCP-02 domain lock candidate
- protected-PR evidence for final MCP-02 domain lock

This rubric does not authorize:
- changes to the repository authority chain
- implicit domain lock through generated or derived artifacts
- expansion from one event class to multiple event classes
- unbounded product or governance scope growth

## Canonical MCP-02 Constraint
MCP-02 MUST remain domain-open but outcome-closed until a protected PR canonically locks exactly one domain.

For MCP-02, the locked domain MUST produce:
- a buyer-credible decision surface
- evidence-backed operation
- a Decision API
- exactly one event class
- machine-readable outputs
- reason codes
- evidence links
- deterministic replay
- fail-closed validation

## Hard Gate Requirements
A domain candidate MUST NOT be eligible for canonical lock unless all of the following are present:

- buyer problem statement
- exactly one event class definition
- bounded output contract
- replayable fixture pack
- benchmark evidence
- legal/compliance note

If any required item is missing, the candidate result MUST be hard-fail.

## Candidate Requirements

### Buyer Problem Statement
A candidate MUST identify:
- the buyer or buyer-equivalent operator
- the decision to be made
- the current failure mode
- the operational or economic value of the decision
- why the decision is suitable for constrained automation

### Event Class Definition
A candidate MUST define exactly one event class.
The event class definition MUST be:
- operationally precise
- bounded
- non-editorial
- time-scoped where necessary
- distinct from adjacent decision families

A candidate MUST hard-fail if it introduces multiple event classes or leaves the event boundary ambiguous.

### Bounded Output Contract
A candidate MUST define outputs that are:
- machine-readable
- bounded
- deterministic for replayed inputs
- reason-coded
- evidence-linked
- compatible with fail-closed validation

Open-ended narrative outputs, editorial recommendations, or unconstrained result shapes are prohibited.

### Replayable Fixture Pack
A candidate MUST include:
- representative fixtures
- edge-case fixtures
- negative-case fixtures
- expected outputs
- expected reason codes
- replay instructions sufficient for deterministic reproduction

### Benchmark Evidence
A candidate MUST include enough benchmark evidence to support a credible lock decision.
Benchmark evidence SHOULD demonstrate:
- realistic input coverage
- measurable decision quality
- operational feasibility within MCP-02 delivery bounds

### Legal/Compliance Note
A candidate MUST include a legal/compliance note that identifies:
- material constraints
- data handling concerns
- deployment or usage restrictions
- whether the candidate is controllable at MCP-02 scope

## Scoring Model

### Evaluation Order
Evaluation MUST proceed in this order:
1. hard gate completeness
2. hard-fail condition screening
3. weighted scoring
4. final lock recommendation

A candidate that fails gating MUST NOT enter weighted scoring.

### Weighted Criteria
The weighted scoring model is:

| Criterion | Weight |
|---|---:|
| Buyer credibility | 20 |
| Event-class discipline | 20 |
| Output boundedness | 15 |
| Replayability | 15 |
| Evidence strength | 15 |
| Compliance controllability | 10 |
| Delivery fit | 5 |

Maximum score: 100

### Minimum Acceptance Thresholds
A candidate is eligible for domain lock recommendation only if:
- total score is at least 80 out of 100
- Buyer credibility is at least 16 out of 20
- Event-class discipline is at least 16 out of 20
- Output boundedness is at least 12 out of 15
- Replayability is at least 12 out of 15
- no hard-fail condition is present

### Tie Rule
If multiple candidates pass:
1. highest Event-class discipline wins
2. if tied, highest Replayability wins
3. if tied, lowest compliance burden wins
4. if still tied, result MUST be no-lock pending additional evidence

## Hard-Fail Conditions
A candidate MUST hard-fail if any of the following is true:

- more than one event class is defined
- buyer is undefined, non-credible, or not decision-bearing
- output contract is open-ended, ambiguous, or editorial
- reason codes are absent
- evidence links are absent
- replayable fixtures are absent
- evaluation depends on non-replayable discretionary judgment
- governance expansion is required without delivery-critical justification
- product or schema surface is materially unbounded
- legal/compliance risk is identified without a credible control approach
- benchmark evidence is absent or materially insufficient
- the candidate is a research program rather than a bounded Decision API

## Warning Conditions
A candidate MAY carry warnings when:
- benchmark coverage is still limited but sufficient for preliminary comparison
- buyer evidence is indirect but still credible
- legal/compliance treatment is adequate but not yet fully refined
- fixture coverage is minimal but deterministic replay is still possible
- limited governance expansion is needed and is explicitly delivery-critical

Warnings MUST be:
- explicitly recorded
- assigned an owner
- bounded by a resolution condition or date

Warnings MUST NOT be open-ended.

## Protected PR Requirements
A final MCP-02 domain lock MUST occur only through a protected PR.

The protected PR MUST include:
- the selected candidate
- rejected alternatives and rejection rationale
- the completed scoring table
- evidence references
- fixture pack references
- the bounded output contract
- the single event class definition
- the legal/compliance note
- an explicit lock recommendation statement

## Governance Constraints During Selection
Before domain lock:
- MCP-02 MUST remain domain-open
- canonical roadmap intent MUST NOT imply a final domain
- generated or derived artifacts MUST NOT claim final domain authority
- validators MUST NOT assume a final domain implicitly

Governance expansion during domain selection MUST NOT occur unless it is:
- delivery-critical
- explicitly justified
- narrowly scoped
- migration-defined where applicable

## Stop Rule
If no candidate passes the rubric by the designated lock gate, MCP-02 MUST:
- pause, or
- re-scope, or
- retry with a narrower single event class

Continuation beyond the designated gate without a valid domain lock MUST NOT occur.

## Candidate Record Template

### Candidate
`<candidate-name>`

### Buyer Problem Statement
`...`

### Event Class Definition
`...`

### Bounded Output Contract
`...`

### Replayable Fixture Pack
`...`

### Benchmark Evidence
`...`

### Legal/Compliance Note
`...`

### Scores
- Buyer credibility: `x/20`
- Event-class discipline: `x/20`
- Output boundedness: `x/15`
- Replayability: `x/15`
- Evidence strength: `x/15`
- Compliance controllability: `x/10`
- Delivery fit: `x/5`
- Total: `x/100`

### Result
`Pass | Fail | Warning`

### Rationale
`...`

### Lock Recommendation
`Yes | No`