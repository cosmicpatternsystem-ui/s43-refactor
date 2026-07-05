# ASO-X PR and Safe Merge Policy

Status: active
Applies to: durable repository changes

## 1. Policy Statement

All durable changes to ASO-X must enter through a pull request and be merged through policy-audited Safe Merge automation after required checks pass.

## 2. Required Flow

    feature branch
      -> pull request
      -> required checks
      -> policy validation
      -> audit artifact
      -> safe merge
      -> post-merge readiness check

## 3. Main Branch Rule

Main is treated as immutable by operating policy. Changes to main must happen only through approved merge automation.

## 4. Direct Push Rule

Direct push to main is prohibited.

## 5. Manual Merge Rule

Manual unaudited merge is prohibited for durable project changes.

## 6. Automation Change Rule

Changes to workflows, merge logic, policy logic, or repository automation require smoke validation.

## 7. Documentation Rule

Roadmap, governance, and operating decisions must be stored in the repository. Chat history, local notes, and external memory are not authoritative unless converted into repository documentation through PR.

## 8. Evidence Rule

Important automation milestones must record evidence, including PR number, workflow run ID, merge commit, and final readiness state where applicable.

## 9. Current Baseline Evidence

    P1.7 Safe Merge Automation: completed
    P1.8 Safe Merge Smoke Test: passed
    PR #204: merged
    Safe Merge Run ID: 28721789327
    Merge Commit: 646f12daa76f90110c91efc9b1093aabaabaefcc
    Final autopilot-status: ready
