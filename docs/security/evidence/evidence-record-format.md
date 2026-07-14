# Evidence Record Format (Policy P3.2)

This document specifies the schema, serialization constraints, and validation requirements for ASO-X Evidence Records.

## Specifications

- **Encoding**: UTF-8 (Strictly BOM-free)
- **Line Endings**: LF (`\n`)
- **Schema Reference**: `/schemas/evidence-record.schema.json`

## Validation Rules

1. All records must strictly comply with the JSON Schema.
2. `payload_hash` must use the prefix `sha256:` followed by a valid 64-character hex string.
3. At least one cryptographic signature must be present in the `signatures` array.