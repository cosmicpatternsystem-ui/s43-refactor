# Canonical Roadmap Declaration

Status: Active
Scope: ASO-X / s43-refactor
Canonical source: `docs/ROADMAP.md`
Governance class: 50-year durable roadmap governance
Baseline date: 2026-07-05
Baseline state: CLOSED / MERGED / VERIFIED / BASELINE-RECORDED / CLEAN

## Purpose

This document declares the official roadmap governance model for the repository.

## Canonical Sources

- Human-readable canonical roadmap source: `docs/ROADMAP.md`
- Machine-readable canonical roadmap index: `docs/roadmap/roadmap.index.json`

## Governance Rules

1. `docs/ROADMAP.md` is the canonical human-readable roadmap.
2. `docs/roadmap/roadmap.index.json` is the canonical machine-readable roadmap index.
3. Durable roadmap requirements must have stable IDs.
4. Requirement IDs must never be reused after retirement.
5. Active governance requirements must be CI-validatable where applicable.
6. Governance artifacts must remain portable and long-lived.
7. Repository state is authoritative over prior conversation state.
