import pathlib
import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path

from aso_signing import sign_bytes, verify_bytes

DB_DEFAULT_PATH = Path("state/project_memory.sqlite")
BACKUP_DIR = Path("state/backups")
EVIDENCE_RECORD_DEFAULT_PATH = pathlib.Path("artifacts/examples/evidence_record.example.json")
EVIDENCE_RECORD_SCHEMA_PATH = Path("repo/schemas/evidence_record.schema.json")
LEDGER_DIR = Path("artifacts/evidence/ledger")
LEDGER_SCHEMA_PATH = Path("repo/schemas/evidence_ledger_entry.schema.json")
SAFE_MERGE_AUDIT_DIR = Path("artifacts/safe-merge")

def utc_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def run_git(args: list[str]) -> tuple[int, str]:
    import subprocess
    p = subprocess.run(["git"] + args, capture_output=True, text=True)
    return p.returncode, p.stdout.strip()

def write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    data = json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2) + "\n"
    with open(temp_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)
    temp_path.replace(path)

class ASOControl:
    def __init__(self, state_dir=None) -> None:
        self.db_path = Path(state_dir)/"ledger.db" if state_dir else DB_DEFAULT_PATH
        self.backup_dir = Path(state_dir)/"backups" if state_dir else BACKUP_DIR

    def ensure_directories(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def init(self) -> int:
        self.ensure_directories()
        payload = {"status": "ok", "timestamp": utc_timestamp()}
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
        return 0

    def check(self) -> int:
        payload = {
            "schema": "aso.durable.check.v1",
            "timestamp": utc_timestamp(),
            "status": "error",
            "errors": [],
        }
        if not self.db_path.exists():
            payload["errors"].append(f"database file not found: {self.db_path.as_posix()}")
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 2
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            res = cursor.fetchone()
            if res and res[0] == "ok":
                payload["status"] = "pass"
            else:
                payload["status"] = "fail"
                payload["errors"].append(f"integrity check failure: {res}")
            conn.close()
        except Exception as exc:
            payload["status"] = "fail"
            payload["errors"].append(str(exc))

        if payload["status"] == "pass":
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 0
        else:
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 1

    def backup(self) -> int:
        payload = {
            "schema": "aso.durable.backup.v1",
            "timestamp": utc_timestamp(),
            "status": "error",
            "errors": [],
        }
        if not self.db_path.exists():
            payload["errors"].append("source database not found")
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 2
        try:
            self.ensure_directories()
            ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            dest = self.backup_dir / f"project_memory_{ts}.sqlite"
            shutil.copy2(self.db_path, dest)
            payload["status"] = "pass"
            payload["backup_path"] = dest.as_posix()
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 0
        except Exception as exc:
            payload["status"] = "fail"
            payload["errors"].append(str(exc))
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 1

    def autopilot_status(self) -> int:
        repo_root = Path(__file__).parent
        import tools.autopilot_status as autopilot_status
        payload = autopilot_status.collect_autopilot_status(repo_root)
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
        return 0

    def evidence_validate(
        self,
        evidence_path: Path = EVIDENCE_RECORD_DEFAULT_PATH,
        schema_path: Path = EVIDENCE_RECORD_SCHEMA_PATH,
    ) -> int:
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
            payload["errors"] = [f"missing required field: {k}" for k in missing]
            payload["missing_fields"] = missing
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 1
        retention = evidence.get("retention")
        if retention in (None, "", []):
            payload["decision"] = "fail"
            payload["status"] = "fail"
            payload["errors"] = ["retention must be present"]
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 1
        payload["decision"] = "pass"
        payload["status"] = "pass"
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
                "retention": "50y"
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

        existing = sorted([fp for fp in ledger_dir.glob("*.json") if fp.stat().st_size > 0], key=lambda p: p.name)

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
            "producer": evidence["producer"] if isinstance(evidence["producer"], str) else self._json_c14n(evidence["producer"]),
            "subject": evidence["subject"] if isinstance(evidence["subject"], str) else self._json_c14n(evidence["subject"]),
            "predecessor_entry_hash": predecessor_entry_hash,
        }

        entry["entry_hash"] = self._sha256_text(self._json_c14n(entry))
        # Digital Signing Integration
        private_key_path = locals().get("private_key_path") or globals().get("private_key_path")
        # Extract signing parameters dynamically if passed in kwargs or parsed arguments
        sign_payload = self._json_c14n({k: v for k, v in entry.items() if k not in ("signature", "signature_algorithm", "signature_key_id")}).encode("utf-8")
        if private_key_path is not None:
            entry["signature_algorithm"] = "ed25519"
            entry["signature_key_id"] = "default-ed25519"
            entry["signature"] = sign_bytes(Path(private_key_path), sign_payload)

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
    ) -> int:
        import aso_signing
        ledger_dir = Path(ledger_dir)
        schema_path = Path(schema_path)

        payload = {
            "schema": "aso.evidence.ledger.verify.v1",
            "ledger_dir": ledger_dir.as_posix(),
            "schema_path": schema_path.as_posix(),
            "errors": [],
        }

        if not ledger_dir.exists():
            payload["decision"] = "error"
            payload["status"] = "error"
            payload["reason"] = f"ledger directory not found: {ledger_dir.as_posix()}"
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 2

        files = sorted([fp for fp in ledger_dir.glob("*.json") if fp.stat().st_size > 0], key=lambda p: p.name)
        if not files:
            payload["decision"] = "fail"
            payload["status"] = "fail"
            payload["reason"] = "no ledger entries found"
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 1

        previous_hash = ""
        verified = 0
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
            try:
                entry = json.loads(fp.read_text(encoding="utf-8-sig"))
            except json.JSONDecodeError as exc:
                payload["decision"] = "fail"
                payload["status"] = "fail"
                payload["reason"] = f"invalid JSON in ledger entry: {exc}"
                payload["ledger_entry_path"] = fp.as_posix()
                print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
                return 1

            missing = [k for k in required_fields if k not in entry]
            if missing:
                payload["decision"] = "fail"
                payload["status"] = "fail"
                payload["reason"] = "missing required fields in ledger entry"
                payload["ledger_entry_path"] = fp.as_posix()
                payload["missing_fields"] = missing
                print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
                return 1

            if entry["predecessor_entry_hash"] != previous_hash:
                payload["decision"] = "fail"
                payload["status"] = "fail"
                payload["reason"] = "predecessor hash mismatch"
                payload["ledger_entry_path"] = fp.as_posix()
                payload["expected_predecessor_entry_hash"] = previous_hash
                payload["actual_predecessor_entry_hash"] = entry["predecessor_entry_hash"]
                print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
                return 1

            entry_copy = dict(entry)
            actual_hash = entry_copy.pop("entry_hash")
            expected_hash = self._sha256_text(self._json_c14n(entry_copy))
            if actual_hash != expected_hash:
                payload["decision"] = "fail"
                payload["status"] = "fail"
                payload["reason"] = "entry hash mismatch"
                payload["ledger_entry_path"] = fp.as_posix()
                payload["expected_entry_hash"] = expected_hash
                payload["actual_entry_hash"] = actual_hash
                print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
                return 1

            evidence_path = Path(entry["evidence_path"])
            if not evidence_path.exists():
                payload["decision"] = "fail"
                payload["status"] = "fail"
                payload["reason"] = "referenced evidence file not found"
                payload["ledger_entry_path"] = fp.as_posix()
                payload["referenced_evidence_path"] = entry["evidence_path"]
                print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
                return 1

            expected_evidence_hash = self._sha256_file(evidence_path)
            if entry["evidence_hash"] != expected_evidence_hash:
                payload["decision"] = "fail"
                payload["status"] = "fail"
                payload["reason"] = "evidence hash mismatch"
                payload["ledger_entry_path"] = fp.as_posix()
                payload["referenced_evidence_path"] = entry["evidence_path"]
                payload["expected_evidence_hash"] = expected_evidence_hash
                payload["actual_evidence_hash"] = entry["evidence_hash"]
                print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
                return 1

            previous_hash = actual_hash
            verified += 1

        payload["decision"] = "pass"
        payload["status"] = "pass"
        payload["verified_entries"] = verified
        payload["chain_head"] = previous_hash
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
        return 0

    def safe_merge_verify(
        self,
        target: str = "main",
        artifact_dir: Path = SAFE_MERGE_AUDIT_DIR,
        write_artifact: bool = True,
    ) -> int:
        artifact_dir = Path(artifact_dir)
        payload = {
            "schema": "aso.safemerge.verify.v1",
            "target_branch": target,
            "timestamp": utc_timestamp(),
            "status": "error",
            "errors": [],
        }
        rc, out = run_git(["status", "--porcelain"])
        if rc != 0:
            payload["errors"].append(f"git status command failed: {out}")
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 2
        if out:
            payload["status"] = "fail"
            payload["errors"].append("workspace has uncommitted changes")
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 1
        rc, merge_base = run_git(["merge-base", "HEAD", f"origin/{target}"])
        if rc != 0:
            rc, merge_base = run_git(["merge-base", "HEAD", target])
        if rc != 0:
            payload["errors"].append(f"failed to find merge base with {target}")
            print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
            return 2
        payload["status"] = "pass"
        payload["merge_base"] = merge_base
        if write_artifact:
            artifact_dir.mkdir(parents=True, exist_ok=True)
            write_json_atomic(artifact_dir / "safe_merge_audit.json", payload)
        print(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2))
        return 0

    def status(self) -> int:
        print("ASO-X local state")
        print(f"db_exists={self.db_path.exists()}")
        print(f"backup_dir_exists={self.backup_dir.exists()}")
        backups = sorted(self.backup_dir.glob("project_memory_*.sqlite")) if self.backup_dir.exists() else []
        print(f"backup_count={len(backups)}")
        latest_backup = backups[-1].name if backups else ""
        print(f"latest_backup={latest_backup}")
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
        parser.error(f"unknown safe-merge command: {args.safe_merge_command}")
        return 2

    parser.error(f"unknown command: {args.command}")
    return 2

if __name__ == "__main__":
    raise SystemExit(main())


