# Durability Standard

This document defines long-horizon durability requirements.

## Encoding

Text files should use UTF-8 without BOM and LF line endings.

## Formats

Critical governance data should prefer durable plain-text formats:

- Markdown for human-readable policy
- YAML or JSON for machine-readable contracts
- Python standard library where practical for validators

## Repository Survival

The repository must contain enough information for a new operator to continue without chat memory.

## Toolchain Survival

Critical validation should avoid unnecessary proprietary or fragile dependencies.

Dependencies must be explicit when needed.

## Migration

Schemas should be versioned.

Breaking changes should include migration notes.

## Portability

Project-critical processes should remain understandable on common operating systems and common development environments.

## Artifact Retention

Important decisions, contracts, and generated summaries should be retained in repository-visible locations.

## Anti-Obsolescence

The project should prefer replaceable adapters, stable contracts, and documented invariants over tightly coupled implementation details.

## Durability Compliance Terms

- Required governance phrase: bom-free
