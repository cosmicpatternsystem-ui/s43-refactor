# FUTURE PHASES — POST-VALIDATION ROADMAP

## Current Confirmed State
- Repository: ~/s43_refactor
- Target: s43.py
- Validation: PHOENIX_SELFTEST: OK
- SHA256: 0809115f0f433b93ad9776730b1fb665f916d17b2e15073fa80a003915dffda1
- Governance: SAFE-NO-TRADE ACTIVE
- State: FROZEN & SEALED
- Next Mandatory Gate: HUMAN AUDIT

---

## Phase 17 — Human Audit & Formal Merge Review
**Goal:** Review local diff and confirm architectural quality before any git integration.

Checklist:
- Review `s43.py.local.diff`
- Review `phase13_human_audit_package_*.tar.gz`
- Review `phase14_handoff_seal_*.tar.gz`
- Confirm `get_best_snapshot` fallback chain is acceptable
- Confirm `_market_snapshot`, `feed._cache`, `_phoenix_px_hist`, `_spot_cache` usage is safe
- Confirm `NO_DATA`, `DEPTH_REQUIRED`, `NO_DEPTH_PRICE` behavior is correct
- Decide whether change should be committed standalone or bundled

Exit Criteria:
- Human approval recorded
- Merge authorization explicitly granted

---

## Phase 18 — Dry-Run / Sandbox Validation
**Goal:** Run strategy against live market data without real trading.

Checklist:
- No live order placement
- Verify snapshot freshness behavior
- Verify stale_reason transitions
- Verify spot-only readiness gates
- Verify logging quality under real feed conditions
- Capture evidence logs

Exit Criteria:
- Stable dry-run logs
- No unexpected crash or unsafe signal generation

---

## Phase 19 — Hardening & Failure Handling
**Goal:** Make runtime behavior production-grade.

Checklist:
- Add strategic exception handling
- Improve structured logging
- Add reconnect / retry handling
- Add watchdog or supervised restart design
- Review timeout handling
- Review data integrity checks

Exit Criteria:
- Failure modes documented
- Recovery behavior defined and tested

---

## Phase 20 — Risk Controls & Circuit Breakers
**Goal:** Ensure system knows when NOT to trade.

Checklist:
- Max daily loss guard
- Slippage guard
- No-data / stale-data trade blocks
- Spread / depth safety checks
- Emergency kill switch
- Session stop rules

Exit Criteria:
- Risk controls tested and documented
- Unsafe market conditions blocked automatically

---

## Phase 21 — Canary Deployment / Minimal Exposure
**Goal:** First controlled production exposure with smallest acceptable size.

Checklist:
- Minimum size only
- Human monitoring active
- Compare theoretical vs actual execution
- Verify order acknowledgements
- Verify cancel/stop behavior
- Capture full evidence package

Exit Criteria:
- No safety breach
- Execution quality acceptable

---

## Phase 22 — Monitoring & Operational Dashboard
**Goal:** Establish ongoing operational visibility.

Checklist:
- Structured logs
- Health metrics
- Error counters
- Feed freshness visibility
- Runtime state summary
- Alerting plan

Exit Criteria:
- Operator can assess health in real time
- Alerts available for critical failure conditions

---

## Non-Negotiable Rules
- NO COMMIT before human audit approval
- NO MERGE before explicit authorization
- NO LIVE TRADING before dry-run and risk controls
- NO DEPLOYMENT before hardening review
- SAFE-NO-TRADE remains ACTIVE until governance changes are formally approved
