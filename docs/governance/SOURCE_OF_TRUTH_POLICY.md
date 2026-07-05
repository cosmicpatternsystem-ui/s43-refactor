# Source of Truth Policy

## Purpose

Defines the repository as the authoritative source for governance state.

## Required Controls

1. The repository is the source of truth.
2. External tools may automate but must not replace repository records.
3. Generated governance artifacts must be reproducible.
4. Policy state must be reviewable through Git history.

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