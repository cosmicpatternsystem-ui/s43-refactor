# Unified Operational Roadmap

Status: Active
Phase: 19
Purpose: Define the single operational roadmap for release readiness, CI enforcement, branch protection, and commercial automation backlog.

## Phase 19 Operational Contract

This document is the canonical operational roadmap for the repository.

Required operational pillars:

1. Release readiness gate dependency
2. CI enforcement
3. Branch protection required
4. Commercial automation backlog
5. Security automation backlog
6. Release automation backlog
7. Observability backlog
8. Audit evidence continuity

## Release Readiness Gate Dependency

The Phase 18 release readiness gate remains the foundation for operational enforcement.

Required evidence:

- AUDIT/RELEASE_READINESS_MASTER.md
- AUDIT/RELEASE_READINESS_POLICY.json
- AUDIT/PHASE18_RELEASE_READINESS_DECISION.md
- AUDIT/PHASE18_RELEASE_READINESS_SNAPSHOT.md
- tools/assert_release_readiness.ps1
- .github/workflows/release-readiness.yml

## CI Enforcement

The repository must enforce operational checks through GitHub Actions.

Required checks:

- Hardening Tests
- Release Readiness Gate
- Operational Roadmap Gate

## Branch Protection Required

The master branch must be protected before the repository can be considered fully commercial-operational.

Required GitHub settings:

- Require pull request before merging
- Require status checks to pass before merging
- Require Release Readiness Gate
- Require Hardening Tests
- Require Operational Roadmap Gate
- Prevent direct pushes to master where possible
- Require conversation resolution where possible

Current status: documented pending GitHub enforcement.

## Commercial Automation Backlog

The repository is not yet fully commercial end-to-end automated until these items are implemented or explicitly waived:

- Release artifact generation
- Versioning and changelog automation
- GitHub Release publishing
- Package or installer publishing
- License and entitlement model
- Customer delivery process
- Support and incident workflow
- SLA or operational response policy

## Security Automation Backlog

Required future hardening:

- Dependency scanning
- Secret scanning policy
- CodeQL or equivalent static analysis
- SBOM generation
- Artifact signing
- Provenance or attestation

## Release Automation Backlog

Required future release pipeline items:

- Build artifact workflow
- Release notes workflow
- Tag validation workflow
- Release approval checklist
- Rollback instructions

## Observability Backlog

Required future operational visibility:

- Runtime health checks
- Runtime logging policy
- Alerting policy
- Incident response checklist
- Operational dashboard or report

## Audit Evidence Continuity

Operational decisions must remain recorded under AUDIT.

Phase 19 establishes the unified operational roadmap but does not claim that all commercial automation is complete.