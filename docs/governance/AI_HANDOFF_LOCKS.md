# AI Handoff Locks

## Purpose

Defines continuity requirements for safe AI-assisted development handoff.

## Required Controls

1. AI handoff must preserve project context.
2. Governance and roadmap files must be discoverable.
3. Machine-readable files must remain valid.
4. Critical decisions must be documented before automation depends on them.

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