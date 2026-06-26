from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
os.chdir(REPO_ROOT)

AUTO_BRANCH_PREFIX = "auto/aso-x-"
AUTO_STAGE_PATHS = [
    "docs/AUTO_ROADMAP_STATUS.md",
    "runtime/state/project_memory.sqlite",
    "tools/asoctl.py",
    "tools/heartbeat.py",
    "tools/durable_state.py",
    "tools/migrate_audit_to_sqlite.py",
    "tools/roadmap_sync.py",
]


def run_command(cmd: list[str], name: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    print(f"[EXECUTING] {name}...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"[SUCCESS] {name}")
        if result.stdout.strip():
            print(result.stdout.strip())
        return result

    print(f"[FAILED] {name}")
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())

    if check:
        sys.exit(result.returncode)

    return result


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def current_branch() -> str:
    return git_output(["branch", "--show-current"])


def working_tree_has_changes() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    return bool(result.stdout.strip())


def branch_exists(branch_name: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", branch_name],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def ensure_auto_branch() -> str:
    branch = current_branch()
    if branch.startswith(AUTO_BRANCH_PREFIX):
        print(f"[INFO] Reusing current automation branch: {branch}")
        return branch

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    new_branch = f"{AUTO_BRANCH_PREFIX}{timestamp}"

    if branch_exists(new_branch):
        run_command(["git", "switch", new_branch], f"Switch To Existing Branch {new_branch}")
    else:
        run_command(["git", "switch", "-c", new_branch], f"Create Automation Branch {new_branch}")

    return new_branch


def stage_durable_assets() -> None:
    existing_paths = [path for path in AUTO_STAGE_PATHS if (REPO_ROOT / path).exists()]

    if not existing_paths:
        print("[INFO] No known durable assets found to stage.")
        return

    run_command(["git", "add", *existing_paths], "Git Stage Durable Assets")


def commit_if_needed(message: str) -> bool:
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        capture_output=True,
        text=True,
    )

    if staged.returncode == 0:
        print("[INFO] No staged changes detected. Skipping commit.")
        return False

    run_command(["git", "commit", "-m", message], "Git Commit")
    return True


def push_branch(branch: str) -> None:
    result = run_command(
        ["git", "push", "-u", "origin", branch],
        f"Push Automation Branch {branch}",
        check=False,
    )

    if result.returncode == 0:
        print("=== CYCLE COMPLETE: LOCAL & REMOTE SECURED ===")
        print(f"[NEXT] Open a Pull Request from '{branch}' into 'main'.")
        return

    print("--- CYCLE PARTIAL: Local durable state saved, remote branch push failed ---")
    print(f"[NEXT] Resolve remote/auth/network issue, then run: git push -u origin {branch}")
    sys.exit(result.returncode)


def main() -> None:
    print("=== ASO-X AUTOMATION CYCLE START ===")

    run_command(["python", "tools/heartbeat.py"], "Heartbeat & Roadmap Sync")

    auto_branch = ensure_auto_branch()

    stage_durable_assets()

    if not working_tree_has_changes():
        print("[INFO] Working tree is clean after staging. Nothing to publish.")
        print(f"[INFO] Current branch: {auto_branch}")
        return

    commit_message = (
        "ASO-X Auto-Pulse: Durable State & Roadmap Sync "
        "[Traceability Maintained]"
    )
    created_commit = commit_if_needed(commit_message)

    if not created_commit:
        print(f"[INFO] No new commit created. Branch remains: {auto_branch}")
        return

    push_branch(auto_branch)


if __name__ == "__main__":
    main()
