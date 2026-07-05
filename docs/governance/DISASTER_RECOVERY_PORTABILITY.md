# Disaster Recovery and Repository Portability

## Purpose

Defines controls for preserving repository usability across platforms and time.

## Required Controls

1. Governance files must use portable UTF-8 LF text.
2. Critical documentation must not depend on one machine.
3. Repository history must remain sufficient to reconstruct governance state.
4. Disaster recovery procedures must preserve lock IDs.

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