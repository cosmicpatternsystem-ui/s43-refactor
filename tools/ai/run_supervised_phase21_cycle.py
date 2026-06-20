#!/usr/bin/env python3
"""Run the non-destructive Phase 21 supervised operating cycle."""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple


REQUIRED_PHASE21_FILES = (
    "AUDIT/PHASE21_AI_SUPERVISOR_TOOLING_ADOPTION.md",
    "AUDIT/PHASE21_AUTONOMOUS_OPERATION_GOVERNANCE.md",
    "AUDIT/PHASE21_LOCAL_REMOTE_SYNC_RUNBOOK.md",
    "AUDIT/PHASE21_LONG_TERM_AUTONOMOUS_FINANCIAL_SYSTEM_VISION.md",
    "AUDIT/PHASE21_RELEASE_AUTOMATION_DRY_RUN_DESIGN.md",
    "AUDIT/PHASE21_SELF_SUFFICIENT_AI_OPERATING_LOOP.md",
    "tools/ai/verify_repo_sync.py",
    "tools/ai/precommit_inventory.py",
    "tools/ai/safety_policy.py",
    "tools/ai/run_supervised_phase21_cycle.py",
)


@dataclass
class StepResult:
    name: str
    returncode: int
    stdout: str
    stderr: str


@dataclass
class CycleReport:
    steps: List[StepResult]
    missing_files: List[str]
    phase21_files: List[str]
    ai_audit_files: List[str]


def run_command(name: str, command: Sequence[str], repo: Path) -> StepResult:
    completed = subprocess.run(
        list(command),
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return StepResult(
        name=name,
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def validate_python_syntax(repo: Path, paths: Sequence[str]) -> StepResult:
    output: List[str] = []
    failures: List[Tuple[str, str]] = []

    for item in paths:
        path = repo / item
        try:
            source = path.read_text(encoding="utf-8")
            ast.parse(source, filename=item)
            output.append(f"PASS: {item}")
        except SyntaxError as exc:
            detail = f"{exc.msg} at line {exc.lineno}, column {exc.offset}"
            failures.append((item, detail))
            output.append(f"FAIL: {item}: {detail}")
        except OSError as exc:
            failures.append((item, str(exc)))
            output.append(f"FAIL: {item}: {exc}")

    return StepResult(
        name="python syntax validation",
        returncode=1 if failures else 0,
        stdout="\n".join(output),
        stderr="",
    )


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError("not inside a Git repository")
    return Path(result.stdout.strip()).resolve()


def list_files(root: Path, relative_dir: str, pattern: str) -> List[str]:
    base = root / relative_dir
    if not base.exists():
        return []
    return sorted(path.relative_to(root).as_posix() for path in base.rglob(pattern) if path.is_file())


def collect_phase21_files(root: Path) -> List[str]:
    audit_files = list_files(root, "AUDIT", "PHASE21_*.md")
    tool_files = list_files(root, "tools/ai", "*.py")
    return sorted(audit_files + tool_files)


def run_cycle(args: argparse.Namespace) -> CycleReport:
    root = repo_root()
    steps: List[StepResult] = []

    sync_command = ["python3", "-B", "tools/ai/verify_repo_sync.py"]
    if args.allow_dirty:
        sync_command.append("--allow-dirty")
    if args.allow_ahead:
        sync_command.append("--allow-ahead")
    steps.append(run_command("repo sync verification", sync_command, root))

    inventory_command = ["python3", "-B", "tools/ai/precommit_inventory.py"]
    if args.inventory_warn_only:
        inventory_command.append("--warn-only")
    steps.append(run_command("precommit inventory", inventory_command, root))

    if args.validate:
        steps.append(
            validate_python_syntax(
                root,
                [
                    "tools/ai/verify_repo_sync.py",
                    "tools/ai/precommit_inventory.py",
                    "tools/ai/safety_policy.py",
                    "tools/ai/run_supervised_phase21_cycle.py",
                ],
            )
        )

    missing_files = [item for item in REQUIRED_PHASE21_FILES if not (root / item).is_file()]
    phase21_files = collect_phase21_files(root)
    ai_audit_files = list_files(root, "AI_AUDIT", "*")
    return CycleReport(
        steps=steps,
        missing_files=missing_files,
        phase21_files=phase21_files,
        ai_audit_files=ai_audit_files,
    )


def print_step(step: StepResult) -> None:
    status = "PASS" if step.returncode == 0 else "FAIL"
    print(f"## {step.name}: {status}")
    if step.stdout:
        print(step.stdout)
    if step.stderr:
        print("STDERR:")
        print(step.stderr)
    print("")


def print_report(report: CycleReport) -> int:
    print("Phase 21 supervised operating cycle")
    print("Mode: non-destructive read-only/dry-run orchestration")
    print("")

    for step in report.steps:
        print_step(step)

    print("## Phase 21 file inventory")
    for path in report.phase21_files:
        print(f"  {path}")
    if not report.phase21_files:
        print("  none")
    print("")

    print("## AI audit file inventory")
    for path in report.ai_audit_files:
        print(f"  {path}")
    if not report.ai_audit_files:
        print("  none")
    print("")

    if report.missing_files:
        print("## Missing required files")
        for path in report.missing_files:
            print(f"FAIL: {path}")
        print("")

    failed_steps = [step for step in report.steps if step.returncode != 0]
    if failed_steps or report.missing_files:
        print("RESULT: FAIL")
        return 1

    print("RESULT: PASS")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Phase 21 supervised non-destructive operating cycle.")
    parser.add_argument("--allow-dirty", action="store_true", help="Pass documented dirty dry-run allowance to sync verifier.")
    parser.add_argument("--allow-ahead", action="store_true", help="Pass documented ahead dry-run allowance to sync verifier.")
    parser.add_argument("--inventory-warn-only", action="store_true", help="Do not fail the cycle on inventory findings.")
    parser.add_argument("--validate", action="store_true", help="Run no-artifact Python syntax validation with ast.parse.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = run_cycle(args)
    except RuntimeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return print_report(report)


if __name__ == "__main__":
    raise SystemExit(main())
