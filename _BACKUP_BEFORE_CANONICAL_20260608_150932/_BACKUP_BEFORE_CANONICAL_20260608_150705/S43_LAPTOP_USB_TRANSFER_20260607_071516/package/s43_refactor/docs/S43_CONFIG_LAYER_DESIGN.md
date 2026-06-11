# S43 Config Layer Design

Date: 2026-06-07
Status: DESIGN_DRAFT
Mode: no-change-to-s43
S43_MODIFIED=NO

## 1. Purpose

This document defines a proposed configuration abstraction layer for s43.py portability work.

This is a design-only document.
This document does not modify s43.py.
This document does not finalize implementation details.
This document exists to prepare a safe standalone migration path.

## 2. Baseline Control

Canonical s43.py SHA256:

8270dbb24d728c22e4a1c42b00c148dc0bf81e00454a1932003531963eef3786

Control state:

S43_EDIT_ALLOWED=NO
PATCH_APPROVED=NO
CONFIG_LAYER_MODE=DESIGN_ONLY

## 3. Problem Statement

Current observations suggest that s43.py is heavily environment-driven.

This creates the following portability issues:

- runtime behavior depends on many environment variables
- defaults are not centrally documented
- platform-specific branches may be mixed with feature flags
- state/file paths may be injected from the environment
- standalone operation is difficult without a reproducible config model

Conclusion:

ENV_DEPENDENCY_HIGH=YES
CONFIG_LAYER_REQUIRED=YES

## 4. Design Goals

The config layer should aim to provide:

1. a single normalized configuration object
2. deterministic defaults for non-Termux environments
3. optional environment variable override support
4. optional profile-based loading
5. separation between platform profile and feature configuration
6. safe migration path without immediate logic deletion
7. support for Windows/Linux standalone execution
8. future ability to retire scattered env lookups

## 5. Non-Goals

This phase will not:

- rewrite strategy logic
- remove trading logic
- remove watchdog logic
- remove dashboard logic
- patch every os.getenv call immediately
- prove runtime correctness yet

## 6. Proposed Configuration Sources

Recommended precedence order:

1. built-in safe defaults
2. profile file
3. local override file
4. environment variables
5. explicit command-line overrides in future

Interpretation:

DEFAULTS < PROFILE < LOCAL_OVERRIDE < ENV < CLI

## 7. Proposed File Set

Recommended candidate files:

- config/default.json
- config/profiles/standalone.json
- config/profiles/termux.json
- config/local.json
- .env
- .env.example

Alternative YAML variant is possible, but JSON is preferred for simplicity and portability.

## 8. Proposed Normalized Structure

Suggested high-level config sections:
```json
{
  "runtime": {},
  "network": {},
  "market": {},
  "depth": {},
  "trading": {},
  "risk": {},
  "wallet": {},
  "paths": {},
  "dashboard": {},
  "watchdog": {},
  "health": {},
  "analytics": {},
  "ai": {},
  "platform": {}
}

Purpose of each section:

- runtime: loop timing, debug flags, global switches
- network: HTTP timeouts, retry/backoff, DNS behavior
- market: snapshot freshness, market polling behavior
- depth: orderbook/depth endpoints, cache, retry policy
- trading: live/dry-run modes, entry/exit execution controls
- risk: limits, notional caps, stop-loss / take-profit values
- wallet: wallet slots, registry, concurrency
- paths: state files, journals, caches, database files
- dashboard: terminal UI and refresh behavior
- watchdog: restart, memory, and process supervision
- health: monitoring thresholds and halt behavior
- analytics: signal and score tuning
- ai: AI/ML feature toggles
- platform: termux, non-termux, and platform-specific behavior

## 9. Proposed Platform Model

Instead of treating Termux as the entire runtime identity, use a platform profile model.

Recommended conceptual model:

- platform.name = standalone
- platform.name = termux
- platform.name = custom

Platform-specific settings should be isolated under:

json
{
  "platform": {
"name": "standalone",
"termux_mode": false
  }
}

This avoids mixing platform assumptions into unrelated strategy config.

## 10. Proposed Migration Strategy

Safe staged migration:

### Stage 1: Documentation only

- inventory env variables
- group variables
- identify path, state, runtime, and platform categories

Status:

COMPLETED_OR_IN_PROGRESS=YES

### Stage 2: Config design

- define normalized schema
- define source precedence
- define platform profile model

Status:

CURRENT_STAGE=YES

### Stage 3: Default profile drafting

- create standalone-safe defaults
- create termux profile mapping
- mark unknown values explicitly

### Stage 4: Mapping layer

- map env var names to normalized config keys
- document conversion rules
- define bool, int, float, and list parsers

### Stage 5: Loader implementation

- create config loader module outside s43.py
- no invasive edits initially
- verify loader can reproduce env-driven behavior

### Stage 6: Controlled integration

- replace scattered env reads gradually
- preserve compatibility mode
- keep fallback path during transition

### Stage 7: Cleanup

- deprecate redundant env-only branches
- simplify platform-specific code if safe

## 11. Env-to-Config Mapping Concept

Examples:

- LOOP_INTERVAL_SEC -> runtime.loop_interval_sec
- S43_DEBUG_PRINTS -> runtime.debug_prints
- REQ_TIMEOUT_SEC -> network.request_timeout_sec
- HTTP_RETRY_BASE_SEC -> network.retry_base_sec
- HTTP_RETRY_CAP_SEC -> network.retry_cap_sec
- DEPTH_FETCH_TIMEOUT_SEC -> depth.fetch_timeout_sec
- DEPTH_RETRY_MAX -> depth.retry_max
- LIVE_TRADING -> trading.live_trading
- DRY_RUN -> trading.dry_run
- MAX_OPEN_POSITIONS -> risk.max_open_positions
- STOP_LOSS_PCT -> risk.stop_loss_pct
- TAKE_PROFIT_PCT -> risk.take_profit_pct
- STATE_PATH -> paths.state_path
- RECORD_DB_PATH -> paths.record_db_path
- DASH_REFRESH_SEC -> dashboard.refresh_sec
- WATCHDOG_MEM_HARD_MB -> watchdog.mem_hard_mb
- HEALTH_WD_INTERVAL_SEC -> health.watchdog_interval_sec
- AI_TRADER_ENABLE -> ai.trader_enable
- TERMUX_MODE -> platform.termux_mode

## 12. Type Normalization Requirements

The future loader should support normalized parsing for:

- bool
- int
- float
- string
- string list
- path
- enum-like values

Examples:

- "1", "true", "yes", "on" -> true
- "0", "false", "no", "off" -> false

Special handling likely required for:

- percentages
- basis points
- durations in seconds
- path lists
- endpoint candidate lists

## 13. Defaulting Policy

Recommended default policy:

- safe defaults for standalone mode
- explicit null or unknown for unresolved high-risk parameters
- no silent enabling of live trading
- no silent enabling of AI execution
- no silent enabling of self-restart behaviors

Recommended baseline safety:

LIVE_TRADING_DEFAULT=FALSE
DRY_RUN_DEFAULT=TRUE
SELF_RESTART_DEFAULT=FALSE
TERMUX_MODE_DEFAULT=FALSE

## 14. Compatibility Policy

Transition should preserve compatibility by allowing:

- existing env variables to continue working
- profile-based runs to coexist with env-based runs
- legacy behavior to remain available until verified

Interpretation:

BREAKING_CHANGE_ALLOWED_NOW=NO
COMPATIBILITY_MODE_REQUIRED=YES

## 15. Risks

Main risks:

- hidden coupling between env flags and logic branches
- undocumented required variables
- path assumptions embedded outside env lookups
- subprocess or platform behavior not yet fully audited
- unsafe defaults if migration is rushed

## 16. Recommended Next Documents

Next recommended files:

- docs/S43_ENV_DEFAULTS_CANDIDATE.md
- docs/S43_ENV_TO_CONFIG_MAPPING.md
- docs/S43_SUBPROCESS_AUDIT.md
- docs/S43_PATHS_AND_STATE_INVENTORY.md

## 17. Design Decision Summary

Current design decision:

CONFIG_LAYER_APPROACH=ADOPT
PROFILE_MODEL_APPROACH=ADOPT
ENV_COMPATIBILITY_MODE=KEEP
DIRECT_S43_PATCH_NOW=NO
SAFE_NEXT_STEP=ENV_DEFAULTS_CANDIDATE

## 18. Control State

CONFIG_LAYER_DESIGN_CREATED=YES
S43_PY_MODIFIED=NO
PATCH_APPROVED=NO
NEXT_ACTION=ENV_DEFAULTS_CANDIDATE


