# ASO-X Decision Log

This file records durable operating decisions that must remain visible in the repository.

## D-2026-07-04-P1-9 - Adopt PR-Based Automation and Policy-Audited Safe Merge

Status: accepted  
Phase: P1.9  
Decision type: operating model  
Scope: repository governance, automation, merge policy, long-horizon durability

### Context

P1.7 implemented Safe Merge automation.  
P1.8 validated the automation through a real smoke test.

Evidence:

text
PR: #204
Workflow: Autopilot Safe Merge
Run ID: 28721789327
Conclusion: success
Merged At: 2026-07-04T22:33:27Z
Merge Commit: 646f12daa76f90110c91efc9b1093aabaabaefcc
Final autopilot-status: ready
Final worktree state: clean

### Decision

ASO-X will use the following standard path for durable project changes:

text
branch -> PR -> checks -> policy gate -> audit artifact -> safe merge

The repository is the single source of truth. Decisions that affect the long-term direction, automation, security, release process, financial logic, or governance of the project must be recorded in version-controlled files.

### Consequences

The following are prohibited by operating policy:

text
direct_push_to_main
manual_unaudited_merge
autonomous_merge_without_policy_audit
business_critical_change_without_PR
workflow_change_without_smoke_validation

Safe Merge automation is the approved merge path for eligible PRs.

### Rationale

ASO-X has a long-horizon financial-intelligence operating posture. The cost of uncontrolled change is assumed to be high. The project therefore optimizes for traceability, auditability, repeatability, and policy enforcement rather than informal speed.

### Follow-Up

Planned hardening work:

1. Add or improve `autopilot-doctor`.
2. Strengthen Safe Merge workflow concurrency.
3. Add or confirm workflow timeout controls.
4. Add label-based merge gates.
5. Expand audit artifact metadata.
6. Add repeatable smoke-test runbook.
