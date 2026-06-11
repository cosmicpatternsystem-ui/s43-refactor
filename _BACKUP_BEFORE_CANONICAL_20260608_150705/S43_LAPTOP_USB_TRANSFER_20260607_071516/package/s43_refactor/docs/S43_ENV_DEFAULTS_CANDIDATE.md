# S43 Environment Defaults Candidate

Date: 2026-06-07
Status: DEFAULTS_CANDIDATE_DRAFT
Mode: design-only
S43_MODIFIED=NO

## 1. Purpose

This document defines candidate safe default values for running s43 outside Termux.

This is a design-only document.
This document does not modify s43.py.
This document does not enable live trading.
This document does not finalize implementation defaults.

## 2. Baseline Control

Canonical s43.py SHA256:

8270dbb24d728c22e4a1c42b00c148dc0bf81e00454a1932003531963eef3786

Control state:

S43_EDIT_ALLOWED=NO
PATCH_APPROVED=NO
CONFIG_LAYER_MODE=DESIGN_ONLY
DEFAULTS_MODE=CANDIDATE_ONLY

## 3. Source Notes

The current project is highly environment-driven.

Observed dependency state:

ENV_CONFIG_DEPENDENCY=VERY_HIGH
TERMUX_DEPENDENCY_TYPE=PROFILE_DEPENDENCY
STANDALONE_MIGRATION_POSSIBLE=YES

Important extracted observations:

- TERMUX_MODE is used as a platform behavior switch.
- LOOP_INTERVAL_SEC has different effective behavior between Termux and server-like profiles.
- Depth/network timeouts and retry values are environment-sensitive.
- Live trading must not be silently enabled.
- Standalone defaults must be conservative and reproducible.

Reference observations from s43.py extraction:

- DRY_RUN observed near line 292
- LOOP_INTERVAL_SEC observed near line 293
- RUNTIME_PROFILE observed near line 331
- DEPTH_DISCOVER_TIMEOUT_SEC observed near line 1277
- DEPTH_REQ_TIMEOUT_SEC observed near line 1462
- DEPTH_RETRY_MAX observed near line 5216
- ARZPLUS_LIVE_ARMED observed near lines 7271 and 13347
- DASH_EXPORT_PATH observed near line 13841
- TERMUX_MODE detection observed near line 21823

## 4. Defaulting Principles

Standalone defaults should follow these principles:

1. prefer safety over speed
2. prefer dry-run over live execution
3. prefer explicit paths over platform-specific assumptions
4. prefer disabled self-restart until audited
5. prefer deterministic values over auto-detection
6. preserve compatibility with existing env variables
7. avoid enabling trading, AI execution, or restart features by default

Required safety position:

LIVE_TRADING_DEFAULT=FALSE
DRY_RUN_DEFAULT=TRUE
AI_EXECUTION_DEFAULT=FALSE
SELF_RESTART_DEFAULT=FALSE
TERMUX_MODE_DEFAULT=FALSE

## 5. Candidate Standalone Profile Identity

Recommended standalone identity:
```env
TERMUX_MODE=0
RUNTIME_PROFILE=standalone
S43_PROFILE=standalone

Rationale:

- TERMUX_MODE should be explicit.
- Runtime profile should not rely on Android or Termux detection.
- Standalone behavior should be reproducible on Windows and Linux.

## 6. Runtime Defaults Candidate

| Variable | Candidate Standalone Default | Safety Level | Notes |
|---|---:|---|---|
| TERMUX_MODE | 0 | safe | Explicit non-Termux mode |
| RUNTIME_PROFILE | standalone | safe | Replaces implicit termux/server profile naming |
| S43_PROFILE | standalone | safe | Future config-layer profile selector |
| DRY_RUN | 1 | critical | Prevents real execution by default |
| LIVE_TRADING | 0 | critical | Must remain disabled unless explicitly approved |
| LOOP_INTERVAL_SEC | 2.0 | medium | Observed standalone/server-like candidate |
| S43_DEBUG_PRINTS | 0 | safe | Avoid noisy default output |
| S43_VERBOSE | 0 | safe | Keep default output controlled |

Candidate env block:

env
TERMUX_MODE=0
RUNTIME_PROFILE=standalone
S43_PROFILE=standalone
DRY_RUN=1
LIVE_TRADING=0
LOOP_INTERVAL_SEC=2.0
S43_DEBUG_PRINTS=0
S43_VERBOSE=0

## 7. Network Defaults Candidate

| Variable | Candidate Standalone Default | Safety Level | Notes |
|---|---:|---|---|
| REQ_TIMEOUT_SEC | 10.0 | safe | General HTTP timeout candidate |
| HTTP_RETRY_BASE_SEC | 0.5 | safe | Conservative retry base |
| HTTP_RETRY_CAP_SEC | 5.0 | safe | Prevents excessive backoff |
| DEPTH_REQ_TIMEOUT_SEC | 5.0 | medium | Extracted standalone/server-like candidate |
| DEPTH_DISCOVER_TIMEOUT_SEC | 2.0 | medium | Extracted standalone/server-like candidate |
| DEPTH_RETRY_MAX | 3 | medium | Extracted standalone/server-like candidate |

Candidate env block:

env
REQ_TIMEOUT_SEC=10.0
HTTP_RETRY_BASE_SEC=0.5
HTTP_RETRY_CAP_SEC=5.0
DEPTH_REQ_TIMEOUT_SEC=5.0
DEPTH_DISCOVER_TIMEOUT_SEC=2.0
DEPTH_RETRY_MAX=3

## 8. Trading Safety Defaults Candidate

| Variable | Candidate Standalone Default | Safety Level | Notes |
|---|---:|---|---|
| DRY_RUN | 1 | critical | Mandatory safe default |
| LIVE_TRADING | 0 | critical | Must not be enabled silently |
| ARZPLUS_LIVE_ARMED | NO | critical | Do not arm live execution by default |
| MAX_OPEN_POSITIONS | 0 | critical | No live positions by default |
| ENABLE_REAL_ORDERS | 0 | critical | Explicitly disabled if supported |
| AI_TRADER_ENABLE | 0 | critical | AI trading disabled by default |

Candidate env block:

env
DRY_RUN=1
LIVE_TRADING=0
ARZPLUS_LIVE_ARMED=NO
MAX_OPEN_POSITIONS=0
ENABLE_REAL_ORDERS=0
AI_TRADER_ENABLE=0

## 9. Risk Defaults Candidate

| Variable | Candidate Standalone Default | Safety Level | Notes |
|---|---:|---|---|
| MAX_OPEN_POSITIONS | 0 | critical | No exposure by default |
| MAX_NOTIONAL_USDT | 0 | critical | No capital allocation by default |
| STOP_LOSS_PCT | null | unresolved | Must be strategy-reviewed |
| TAKE_PROFIT_PCT | null | unresolved | Must be strategy-reviewed |
| MAX_DAILY_LOSS_PCT | null | unresolved | Must be strategy-reviewed |

Candidate status:

RISK_DEFAULTS_FINALIZED=NO
RISK_VALUES_REQUIRE_REVIEW=YES

## 10. Path Defaults Candidate

Standalone paths should avoid Termux-specific directories.

Recommended relative-path model:

env
S43_DATA_DIR=./data
S43_LOG_DIR=./logs
S43_CACHE_DIR=./cache
S43_EXPORT_DIR=./exports
STATE_PATH=./data/state.json
RECORD_DB_PATH=./data/records.sqlite3
DASH_EXPORT_PATH=./exports/dashboard.json

Path policy:

- prefer relative project-local paths
- avoid hardcoded Android paths
- avoid hardcoded drive-specific Windows paths
- allow local override file or env override later

## 11. Dashboard Defaults Candidate

| Variable | Candidate Standalone Default | Safety Level | Notes |
|---|---:|---|---|
| DASH_REFRESH_SEC | 2.0 | safe | Reasonable terminal refresh |
| DASH_EXPORT_PATH | ./exports/dashboard.json | safe | Local export path |
| DASHBOARD_ENABLE | 1 | safe | UI only; no trading effect |

Candidate env block:

env
DASH_REFRESH_SEC=2.0
DASH_EXPORT_PATH=./exports/dashboard.json
DASHBOARD_ENABLE=1

## 12. Watchdog Defaults Candidate

Self-restart and aggressive process supervision should not be enabled until audited.

| Variable | Candidate Standalone Default | Safety Level | Notes |
|---|---:|---|---|
| WATCHDOG_ENABLE | 0 | safe | Disabled until subprocess audit |
| SELF_RESTART | 0 | critical | Prevents unexpected restarts |
| WATCHDOG_MEM_HARD_MB | null | unresolved | Requires platform-specific review |
| HEALTH_WD_INTERVAL_SEC | 30 | safe | Monitoring interval candidate |

Candidate env block:

env
WATCHDOG_ENABLE=0
SELF_RESTART=0
HEALTH_WD_INTERVAL_SEC=30

## 13. AI Defaults Candidate

AI-assisted features must not execute trades by default.

| Variable | Candidate Standalone Default | Safety Level | Notes |
|---|---:|---|---|
| AI_TRADER_ENABLE | 0 | critical | Disabled by default |
| AI_EXECUTE_TRADES | 0 | critical | No AI execution |
| AI_SIGNAL_ONLY | 1 | safe | Analysis-only if supported |

Candidate env block:

env
AI_TRADER_ENABLE=0
AI_EXECUTE_TRADES=0
AI_SIGNAL_ONLY=1

## 14. Candidate .env.standalone Draft

This block is a candidate only.
It should not be treated as production-approved.

env
TERMUX_MODE=0
RUNTIME_PROFILE=standalone
S43_PROFILE=standalone

DRY_RUN=1
LIVE_TRADING=0
ARZPLUS_LIVE_ARMED=NO
ENABLE_REAL_ORDERS=0
MAX_OPEN_POSITIONS=0
MAX_NOTIONAL_USDT=0

LOOP_INTERVAL_SEC=2.0
S43_DEBUG_PRINTS=0
S43_VERBOSE=0

REQ_TIMEOUT_SEC=10.0
HTTP_RETRY_BASE_SEC=0.5
HTTP_RETRY_CAP_SEC=5.0
DEPTH_REQ_TIMEOUT_SEC=5.0
DEPTH_DISCOVER_TIMEOUT_SEC=2.0
DEPTH_RETRY_MAX=3

S43_DATA_DIR=./data
S43_LOG_DIR=./logs
S43_CACHE_DIR=./cache
S43_EXPORT_DIR=./exports
STATE_PATH=./data/state.json
RECORD_DB_PATH=./data/records.sqlite3
DASH_EXPORT_PATH=./exports/dashboard.json

DASH_REFRESH_SEC=2.0
DASHBOARD_ENABLE=1

WATCHDOG_ENABLE=0
SELF_RESTART=0
HEALTH_WD_INTERVAL_SEC=30

AI_TRADER_ENABLE=0
AI_EXECUTE_TRADES=0
AI_SIGNAL_ONLY=1

## 15. Unknowns Requiring Review

The following values require deeper review before becoming final defaults:

- STOP_LOSS_PCT
- TAKE_PROFIT_PCT
- MAX_DAILY_LOSS_PCT
- WATCHDOG_MEM_HARD_MB
- wallet-related path variables
- exchange/API endpoint variables
- database migration behavior
powershell -NoProfile -Command "Add-Content -Path docs\S43_ENV_DEFAULTS_CANDIDATE.md -Value @'

- subprocess and restart behavior
- platform-specific shell command behavior

Status:

UNRESOLVED_DEFAULTS_EXIST=YES
FINAL_DEFAULTS_APPROVED=NO

## 16. Migration Notes

Recommended next step after this document:

1. create env-to-config mapping document
2. map each existing env variable to normalized config keys
3. classify each variable as safe, risky, platform, path, trading, or unknown
4. create config/default.json draft
5. create config/profiles/standalone.json draft
6. create config/profiles/termux.json draft

No code change should be made until mapping is reviewed.

## 17. Design Decision Summary

Current design decision:

ENV_DEFAULTS_CANDIDATE_CREATED=YES
STANDALONE_DEFAULTS_DEFINED=PARTIAL
LIVE_TRADING_DEFAULT=FALSE
DRY_RUN_DEFAULT=TRUE
TERMUX_MODE_DEFAULT=FALSE
SELF_RESTART_DEFAULT=FALSE
DIRECT_S43_PATCH_NOW=NO
SAFE_NEXT_STEP=ENV_TO_CONFIG_MAPPING

## 18. Control State

S43_PY_MODIFIED=NO
PATCH_APPROVED=NO
CONFIG_LAYER_MODE=DESIGN_ONLY
DEFAULTS_FINALIZED=NO
NEXT_ACTION=ENV_TO_CONFIG_MAPPING
