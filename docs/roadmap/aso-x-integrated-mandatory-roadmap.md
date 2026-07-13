> DERIVED VIEW - NOT AUTHORITATIVE

# DERIVED VIEW - NOT AUTHORITATIVE

Status: active
Authority: non-prevailing
Canonical machine-readable roadmap state: ROADMAP_CURRENT.json
Canonical human-readable roadmap: ROADMAP_CANONICAL.md
Purpose: Derived/public/traceability view only. This file must not be used as the prevailing roadmap authority.
# ASO-X Integrated Mandatory Roadmap

Status: Mandatory
Scope: ASO-X core repository and all future commercial extensions
Owner: ASO-X maintainers
Durability Target: 50 years
Primary Objective: Non-obsolescent, evidence-retaining, policy-driven, cryptography-agile intelligence infrastructure
Last Updated: 2026-07-05

---

## 1. Executive Mandate

ASO-X MUST evolve from a repository-centered automation project into a durable intelligence operating layer.

The project MUST remain useful, auditable, migratable, and commercially extensible across multiple technology eras, including future post-quantum and hybrid classical/quantum computing environments.

ASO-X MUST NOT depend permanently on any single hosting vendor, runtime, cryptographic algorithm, CI provider, storage backend, or programming language implementation.

This roadmap is mandatory for all future high-impact work.

---

## 2. Long-Horizon Mission

ASO-X exists to provide a durable, policy-governed, evidence-retaining automation and intelligence framework for financial, compliance, audit, release-governance, and commercial decision systems.

The system MUST support:

- global financial intelligence workflows;
- long-term artifact retention;
- auditability and evidence preservation;
- safe concurrent development;
- immutable change history;
- policy-driven automation;
- cryptographic agility;
- post-quantum readiness;
- migration across infrastructure generations;
- commercial module expansion;
- independent verification by future maintainers.

---

## 3. Non-Obsolescence Principles

Every strategic feature MUST satisfy the following questions:

1. Can it be understood 10 years from now?
2. Can it be migrated 20 years from now?
3. Can it be independently verified 50 years from now?
4. Can it survive without GitHub as the sole operational dependency?
5. Can it survive runtime, CI, cloud, and cryptographic algorithm replacement?
6. Does it produce durable evidence when it changes state?
7. Does it have a schema, policy, test, and operational documentation when required?
8. Can commercial modules reuse it without corrupting the core?

If a feature fails these questions, it is not considered ASO-X-grade.

---

## 4. Mandatory Architecture Layers

ASO-X MUST be organized around the following durable architecture layers.

### 4.1 Canonical Data Layer

The canonical data layer MUST define stable, versioned, human-readable, machine-validatable records.

Required practices:

- JSON Schema for durable machine validation;
- Markdown for human-readable governance documents;
- plain text formats for long-term preservation where practical;
- explicit schema versions;
- migration records for breaking changes;
- no undocumented binary-only source of truth.

### 4.2 Policy and Governance Layer

Policy MUST drive critical automation behavior.

The following domains MUST be policy-governed:

- artifact retention;
- audit execution;
- release evidence;
- merge safety;
- branch lifecycle;
- dependency integrity;
- commercial module boundaries;
- cryptographic algorithm lifecycle;
- re-attestation schedules;
- migration requirements.

Hardcoded business-critical behavior SHOULD be avoided unless justified and documented.

### 4.3 Automation Control Plane

`asoctl.py` MUST become the stable control plane for ASO-X operations.

The control plane SHOULD converge toward the following command families:
```text
asoctl doctor
asoctl audit
asoctl retain
asoctl verify
asoctl policy check
asoctl evidence create
asoctl evidence verify
asoctl release evidence
asoctl migrate
asoctl crypto attest
asoctl crypto reattest
asoctl module validate

The CLI MUST remain scriptable, deterministic, and suitable for CI and local execution.

### 4.4 Artifact and Evidence Layer

Every critical operation SHOULD produce durable evidence.

Evidence records SHOULD include:

- artifact identifier;
- artifact hash;
- schema version;
- policy version;
- command or workflow name;
- actor or automation identity when available;
- timestamp;
- result;
- relevant commit SHA;
- dependency or environment summary when required;
- retention classification;
- verification status.

### 4.5 Cryptographic Trust Layer

ASO-X MUST be cryptography-agile.

The project MUST NOT assume that one hash, signature, key type, certificate model, or trust provider remains valid forever.

The cryptographic trust layer MUST support:

- algorithm metadata;
- algorithm deprecation;
- multiple attestations for the same artifact;
- re-attestation over time;
- post-quantum readiness;
- migration away from weakened algorithms;
- external trust anchors where appropriate.

### 4.6 Business Extension Layer

ASO-X MUST support commercial expansion without weakening the core.

Commercial domains MAY include:

- financial intelligence;
- risk intelligence;
- compliance automation;
- artifact custody;
- release governance;
- evidence operations;
- market intelligence;
- enterprise workflow automation;
- audit and assurance tooling.

Extensions MUST respect core policies, schemas, evidence requirements, and security constraints.

### 4.7 Migration and Longevity Layer

Migration MUST be a first-class capability.

The project MUST define and preserve migration paths for:

- schemas;
- policies;
- evidence records;
- artifact formats;
- cryptographic attestations;
- workflow definitions;
- module interfaces;
- runtime dependencies.

Any breaking change MUST include a migration note or migration tool unless explicitly exempted.

---

## 5. Quantum and Post-Quantum Readiness

ASO-X recognizes that future computing systems may include quantum or hybrid classical/quantum infrastructure.

The primary risk to ASO-X is not immediate replacement of all classical computing. The primary long-term risk is cryptographic weakening of historical signatures, keys, certificates, and trust chains.

Therefore, ASO-X MUST follow this rule:

text
No cryptographic era is trusted forever.

Mandatory implications:

- hash and signature algorithms MUST be replaceable;
- artifacts SHOULD support multiple attestations;
- historical evidence SHOULD be periodically re-attested;
- weakened algorithms MUST be marked deprecated;
- post-quantum algorithms SHOULD be introduced when practical and stable;
- verification logic MUST preserve algorithm metadata;
- future maintainers MUST be able to understand which algorithms were trusted at which time.

---

## 6. Evidence Ledger Model

ASO-X MUST move toward an evidence ledger model.

The evidence ledger is the durable record of important operational events.

Initial evidence domains:

- artifact retention audits;
- release evidence bundles;
- PR and merge governance;
- policy validation;
- dependency and supply-chain checks;
- SBOM and provenance records;
- cryptographic attestations;
- migration execution records;
- commercial module validation.

The evidence ledger MAY initially live in the repository under documented paths, but the architecture MUST allow future replication into external durable storage.

Recommended paths:

text
docs/security/audit/
docs/security/evidence/
docs/release/evidence/
docs/roadmap/
schemas/

---

## 7. Artifact Retention Requirements

Artifact retention MUST remain a core ASO-X pillar.

Retention automation MUST define:

- what is retained;
- why it is retained;
- where it is retained;
- how long it is retained;
- how it is verified;
- how it is migrated;
- when it is re-attested;
- when deletion is allowed or forbidden.

Retention policies MUST be testable.

Retention outputs MUST be auditable.

---

## 8. Source, History, and Repository Governance

The repository remains the operational source of truth for current development, but long-horizon durability MUST NOT assume GitHub alone is permanent.

Mandatory requirements:

- changes MUST be made through reviewable commits;
- important changes SHOULD use pull requests;
- branch deletion MUST be safe and intentional;
- generated durable documents MUST use UTF-8 without BOM and LF line endings;
- scripts SHOULD be cp1252-safe in console output where practical;
- local automation MUST avoid unsafe concurrent writes;
- atomic writes SHOULD be used for generated records;
- evidence-producing automation MUST be deterministic where practical.

---

## 9. Commercial Expansion Requirements

Commercial expansion MUST be modular.

A commercial extension MUST define:

- its domain boundary;
- input and output contracts;
- policy dependencies;
- evidence records;
- security assumptions;
- migration requirements;
- failure modes;
- retention requirements;
- test coverage.

Commercial modules MUST NOT silently alter core governance behavior.

The core MUST remain reusable as a reference framework.

---

## 10. Mandatory Roadmap Phases

### Phase P3: Durability Foundation

Required deliverables:

- P3.1 Integrated Mandatory Roadmap;
- P3.2 Evidence Record Schema;
- P3.3 Cryptographic Agility Policy;
- P3.4 Re-Attestation Workflow;
- P3.5 Commercial Module Boundary;
- P3.6 Long-Horizon Threat Model;
- P3.7 Migration Governance Baseline.

### Phase P4: Evidence Operating Layer

Required deliverables:

- evidence record creation through `asoctl.py`;
- evidence verification command;
- artifact hash manifest;
- release evidence bundle integration;
- audit evidence indexing;
- CI validation for evidence schema.

### Phase P5: Cryptographic Agility Layer

Required deliverables:

- supported algorithm registry;
- deprecated algorithm registry;
- re-attestation policy;
- multi-algorithm artifact attestation;
- post-quantum readiness note;
- crypto migration procedure.

### Phase P6: Commercial Module Framework

Required deliverables:

- module boundary specification;
- module validation command;
- commercial policy interface;
- domain extension template;
- finance intelligence module baseline;
- compliance intelligence module baseline.

### Phase P7: Independence and Replication

Required deliverables:

- GitHub independence plan;
- artifact registry abstraction;
- external evidence mirror design;
- disaster recovery procedure;
- offline verification documentation;
- long-term archive export format.

---

## 11. Mandatory Definition of Done for Strategic Features

A strategic feature is not complete unless the following are satisfied or explicitly waived:

- documented purpose;
- policy impact identified;
- evidence impact identified;
- schema impact identified;
- migration impact identified;
- security impact identified;
- commercial extension impact identified;
- tests added or updated;
- CI validation considered;
- durable documentation added or updated;
- artifact or evidence output added where applicable.

---

## 12. Prohibited Patterns

The following patterns are prohibited for strategic ASO-X work:

- undocumented source-of-truth files;
- critical behavior hidden only in ad-hoc scripts;
- irreversible format changes without migration notes;
- cryptographic algorithm lock-in;
- vendor-only operational assumptions;
- evidence-free release or audit workflows;
- policy bypass without documented exception;
- commercial extensions that mutate core behavior silently;
- generated files with unstable formatting when durability is required.

---

## 13. Reference Identity

ASO-X SHOULD present itself as:

text
A long-horizon, policy-driven, cryptography-agile, evidence-retaining automation framework for financial and enterprise intelligence systems.

The intended reference class is not a simple application.

The intended reference class is:

text
Durable Intelligence Operating Layer

---

## 14. Immediate Next Work Items

The following work items SHOULD follow this roadmap:

1. Add `schemas/evidence-record.schema.json`.
2. Add `docs/security/policies/cryptographic-agility-policy.md`.
3. Add `docs/security/policies/reattestation-policy.md`.
4. Add `docs/architecture/aso-x-50-year-durability-architecture.md`.
5. Add `asoctl.py` evidence commands.
6. Add CI validation for evidence records.
7. Add commercial module boundary documentation.

---

## 15. Governance Rule

This roadmap is mandatory guidance for all future ASO-X work.

A future change may update this roadmap, but it MUST do so explicitly, through reviewable repository history, and with clear rationale.

Silent drift away from this roadmap is not allowed.
