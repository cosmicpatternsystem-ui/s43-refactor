# P2.0 Production Readiness Checklist

## Purpose

This checklist defines the minimum production readiness baseline for ASO-X release candidates.

## Required Checks

A release candidate is production-ready only when:

- source branch is derived from current `main`
- pull request checks are green
- policy gate passed
- safe merge path is available
- release scope is documented
- rollback protocol is documented
- incident response owner is identified
- dependency freeze decision is recorded
- artifact integrity evidence exists
- audit evidence exists

## Blocking Conditions

A release candidate is blocked if:

- worktree is dirty
- checks are failing
- direct push to `main` is required
- unaudited merge is required
- rollback target is unknown
- dependency state is uncontrolled
- artifact integrity is unknown

## Go/No-Go Verification

A formal go/no-go decision is required before production release execution.
Verification must confirm release scope, readiness evidence, rollback readiness, and accountable approval.
