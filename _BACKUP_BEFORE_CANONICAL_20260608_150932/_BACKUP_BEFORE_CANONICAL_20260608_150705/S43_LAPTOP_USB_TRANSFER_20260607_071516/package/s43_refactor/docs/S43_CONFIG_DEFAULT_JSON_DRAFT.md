# S43 Config Default JSON Draft

## Purpose
This document defines the proposed default configuration structure for moving s43.py toward a standalone-ready configuration model.

## Scope
This document is a configuration design draft and migration note.

S43_PY_MODIFIED=NO
CONFIG_DEFAULT_JSON_DRAFT_CREATED=YES
CONFIG_DEFAULT_JSON_CREATED=YES
CONFIG_DEFAULT_JSON_VALID=YES

## Current Implementation Note

The current s43.py implementation still reads operational settings from environment variables and internal defaults.

The newly created config/default.json is valid JSON, but it is not yet wired into s43.py runtime loading.

Therefore, this document records the intended standalone configuration shape before code modification.

## Target Model

NORMALIZED_TARGET_MODEL=CENTRALIZED_BUT_BACKWARD_AWARE

The application should eventually prefer centralized configuration and output paths, while remaining aware of existing legacy/root-level artifacts.

## Proposed Directory Layout

config/
  default.json

logs/
  *.log

state/
  *.json
  *.sqlite
  *.db

exports/
  optional generated outputs

tmp/
  temporary runtime files

## Proposed default.json Structure

{
  "paths": {
    "logs_dir": "logs",
    "state_dir": "state",
    "exports_dir": "exports",
    "tmp_dir": "tmp"
  },
  "logging": {
    "enabled": true,
    "level": "INFO",
    "write_to_logs_dir": true,
    "legacy_root_log_detection": true
  },
  "state": {
    "enabled": true,
    "prefer_state_dir": true,
    "legacy_root_state_detection": true
  },
  "runtime": {
    "standalone_mode": true,
    "create_missing_directories": true,
    "safe_startup_validation": true
  },
  "compatibility": {
    "backward_aware": true,
    "do_not_delete_legacy_files": true,
    "report_legacy_artifacts": true
  }
}

## Migration Notes

Current validated Windows output model:

CURRENT_OUTPUT_MODEL=MIXED
ROOT_JSON_PRESENT=NO
ROOT_SQLITE_PRESENT=NO
ROOT_DB_PRESENT=NO
ROOT_LOG_PRESENT=YES
LOGS_LOG_PRESENT=YES
LOGS_JSON_PRESENT=NO
LOGS_SQLITE_PRESENT=NO
LOGS_DB_PRESENT=NO

Implication:

- State artifacts are not currently observed in root or logs.
- Log artifacts are currently mixed between root and logs.
- Future standalone behavior should centralize logs under logs/.
- Existing root-level logs should be detected but not deleted automatically.

## Non-Goals

The following actions are intentionally excluded from this draft:

- No modification to s43.py
- No automatic file movement
- No deletion of legacy root-level logs
- No runtime behavior change

## Approval Gate

The actual config/default.json file has now been created from this approved draft.

CONFIG_DEFAULT_JSON_APPROVED=YES

## Next Recommended Step

Prepare a code-readiness plan for loading config/default.json while preserving existing environment-variable behavior.
