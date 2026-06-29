#!/usr/bin/env python3
"""Roadmap Guard â€” Startup & CI Validation"""
import json
import sys
from pathlib import Path

SOURCE_OF_TRUTH = "repository_files_only"
ROADMAP_PATH = Path("docs/governance/ROADMAP_CURRENT.json")

def validate() -> None:
    if not ROADMAP_PATH.exists():
        print(f"âœ— Roadmap not found: {ROADMAP_PATH}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(ROADMAP_PATH.read_text(encoding="utf-8"))
    required = ["schema_version", "roadmap_version", "authority", "lifecycle"]
    missing = [f for f in required if f not in data]
    if missing:
        print(f"âœ— Missing fields: {missing}", file=sys.stderr)
        sys.exit(1)
    source = data.get("authority", {}).get("source")
    if source != SOURCE_OF_TRUTH:
        print(f"âœ— source_of_truth mismatch:\n  Expected: {SOURCE_OF_TRUTH}\n  Got: {source}", file=sys.stderr)
        sys.exit(1)
    if data.get("schema_version") != "2.0":
        print(f"âœ— Invalid schema_version: {data.get('schema_version')}", file=sys.stderr)
        sys.exit(1)
    print("[OK] Roadmap validation passed")

if __name__ == "__main__":
    validate()