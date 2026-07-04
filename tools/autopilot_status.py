from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "aso-x.autopilot_readiness.v1"


def _run_git(repo_root: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _current_branch(repo_root: Path) -> tuple[str, bool]:
    branch = _run_git(repo_root, ["branch", "--show-current"])
    if branch:
        return branch, False

    commit = _run_git(repo_root, ["rev-parse", "--short", "HEAD"])
    return commit or "unknown", True


def _worktree_clean(repo_root: Path) -> bool:
    return _run_git(repo_root, ["status", "--porcelain"]) == ""


def _tracked_dependency_files(repo_root: Path) -> list[str]:
    tracked = _run_git(repo_root, ["ls-files"]).splitlines()
    dependency_names = {
        "requirements.txt",
        "requirements-dev.txt",
        "pyproject.toml",
        "setup.cfg",
        "setup.py",
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
    }

    matches: list[str] = []
    for item in tracked:
        normalized = item.replace("\\", "/")
        name = normalized.rsplit("/", 1)[-1]
        if name in dependency_names:
            matches.append(normalized)

    return sorted(matches)


def _workflow_files(repo_root: Path) -> list[Path]:
    workflow_dir = repo_root / ".github" / "workflows"
    if not workflow_dir.exists():
        return []

    return sorted(
        path
        for path in workflow_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".yml", ".yaml"}
    )


def _contains_any(paths: list[Path], needles: tuple[str, ...]) -> bool:
    lowered_needles = tuple(needle.lower() for needle in needles)

    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        lowered = text.lower()
        if any(needle in lowered for needle in lowered_needles):
            return True

    return False


def collect_autopilot_status(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    workflows = _workflow_files(repo_root)
    branch, head_detached = _current_branch(repo_root)

    scheduled_workflow_present = _contains_any(
        workflows,
        (
            "schedule:",
            "schedule :",
        ),
    )
    pr_creation_automation_present = _contains_any(
        workflows,
        (
            "gh pr create",
            "peter-evans/create-pull-request",
            "create-pull-request",
        ),
    )
    safe_merge_automation_present = _contains_any(
        workflows,
        (
            "gh pr merge",
            "enable-auto-merge",
            "automerge",
            "auto-merge",
        ),
    )
    audit_artifact_capable = _contains_any(
        workflows,
        (
            "upload-artifact",
            "artifacts/autopilot",
            "autopilot/readiness",
            "autopilot_status",
            "autopilot-status",
        ),
    )

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "not_ready",
        "branch": branch,
        "head_detached": head_detached,
        "worktree_clean": _worktree_clean(repo_root),
        "asoctl_present": (repo_root / "asoctl.py").exists(),
        "auto_pilot_present": (repo_root / "tools" / "auto_pilot.py").exists(),
        "policy_matrix_present": (repo_root / "tools" / "policy_matrix.py").exists(),
        "github_workflows_present": bool(workflows),
        "scheduled_workflow_present": scheduled_workflow_present,
        "pr_creation_automation_present": pr_creation_automation_present,
        "safe_merge_automation_present": safe_merge_automation_present,
        "audit_artifact_capable": audit_artifact_capable,
        "tracked_dependency_files": _tracked_dependency_files(repo_root),
        "blocked_actions": [
            "direct_push_to_main",
            "autonomous_merge_without_policy_audit",
        ],
        "review_actions": [],
    }

    if head_detached:
        result["review_actions"].append("attach_head_to_branch")
    if not result["scheduled_workflow_present"]:
        result["review_actions"].append("add_scheduled_workflow")
    if not result["pr_creation_automation_present"]:
        result["review_actions"].append("add_pr_creation_automation")
    if not result["safe_merge_automation_present"]:
        result["review_actions"].append("add_safe_merge_gate")
    if not result["audit_artifact_capable"]:
        result["review_actions"].append("add_audit_artifact_output")

    required_true_keys = [
        "worktree_clean",
        "asoctl_present",
        "auto_pilot_present",
        "policy_matrix_present",
        "github_workflows_present",
        "scheduled_workflow_present",
        "pr_creation_automation_present",
        "safe_merge_automation_present",
        "audit_artifact_capable",
    ]

    result["status"] = (
        "ready"
        if not head_detached and all(bool(result[key]) for key in required_true_keys)
        else "not_ready"
    )

    return result
