# Dependency and Supply Chain Policy

## Purpose

Defines governance controls for dependencies, workflows, and automation supply chain.

## Required Controls

1. Dependency changes must be reviewable.
2. Automation changes must be covered by PR review.
3. High-risk dependency changes require evidence.
4. CI definitions are governance-sensitive artifacts.

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