# PHASE 18 — ENGINEERING DRY-RUN CHECKLIST

## Governance Baseline
- SAFE-NO-TRADE: ACTIVE unless explicitly changed by authorized human governance
- This checklist does NOT authorize live runtime, deployment, or trading
- This checklist is for sandbox / simulation / dry-run planning only

---

## 1. Objective
Define the minimum engineering controls required before any future dry-run or sandbox validation of the frozen `s43.py` state can be considered.

Target goals:
- verify snapshot behavior under controlled inputs
- validate fallback determinism
- detect stale-data edge cases
- confirm no false-ready execution path is created
- keep all testing non-live and non-trading

---

## 2. Preconditions
Dry-run must NOT begin unless all of the following are true:

- [ ] Human audit has been completed
- [ ] Human reviewer has issued written result
- [ ] Reviewed SHA256 matches frozen state
- [ ] Dry-run eligibility is explicitly marked GRANTED by authorized human reviewer
- [ ] SAFE-NO-TRADE constraints for live trading remain active
- [ ] Environment is confirmed sandbox / offline / non-production
- [ ] No exchange keys with live permissions are present
- [ ] No real order-routing path is enabled
- [ ] Logging path for dry-run evidence is prepared

If any item above is false, dry-run must not proceed.

---

## 3. Environment Constraints
Dry-run environment must satisfy all of the following:

- isolated from production execution
- no live broker / exchange connectivity for trading actions
- safe handling of credentials
- deterministic or recorded inputs where possible
- ability to capture logs, errors, and state transitions
- ability to stop immediately without external effect

Reviewer / operator must explicitly verify:

- [ ] No live order execution path exists
- [ ] No deployment target is connected
- [ ] No auto-restart loop can push into runtime accidentally
- [ ] No cron / scheduler / bot supervisor can trigger unintended execution
- [ ] Sandbox markers are visible in runtime logs

---

## 4. Dry-Run Technical Focus
Primary engineering focus for dry-run should remain:

- `get_best_snapshot(...)`
- fallback source precedence
- normalization behavior
- stale-state handling
- depth-required gating
- compatibility with mixed snapshot source shapes

---

## 5. Required Test Scenarios
At minimum, dry-run planning should cover the following scenarios.

### 5.1 Preferred Snapshot Available
- high-quality snapshot source exists
- lower-priority fallbacks also exist

Verify:
- preferred source wins deterministically
- no unnecessary overwrite from fallback source
- normalized output remains internally consistent

### 5.2 Only Legacy/Internal Snapshot Available
Inputs may exist only in:
- `bot._snapshots`
- `bot._market_snapshots`
- `bot._market_snapshot`

Verify:
- compatibility path works
- symbol lookup is correct
- no silent empty-success result is produced

### 5.3 Only Ticker Cache Available
Inputs may exist only in:
- `bot.ticker_cache`
- `bot._ticker_cache`

Verify:
- fallback is deterministic
- field normalization is correct
- output is marked appropriately if depth-quality data is missing

### 5.4 Feed Cache Only
Input available only from:
- `bot.feed._cache`

Verify:
- tuple/object variants do not break parsing
- malformed entries fail safely
- stale or incomplete cache does not look tradable

### 5.5 Phoenix History + Spot Cache Reconstruction
Inputs available through:
- `bot._phoenix_px_hist`
- `bot.feed._spot_cache`

Verify:
- reconstruction logic is consistent
- `dp_pct` calculation behaves as intended
- symbol/time mismatches fail safely
- partial availability does not create misleading readiness

### 5.6 No Usable Data
No valid snapshot source available.

Verify:
- result indicates `NO_DATA`
- no fabricated valid-looking snapshot is returned
- no downstream false readiness is created

### 5.7 Spot Present But Depth Missing
Spot-like information available, but depth price absent where required.

Verify:
- `NO_DEPTH_PRICE` or `DEPTH_REQUIRED` handling is correct
- system does not present this state as execution-ready

### 5.8 Mixed / Conflicting Source Data
Multiple sources present with inconsistent values.

Verify:
- precedence is deterministic
- output does not blend incompatible states unsafely
- reviewer can explain why chosen source won

---

## 6. Output Validation Checklist
For each dry-run scenario, operator should capture:

- input source(s) used
- symbol under test
- chosen snapshot source
- normalized output fields
- stale flags / stale reason
- whether result appears execution-ready
- whether this readiness is correct
- any ambiguity, mismatch, or unsafe behavior

---

## 7. Logging & Evidence Requirements
Dry-run planning should require evidence capture for every run:

- [ ] command or harness used
- [ ] test timestamp (UTC)
- [ ] scenario identifier
- [ ] relevant log excerpt
- [ ] exit code
- [ ] observed stale reason, if any
- [ ] observed snapshot field set
- [ ] reviewer/operator notes

Suggested evidence outputs:
- dry-run logs
- scenario matrix
- anomaly list
- final dry-run summary report

---

## 8. Failure Conditions
Dry-run must be stopped and escalated if any of the following occurs:

- output appears tradable despite stale or incomplete data
- source precedence is ambiguous or inconsistent
- normalization changes semantic meaning unexpectedly
- symbol mismatch is detected
- depth-required logic is bypassed
- any path attempts external live action
- environment isolation is uncertain

---

## 9. Post Dry-Run Decision Outcomes
After future dry-run completion, human reviewer/operator should classify result as one of:

### A. READY FOR HARDENING PHASE
- no critical correctness issues found
- no live-risk behavior observed in sandbox
- acceptable for Phase 19 hardening work

### B. REQUIRES REFACTOR BEFORE HARDENING
- logic broadly works
- one or more structural/safety problems require code revision first

### C. RETURN TO ENGINEERING REVIEW
- dry-run exposed correctness uncertainty
- fallback behavior not trustworthy
- governance or environment controls were insufficient

---

## 10. Non-Negotiable Restrictions
Even if future dry-run is approved:

- NO LIVE TRADING
- NO PRODUCTION DEPLOYMENT
- NO REAL ORDER EXECUTION
- NO MERGE WITHOUT HUMAN AUTHORIZATION
- NO COMMIT WITHOUT GOVERNANCE APPROVAL

Dry-run approval is not equivalent to production approval.

---

## 11. Suggested Follow-On Artifacts
If Phase 18 is ever activated, the following documents should be created:

- `PHASE18_DRYRUN_SCENARIO_MATRIX.md`
- `PHASE18_DRYRUN_EXECUTION_LOG.md`
- `PHASE18_DRYRUN_SUMMARY_REPORT.md`

---

## 12. Sign-Off Preparation Template
Operator / Reviewer Name:
Planned Dry-Run Date (UTC):
Reviewed SHA256:
Dry-Run Eligibility Confirmed: YES / NO
Sandbox Confirmed: YES / NO
Live Trading Disabled: YES / NO
External Order Routing Disabled: YES / NO
Proceed to Dry-Run: YES / NO

Comments:
- 
- 
- 

