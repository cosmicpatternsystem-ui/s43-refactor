# Fifty-Year Durability Doctrine

This document defines the canonical 50-year durability doctrine for the ASO-X repository.

## Durability Principles

- The repository is the source of truth.
- Plain text first.
- BOM-free UTF-8 LF where repository standards require it.
- Deterministic validation over implicit assumptions.
- Minimal hidden state.
- Migration-friendly structure.
- Replaceable dependencies and abstraction over critical external integrations.
- Human-readable and machine-readable documentation.
- Archival readability and future operator comprehension.
- Autonomous agent readability through explicit structure and canonical entrypoints.

## Long-Horizon Requirements

- Strategic and governance artifacts must remain discoverable.
- Core operational knowledge must live in versioned repository documents.
- Validation must detect drift in critical control-plane relationships.
- Files that become obsolete must be deprecated explicitly or removed.
- The project must favor long-term survivability over short-term convenience where they conflict materially.
