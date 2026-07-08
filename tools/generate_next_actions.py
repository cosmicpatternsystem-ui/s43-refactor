from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TEXT = """# ASO-X Next Actions

1. Run `python tools\\project_status.py`.
2. Run `python asoctl.py validate`.
3. Run `python asoctl.py governance-check`.
4. Run `python asoctl.py revenue-readiness`.
5. Run `python -m pytest -q`.
6. Commit through a PR when checks pass.
"""

def main() -> int:
    (ROOT / "NEXT_ACTIONS.md").write_text(TEXT, encoding="utf-8", newline="\n")
    print("NEXT_ACTIONS.md updated")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
