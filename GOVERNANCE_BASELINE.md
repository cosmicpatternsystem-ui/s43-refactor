# ASO-X Governance Baseline

This repository is the durable source of truth for ASO-X governance, continuity, operating model, and revenue-oriented execution.

## Canonical 32 Locks

- **LOCK-001 / repo_only_source_of_truth**: All operational truth must live in the repository.
- **LOCK-002 / immutable_git_history**: Durable project memory must be retained through Git commits and PRs.
- **LOCK-003 / pull_request_only_main**: Protected branches require PR-based changes.
- **LOCK-004 / bom_free_utf8_lf**: Text artifacts must use UTF-8 without BOM and LF line endings.
- **LOCK-005 / atomic_writes**: Generated artifacts must be written atomically or deterministically.
- **LOCK-006 / cp1252_safe_stdout**: CLI output must avoid fragile terminal-only Unicode assumptions.
- **LOCK-007 / safe_concurrent_edits**: Automation must avoid overwriting human work without checks.
- **LOCK-008 / governance_enforced_by_ci**: Governance rules must be testable in CI.
- **LOCK-009 / artifact_retention**: Decision, status, roadmap, and evidence artifacts must be retained.
- **LOCK-010 / manual_gate_for_high_risk_actions**: High-risk or real-money actions require explicit human approval.
- **LOCK-011 / revenue_directionality**: Roadmap and operating model must preserve revenue orientation.
- **LOCK-012 / real_money_resilience**: Systems touching money must prefer safety, auditability, and rollback.
- **LOCK-013 / policy_matrix_required**: Autopilot behavior must be governed by an explicit policy matrix.
- **LOCK-014 / next_actions_required**: Every continuity checkpoint must expose executable next actions.
- **LOCK-015 / project_state_required**: Current repo state must be restorable from committed project-state files.
- **LOCK-016 / decision_log_required**: Material decisions must be captured in a durable decision log.
- **LOCK-017 / roadmap_required**: Long-horizon direction must be captured in a durable roadmap.
- **LOCK-018 / operating_model_required**: The repo must define how humans and automation cooperate.
- **LOCK-019 / revenue_model_required**: The repo must define revenue hypotheses and readiness checks.
- **LOCK-020 / asoctl_required**: A single repo-native control entrypoint must exist.
- **LOCK-021 / validation_before_commit**: Generated governance changes must be locally validated before commit.
- **LOCK-022 / tests_for_governance**: Canonical governance invariants must have tests.
- **LOCK-023 / schema_for_locks**: The lock registry must have a machine-readable schema.
- **LOCK-024 / stable_lock_ids**: Canonical lock IDs must be stable and non-reused.
- **LOCK-025 / human_readable_baseline**: Governance must have a human-readable baseline document.
- **LOCK-026 / machine_readable_baseline**: Governance must have machine-readable registry artifacts.
- **LOCK-027 / safe_merge_automation**: Merge automation must respect branch protections and checks.
- **LOCK-028 / github_pr_workflow**: GitHub contribution flow must use PRs for protected changes.
- **LOCK-029 / no_secret_material_in_repo**: Generated governance files must not require secrets.
- **LOCK-030 / durability_50y_orientation**: Architecture choices must prefer long-term maintainability.
- **LOCK-031 / continuity_across_chats**: A new assistant session must be able to resume from repo artifacts.
- **LOCK-032 / global_financial_intelligence_focus**: The strategic focus remains global financial intelligence.

## High-Risk Action Rule

Any action involving production money movement, credential changes, destructive history operations, or protected-branch mutation requires explicit human approval.
