# PHASE 18 — DRY-RUN SCENARIO MATRIX

## Governance Notice
- SAFE-NO-TRADE: ACTIVE
- This document does NOT authorize production runtime, deployment, or trading
- This matrix is for sandbox / simulation / dry-run validation planning only
- Dry-run approval, if ever granted, is not equivalent to live approval

---

## 1. Purpose
Define a scenario-by-scenario validation matrix for future engineering dry-run review of frozen `s43.py`, with emphasis on:

- `get_best_snapshot(...)`
- source precedence
- normalization consistency
- stale / incomplete data handling
- readiness safety
- deterministic fallback behavior

---

## 2. Result Classification Reference

### Expected Result Types
- `VALID_SNAPSHOT`
- `NO_DATA`
- `NO_DEPTH_PRICE`
- `DEPTH_REQUIRED`
- `STALE_DATA`
- `SYMBOL_MISMATCH`
- `MALFORMED_SOURCE`
- `UNSAFE_READINESS`
- `AMBIGUOUS_PRECEDENCE`

### Readiness Interpretation
- `READY = NO` unless output is explicitly complete, current enough, internally consistent, and approved by logic
- Any stale, partial, missing-depth, malformed, or conflicting state must not look execution-ready

---

## 3. Scenario Matrix

| Scenario ID | Scenario Name | Input Sources Present | Key Input Condition | Expected Winning Source | Expected Result Type | Expected Readiness | Required Verification Notes |
|---|---|---|---|---|---|---|---|
| S01 | Preferred Snapshot Wins | preferred snapshot + lower-priority fallbacks | preferred source complete and fresh | preferred source | VALID_SNAPSHOT | NO or logic-derived only if explicitly valid in sandbox review | verify deterministic precedence and no fallback overwrite |
| S02 | Legacy Snapshot Only | `bot._snapshots` only | valid symbol entry exists | `bot._snapshots` | VALID_SNAPSHOT or STALE_DATA | NO unless explicitly complete and accepted by logic | verify legacy compatibility |
| S03 | Market Snapshots Only | `bot._market_snapshots` only | symbol present and parseable | `bot._market_snapshots` | VALID_SNAPSHOT or STALE_DATA | NO unless clearly valid | verify lookup behavior |
| S04 | Single Market Snapshot Object | `bot._market_snapshot` only | singleton object contains matching symbol | `bot._market_snapshot` | VALID_SNAPSHOT or SYMBOL_MISMATCH | NO | verify singleton compatibility |
| S05 | Public Ticker Cache Only | `bot.ticker_cache` only | ticker exists but depth fields may be absent | `bot.ticker_cache` | NO_DEPTH_PRICE or VALID_SNAPSHOT | NO unless depth-safe and logic permits | verify normalization and safe downgrade |
| S06 | Internal Ticker Cache Only | `bot._ticker_cache` only | internal cache present | `bot._ticker_cache` | NO_DEPTH_PRICE or VALID_SNAPSHOT | NO unless fully sufficient | verify private cache fallback |
| S07 | Feed Cache Tuple Variant | `bot.feed._cache` only | tuple-shaped cache entry | `bot.feed._cache` | VALID_SNAPSHOT or MALFORMED_SOURCE | NO unless parse is complete and safe | verify tuple parsing |
| S08 | Feed Cache Object Variant | `bot.feed._cache` only | object/dict-like cache entry | `bot.feed._cache` | VALID_SNAPSHOT or MALFORMED_SOURCE | NO unless parse is complete and safe | verify object parsing |
| S09 | Feed Cache Malformed | `bot.feed._cache` only | missing required fields / bad shape | none safely accepted | MALFORMED_SOURCE | NO | verify fail-safe rejection |
| S10 | Phoenix + Spot Reconstruction | `bot._phoenix_px_hist` + `bot.feed._spot_cache` | reconstruction path available | reconstruction path | VALID_SNAPSHOT or STALE_DATA | NO unless reconstruction is complete and acceptable | verify `dp_pct`, time alignment, symbol alignment |
| S11 | Phoenix Present, Spot Missing | `bot._phoenix_px_hist` only | insufficient reconstruction inputs | none safely accepted | NO_DATA or NO_DEPTH_PRICE | NO | verify no fabricated completeness |
| S12 | Spot Present, Phoenix Missing | `bot.feed._spot_cache` only | spot exists without full reconstruction support | spot cache fallback or none | NO_DEPTH_PRICE or NO_DATA | NO | verify safe handling |
| S13 | No Usable Data | no valid source | all sources absent or empty | none | NO_DATA | NO | verify no fake snapshot returned |
| S14 | Spot Without Depth | spot-like source only | best bid/ask or depth-required field missing | spot-like source or none | NO_DEPTH_PRICE or DEPTH_REQUIRED | NO | verify no execution-ready state |
| S15 | Mixed Conflicting Sources | multiple sources | prices or timestamps materially disagree | highest-priority valid source only | VALID_SNAPSHOT or AMBIGUOUS_PRECEDENCE | NO unless deterministic and safe | verify conflict resolution |
| S16 | Symbol Mismatch in Source | one or more sources | source payload symbol != requested symbol | none safely accepted | SYMBOL_MISMATCH | NO | verify mismatch is rejected |
| S17 | Stale Preferred, Fresh Fallback | preferred source stale, lower source fresher | precedence vs freshness tension | logic-defined source | STALE_DATA or VALID_SNAPSHOT | NO unless logic explicitly allows and marks safely | verify stale handling policy |
| S18 | Empty Success Risk | source exists but resolves to empty/partial structure | structurally present but semantically unusable | none safely accepted | MALFORMED_SOURCE or NO_DATA | NO | verify no silent success |
| S19 | Partial Normalization Risk | source has enough fields to parse partially | normalization may omit critical semantics | source under test or none | MALFORMED_SOURCE or UNSAFE_READINESS | NO | verify semantic preservation |
| S20 | Readiness False Positive Check | any partial/stale/conflicting source | output accidentally appears tradable | none should be considered ready | UNSAFE_READINESS if observed | NO | escalate immediately if readiness appears true incorrectly |

---

## 4. Per-Scenario Evidence Template
For each executed dry-run scenario, capture:

- Scenario ID:
- Test timestamp (UTC):
- Requested symbol:
- Input source(s) injected:
- Winning source observed:
- Output fields observed:
- `stale_reason` observed:
- Result classification observed:
- Readiness observed:
- Expected vs actual match: YES / NO
- Notes:
- Escalation required: YES / NO

---

## 5. Mandatory Assertions Across All Scenarios
The following assertions should be evaluated for every scenario:

- [ ] source selection is deterministic
- [ ] symbol mapping is correct
- [ ] malformed input fails safely
- [ ] stale input does not masquerade as fresh
- [ ] missing depth does not masquerade as executable depth
- [ ] normalization preserves semantic meaning
- [ ] no partial state appears falsely ready
- [ ] no external live action path is reached
- [ ] evidence is sufficient for human review

---

## 6. Escalation Triggers
Stop the dry-run and escalate to human review immediately if any of the following occurs:

- readiness becomes `YES` for stale, partial, malformed, or conflicting data
- selected source cannot be explained by deterministic precedence
- output symbol differs from requested symbol
- reconstruction creates inconsistent values
- stale detection appears missing or incorrect
- malformed data is accepted as valid
- any code path suggests external live interaction
- logs are insufficient to reconstruct what happened

---

## 7. Scenario Outcome Summary Table
Use this after future dry-run execution.

| Scenario ID | Expected Result | Actual Result | Match (Y/N) | Readiness Safe (Y/N) | Escalate (Y/N) | Notes |
|---|---|---|---|---|---|---|
| S01 |  |  |  |  |  |  |
| S02 |  |  |  |  |  |  |
| S03 |  |  |  |  |  |  |
| S04 |  |  |  |  |  |  |
| S05 |  |  |  |  |  |  |
| S06 |  |  |  |  |  |  |
| S07 |  |  |  |  |  |  |
| S08 |  |  |  |  |  |  |
| S09 |  |  |  |  |  |  |
| S10 |  |  |  |  |  |  |
| S11 |  |  |  |  |  |  |
| S12 |  |  |  |  |  |  |
| S13 |  |  |  |  |  |  |
| S14 |  |  |  |  |  |  |
| S15 |  |  |  |  |  |  |
| S16 |  |  |  |  |  |  |
| S17 |  |  |  |  |  |  |
| S18 |  |  |  |  |  |  |
| S19 |  |  |  |  |  |  |
| S20 |  |  |  |  |  |  |

---

## 8. Follow-On Artifacts
If future dry-run execution is actually authorized, use this matrix together with:

- `PHASE18_ENGINEERING_DRYRUN_CHECKLIST.md`
- `PHASE18_DRYRUN_EXECUTION_LOG.md`
- `PHASE18_DRYRUN_SUMMARY_REPORT.md`

---

## 9. Final Restriction
This document is planning evidence only.

It does NOT authorize:
- live runtime
- deployment
- exchange connectivity for real execution
- real order routing
- production release
- trading activity

