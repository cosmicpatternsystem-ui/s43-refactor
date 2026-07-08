from pathlib import Path
import json

ROOT = Path.cwd()

files = {
    "docs/governance/CANONICAL_ROADMAP_DECLARATION.md": """# Canonical Roadmap Declaration

Status: Active
Scope: ASO-X / s43-refactor
Canonical source: `docs/ROADMAP.md`
Governance class: 50-year durable roadmap governance
Baseline date: 2026-07-05
Baseline state: CLOSED / MERGED / VERIFIED / BASELINE-RECORDED / CLEAN

## Purpose

This document declares the official roadmap governance model for the repository.

## Canonical Sources

- Human-readable canonical roadmap source: `docs/ROADMAP.md`
- Machine-readable canonical roadmap index: `docs/roadmap/roadmap.index.json`

## Governance Rules

1. `docs/ROADMAP.md` is the canonical human-readable roadmap.
2. `docs/roadmap/roadmap.index.json` is the canonical machine-readable roadmap index.
3. Durable roadmap requirements must have stable IDs.
4. Requirement IDs must never be reused after retirement.
5. Active governance requirements must be CI-validatable where applicable.
6. Governance artifacts must remain portable and long-lived.
7. Repository state is authoritative over prior conversation state.
""",
    "docs/governance/ROADMAP_STEWARDSHIP_50Y.md": """# 50-Year Roadmap Stewardship

Status: Active
Horizon: 50 years

## Stewardship Principles

1. Preserve roadmap history in Git.
2. Avoid undocumented rewrites of durable requirements.
3. Use stable requirement IDs.
4. Prefer portable text formats.
5. Keep governance understandable for future humans and AI systems.
6. Validate machine-readable roadmap metadata in CI.
7. Record major baseline transitions in repository documentation.
""",
    "docs/governance/DEPRECATION_RESISTANCE.md": """# Deprecation Resistance Policy

Status: Active

## Rules

1. Prefer plain text formats.
2. Prefer Markdown for human-readable governance.
3. Prefer JSON for machine-readable governance.
4. Avoid binary-only governance formats.
5. Preserve historical records.
6. Use UTF-8 without BOM and LF line endings.
""",
    "docs/governance/AI_HANDOFF.md": """# AI Handoff

Status: Active

## First Files To Inspect

1. `docs/ROADMAP.md`
2. `docs/roadmap/roadmap.index.json`
3. `docs/governance/CANONICAL_ROADMAP_DECLARATION.md`
4. `docs/governance/CURRENT_PROJECT_BASELINE.md`
5. relevant policy files
6. relevant GitHub Actions workflows

## Safety Rule

If repository state and prior conversation conflict, repository state wins.
""",
    "docs/governance/CURRENT_PROJECT_BASELINE.md": """# Current Project Baseline

Status: Active
Baseline date: 2026-07-05
Repository state class: CLOSED / MERGED / VERIFIED / BASELINE-RECORDED / CLEAN

## Purpose

This document records the durable baseline before roadmap governance hardening.
""",
    "docs/value/VALUE_MODEL.md": """# Value Model

Status: Active

## Value Drivers

1. Reduced merge risk
2. Better auditability
3. Better AI continuation
4. Better long-term maintainability
5. Better policy visibility
6. Better transferability to other repositories
""",
    "docs/roadmap/roadmap.index.json": json.dumps({
        "schema_version": "1.0",
        "repository": "s43-refactor",
        "project": "ASO-X",
        "canonical_source": "docs/ROADMAP.md",
        "horizon_years": 50,
        "status": "active",
        "baseline_date": "2026-07-05",
        "governance_documents": [
            "docs/governance/CANONICAL_ROADMAP_DECLARATION.md",
            "docs/governance/ROADMAP_STEWARDSHIP_50Y.md",
            "docs/governance/DEPRECATION_RESISTANCE.md",
            "docs/governance/AI_HANDOFF.md",
            "docs/governance/CURRENT_PROJECT_BASELINE.md",
            "docs/value/VALUE_MODEL.md"
        ],
        "validation": {
            "ci_required": True,
            "workflow": ".github/workflows/roadmap-governance-gate.yml",
            "test_file": "tests/test_roadmap_governance.py"
        },
        "requirements": [
            {
                "id": "ASO-ROADMAP-GLOBAL-001",
                "phase": "global",
                "type": "top-level",
                "title": "Canonical roadmap source",
                "status": "active",
                "description": "The repository must define a canonical human-readable roadmap source.",
                "canonical_source": "docs/ROADMAP.md",
                "evidence_required": True,
                "ci_enforced": True
            },
            {
                "id": "ASO-ROADMAP-GLOBAL-002",
                "phase": "global",
                "type": "global",
                "title": "50-year roadmap horizon",
                "status": "active",
                "description": "The roadmap governance model must preserve a 50-year durability horizon.",
                "evidence_required": True,
                "ci_enforced": True
            }
        ]
    }, indent=2) + "\n",
    "tests/test_roadmap_governance.py": """import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "docs" / "roadmap" / "roadmap.index.json"
REQ_ID_RE = re.compile(r"^ASO-[A-Z0-9]+(?:-[A-Z0-9]+)*-\\d{3}$")

def assert_utf8_no_bom_lf(path):
    data = path.read_bytes()
    assert not data.startswith(b"\\xef\\xbb\\xbf")
    assert b"\\r\\n" not in data
    assert b"\\r" not in data
    data.decode("utf-8")

def test_roadmap_index_exists_and_is_valid_json():
    assert INDEX_PATH.exists()
    assert_utf8_no_bom_lf(INDEX_PATH)
    payload = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    assert payload["canonical_source"] == "docs/ROADMAP.md"
    assert payload["horizon_years"] >= 50
    assert payload["status"] == "active"

def test_governance_documents_exist():
    payload = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    docs = payload.get("governance_documents", [])
    assert docs
    for rel in docs:
        path = ROOT / rel
        assert path.exists()
        assert_utf8_no_bom_lf(path)

def test_requirement_ids_are_unique_and_valid():
    payload = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    ids = [r["id"] for r in payload["requirements"]]
    assert len(ids) == len(set(ids))
    for rid in ids:
        assert REQ_ID_RE.match(rid)
""",
    ".github/workflows/roadmap-governance-gate.yml": """name: Roadmap Governance Gate

on:
  pull_request:
    branches: [ "main" ]
    paths:
      - "docs/ROADMAP.md"
      - "docs/roadmap/**"
      - "docs/governance/**"
      - "docs/value/**"
      - "tests/test_roadmap_governance.py"
      - ".github/workflows/roadmap-governance-gate.yml"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  roadmap-governance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.x"
      - run: python -m pytest tests/test_roadmap_governance.py
"""
}

for rel, content in files.items():
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    text = content.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8", newline="\n")

print(f"WROTE {len(files)} files")