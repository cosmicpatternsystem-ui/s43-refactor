# Evidence Record Format (v1.1.0)

## Overview
This document defines the formal structure for evidence records within the ASO-X ecosystem.

## Fields
- `event_type`: (Required) The category of the event (formerly `evidence_type`).
- `payload_hash`: (Required) SHA-256 hash of the content encoded as `sha256:<64 lowercase hex>`.
- `timestamp`: ISO-8601 formatted UTC timestamp.

## Compliance
All systems MUST emit records matching the `evidence-record.schema.json`.
All systems MUST encode `payload_hash` in canonical prefixed form: `sha256:<64 lowercase hex>`.
Bare hexadecimal hashes without the `sha256:` prefix are invalid.
