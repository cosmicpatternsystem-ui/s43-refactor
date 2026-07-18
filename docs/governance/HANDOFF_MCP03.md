# HANDOFF_MCP03 - ASO-X Project Transfer Document

> Status: ACTIVE
> Scope: MCP-03 Formal Trading Correctness Envelope
> Repo: `G:\s43_work\s43_g11_work`
> Runtime: Python 3.13, PowerShell 7.6.3, JS
> Baseline dependency: `jsonschema==4.26.0`
> Optional dependencies: `pytest`, `hypothesis`, `ruff`, `mypy`, `z3-solver`

## 1. Project Context

- Project: ASO-X
- Domain: algorithmic trading system with formal governance
- Repository root: `G:\s43_work\s43_g11_work`
- Standards:
  - BOM-free UTF-8
  - LF line endings
  - atomic writes
  - Evidence Ledger
  - Governance-by-Manifest
  - CI integrity
  - 50-year durability target

## 2. Current Repository State

Verified repository state:

- `git status` is clean on `main`
- `HEAD` is aligned with `origin/main`
- PR #313 has been merged
- Branch `governance/mcp03-enforcement-alignment` was merged and deleted
- Reference commit for the merged alignment work: `d63720cd`

Existing execution core is already present:

- `core/`
  - `autonomy/engine.py`
  - `execution_engine/`
  - `intelligence/offline_ai.py`
  - `safety/safety_gate.py`
  - `market_oracle/`
  - `pure_logic/`
- `intelligence/`
  - `backtester.py`
  - `core/engine.py`
  - `core/risk_manager.py`
  - `data_pipeline/ingestor.py`
  - `models/output_contract.py`
  - `strategies/` including momentum and SMA variants
- `ops/`
  - `policy_engine.py`
  - smoke tests such as `g11_capital_kill_switch_smoke.py`
- testing infrastructure
  - `tests/`
  - `pytest.ini`

Existing governance layer is already present:

- `docs/governance/`
  - `ROADMAP_CURRENT.json`
  - `ROADMAP_MANIFEST.json`
  - `GOVERNANCE_FRAMEWORK.md`
  - `SOURCE_OF_TRUTH_HIERARCHY.md`
- `AUDIT/`
  - phases 17 through 42
- `tools/governance.ps1`
- `.github/scripts/governance-guard.ps1`

Important status note:

- MCP-03 currently exists at the governance/enforcement layer
- The formal verification layer for MCP-03 is not yet connected to the live execution core
- Missing connection points include:
  - property-based tests against real trading domain logic
  - formal invariant models
  - deterministic replay enforcement tied to execution behavior

## 3. Locked Architectural Decisions

Do not change these decisions without explicit governance review.

Validation chain:

`LLM Codegen -> Property-Based Testing -> Static Analysis -> Formal Methods -> Deterministic Replay + Backtesting -> CI Gate -> Evidence Ledger`

Interpretation of each stage:

- LLM Codegen:
  - LLM output may accelerate implementation
  - LLM output is never accepted as a source of correctness
- Property-Based Testing:
  - use Hypothesis to generate broad behavioral coverage
- Static Analysis:
  - use `mypy --strict`
  - use `ruff`
- Formal Methods:
  - use TLA+ for order lifecycle modeling where appropriate
  - use Z3 for invariant checking
- Deterministic Replay and Backtesting:
  - validate reproducibility and executable correctness
- CI Gate:
  - only passing evidence-backed changes may proceed
- Evidence Ledger:
  - persist outputs and decision evidence as project artifacts

Core principle:

- The LLM is not the authority for correctness
- Acceptance authority comes from:
  - formal specification
  - generative tests
  - static analysis
  - deterministic replay
  - CI gate
  - signed or recorded evidence

## 4. MCP-03 Scope

MCP-03 scope is intentionally limited to the formal trading correctness envelope.

In-scope state transitions:

- orders
- fills
- positions
- risk
- realized PnL

Core invariants to establish and enforce:

- Risk Limit
  - for all time steps, position must remain within configured risk limits
- Gross Exposure Bound
  - gross exposure must not exceed configured portfolio or instrument boundaries
- Realized PnL Correctness
  - realized profit and loss must match executed fills and position transitions
- Replay Determinism
  - deterministic replay of the same event stream must produce identical outputs
- Idempotent Fill Application
  - duplicate processing of the same fill must not corrupt state
- Conservation Constraints
  - state transitions must preserve accounting consistency across fills, quantities, and PnL

Phased delivery model:

- Phase 1: Spec and Skeleton
- Phase 2: Deterministic Replay
- Phase 3: Formal Core
- Phase 4: CI Enforcement

## 5. Immediate Next Step

Do not build a new skeleton in isolation.

The execution core already exists. The next step is to connect the verification layer to the real code already present in the repository.

Start here:

### Step 1: Audit Existing Domain Logic

Read and map the current implementation in:

- `intelligence/core/risk_manager.py`
- `core/execution_engine/`
- `intelligence/models/output_contract.py`

Goal:

- identify the current domain model
- identify how orders, fills, positions, and risk are represented
- identify where state transitions happen
- identify which functions and classes are the correct attachment points for invariants

Expected output:

- a concise mapping of domain entities to code locations
- a list of functions and methods that mutate or validate trading state

### Step 2: Build the Invariant Specification Pack

Create:

- `specs/invariants/MCP03_INVARIANTS.md`

This document should map each invariant to:

- the relevant code path
- the target class or function
- the enforcement mechanism
- the planned test strategy
- the planned formal model strategy
- the evidence artifact expected from validation

Minimum structure recommendation:

- invariant name
- natural-language definition
- formal intent
- code attachment point
- test method
- replay implication
- formal model note
- evidence output

### Step 3: Add the Property-Based Test Harness

Create:

- `tests/property/test_risk_invariants.py`

Requirements:

- use Hypothesis
- connect tests to the real `risk_manager` implementation
- avoid fake domain abstractions unless absolutely necessary
- focus first on risk-bound and position-bound behavior
- prefer deterministic fixture construction where needed
- ensure failures are diagnosable and evidence-friendly

Initial targets:

- position never exceeds configured risk limit under generated event sequences
- invalid transitions are rejected or blocked
- repeated fill application is either rejected or safely idempotent, depending on intended design

### Step 4: Establish the Static Gate

Run static analysis on:

- `core/`
- `intelligence/`

Initial tools:

- `ruff`
- `mypy --strict`

Initial policy:

- start in reporting mode if necessary
- move to progressive enforcement
- do not weaken correctness expectations permanently
- every suppression must be justified

### Step 5: Add a Minimal Formal Smoke

Create:

- `specs/z3/risk_smoke.py`

Purpose:

- encode a minimal abstract model of the risk invariant
- prove or check that position cannot exceed a specified bound under allowed transitions
- keep the first version intentionally small and readable

This is a smoke layer, not the final formal system.

### Step 6: Integrate Evidence Outputs

Write outputs to artifact locations consistent with the repository pattern, including:

- `artifacts/`
- `out/evidence/`

Every gate introduced for MCP-03 should leave traceable evidence, such as:

- test output
- static analysis output
- formal smoke output
- replay validation output
- references suitable for ledger recording

## 6. Working Rules

Mandatory working rules:

- every change must happen on a new branch
- branch names must use the prefix `governance/` or `mcp03/`
- create a PR for all meaningful changes
- no BOM
- no CRLF
- use atomic writes
- before any PR, ensure these pass:
  - `pytest`
  - `ruff`
  - `mypy`

## 7. Strategic Guidance

Strategic priority is not infrastructure perfection for its own sake.

Primary project direction:

- move toward the first real trade
- begin building an actual track record
- use formal verification to protect live correctness, not to stall delivery indefinitely

Interpretation:

- prioritize correctness where it touches real execution
- prefer thin, enforceable verification slices over broad speculative framework work
- connect evidence-producing controls to the trading path as early as possible

## 8. Recommended Starting Sequence for the Next Session

Recommended execution order:

1. audit `intelligence/core/risk_manager.py`
2. audit `core/execution_engine/`
3. audit `intelligence/models/output_contract.py`
4. write `specs/invariants/MCP03_INVARIANTS.md`
5. add `tests/property/test_risk_invariants.py`
6. add `specs/z3/risk_smoke.py`
7. run `ruff`
8. run `mypy --strict`
9. run `pytest`
10. store outputs in evidence/artifact locations
11. open a PR from an `mcp03/` or `governance/` branch

## 9. Handoff Summary

This document is self-contained.

A new session should be able to begin from Section 5 without requiring prior chat history.

If the next agent follows this document correctly, the first action is:

- inspect the live trading domain implementation
- map invariants to real code
- attach the first verification layer to the existing execution core