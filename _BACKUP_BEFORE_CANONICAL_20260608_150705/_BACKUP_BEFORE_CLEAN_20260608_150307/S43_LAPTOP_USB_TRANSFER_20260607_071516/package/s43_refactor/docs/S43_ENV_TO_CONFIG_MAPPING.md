# S43 ENV to Config Mapping

## 1. Purpose

This document defines the first-pass mapping from existing environment variables in `s43.py` to a normalized configuration structure.

Goal:

- reduce direct dependency on raw environment variables
- prepare a standalone configuration layer
- preserve backward compatibility during migration
- avoid direct modification of `s43.py` at this stage

## 2. Current State

Observed condition:

- the project is heavily env-driven
- several variables are platform-specific
- some variables are safety-critical
- some extracted names may be false positives
- manual review is still required before final config implementation

Current decision:

ENV_TO_CONFIG_MAPPING_CREATED=IN_PROGRESS
DIRECT_S43_PATCH_NOW=NO
COMPATIBILITY_MODE_REQUIRED=YES
SAFE_NEXT_STEP=MAPPING_GROUPS

## 3. Mapping Rules

Normalization rules:

1. environment variable names remain uppercase in compatibility mode
2. config keys use lowercase dotted paths
3. boolean-like values should normalize to true or false
4. numeric values should normalize to int or float where applicable
5. path values should move under `paths.*`
6. platform-specific behavior should move under `platform.*`
7. trading and execution flags should remain explicit and safety-first
8. unknown or ambiguous variables should be marked for manual review

## 4. Precedence Model

Proposed precedence:

DEFAULTS < PROFILE < LOCAL_OVERRIDE < ENV < CLI

Meaning:

- defaults provide deterministic baseline behavior
- profiles define environment-specific behavior such as `standalone` or `termux`
- local override supports machine-specific adjustments
- env keeps backward compatibility with current runtime
- cli may override all lower layers when implemented

## 5. Normalized Config Sections

Proposed top-level sections:

- `runtime`
- `network`
- `market`
- `depth`
- `trading`
- `risk`
- `wallet`
- `paths`
- `dashboard`
- `watchdog`
- `health`
- `analytics`
- `ai`
- `platform`

## 6. Initial Mapping Set

### Runtime

- `LOOP_INTERVAL_SEC -> runtime.loop_interval_sec`
- `S43_DEBUG_PRINTS -> runtime.debug_prints`
- `S43_VERBOSE -> runtime.verbose`
- `RUNTIME_PROFILE -> runtime.profile`
- `S43_PROFILE -> runtime.profile_name`

### Network

- `REQ_TIMEOUT_SEC -> network.request_timeout_sec`
- `HTTP_RETRY_BASE_SEC -> network.retry_base_sec`
- `HTTP_RETRY_CAP_SEC -> network.retry_cap_sec`
- `API_STALE_SEC -> network.api_stale_sec`

### Depth

- `DEPTH_REQ_TIMEOUT_SEC -> depth.request_timeout_sec`
- `DEPTH_DISCOVER_TIMEOUT_SEC -> depth.discover_timeout_sec`
- `DEPTH_RETRY_MAX -> depth.retry_max`

### Trading

- `DRY_RUN -> trading.dry_run`
- `LIVE_TRADING -> trading.live_trading`
- `ENABLE_REAL_ORDERS -> trading.enable_real_orders`
- `ARZPLUS_LIVE_ARMED -> trading.live_armed`

### AI

- `AI_TRADER_ENABLE -> ai.trader_enable`
- `AI_EXECUTE_TRADES -> ai.execute_trades`
- `AI_SIGNAL_ONLY -> ai.signal_only`

Status:

MAPPING_PART_1_WRITTEN=YES
FILE_COMPLETE=NO
NEXT_ACTION=MAPPING_PART_2
## 7. Additional Mapping Groups

### Risk

- `MAX_OPEN_POSITIONS -> risk.max_open_positions`
- `MAX_NOTIONAL_USDT -> risk.max_notional_usdt`
- `STOP_LOSS_PCT -> risk.stop_loss_pct`
- `TAKE_PROFIT_PCT -> risk.take_profit_pct`
- `MAX_DAILY_LOSS_PCT -> risk.max_daily_loss_pct`

### Paths

- `S43_DATA_DIR -> paths.data_dir`
- `S43_LOG_DIR -> paths.log_dir`
- `S43_CACHE_DIR -> paths.cache_dir`
- `S43_EXPORT_DIR -> paths.export_dir`
- `STATE_PATH -> paths.state_path`
- `RECORD_DB_PATH -> paths.record_db_path`
- `DASH_EXPORT_PATH -> paths.dashboard_export_path`
- `PP200_LOG_PATH -> paths.pp200_log_path`

### Dashboard

- `DASH_REFRESH_SEC -> dashboard.refresh_sec`
- `DASH_HEAD_MAX_CHARS -> dashboard.head_max_chars`
- `DASHBOARD_ENABLE -> dashboard.enable`
- `DASH_EXPORT_PATH -> dashboard.export_path`

### Watchdog and Health

- `WATCHDOG_ENABLE -> watchdog.enable`
- `WATCHDOG_MEM_HARD_MB -> watchdog.mem_hard_mb`
- `SELF_RESTART -> watchdog.self_restart`
- `HEALTH_WD_INTERVAL_SEC -> health.watchdog_interval_sec`
- `MEM_SCRUB_SEC -> health.mem_scrub_sec`

### Platform

- `TERMUX_MODE -> platform.termux_mode`
- `TERMUX_* -> platform.termux_settings`
- `S43_PROFILE -> platform.profile`
- `RUNTIME_PROFILE -> platform.runtime_profile`

### Market and API

- `API_STALE_SEC -> market.api_stale_sec`
- `ARZPLUS_* -> market.arzplus_settings`
- `DEPTH_* -> depth.settings`

## 8. Compatibility Policy

During migration, existing environment variables must continue to work.

Compatibility requirements:

- do not remove current env behavior immediately
- config loader should read normalized config first
- env values may override config values
- safety-critical env flags must remain explicit
- live trading must never become enabled by default

Required safety defaults:

LIVE_TRADING_DEFAULT=FALSE
DRY_RUN_DEFAULT=TRUE
TERMUX_MODE_DEFAULT=FALSE
SELF_RESTART_DEFAULT=FALSE

## 9. Manual Review Required

The following groups require deeper review before final implementation:

- all `ARZPLUS_*` variables
- all wallet-related variables
- all exchange/API endpoint variables
- all subprocess/restart variables
- all Termux-specific command/path variables
- ambiguous extraction results such as `YES`, `CRITICAL`, and `WALLET_`
- trading execution flags and live order switches
- database and migration paths

Status:

MANUAL_REVIEW_REQUIRED=YES
FALSE_POSITIVE_POSSIBLE=YES
FINAL_MAPPING_APPROVED=NO

## 10. Proposed Next Files

Recommended next documentation files:

- `docs/S43_SUBPROCESS_AUDIT.md`
- `docs/S43_PATHS_AND_STATE_INVENTORY.md`
- `docs/S43_CONFIG_DEFAULT_JSON_DRAFT.md`
- `docs/S43_PROFILE_STANDALONE_DRAFT.md`
- `docs/S43_PROFILE_TERMUX_DRAFT.md`

## 11. Design Decision Summary

Current design decision:

ENV_TO_CONFIG_MAPPING_CREATED=YES
MAPPING_PART_1_WRITTEN=YES
MAPPING_PART_2_WRITTEN=YES
CONFIG_LAYER_APPROACH=ADOPT
ENV_COMPATIBILITY_MODE=KEEP
DIRECT_S43_PATCH_NOW=NO
SAFE_NEXT_STEP=SUBPROCESS_AUDIT_OR_PATHS_INVENTORY

## 12. Control State

S43_PY_MODIFIED=NO
PATCH_APPROVED=NO
CONFIG_LAYER_MODE=DESIGN_ONLY
MAPPING_FINALIZED=NO
NEXT_ACTION=SUBPROCESS_AUDIT_OR_PATHS_INVENTORY
