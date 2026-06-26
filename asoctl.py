#!/usr/bin/env python3
"""ASO-X project control utility.

Provides durable-state checks, local backups, and basic environment bootstrap
for the ASO-X workspace.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import sqlite3
import sys
from pathlib import Path


PROJECT_NAME = "ASO-X"
STATE_DIR = Path("runtime/state")
DB_PATH = STATE_DIR / "project_memory.sqlite"
BACKUP_DIR = STATE_DIR / "backups"


def utc_timestamp() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")


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

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
