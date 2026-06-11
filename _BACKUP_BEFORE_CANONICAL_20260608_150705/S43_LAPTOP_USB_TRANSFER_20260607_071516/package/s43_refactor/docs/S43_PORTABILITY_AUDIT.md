# S43 Portability Audit

Date: 2026-06-07
Status: PRELIMINARY_FINDINGS
Source: s43.py
Mode: observation only
S43_MODIFIED=NO

## 1. Purpose

This document summarizes portability findings discovered during the standalone migration review.

This document does not authorize modification of s43.py.

## 2. Baseline Control

Canonical s43.py SHA256:

8270dbb24d728c22e4a1c42b00c148dc0bf81e00454a1932003531963eef3786

Current rule:

S43_EDIT_ALLOWED=NO
PATCH_APPROVED=NO
INVENTORY_MODE=OBSERVATION_ONLY

## 3. Files Created During This Phase

Created audit outputs:

- docs/S43_DEPENDENCY_INVENTORY.md
- docs/S43_IMPORTS_INDEX.txt
- docs/S43_OS_PATH_AUDIT.md
- docs/S43_PORTABILITY_AUDIT.md

## 4. Import Findings

### 4.1 Standard Library Imports Observed

Observed standard library modules include:

- os
- sys
- re
- json
- time
- math
- random
- asyncio
- logging
- traceback
- subprocess
- threading
- sqlite3
- hashlib
- hmac
- base64
- html
- urllib.parse
- pathlib
- datetime
- dataclasses
- typing
- collections
- email.utils
- inspect
- enum
- argparse
- gc

Portability impact:

STANDARD_LIBRARY_DEPENDENCIES=YES
GENERAL_PORTABILITY_RISK=LOW_TO_MEDIUM
REVIEW_REQUIRED_FOR_OS_SUBPROCESS_PATHS=YES

### 4.2 Third-Party Imports Observed

Observed third-party packages:

- requests
- aiohttp
- telebot
- telegram
- rich

Candidate package names for future requirements review:

- requests
- aiohttp
- pyTelegramBotAPI
- python-telegram-bot
- rich

Portability impact:

THIRD_PARTY_DEPENDENCIES=YES
REQUIREMENTS_TXT_NEEDED=YES
PACKAGING_IMPACT=YES

## 5. Termux and Android Findings

Termux-related references were found.

Examples include:

- TERMUX_MODE
- TERMUX_VERSION
- TERMUX_EXEC_MIN_SEC
- TERMUX_EXEC_MAX_SEC
- TERMUX_MOMENTUM_SCANNER
- TERMUX_ALLOW_ENTRY_DEGRADED
- TERMUX_TOP8_WARN_MIN_SEC
- TERMUX_API_WARN_MIN_SEC
- TERMUX_RADAR_WARN_MIN_SEC

Preliminary conclusion:

TERMUX_REFERENCES_FOUND=YES
TERMUX_RUNTIME_PROFILE_FOUND=YES
TERMUX_HARD_REQUIREMENT_PROVEN=NO
ANDROID_ABSOLUTE_PATH_FOUND_BY_CURRENT_SCAN=NO

Important note:

The current scan found many Termux-aware branches and environment variables, but did not prove that the program can only run inside Termux.

## 6. Android Path Findings

The current scan searched for:

- /sdcard
- /storage/emulated
- /data/data
- Windows drive paths such as C:\ or E:\

Preliminary result:

ANDROID_STORAGE_PATH_FOUND=NO_FROM_CURRENT_SCAN
PHONE_ONLY_PATH_FOUND=NO_FROM_CURRENT_SCAN
MACHINE_SPECIFIC_WINDOWS_PATH_FOUND=NO_FROM_CURRENT_SCAN

This must be rechecked with a deeper string-literal scan later.

## 7. Environment Variable Findings

The code heavily uses environment variables.

Observed examples:

- S43_DEBUG_PRINTS
- LOOP_INTERVAL_SEC
- MARKET_AGE_SKIP_SEC
- MARKET_AGE_SLEEP_SEC
- RUNTIME_PROFILE
- TERMUX_MODE
- DEPTH_ENDPOINT_CANDIDATES
- DEPTH_DISCOVER_TIMEOUT_SEC
- DEPTH_REQ_TIMEOUT_SEC
- DEPTH_TIMEOUT_SEC
- DEPTH_RETRY_MAX
- DEPTH_HARD_FAIL_TTL_SEC
- DEPTH_DISK_CACHE_MAX_AGE_SEC
- ARZPLUS_LIVE_ARMED
- LIVE_TRADING
- DRY_RUN
- PP_SYMBOLS
- WALLET_SLOTS
- RECORD_TICKS
- RECORD_DB_PATH
- DASH
- WATCHDOG
- WALLET_CONCURRENCY
- TERM
- DASH_ASCII
- S43_WALLET_REGISTRY_PATH
- S43_WALLET_REGISTRY_JSON

Portability impact:

ENV_CONFIG_DEPENDENCY=HIGH
CONFIG_LAYER_RECOMMENDED=YES
LOCAL_EXAMPLE_CONFIG_RECOMMENDED=YES

## 8. Filesystem Findings

The code performs multiple file operations.

Observed patterns:

- open(path, "r")
- open(path, "w")
- open(path, "rb")
- open(path, "wb")
- os.path.abspath
- os.path.dirname
- Path(...)
- mkdir(...)

Portability impact:

FILESYSTEM_DEPENDENCY=YES
PATH_CONFIG_RECOMMENDED=YES
CACHE_LOG_DB_PATH_REVIEW_REQUIRED=YES

## 9. Subprocess Findings

Subprocess-related functionality was observed.

Observed examples:

- import subprocess
- asyncio.subprocess.Process
- asyncio.create_subprocess_exec

Portability impact:

SUBPROCESS_USAGE=YES
STANDALONE_BUILD_REVIEW_REQUIRED=YES
EXECUTABLE_PACKAGING_RISK=MEDIUM

Required follow-up:

Identify what command or script is executed by create_subprocess_exec and whether it depends on Python interpreter path, shell behavior, or platform-specific command availability.

## 10. Preliminary Risk Classification

### Low Risk

- Standard library imports
- pathlib usage
- json/time/datetime/hashlib/base64 usage

### Medium Risk

- subprocess usage
- many file operations
- environment-heavy runtime
- rich terminal UI behavior
- telegram/bot package compatibility during packaging

### High Review Priority

- Termux-specific runtime branches
- environment variable configuration
- file path resolution
- standalone executable packaging impact

## 11. Current Answers

TERMUX_REQUIRED=NOT_PROVEN
ANDROID_LAYOUT_REQUIRED=NO_FROM_CURRENT_SCAN
PHONE_STORAGE_REQUIRED=NO_FROM_CURRENT_SCAN
USB_TRANSFER_REQUIRED=NO_FROM_CURRENT_SCAN
STANDALONE_POSSIBLE=LIKELY_AFTER_CONFIG_AND_DEPENDENCY_WORK
S43_EDIT_REQUIRED_NOW=NO

## 12. Recommended Next Actions

Next safe actions:

1. Create a requirements candidate document.
2. Run deeper string-literal path scan.
3. Identify all environment variable names.
4. Identify exact subprocess command target.
5. Keep s43.py unchanged.

Recommended next files:

- docs/S43_REQUIREMENTS_CANDIDATE.md
- docs/S43_ENVIRONMENT_VARIABLES_INDEX.txt
- docs/S43_SUBPROCESS_AUDIT.md
- docs/S43_STRING_PATH_SCAN.txt

## 13. Control State

PORTABILITY_AUDIT_CREATED=YES
S43_PY_MODIFIED=NO
PATCH_APPROVED=NO
NEXT_ACTION=REQUIREMENTS_AND_ENV_INDEX
