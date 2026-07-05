# Release Evidence Policy

## Purpose

Defines evidence requirements for releases and high-risk changes.

## Required Controls

1. Release-impacting governance changes require evidence.
2. CI results must be retained through durable references.
3. Release gates must not be bypassed silently.
4. Financial-risk changes require additional review evidence.

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