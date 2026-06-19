# Phase 18 One Copy Paste Automation Standard - 2026-06-14

## Standard

All future operational actions should be delivered as one safe copy/paste PowerShell block whenever practical.

## Requirements

- The block must fail fast.
- The block must set process execution policy safely when needed.
- The block must normalize console output to UTF-8.
- The block must use the repository literal path.
- The block must validate the official branch when operating on protected baseline files.
- The block must validate HEAD and origin when the operation depends on a synchronized baseline.
- The block must refuse unsafe dirty-tree operations.
- The block must allow only explicit expected files to be dirty before approved sync.
- The block must stage only explicit files through approved sync.
- The block must not use blind git add .
- The block must not use manual git push.
- The block must not contain inline explanatory comments.
- The block must print success only after real verification passes.
- The block must be suitable for a single user copy/paste execution.

## Operational Rule

Manual multi-step execution is not the default operating model.

The default operating model is:

1. Prepare one safe PowerShell block.
2. Validate branch and repository state.
3. Create or modify explicit files.
4. Run approved sync.
5. Let approved sync run quality gate, commit, health check, and push.
6. Verify clean state and HEAD equals origin.
7. Print final PASS only after verification.

## Enforcement

Any future workflow that cannot be safely executed as one copy/paste block must explain why and must still preserve approved sync, explicit file staging, quality gate, health check, final verification, and auditability.
