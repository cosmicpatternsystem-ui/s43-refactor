# Concurrency and Atomicity Policy

## Purpose

Defines safe editing and writing expectations for concurrent automation and scripts.

## Required Controls

1. Generated files must be written atomically when practical.
2. Concurrent edits must avoid silent overwrite.
3. Automation must prefer deterministic outputs.
4. Scripts must preserve BOM-free UTF-8 LF files.

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