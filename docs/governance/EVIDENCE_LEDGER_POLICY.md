# Evidence Ledger Policy

## Purpose

Defines how governance evidence is recorded, retained, and reviewed.

## Required Controls

1. Critical and high-risk locks require evidence.
2. Release decisions require traceable evidence.
3. Evidence retention is 50 years.
4. Missing evidence must block merge.

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