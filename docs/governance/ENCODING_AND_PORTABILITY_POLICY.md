# Encoding and Portability Policy

## Purpose

Defines encoding, line-ending, and output portability requirements.

## Required Controls

1. Text files must be BOM-free UTF-8.
2. Line endings must be LF.
3. CLI output should remain safe for cp1252 terminals when practical.
4. Portable plain-text formats are preferred for governance artifacts.

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