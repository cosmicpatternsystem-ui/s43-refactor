from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_governance_hardening_check_passes() -> None:
result = subprocess.run(
[sys.executable, "tools/governance_hardening_check.py"],
cwd=ROOT,
text=True,
stdout=subprocess.PIPE,
stderr=subprocess.STDOUT,
check=False,
)

assert result.returncode == 0, result.stdout
assert "OK: governance hardening pack validated" in result.stdout


def test_canonical_sources_contract_exists() -> None:
path = ROOT / "repo/contracts/CANONICAL_SOURCES.yaml"
text = path.read_text(encoding="utf-8")

required = [
"project_charter:",
"roadmap:",
"governance_baseline:",
"policy_matrix:",
"decision_log:",
"compatibility_contract:",
"chat_memory_is_not_source_of_truth: true",
]

for fragment in required:
assert fragment in text, f"missing canonical source fragment: {fragment}"


def test_project_charter_rejects_chat_memory_dependency() -> None:
text = (ROOT / "PROJECT_CHARTER.md").read_text(encoding="utf-8")

assert "No operating decision may depend on chat memory" in text
assert "Every future session, contributor, or automation agent must begin from repository state" in text