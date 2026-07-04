# ASO-X Autopilot Operating Model

Status: active  
Model: PR-based automation with policy-audited Safe Merge  
Source of truth: repository only

## 1. Operating Decision

ASO-X operates as a policy-first, audit-first, PR-only system.

From P1.9 onward, the approved standard path for durable project changes is:

text
branch -> PR -> checks -> policy gate -> audit artifact -> safe merge

This model is mandatory for changes affecting:

- application code
- automation
- workflows
- governance
- dependencies
- release process
- financial logic
- operational documentation
- security posture
- roadmap and decision records

## 2. Approved Path

A normal change must follow this sequence:

1. Start from updated `main`.
2. Create a scoped feature branch.
3. Make a small, reviewable change.
4. Commit with a clear message.
5. Open a pull request.
6. Allow required checks to run.
7. Satisfy policy gates.
8. Generate or preserve audit evidence.
9. Merge only through Safe Merge automation.
10. Sync local `main`.
11. Confirm `python asoctl.py autopilot-status` reports `ready`.

## 3. Prohibited Paths

The following are prohibited by operating policy:

text
direct_push_to_main
manual_unaudited_merge
autonomous_merge_without_policy_audit
workflow_change_without_smoke_validation
roadmap_change_without_repository_record
business_critical_change_without_PR

Emergency work must still preserve traceability. If a temporary exception is unavoidable, it must be recorded in the repository with evidence and follow-up remediation.

## 4. Required Baseline Readiness

The repository should maintain:

text
autopilot-status: ready
worktree_clean: true
github_workflows_present: true
policy_matrix_present: true
safe_merge_automation_present: true
pr_creation_automation_present: true
audit_artifact_capable: true

## 5. Safe Merge Evidence Baseline

The operating model was validated with:

text
PR: #204
Workflow Run ID: 28721789327
Conclusion: success
Merge Commit: 646f12daa76f90110c91efc9b1093aabaabaefcc
Final Branch: main
Final Status: ready

## 6. Durable Automation Rules

Automation must be:

- explicit
- version-controlled
- auditable
- smoke-tested
- reversible or recoverable
- safe for concurrent operation
- conservative around `main`
- clear in failure messages
- compatible with long-term maintenance

## 7. Merge Governance

A PR is eligible for Safe Merge only when:

1. It is open.
2. It is not draft.
3. It targets the approved base branch.
4. It is mergeable.
5. It is not behind the base branch.
6. Required checks pass.
7. Policy gates pass.
8. No blocking labels or states apply.
9. Audit metadata can be produced.
10. The merge operation is performed by the approved workflow.

## 8. Future Hardening Requirements

Future hardening should include:

- `autopilot-doctor`
- workflow concurrency guards
- workflow timeout guards
- required approval labels where appropriate
- blocking labels such as `do-not-merge`
- expanded audit artifacts
- repeatable smoke-test procedures
- dependency drift detection
- local readiness diagnostics
- recovery runbooks
