from __future__ import annotations

from pathlib import Path

from tools.autopilot_status import collect_autopilot_status


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_collect_autopilot_status_detects_missing_autonomy(monkeypatch, tmp_path):
    repo = tmp_path
    _write(repo / "asoctl.py", "")
    _write(repo / "tools" / "auto_pilot.py", "")
    _write(repo / "tools" / "policy_matrix.py", "")
    _write(
        repo / ".github" / "workflows" / "ci.yml",
        """
name: CI
on:
  pull_request:
  push:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: python -m pytest -q
""",
    )

    import tools.autopilot_status as autopilot_status

    monkeypatch.setattr(
        autopilot_status,
        "_current_branch",
        lambda repo_root: ("main", False),
    )
    monkeypatch.setattr(
        autopilot_status,
        "_worktree_clean",
        lambda repo_root: True,
    )
    monkeypatch.setattr(
        autopilot_status,
        "_tracked_dependency_files",
        lambda repo_root: ["requirements.txt", "dashboard/package.json"],
    )

    result = collect_autopilot_status(repo)

    assert result["schema_version"] == "aso-x.autopilot_readiness.v1"
    assert result["status"] == "not_ready"
    assert result["branch"] == "main"
    assert result["head_detached"] is False
    assert result["worktree_clean"] is True
    assert result["asoctl_present"] is True
    assert result["auto_pilot_present"] is True
    assert result["policy_matrix_present"] is True
    assert result["github_workflows_present"] is True
    assert result["scheduled_workflow_present"] is False
    assert result["pr_creation_automation_present"] is False
    assert result["safe_merge_automation_present"] is False
    assert result["audit_artifact_capable"] is False
    assert result["tracked_dependency_files"] == [
        "requirements.txt",
        "dashboard/package.json",
    ]
    assert "add_scheduled_workflow" in result["review_actions"]


def test_collect_autopilot_status_can_report_ready(monkeypatch, tmp_path):
    repo = tmp_path
    _write(repo / "asoctl.py", "")
    _write(repo / "tools" / "auto_pilot.py", "")
    _write(repo / "tools" / "policy_matrix.py", "")
    _write(
        repo / ".github" / "workflows" / "autopilot.yml",
        """
name: Autopilot
on:
  schedule:
    - cron: "0 * * * *"
  workflow_dispatch:
jobs:
  autopilot:
    runs-on: ubuntu-latest
    steps:
      - run: gh pr create --title test --body test
      - run: gh pr merge --squash
      - uses: actions/upload-artifact@v4
        with:
          name: autopilot-status
          path: artifacts/autopilot/readiness.json
""",
    )

    import tools.autopilot_status as autopilot_status

    monkeypatch.setattr(
        autopilot_status,
        "_current_branch",
        lambda repo_root: ("main", False),
    )
    monkeypatch.setattr(
        autopilot_status,
        "_worktree_clean",
        lambda repo_root: True,
    )
    monkeypatch.setattr(
        autopilot_status,
        "_tracked_dependency_files",
        lambda repo_root: [],
    )

    result = collect_autopilot_status(repo)

    assert result["status"] == "ready"
    assert result["scheduled_workflow_present"] is True
    assert result["pr_creation_automation_present"] is True
    assert result["safe_merge_automation_present"] is True
    assert result["audit_artifact_capable"] is True
    assert result["review_actions"] == []


def test_collect_autopilot_status_reports_detached_head(monkeypatch, tmp_path):
    repo = tmp_path
    _write(repo / "asoctl.py", "")
    _write(repo / "tools" / "auto_pilot.py", "")
    _write(repo / "tools" / "policy_matrix.py", "")

    import tools.autopilot_status as autopilot_status

    monkeypatch.setattr(
        autopilot_status,
        "_current_branch",
        lambda repo_root: ("abc1234", True),
    )
    monkeypatch.setattr(
        autopilot_status,
        "_worktree_clean",
        lambda repo_root: True,
    )
    monkeypatch.setattr(
        autopilot_status,
        "_tracked_dependency_files",
        lambda repo_root: [],
    )

    result = collect_autopilot_status(repo)

    assert result["status"] == "not_ready"
    assert result["head_detached"] is True
    assert "attach_head_to_branch" in result["review_actions"]
