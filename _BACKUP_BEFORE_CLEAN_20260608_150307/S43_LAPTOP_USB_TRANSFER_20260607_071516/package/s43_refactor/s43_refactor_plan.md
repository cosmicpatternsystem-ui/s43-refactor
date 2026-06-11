# S43 Readonly Refactor Plan

## 1. Policy

This document is a readonly refactor plan for `s43.py`.

No direct modification is allowed in this phase.

### Explicit restrictions

- Do not edit `s43.py`.
- Do not rewrite `s43.py`.
- Do not apply manual patches to `s43.py`.
- Do not perform restore operations.
- Do not inject monkey patches.
- Use this document only as a planning artifact.

## 2. Probe Summary

Source file:
```text
target_file: s43.py
lines: 29958
bytes: 2620287
sha256: c5b0b5cf1e20dc253d91867d833cf5a02f53324b07f491f4acb891caad45b334
py_compile: PASS

Readonly probe status:

text
s43_readonly_probe.sh: syntax OK
s43.py compile check: PASS
target source modified: NO

## 3. Project Markers

Detected markers:

text
AUTOPATCH_STAGE1_MARKER_count: 1
_s43_autopatch_probe_count: 1

Known marker locations from report:

text
15376:# AUTOPATCH_STAGE1_MARKER
15377:def _s43_autopatch_probe():

Conclusion:

The project contains its own internal autopatch/probe mechanism. Any future code-level change must respect the native project mechanism instead of manual direct editing.

## 4. High-Level Structure Inventory

From readonly report:

text
class_count:       101
def_count:         54
async_def_count:   3
import_count:      23
from_import_count: 6

Important observation:

`grep`-based counts are top-level oriented and do not include all class methods. A future AST-based readonly analyzer should be used for a deeper map.

## 5. Approximate Region Map

Based on top-level class/function locations:

| Region | Approximate Lines | Area |
|---|---:|---|
| Bootstrap and audit guards | 1-700 | startup guards, config, embedded code helpers |
| Core infrastructure | 700-1300 | logger, circuit breaker, rate limiting |
| Exchange/client layer | 1250-5000 | exchange client, market specs, order normalization |
| Market data and signal models | 5000-7100 | feed, signal, positions, analytics |
| Analytics and decision layer | 7100-7900 | analytics engine, memory, sovereign decision |
| Async and health infrastructure | 7900-9200 | event loop, health monitor, retry and resilience |
| Dashboard and risk metrics | 9200-11000 | dashboard, sanity, integrity base |
| Data feed and risk management | 10600-12200 | feed, integrity, risk manager, execution |
| Runtime state and decision cortex | 12200-13000 | dashboard manager, cortex, wallet runtime |
| Runtime telemetry and parser | 12900-15400 | no-trade records, parser, run entry, autopatch probe |
| Recorder and GC runtime | 24200-24400 | recorder child and GC freeze |
| Main runtime entry | 24300-29400 | run/main/selftests/orchestrator |
| Safety and guard helpers | 29400-29958 | env helpers, live order guard, balance guards |

## 6. Duplication and Shadowing Candidates

These are not confirmed bugs. They are candidates for manual review only.

### Candidate 1: duplicate class name

text
667:class _NoopLock:
6426:class _NoopLock:

Risk:

- Later definition may shadow earlier definition at module scope.
- Existing references may depend on local timing or definition order.
- Direct renaming is not allowed in this phase.

Recommended action:

- Document behavior.
- Use readonly AST map in a later phase.
- Do not change source directly.

### Candidate 2: duplicate function name

text
29608:def _audit_only_block(*args, **kwargs):
29638:def _audit_only_block(*args, **kwargs):

Risk:

- The second definition likely shadows the first at module scope.
- This may be intentional safety-layer override.
- Must not be changed without project-compliant patch mechanism.

Recommended action:

- Inspect both definitions in readonly mode.
- Record semantic difference.
- Preserve behavior in any future proposal.

## 7. Sensitive Keyword Summary

From readonly report:

text
eval_count:        2
exec_count:        5
subprocess_count:  7
os_system_count:   0
pickle_count:      0
requests_count:    9
sqlite_count:      9
thread_count:      2
asyncio_count:     251

Interpretation:

These counts do not imply vulnerabilities by themselves. They identify areas that need careful audit.

### Audit priorities

1. `exec(` and `eval(`
2. `subprocess`
3. live trading and order execution guards
4. requests/network boundaries
5. sqlite persistence boundaries
6. asyncio cancellation and lifecycle handling

## 8. Refactor Strategy

### Phase A: Readonly Mapping

Allowed:

- Generate reports.
- Generate AST maps.
- Generate dependency maps.
- Generate duplication maps.
- Generate long-method reports.

Forbidden:

- Editing `s43.py`
- Auto-formatting `s43.py`
- Renaming symbols in `s43.py`
- Reordering imports
- Rewriting functions

### Phase B: Proposal Documents

Allowed outputs:

text
s43_refactor_plan.md
s43_symbol_inventory.txt
s43_duplicate_candidates.txt
s43_risk_keyword_audit.txt
s43_long_blocks_report.txt

### Phase C: Project-Compliant Patch Proposal

Only after review:

- Prepare isolated proposal.
- Reference exact line ranges.
- Preserve behavior.
- Use native project patch/probe mechanism if required.
- Never apply direct patch blindly.

## 9. Recommended Next Readonly Tools

The next tool should be an AST-based readonly analyzer.

Suggested file:

text
s43_ast_inventory.py

Purpose:

- Parse `s43.py` with Python AST.
- List classes and methods.
- List duplicate top-level symbols.
- List large classes/functions.
- List import graph.
- Write report only.
- Do not modify `s43.py`.

## 10. Current Decision

text
S43_SOURCE_COMPILES: YES
DIRECT_REFACTOR_ALLOWED: NO
PATCH_ALLOWED_NOW: NO
READONLY_ANALYSIS_ALLOWED: YES
NEXT_STEP: BUILD_AST_INVENTORY_REPORT
