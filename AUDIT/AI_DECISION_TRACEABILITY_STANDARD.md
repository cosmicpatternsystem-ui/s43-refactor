# AI Decision Traceability Standard

## Purpose

This standard defines the minimum traceability expectations for AI-assisted decision support in the project.

The standard is documentation-only and does not introduce runtime AI execution or autonomous decision behavior.

## Traceability Baseline

An AI-assisted decision must preserve enough context for later review.

Minimum traceability fields should include:

- Decision identifier.
- Decision category.
- Source input reference.
- AI output reference.
- Governing policy or contract reference.
- Operator disposition.
- Evidence reference.
- Timestamp.
- Final status.

## Decision Categories

AI-assisted decisions may include:

- Advisory recommendation.
- Risk classification.
- Release readiness summary.
- Commercial signal interpretation.
- External data source assessment.
- Governance exception review.
- Operator override recommendation.

A future phase may expand these categories, but any expansion should preserve the same auditability expectations.

## Status Values

Recommended decision status values are:

- advisory
- accepted
- rejected
- overridden
- deferred
- expired
- invalid

Unknown or incomplete records should not be promoted to accepted status.

## Trace Requirements

Each decision record should identify:

- The input reviewed by the AI process.
- The output produced by the AI process.
- The operator or governance role responsible for final disposition.
- The evidence bundle supporting the final disposition.
- Any policy, standard, or contract used to evaluate the decision.

## Non-Goals

This standard does not define:

- Live model routing.
- Prompt templates.
- Model vendor selection.
- Automated trade execution.
- Wallet interaction.
- Secret access.
- Runtime enforcement code.

## Audit Expectations

Audit review should confirm that AI-assisted decisions are explainable, attributable, and reproducible from recorded evidence.

Decision records without sufficient traceability should be treated as incomplete.
