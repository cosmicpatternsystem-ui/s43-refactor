# S43 Paths and State Inventory

## 1. Purpose

This document records the currently observed state, persistence, database, and export paths referenced by `s43.py`.

Goals:

- identify path-dependent behavior
- prepare standalone-friendly path normalization
- reduce hidden dependency on current working directory
- document persistence surfaces before config-layer implementation

## 2. Current State

Observed condition:

- several important file paths are controlled by environment variables
- some paths fall back to relative filenames in the current working directory
- persistence behavior exists across runtime state, bot state, phoenix state, dashboard export, and SQLite recording
- path normalization is required before safe standalone migration

Current decision:

PATHS_INVENTORY_CREATED=IN_PROGRESS
DIRECT_S43_PATCH_NOW=NO
SAFE_NEXT_STEP=STATE_AND_DB_INVENTORY

## 3. State and Persistence Files

Observed state-related paths:

- `STATE_PATH` -> default `raz_state.json`
- `BOT_STATE_PATH` -> default `bot_state.json`
- `PHOENIX_STATE_PATH` -> default `phoenix_state.json`

Observed behavior notes:

- these files appear to hold runtime or strategy state
- defaults are relative paths
- standalone execution should avoid accidental writes into an unexpected working directory

## 4. Database and Recorder Paths

Observed database-related paths:

- `RECORD_DB_PATH` -> default `raz_ticks.sqlite`

Observed behavior notes:

- this path is persistence-critical
- SQLite behavior may depend on host filesystem and locking conditions
- standalone mode should prefer an explicit normalized path under a data directory

## 5. Export and Log Paths

Observed output-related paths:

- `DASH_EXPORT_PATH` -> dashboard export target
- `PP200_LOG_PATH` -> PP200 monitoring/log path

Observed behavior notes:

- these outputs should move under normalized export/log path control
- path existence and parent directory creation must be reviewed during implementation

Status:

MAPPING_SOURCE_FROM_S43=YES
PART_1_WRITTEN=YES
FILE_COMPLETE=NO
NEXT_ACTION=PATHS_PART_2
## 6. Ghost and Derived State Files

Observed derived or per-entity state paths:

- `ghost_orders_<wallet_id>.json`

Observed behavior notes:

- filename is dynamically constructed
- file count may grow with wallet or identity count
- standalone path policy should place these files in a predictable state subdirectory

## 7. Path Risk Inventory

Main risks in current path handling:

1. relative-path dependence
2. hidden dependence on current working directory
3. mixed persistence surfaces across JSON, SQLite, and export artifacts
4. unclear directory creation guarantees
5. possible cross-platform separator and location issues

## 8. Standalone-Normalized Target Shape

Recommended future target layout:

- `./data/state/`
- `./data/db/`
- `./data/runtime/`
- `./exports/`
- `./logs/`

Suggested future placements:

- `STATE_PATH` -> `./data/state/raz_state.json`
- `BOT_STATE_PATH` -> `./data/state/bot_state.json`
- `PHOENIX_STATE_PATH` -> `./data/state/phoenix_state.json`
- `RECORD_DB_PATH` -> `./data/db/raz_ticks.sqlite`
- `ghost_orders_<wallet_id>.json` -> `./data/state/ghost_orders_<wallet_id>.json`
- `DASH_EXPORT_PATH` -> `./exports/...`
- `PP200_LOG_PATH` -> `./logs/...`

## 9. Rules for Future Config Layer

Future loader/config behavior should ensure:

- all important persistence paths are centrally defined
- relative defaults are resolved from a known project root
- parent directories are created before write operations
- state, db, export, and log outputs are separated by purpose
- environment variable overrides remain supported
- migration does not require immediate modification of `s43.py`

## 10. Unknowns Requiring Follow-Up

Still requires confirmation from source review:

- whether additional `.log` files are created outside `PP200_LOG_PATH`
- whether any PID, lock, temp, cache, or recovery files exist
- whether dashboard export writes a single file or multiple artifacts
- whether state files are atomically written
- whether any absolute Termux-specific path is hardcoded elsewhere

## 11. Control State

PATHS_INVENTORY_CREATED=YES
PATHS_INVENTORY_PART_2=YES
PATHS_INVENTORY_FINALIZED=YES
S43_PY_MODIFIED=NO
NEXT_RECOMMENDED_STEP=SEARCH_FOR_EXTRA_LOG_PID_TEMP_PATHS

## 12. Additional Logging and Temp File Findings

Additional observed filesystem behavior from `s43.py` review:

- default log file path: `logs/trading_bot.log`
- log parent directory is created when needed
- no file-based `.lock` path was confirmed
- JSON/state writes may use temporary `*.tmp` files before atomic replace
- atomic write behavior reduces corruption risk during interrupted writes

Implications for standalone execution:

- the runtime must have write permission in the effective project working directory
- the `logs/` directory should be treated as a first-class managed output path
- temporary files created during atomic writes should remain inside the same target directory
- no Termux-specific hardcoded filesystem path was confirmed in these findings

Recommended documentation outcome:

- keep `logs/trading_bot.log` in the inventory
- treat `*.tmp` as expected transient write artifacts
- no file-lock migration layer is required at this stage

## 13. Final Inventory Snapshot

Observed filesystem shape currently implied by defaults:
```text
project-root/
├─ logs/
│  └─ trading_bot.log
├─ raz_state.json
├─ bot_state.json
├─ phoenix_state.json
├─ raz_ticks.sqlite
└─ *.tmp

## 14. Control Update

EXTRA_LOG_PATHS_REVIEWED=YES
TEMP_WRITE_PATTERN_REVIEWED=YES
FILE_LOCK_PATHS_FOUND=NO
TERMUX_HARDCODED_PATH_IN_THIS_PASS=NO
PATHS_INVENTORY_APPENDIX_ADDED=YES
S43_PY_MODIFIED=NO
NEXT_RECOMMENDED_STEP=CREATE_WINDOWS_PATH_VALIDATION_CHECKLIST

