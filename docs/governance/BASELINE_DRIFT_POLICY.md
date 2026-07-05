# Baseline Drift Policy

## Purpose

Prevents undocumented drift from canonical governance baselines.

## Required Controls

1. Baseline changes require PR review.
2. Drift-sensitive files must be covered by CI.
3. Unexplained removal of canonical controls is forbidden.
4. Machine-readable indexes must stay synchronized with Markdown documentation.

## Enforcement

1. Repository documentation
2. Machine-readable governance registry
3. Pytest validation
4. GitHub Actions gate
5. Pull request review

## Change Control

text
PR + required review + CI pass

## Retention

text
50y

## Failure Mode

text
block merge