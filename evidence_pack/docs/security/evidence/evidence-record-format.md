# Evidence Record Format (v1.1.0)
## Overview
This document defines the formal structure for evidence records within the ASO-X ecosystem.

## Fields
- `event_type`: (Required) The category of the event (formerly `evidence_type`).
- `payload_hash`: (Required) Cryptographic hash of the content (formerly `content_hash`).
- `timestamp`: ISO-8601 formatted UTC timestamp.

## Compliance
All systems MUST emit records matching the `evidence-record.schema.json`.
