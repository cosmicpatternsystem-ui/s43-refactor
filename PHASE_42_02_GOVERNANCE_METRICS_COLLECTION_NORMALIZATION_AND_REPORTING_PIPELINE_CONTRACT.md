# Phase 42.02: Governance Metrics Collection, Normalization, and Reporting Pipeline Contract

Status: Planned
Owner: Operations / Governance
Priority: High
Documentation Only: true
Depends On: Phase 42.01

## Purpose

Define the operating contract for collecting, normalizing, snapshotting, and reporting governance metrics so that the baseline, trend, and signal quality model from Phase 42.01 can be applied consistently across governance workflows.

This phase establishes how metric inputs move from source records into decision-ready reporting without losing traceability, context, ownership, or confidence boundaries.

## Scope

This phase covers:

- Governance metric collection requirements
- Source record identification and intake expectations
- Normalization rules
- Metric snapshot requirements
- Reporting pipeline expectations
- Ownership and review responsibilities
- Data quality handling
- Traceability preservation
- Reporting output requirements
- Failure and partial-report handling

This phase does not implement dashboards, automation jobs, database schemas, or alerting logic. It defines the contract that later implementation phases can use safely.

## Collection Model

Governance metrics must be collected from authoritative source records rather than inferred from incomplete secondary summaries.

Each collected metric must identify:

- Source system or record location
- Collection date or reporting window
- Metric owner
- Governance domain
- Control or lifecycle area
- Source evidence link or reference
- Collection method
- Known exclusions
- Confidence level
- Last verified timestamp

Metrics without a known source record must be treated as provisional until traceability is restored.

## Source Record Requirements

Source records used for governance metrics must preserve enough context to support later review, audit, and dispute resolution.

Acceptable source records may include:

- Review records
- Attestation records
- Exception and waiver records
- Ownership records
- Escalation records
- Closure records
- Evidence inventories
- Release readiness records
- Lifecycle state records
- Historical baseline records

A source record must not be overwritten in a way that removes the ability to reconstruct the metric state used for a prior governance decision.

## Intake Requirements

Metric intake must distinguish between complete, partial, stale, disputed, and missing inputs.

Each intake action must determine whether the input is:

- Accepted as decision-ready
- Accepted with qualification
- Accepted as low-confidence
- Deferred pending owner review
- Rejected due to missing traceability
- Rejected due to incompatible format
- Rejected due to unresolved dispute

Rejected or deferred inputs must be visible in reporting as governance uncertainty, not silently excluded.

## Normalization Rules

Governance metrics must be normalized before comparison, trend analysis, or aggregated reporting.

Normalization must define:

- Canonical metric name
- Metric category
- Governance domain
- Reporting period
- Unit of measure
- Counting rule
- Inclusion criteria
- Exclusion criteria
- Status vocabulary
- Confidence vocabulary
- Source priority when duplicates exist

Normalization must prevent inconsistent names, ambiguous statuses, or incompatible units from being treated as comparable data.

## Status Vocabulary

Metric status values must be explicit and stable.

Minimum status values include:

- Current
- Stale
- Incomplete
- Missing
- Disputed
- Low Confidence
- Deferred
- Closed
- Reopened
- Superseded

Additional statuses may be added only when their interpretation is documented.

## Confidence Vocabulary

Metric confidence must be reported separately from metric status.

Minimum confidence values include:

- High
- Medium
- Low
- Unknown
- Not Applicable

A metric may be current but low-confidence, or stale but high-confidence historically. Reporting must preserve this distinction.

## Snapshot Requirements

Metric reporting must preserve point-in-time snapshots.

A metric snapshot must include:

- Snapshot timestamp
- Reporting window
- Included metric categories
- Included governance domains
- Source record references
- Normalization version or rule set
- Known exclusions
- Quality limitations
- Owner or reviewer
- Decision context, when applicable

Snapshots used for governance decisions must be retained so later audits can reconstruct the decision state.

## Reporting Pipeline Contract

The governance metrics reporting pipeline must make metric movement understandable from source to report.

The pipeline contract must define:

- Source intake stage
- Validation stage
- Normalization stage
- Quality classification stage
- Snapshot generation stage
- Reporting output stage
- Review and attestation stage
- Escalation or remediation handoff stage

Each stage must preserve traceability to the prior stage.

## Reporting Output Requirements

Governance metric reports must show both metric values and interpretation context.

Reports must include:

- Metric name
- Metric category
- Reporting window
- Current value or state
- Baseline comparison
- Trend direction, when available
- Status
- Confidence
- Source reference
- Owner
- Freshness indicator
- Completeness indicator
- Known limitations
- Required follow-up action, when applicable

Reports must not present low-confidence or incomplete metrics as equivalent to decision-ready metrics.

## Data Quality Handling

Data quality issues must be classified before metrics are used.

Data quality issue categories include:

- Missing source record
- Missing owner
- Missing timestamp
- Missing evidence link
- Inconsistent status
- Duplicate source record
- Conflicting source records
- Stale source record
- Unclear reporting window
- Unmapped governance domain
- Manual override without evidence

Each data quality issue must have an owner or escalation path.

## Duplicate and Conflict Handling

Duplicate or conflicting metric inputs must be resolved through documented source priority or owner review.

Duplicate handling must identify:

- Preferred source
- Superseded source
- Reason for precedence
- Whether historical values are affected
- Whether rebaseline review is required

Conflict handling must identify:

- Conflicting records
- Decision impact
- Temporary confidence classification
- Owner responsible for resolution
- Required follow-up date

## Partial Reporting

Partial reporting is allowed only when the report clearly identifies its coverage limits.

Partial reports must include:

- Included domains
- Excluded domains
- Missing source categories
- Known stale inputs
- Known disputed inputs
- Confidence impact
- Whether the report can support decisions

Partial reports must not be used to close governance obligations outside their coverage.

## Failure Handling

If metric collection, normalization, or reporting fails, the failure must be visible and actionable.

Failure records must include:

- Failed stage
- Affected metric or category
- Affected governance domain
- Failure timestamp
- Known cause
- Owner
- Required recovery action
- Decision impact
- Escalation requirement, when applicable

Pipeline failures must not be hidden by reusing the last successful report unless the report is clearly marked as stale.

## Relationship to Phase 42.01

This phase operationalizes the metric quality principles defined in Phase 42.01.

Phase 42.01 defines what makes a metric useful and decision-ready. This phase defines how metrics are collected, normalized, snapshot, and reported so that usefulness can be preserved in practice.

## Acceptance Criteria

This phase is complete when:

- Metric collection requirements are documented
- Source record and intake expectations are defined
- Normalization rules are documented
- Status and confidence vocabularies are defined
- Snapshot requirements are documented
- Reporting pipeline stages are defined
- Reporting output requirements are documented
- Data quality, duplicate, conflict, partial report, and failure handling are documented
- Relationship to Phase 42.01 is documented
- The roadmap is regenerated and validated
- Roadmap smoke tests pass

## Evidence

Expected evidence includes:

- This phase document
- Updated generated roadmap state
- Passing roadmap validation
- Passing roadmap smoke tests
- Pull request review and merge record

## Definition of Done

Phase 42.02 is done when governance metric collection, normalization, snapshotting, and reporting have a documented pipeline contract that preserves traceability, confidence, and decision context from source records through governance reports.
