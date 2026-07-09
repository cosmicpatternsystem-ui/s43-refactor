# ASO-X Project Constitution
# Single Constitutional Authority and Derived Artifact Policy

## 1. Purpose
This document defines the binding authority hierarchy for ASO-X.
Its purpose is to eliminate duplicate authority, prevent governance drift,
and ensure that roadmap, policy, evidence, and validation operate under one model.

## 2. Core Rule
ASO-X shall operate under a single constitutional authority model.

No file, validator, test, script, or document may assert an independent
canonical authority outside the approved hierarchy defined here.

If multiple canonical claims exist, the repository is in an invalid state.

## 3. Authority Hierarchy

### Level 0  Constitutional Authority
This file (`PROJECT_CONSTITUTION.md`) defines the governance hierarchy and
authority model of the repository.

### Level 1  Canonical Operational Sources
Canonical operational sources are the approved source-of-truth artifacts used
to drive repository state and enforcement.

These include:
- the approved roadmap state artifact(s)
- repository enforcement configuration
- validator-recognized state contracts
- explicitly designated governance control files

A canonical operational source must be uniquely defined.
If more than one file claims the same canonical role, the conflict must fail validation.

### Level 2  Derived Views
Derived files may present, summarize, or publish information from canonical sources,
but they must not redefine authority.

Derived artifacts must be reproducible from canonical sources and must not introduce
independent governance meaning.

### Level 3  Legacy or Archived Material
Legacy, archived, historical, or reference-only files are non-authoritative.

They may be retained for audit and history, but they must not be used by validators,
automation, release logic, or decision workflows as active authority.

## 4. Repository Rules

### 4.1 Single-Voice Governance
ASO-X must maintain one constitutional voice.
Roadmap, governance, policy, evidence, and validation must align to the same authority model.

### 4.2 No Duplicate Canonical Claims
No document, validator, or test may create duplicate canonical authority.
Any such duplication is a repository defect.

### 4.3 Pull Request Governance
Changes to repository policy, roadmap authority, governance hierarchy,
validation rules, or evidence contracts must be introduced through a pull request.

Direct mutation of `main` is not an accepted governance path.

### 4.4 Derived Documents Are Subordinate
Public summaries, convenience documents, and generated views are subordinate to canonical sources.

### 4.5 Legacy Material Must Be Explicit
Legacy material must be clearly marked as legacy, archived, historical,
deprecated, or non-authoritative.

## 5. Validation Expectations
The repository should enforce this constitution through validators, tests,
and CI gates wherever practical.

At minimum, validation must evolve toward detecting:
- duplicate canonical declarations
- conflicting authority definitions
- use of legacy artifacts as active authority
- divergence between canonical state and derived views

## 6. Evidence and Durability
Evidence records must be immutable, schema-valid where applicable,
and retained according to repository policy.

Repository truth must remain repo-resident, reviewable, and durable over time.

## 7. Change Control
This constitution may be amended only through an explicit pull request
whose purpose clearly states the governance change being introduced.

Broad unrelated edits must not be bundled with constitutional changes.