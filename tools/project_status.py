from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "AGENTS.md",
    "docs/PROJECT_STATE.md",
    "docs/ROADMAP.md",
    "docs/NEXT_ACTIONS.md",
    "docs/governance/GOVERNANCE_BASELINE.md",
    "docs/governance/LOCK_REGISTRY.json",
    "docs/governance/LOCK_SCHEMA.json",
    ".github/workflows/governance-enforcement.yml",
    "tests/test_governance_bootstrap.py",
    "tools/project_status.py",
]

def safe(s: str) -> str:
    return s.encode("cp1252", errors="replace").decode("cp1252")

def main() -> int:
    missing = [p for p in REQUIRED_FILES if not (ROOT / p).exists()]
    registry_path = ROOT / "docs/governance/LOCK_REGISTRY.json"
    lock_count = 0
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        lock_count = len(registry.get("locks", []))
    lines = [
        "Project: ASO-X",
        "Bootstrap: active" if not missing else "Bootstrap: incomplete",
        "Source of truth: repository-only",
        "Baseline branch: main",
        f"Critical artifacts present: {len(REQUIRED_FILES) - len(missing)}/{len(REQUIRED_FILES)}",
        f"Governance locks declared: {lock_count}",
        "Next phase: bootstrap-and-hardening",
    ]
    if missing:
        lines.append("Missing artifacts:")
        lines.extend([f"- {m}" for m in missing])
    else:
        lines.append("Missing artifacts: none")
    sys.stdout.write(safe("\n".join(lines) + "\n"))
    return 1 if missing else 0

if __name__ == "__main__":
    raise SystemExit(main())