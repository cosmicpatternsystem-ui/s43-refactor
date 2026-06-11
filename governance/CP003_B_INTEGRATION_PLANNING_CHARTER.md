# CP003-B Integration Planning Charter

## Status

- Phase: CP003-B
- Branch: cp003-b-integration-planning
- Base tag: s43-cp003-a-locked
- Start tag: s43-cp003-b-start
- Base commit: 1f65034a92afa4bd10d7cf20e4fd07266387372e
- Runtime integration: UNAUTHORIZED
- Live trading: UNAUTHORIZED
- Code mutation mode: PLANNING_AND_GOVERNANCE_ONLY

## Purpose

This document opens the CP003-B planning boundary without authorizing runtime integration.

CP003-B is intended to define, review, and approve the integration architecture before any executable baseline mutation is performed.

## Governance Ruling

- CP003-A remains locked.
- CP003-B starts from the locked CP003-A baseline.
- Runtime integration remains unauthorized.
- Live trading remains unauthorized.
- Baseline executable files remain protected unless a later governance receipt explicitly authorizes a specific mutation.
- Any post-lock change must be traceable by branch, commit, and receipt.

## No-Touch Set

The following files and areas must not be modified during the planning-only stage:

- s43_instrumented_LATEST.py
- 11029.py
- Existing baseline executable logic
- Existing governance receipts and manifests from CP003-A
- Any file that changes runtime behavior
- Any file that imports cp003_scaffold into executable baseline flow
- Any file that enables live trading, broker connectivity, or order execution

## Allowed-Touch Set

The following changes are allowed during CP003-B planning-only work:

- New governance documents under governance/
- New architecture notes under governance/
- New planning manifests under governance/
- New review checklists under governance/
- Non-runtime documentation updates
- Read-only analysis outputs that do not modify executable behavior

## Explicitly Unauthorized

The following actions are not authorized in this phase:

- Importing cp003_scaffold from baseline runtime code
- Calling PortfolioBrain from baseline runtime code
- Calling SafetyLawEngine from baseline runtime code
- Calling AuditReceiptEngine from baseline runtime code
- Modifying order execution paths
- Modifying trading authorization gates
- Modifying risk controls
- Enabling live trading
- Replacing or bypassing existing safety boundaries

## Required Before Any Future Runtime Mutation

Before any runtime integration is allowed, CP003-B must produce:

- Integration insertion map
- Baseline impact assessment
- Safety gate compatibility review
- Rollback plan
- Test plan
- Authorized mutation receipt
- Explicit approval statement naming the first allowed integration slice

## Current Decision

CP003-B is opened for planning only.

No runtime integration is authorized by this document.
