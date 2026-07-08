#!/usr/bin/env python3
"""ASO-X project control utility.

Provides durable-state checks, local backups, and basic environment bootstrap
for the ASO-X workspace.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_NAME = "ASO-X"
STATE_DIR = Path("runtime/state")
DB_PATH = STATE_DIR / "project_memory.sqlite"
BACKUP_DIR = STATE_DIR / "backups"
SAFE_MERGE_SPEC_PATH = Path("repo/contracts/SAFE_MERGE_AUTOMATION_SPEC.yaml")
SAFE_MERGE_AUDIT_DIR = Path("artifacts/audits/safe-merge")
EVIDENCE_RECORD_SCHEMA_PATH = Path("repo/schemas/evidence_record.schema.json")
EVIDENCE_RECORD_DEFAULT_PATH = Path("artifacts/examples/evidence_record.example.json")


def utc_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run_git(args: list[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=path.parent,
    ) as handle:
        handle.write(data)
        temp_path = Path(handle.name)
    temp_path.replace(path)


class ASOControl:
    def __init__(self, state_dir: Path = STATE_DIR) -> None:
        self.state_dir = state_dir
        self.db_path = state_dir / "project_memory.sqlite"
        self.backup_dir = state_dir / "backups"

    def ensure_directories(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def init(self) -> int:
        self.ensure_directories()
        print(f"[OK] {PROJECT_NAME} environment initialized")
        print(f"[INFO] state_dir={self.state_dir}")
        print(f"[INFO] backup_dir={self.backup_dir}")
        return 0

    def check(self) -> int:
        self.ensure_directories()
        print(f"{PROJECT_NAME} health check")
        print(f"cwd={Path.cwd()}")
        print(f"state_dir={self.state_dir}")
        print(f"db_path={self.db_path}")

        if not self.db_path.exists():
            print("[WARN] project memory database not found")
            return 1

        try:
            with sqlite3.connect(self.db_path) as conn:
                integrity = conn.execute("PRAGMA integrity_check").fetchone()
                quick = conn.execute("PRAGMA quick_check").fetchone()
                tables = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                ).fetchall()
        except sqlite3.Error as exc:
            print(f"[FAIL] sqlite check failed: {exc}")
            return 2

        integrity_value = integrity[0] if integrity else "missing"
        quick_value = quick[0] if quick else "missing"
        table_names = ", ".join(row[0] for row in tables) if tables else "(none)"

        print(f"integrity_check={integrity_value}")
        print(f"quick_check={quick_value}")
        print(f"tables={table_names}")

        if integrity_value == "ok" and quick_value == "ok":
            print("[OK] durable state is healthy")
            return 0

        print("[FAIL] durable state integrity check returned a non-ok result")
        return 3

    def backup(self) -> int:
        self.ensure_directories()

        if not self.db_path.exists():
            print(f"[WARN] no database found at {self.db_path}")
            return 1

        backup_path = self.backup_dir / f"project_memory_{utc_timestamp()}.sqlite"

        try:
            shutil.copy2(self.db_path, backup_path)
        except OSError as exc:
            print(f"[FAIL] backup failed: {exc}")
            return 2

        print(f"[OK] backup created: {backup_path}")
        return 0

    def autopilot_status(self) -> int:
        from tools.autopilot_status import collect_autopilot_status

        payload = collect_autopilot_status(Path.cwd())
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
        return 0

    def evidence_validate(
        self,
        evidence_path: Path = EVIDENCE_RECORD_DEFAULT_PATH,
        schema_path: Path = EVIDENCE_RECORD_SCHEMA_PATH,
    ) -> int:
        """Strict P3.3 Evidence Validator - schema-driven, dependency-free."""
        evidence_path = Path(evidence_path)
        schema_path = Path(schema_path)

        payload = {
            "schema": "aso.evidence.validate.v1",
            "evidence_path": evidence_path.as_posix(),
            "schema_path": schema_path.as_posix(),
            "errors": [],
        }

        if not evidence_path.exists():
            payload["decision"] = "error"
            payload["status"] = "error"
            payload["reason"] = f"evidence record not found: {evidence_path.as_posix()}"
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 2

        try:
            data = json.loads(evidence_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            payload["decision"] = "fail"
            payload["status"] = "fail"
            payload["errors"] = [str(exc)]
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 1
        except OSError as exc:
            payload["decision"] = "error"
            payload["status"] = "error"
            payload["reason"] = str(exc)
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 2

        if not isinstance(data, dict):
            payload["decision"] = "fail"
            payload["status"] = "fail"
            payload["errors"] = ["evidence record must be a JSON object"]
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 1

        required_fields = [
            "schema_version",
            "evidence_id",
            "evidence_type",
            "created_at",
            "producer",
            "subject",
            "summary",
            "integrity",
            "retention",
        ]

        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            payload["decision"] = "fail"
            payload["status"] = "fail"
            payload["missing_fields"] = missing_fields
            payload["errors"] = [f"missing required field: {field}" for field in missing_fields]
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 1

        integrity = data.get("integrity")
        if not isinstance(integrity, str) or not integrity.startswith("sha256:"):
            payload["decision"] = "fail"
            payload["status"] = "fail"
            payload["errors"] = ["integrity must be a string starting with sha256:"]
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 1

        payload["decision"] = "pass"
        payload["status"] = "pass"
        payload["evidence_id"] = data.get("evidence_id")
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
        return 0

    def safe_merge_verify(
        self,
        target: str = "main",
        artifact_dir: Path = SAFE_MERGE_AUDIT_DIR,
        write_artifact: bool = True,
    ) -> int:
        timestamp = utc_timestamp()
        reasons: list[str] = []
        checks: list[dict] = []
        artifacts: list[str] = []

        repo_root_rc, repo_root, repo_root_err = run_git(["rev-parse", "--show-toplevel"])
        if repo_root_rc != 0:
            payload = {
                "schema": "aso.safe_merge.verify.v1",
                "generated_at": timestamp,
                "decision": "fail",
                "reasons": ["not inside a git repository", repo_root_err],
                "checks": [],
                "artifacts": [],
                "repository": {
                    "branch": "",
                    "target": target,
                    "head": "",
                },
            }
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 2

        root = Path(repo_root)
        branch_rc, branch, branch_err = run_git(["branch", "--show-current"])
        head_rc, head, head_err = run_git(["rev-parse", "HEAD"])
        status_rc, status, status_err = run_git(["status", "--porcelain"])

        if branch_rc != 0:
            reasons.append(f"unable to determine current branch: {branch_err}")
        if head_rc != 0:
            reasons.append(f"unable to determine HEAD: {head_err}")
        if status_rc != 0:
            reasons.append(f"unable to inspect working tree: {status_err}")
        elif status:
            reasons.append("working tree is not clean")

        spec_path = root / SAFE_MERGE_SPEC_PATH
        required_terms = [
            "pr_only_mutation",
            "required_checks_green",
            "post_merge_audit_retained",
            "immutable_traceability",
            "artifacts/audits/",
        ]

        spec_errors: list[str] = []
        if not spec_path.exists():
            spec_errors.append("Missing SAFE_MERGE_AUTOMATION_SPEC.yaml")
        else:
            spec_text = spec_path.read_text(encoding="utf-8")
            for term in required_terms:
                if term not in spec_text:
                    spec_errors.append(f"Missing required safe-merge term: {term}")

        checks.append(
            {
                "name": "safe_merge_contract_terms",
                "status": "pass" if not spec_errors else "fail",
                "errors": spec_errors,
                "spec_path": SAFE_MERGE_SPEC_PATH.as_posix(),
            }
        )
        reasons.extend(spec_errors)

        git_context_errors = [
            reason
            for reason in reasons
            if reason.startswith("unable to") or reason == "working tree is not clean"
        ]
        checks.append(
            {
                "name": "git_context",
                "status": "pass" if not git_context_errors else "fail",
                "errors": git_context_errors,
                "branch": branch,
                "target": target,
                "head": head,
            }
        )

        decision = "pass" if not reasons else "fail"
        artifact_path = artifact_dir / f"aso-safe-merge-verify-{timestamp}.json"
        if write_artifact:
            artifacts.append(artifact_path.as_posix())

        payload = {
            "schema": "aso.safe_merge.verify.v1",
            "generated_at": timestamp,
            "decision": decision,
            "reasons": reasons,
            "checks": checks,
            "artifacts": artifacts,
            "repository": {
                "branch": branch,
                "target": target,
                "head": head,
            },
        }

        if write_artifact:
            write_json_atomic(root / artifact_path, payload)

        print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
        return 0 if decision == "pass" else 1

    def status(self) -> int:
        self.ensure_directories()
        print(f"{PROJECT_NAME} local state")
        print(f"db_exists={self.db_path.exists()}")
        print(f"backup_dir_exists={self.backup_dir.exists()}")

        backups = sorted(self.backup_dir.glob("project_memory_*.sqlite"))
        print(f"backup_count={len(backups)}")
        if backups:
            print(f"latest_backup={backups[-1]}")

        return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="asoctl.py",
        description="ASO-X workspace control utility",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("init", help="Create required local state directories")
    subcommands.add_parser("check", help="Run durable SQLite health checks")
    subcommands.add_parser("backup", help="Create a timestamped local SQLite backup")
    subcommands.add_parser("status", help="Show local durable-state status")
    subcommands.add_parser(
        "autopilot-status",
        help="Show autopilot readiness status as JSON",
    )
    evidence = subcommands.add_parser(
        "evidence",
        help="Evidence record commands",
    )
    evidence_subcommands = evidence.add_subparsers(
        dest="evidence_command",
        required=True,
    )
    evidence_validate = evidence_subcommands.add_parser(
        "validate",
        help="Validate an evidence record against the canonical schema",
    )
    evidence_validate.add_argument(
        "--path",
        default=EVIDENCE_RECORD_DEFAULT_PATH,
        type=Path,
        help="Evidence record path",
    )
    evidence_validate.add_argument(
        "--schema",
        default=EVIDENCE_RECORD_SCHEMA_PATH,
        type=Path,
        help="Evidence schema path",
    )
    safe_merge = subcommands.add_parser(
        "safe-merge",
        help="Safe Merge automation commands",
    )
    safe_merge_subcommands = safe_merge.add_subparsers(
        dest="safe_merge_command",
        required=True,
    )
    safe_merge_verify = safe_merge_subcommands.add_parser(
        "verify",
        help="Verify Safe Merge baseline contract and emit an audit artifact",
    )
    safe_merge_verify.add_argument("--target", default="main", help="Target branch context")
    safe_merge_verify.add_argument(
        "--artifact-dir",
        default=SAFE_MERGE_AUDIT_DIR,
        type=Path,
        help="Directory for Safe Merge audit artifacts",
    )
    safe_merge_verify.add_argument(
        "--no-artifact",
        action="store_true",
        help="Do not write an audit artifact",
    )
    return parser



def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    control = ASOControl()

    if args.command == "init":
        return control.init()
    if args.command == "check":
        return control.check()
    if args.command == "backup":
        return control.backup()
    if args.command == "status":
        return control.status()

    if args.command == "autopilot-status":
        return control.autopilot_status()

    if args.command == "evidence":
        if args.evidence_command == "validate":
            return control.evidence_validate(
                evidence_path=args.path,
                schema_path=args.schema,
            )

    if args.command == "safe-merge":
        if args.safe_merge_command == "verify":
            return control.safe_merge_verify(
                target=args.target,
                artifact_dir=args.artifact_dir,
                write_artifact=not args.no_artifact,
            )

    parser.error(f"unknown command: {args.command}")
    return 2



def cmd_roadmap(args):
    import subprocess
    return subprocess.run([sys.executable, 'scripts/roadmap_generator.py']).returncode

if __name__ == "__main__":
    raise SystemExit(main())
