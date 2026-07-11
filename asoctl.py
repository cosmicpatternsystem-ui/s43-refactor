#!/usr/bin/env python3
"""ASO-X project control utility.

Provides durable-state checks, local backups, and basic environment bootstrap
for the ASO-X workspace.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
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
LEDGER_DIR = Path("artifacts/evidence/ledger")
LEDGER_SCHEMA_PATH = Path("repo/schemas/evidence_ledger_entry.schema.json")


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

    def governance_validate(self) -> int:
        repo_root = Path(__file__).resolve().parent
        gov_script = repo_root / "tools" / "governance.ps1"
        if not gov_script.exists():
            print(
                json.dumps(
                    {"error": "script_not_found", "path": str(gov_script)},
                    ensure_ascii=True,
                    sort_keys=True,
                    indent=2,
                )
            )
            return 2
        return subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(gov_script),
                "validate",
            ],
            check=False,
        ).returncode

    def evidence_validate(
        self,
        evidence_path: Path = EVIDENCE_RECORD_DEFAULT_PATH,
        schema_path: Path = EVIDENCE_RECORD_SCHEMA_PATH,
    ) -> int:
        from repo.tools.validate_evidence_record import validate_record

        payload = {
            "schema": "aso.evidence.validate.v1",
            "evidence_path": evidence_path.as_posix(),
            "schema_path": schema_path.as_posix(),
            "errors": [],
        }

        if not schema_path.exists():
            payload["decision"] = "error"
            payload["reason"] = f"schema not found: {schema_path.as_posix()}"
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 2

        if not evidence_path.exists():
            payload["decision"] = "error"
            payload["reason"] = f"evidence record not found: {evidence_path.as_posix()}"
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 2

        try:
            validate_record(evidence_path)
        except ValueError as exc:
            payload["decision"] = "fail"
            payload["errors"] = [str(exc)]
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 1
        except json.JSONDecodeError as exc:
            payload["decision"] = "fail"
            payload["errors"] = [str(exc)]
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 1
        except OSError as exc:
            payload["decision"] = "error"
            payload["reason"] = str(exc)
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 2

        payload["decision"] = "pass"
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
        return 0

    def _json_c14n(self, value) -> str:
        return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))

    def _sha256_file(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return "sha256:" + h.hexdigest()

    def _sha256_text(self, text: str) -> str:
        return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _atomic_write_text(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        tmp.replace(path)

    def evidence_ledger_record(
        self,
        evidence_path: Path = EVIDENCE_RECORD_DEFAULT_PATH,
        ledger_dir: Path = LEDGER_DIR,
        schema_path: Path = LEDGER_SCHEMA_PATH,
    ) -> int:
        evidence_path = Path(evidence_path)
        ledger_dir = Path(ledger_dir)
        schema_path = Path(schema_path)

        payload = {
            "schema": "aso.evidence.ledger.record.v1",
            "evidence_path": evidence_path.as_posix(),
            "ledger_dir": ledger_dir.as_posix(),
            "schema_path": schema_path.as_posix(),
            "errors": [],
        }

        if not evidence_path.exists() and evidence_path == EVIDENCE_RECORD_DEFAULT_PATH:
            default_evidence = {
                "schema_version": "1.0",
                "evidence_id": "EV-EXAMPLE-001",
                "evidence_type": "bootstrap",
                "created_at": "2026-07-08T00:00:00Z",
                "producer": "asoctl",
                "subject": "ASO-X",
                "summary": "Default bootstrap evidence record",
                "integrity": "sha256:bootstrap",
                "retention": "50y",
            }
            self._atomic_write_text(
                evidence_path,
                json.dumps(default_evidence, ensure_ascii=True, sort_keys=True, indent=2) + "\n",
            )

        if not evidence_path.exists():
            payload["decision"] = "error"
            payload["status"] = "error"
            payload["reason"] = f"evidence record not found: {evidence_path.as_posix()}"
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 2

        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            payload["decision"] = "fail"
            payload["status"] = "fail"
            payload["errors"] = [str(exc)]
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 1

        if not isinstance(evidence, dict):
            payload["decision"] = "fail"
            payload["status"] = "fail"
            payload["errors"] = ["evidence record must be a JSON object"]
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 1

        required = ["schema_version", "evidence_id", "producer", "subject", "retention"]
        missing = [k for k in required if k not in evidence]
        if missing:
            payload["decision"] = "fail"
            payload["status"] = "fail"
            payload["errors"] = [f"missing required field for ledger record: {k}" for k in missing]
            payload["missing_fields"] = missing
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 1

        retention = evidence.get("retention")
        if isinstance(retention, dict):
            retention_class = retention.get("class") or retention.get("policy") or "unspecified"
        else:
            retention_class = str(retention)

        ledger_dir.mkdir(parents=True, exist_ok=True)

        unique_suffix = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        entry_id = f"LEDGER-{evidence['evidence_id']}-{unique_suffix}"
        out_path = ledger_dir / f"{entry_id}.json"

        existing = sorted(
            [fp for fp in ledger_dir.glob("*.json") if fp.stat().st_size > 0],
            key=lambda p: p.name,
        )

        predecessor_entry_hash = ""
        if existing:
            last_file = existing[-1]
            try:
                prev = json.loads(last_file.read_text(encoding="utf-8-sig"))
                predecessor_entry_hash = prev.get("entry_hash", "")
            except Exception:
                pass

        entry = {
            "ledger_version": "1.0",
            "entry_id": entry_id,
            "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
            "evidence_id": evidence["evidence_id"],
            "evidence_path": evidence_path.as_posix(),
            "evidence_hash": self._sha256_file(evidence_path),
            "validator_schema": "aso.evidence.validate.v1",
            "validation_decision": "pass",
            "retention_class": retention_class,
            "producer": (
                evidence["producer"]
                if isinstance(evidence["producer"], str)
                else self._json_c14n(evidence["producer"])
            ),
            "subject": (
                evidence["subject"]
                if isinstance(evidence["subject"], str)
                else self._json_c14n(evidence["subject"])
            ),
            "predecessor_entry_hash": predecessor_entry_hash,
        }

        entry["entry_hash"] = self._sha256_text(self._json_c14n(entry))
        self._atomic_write_text(
            out_path,
            json.dumps(entry, ensure_ascii=True, sort_keys=True, indent=2) + "\n",
        )

        payload["decision"] = "pass"
        payload["status"] = "pass"
        payload["entry_id"] = entry["entry_id"]
        payload["entry_hash"] = entry["entry_hash"]
        payload["ledger_entry_path"] = out_path.as_posix()
        payload["predecessor_entry_hash"] = predecessor_entry_hash
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
        return 0

    def evidence_ledger_verify(
        self,
        ledger_dir: Path = LEDGER_DIR,
        schema_path: Path = LEDGER_SCHEMA_PATH,
        strict_history: bool = False,
        latest_only: bool = False,
        jsonl_audit: bool = False,
    ) -> int:
        ledger_dir = Path(ledger_dir)
        schema_path = Path(schema_path)

        if latest_only and strict_history:
            verification_mode = "latest_only_strict_history"
        elif latest_only:
            verification_mode = "latest_only"
        elif strict_history:
            verification_mode = "strict_history"
        else:
            verification_mode = "historical_scan"

        payload = {
            "schema": "aso.evidence.ledger.verify.v1",
            "ledger_dir": ledger_dir.as_posix(),
            "schema_path": schema_path.as_posix(),
            "verification_mode": verification_mode,
            "errors": [],
        }

        def emit(obj, audit_kind=None):
            if audit_kind == "entry" and not jsonl_audit:
                return

            outbound = dict(obj)

            if jsonl_audit and audit_kind:
                outbound["audit_kind"] = audit_kind

            if jsonl_audit and audit_kind == "entry":
                outbound["verification_mode"] = verification_mode

            if jsonl_audit and audit_kind == "summary" and "entries" in outbound:
                outbound["entry_count"] = len(outbound["entries"])
                outbound.pop("entries", None)

            if jsonl_audit:
                print(json.dumps(outbound, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
            else:
                print(json.dumps(outbound, ensure_ascii=True, sort_keys=True, indent=2))

        if not ledger_dir.exists():
            payload["decision"] = "error"
            payload["status"] = "error"
            payload["reason"] = f"ledger directory not found: {ledger_dir.as_posix()}"
            emit(payload, audit_kind="summary")
            return 2

        files = sorted(
            [fp for fp in ledger_dir.glob("*.json") if fp.stat().st_size > 0],
            key=lambda p: p.name,
        )
        if not files:
            payload["decision"] = "fail"
            payload["status"] = "fail"
            payload["reason"] = "no ledger entries found"
            emit(payload, audit_kind="summary")
            return 1

        previous_hash = ""
        results = []
        evaluatable_results = []
        broken_count = 0

        required_fields = [
            "ledger_version",
            "entry_id",
            "recorded_at",
            "evidence_id",
            "evidence_path",
            "evidence_hash",
            "validator_schema",
            "validation_decision",
            "retention_class",
            "producer",
            "subject",
            "predecessor_entry_hash",
            "entry_hash",
        ]

        for fp in files:
            entry_payload = {
                "ledger_entry_path": fp.as_posix(),
            }

            try:
                entry = json.loads(fp.read_text(encoding="utf-8-sig"))
            except json.JSONDecodeError as exc:
                broken_count += 1
                entry_payload["decision"] = "fail"
                entry_payload["status"] = "fail"
                entry_payload["reason"] = f"invalid JSON in ledger entry: {exc}"
                entry_payload["classification"] = "broken_entry"
                results.append(entry_payload)
                emit(entry_payload, audit_kind="entry")
                continue

            missing = [key for key in required_fields if key not in entry]
            if missing:
                broken_count += 1
                entry_payload["decision"] = "fail"
                entry_payload["status"] = "fail"
                entry_payload["reason"] = "missing required fields in ledger entry"
                entry_payload["missing_fields"] = missing
                entry_payload["classification"] = "broken_entry"
                results.append(entry_payload)
                emit(entry_payload, audit_kind="entry")
                continue

            if entry["predecessor_entry_hash"] != previous_hash:
                broken_count += 1
                entry_payload["decision"] = "fail"
                entry_payload["status"] = "fail"
                entry_payload["reason"] = "predecessor hash mismatch"
                entry_payload["expected_predecessor_entry_hash"] = previous_hash
                entry_payload["actual_predecessor_entry_hash"] = entry["predecessor_entry_hash"]
                entry_payload["classification"] = "broken_entry"
                results.append(entry_payload)
                emit(entry_payload, audit_kind="entry")
                continue

            canonical_entry = dict(entry)
            expected_entry_hash = canonical_entry.pop("entry_hash")
            actual_entry_hash = self._sha256_text(self._json_c14n(canonical_entry))
            if actual_entry_hash != expected_entry_hash:
                broken_count += 1
                entry_payload["decision"] = "fail"
                entry_payload["status"] = "fail"
                entry_payload["reason"] = "entry hash mismatch"
                entry_payload["expected_entry_hash"] = expected_entry_hash
                entry_payload["actual_entry_hash"] = actual_entry_hash
                entry_payload["classification"] = "broken_entry"
                results.append(entry_payload)
                emit(entry_payload, audit_kind="entry")
                continue

            previous_hash = actual_entry_hash
            evidence_path = Path(entry["evidence_path"])

            if not evidence_path.exists():
                broken_count += 1
                entry_payload["decision"] = "fail"
                entry_payload["status"] = "fail"
                entry_payload["reason"] = "referenced evidence file not found"
                entry_payload["referenced_evidence_path"] = entry["evidence_path"]
                entry_payload["classification"] = "broken_entry"
                results.append(entry_payload)
                emit(entry_payload, audit_kind="entry")
                continue

            expected_evidence_hash = entry["evidence_hash"]
            actual_evidence_hash = self._sha256_file(evidence_path)

            entry_payload["referenced_evidence_path"] = entry["evidence_path"]
            entry_payload["expected_evidence_hash"] = expected_evidence_hash
            entry_payload["actual_evidence_hash"] = actual_evidence_hash

            if actual_evidence_hash != expected_evidence_hash:
                entry_payload["decision"] = "fail"
                entry_payload["status"] = "fail"
                entry_payload["reason"] = "evidence hash mismatch"
                entry_payload["classification"] = "stale_referenced_evidence"
                results.append(entry_payload)
                evaluatable_results.append(entry_payload)
                emit(entry_payload, audit_kind="entry")
                continue

            entry_payload["decision"] = "pass"
            entry_payload["status"] = "pass"
            entry_payload["reason"] = "evidence hash matches"
            results.append(entry_payload)
            evaluatable_results.append(entry_payload)
            emit(entry_payload, audit_kind="entry")

        if latest_only:
            selected_results = evaluatable_results[-1:] if evaluatable_results else []
        else:
            selected_results = list(evaluatable_results)

        verified = sum(1 for item in selected_results if item.get("status") == "pass")
        stale_count = sum(
            1
            for item in selected_results
            if item.get("classification") == "stale_referenced_evidence"
        )

        payload["verified_entries"] = verified
        payload["valid_entry_count"] = verified
        payload["stale_entry_count"] = stale_count
        payload["broken_entry_count"] = broken_count
        payload["chain_head"] = previous_hash

        if latest_only and broken_count == 0:
            payload["entries"] = list(selected_results)
        else:
            payload["entries"] = list(results)

        if broken_count > 0:
            payload["decision"] = "fail"
            payload["status"] = "fail"
            payload["reason"] = "one or more ledger entries are structurally broken"
            emit(payload, audit_kind="summary")
            return 1

        if latest_only:
            if verified > 0:
                payload["decision"] = "pass"
                payload["status"] = "pass"
                payload["reason"] = "latest ledger entry matches current evidence state"
                emit(payload, audit_kind="summary")
                return 0

            payload["decision"] = "fail"
            payload["status"] = "fail"
            payload["reason"] = "latest ledger entry does not match current evidence state"
            emit(payload, audit_kind="summary")
            return 1

        if strict_history:
            if stale_count > 0:
                payload["decision"] = "fail"
                payload["status"] = "fail"
                payload["reason"] = (
                    "strict_history requires every historical ledger entry "
                    "to match current evidence state"
                )
                emit(payload, audit_kind="summary")
                return 1

            if verified > 0:
                payload["decision"] = "pass"
                payload["status"] = "pass"
                payload["reason"] = "all historical ledger entries match current evidence state"
                emit(payload, audit_kind="summary")
                return 0

            payload["decision"] = "fail"
            payload["status"] = "fail"
            payload["reason"] = "no ledger entry matches current evidence state"
            emit(payload, audit_kind="summary")
            return 1

        if verified > 0:
            payload["decision"] = "pass"
            payload["status"] = "pass"
            payload["reason"] = (
                "at least one ledger entry matches current evidence state; "
                "stale historical entries retained"
            )
            emit(payload, audit_kind="summary")
            return 0

        payload["decision"] = "fail"
        payload["status"] = "fail"
        payload["reason"] = "no ledger entry matches current evidence state"
        emit(payload, audit_kind="summary")
        return 1

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
        return 0

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

    evidence_ledger_record = evidence_subcommands.add_parser(
        "ledger-record",
        help="Record an immutable evidence ledger entry",
    )
    evidence_ledger_record.add_argument(
        "--record-path",
        default=EVIDENCE_RECORD_DEFAULT_PATH,
        type=Path,
        help="Evidence record path",
    )
    evidence_ledger_record.add_argument(
        "--ledger-dir",
        default=LEDGER_DIR,
        type=Path,
        help="Directory for evidence ledger entries",
    )
    evidence_ledger_record.add_argument(
        "--schema",
        default=LEDGER_SCHEMA_PATH,
        type=Path,
        help="Evidence ledger schema path",
    )

    evidence_ledger_verify = evidence_subcommands.add_parser(
        "ledger-verify",
        help="Verify the evidence ledger chain",
    )
    evidence_ledger_verify.add_argument(
        "--ledger-dir",
        default=LEDGER_DIR,
        type=Path,
        help="Directory for evidence ledger entries",
    )
    evidence_ledger_verify.add_argument(
        "--schema",
        default=LEDGER_SCHEMA_PATH,
        type=Path,
        help="Evidence ledger schema path",
    )
    evidence_ledger_verify.add_argument(
        "--strict-history",
        action="store_true",
        help="Fail if any historical ledger entry is stale or broken.",
    )
    evidence_ledger_verify.add_argument(
        "--latest-only",
        action="store_true",
        help="Verify only the latest ledger entry against the current evidence state.",
    )
    evidence_ledger_verify.add_argument(
        "--jsonl-audit",
        action="store_true",
        help="Emit per-entry audit lines before the final summary payload.",
    )

    validate = subcommands.add_parser('validate', help='Run governance validation')
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
    if args.command == 'validate':
        return control.governance_validate()

    if args.command == "evidence":
        if args.evidence_command == "validate":
            return control.evidence_validate(
                evidence_path=args.path,
                schema_path=args.schema,
            )
        if args.evidence_command == "ledger-record":
            return control.evidence_ledger_record(
                evidence_path=args.record_path,
                ledger_dir=args.ledger_dir,
                schema_path=args.schema,
            )
        if args.evidence_command == "ledger-verify":
            return control.evidence_ledger_verify(
                ledger_dir=args.ledger_dir,
                schema_path=args.schema,
                strict_history=args.strict_history,
                latest_only=args.latest_only,
                jsonl_audit=args.jsonl_audit,
            )
        parser.error(f"unknown evidence command: {args.evidence_command}")
        return 2

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
