from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs" / "release"


REQUIRED_DOCS = {
    "release-governance.md": {
        "title_prefix": "# ",
        "required_terms": [
            "release",
            "governance",
            "audit",
            "owner",
            "evidence",
        ],
    },
    "versioning-policy.md": {
        "title_prefix": "# ",
        "required_terms": [
            "version",
            "semantic",
            "tag",
            "release",
        ],
    },
    "rollback-protocol.md": {
        "title_prefix": "# ",
        "required_terms": [
            "rollback",
            "trigger",
            "authority",
            "verification",
        ],
    },
    "incident-response-protocol.md": {
        "title_prefix": "# ",
        "required_terms": [
            "incident",
            "severity",
            "commander",
            "timeline",
            "post-incident",
        ],
    },
    "production-readiness-checklist.md": {
        "title_prefix": "# ",
        "required_terms": [
            "production",
            "readiness",
            "go/no-go",
            "verification",
            "rollback",
        ],
    },
    "dependency-freeze-policy.md": {
        "title_prefix": "# ",
        "required_terms": [
            "dependency",
            "freeze",
            "window",
            "exception",
            "approval",
        ],
    },
    "artifact-integrity-policy.md": {
        "title_prefix": "# ",
        "required_terms": [
            "artifact",
            "integrity",
            "checksum",
            "signature",
            "provenance",
        ],
    },
}


def _read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate_release_governance() -> dict:
    errors: list[str] = []
    checked_files: list[str] = []

    if not DOCS_DIR.exists():
        errors.append(f"missing_docs_directory:{DOCS_DIR.as_posix()}")
        return {
            "ok": False,
            "docs_dir": DOCS_DIR.as_posix(),
            "checked_files": checked_files,
            "errors": errors,
        }

    for filename, spec in REQUIRED_DOCS.items():
        path = DOCS_DIR / filename
        checked_files.append(path.as_posix())

        if not path.exists():
            errors.append(f"missing_file:{path.as_posix()}")
            continue

        try:
            text = _read_utf8(path)
        except UnicodeDecodeError:
            errors.append(f"not_utf8:{path.as_posix()}")
            continue

        stripped = text.lstrip("\ufeff").strip()
        lines = stripped.splitlines()

        if not lines:
            errors.append(f"empty_file:{path.as_posix()}")
            continue

        first_line = lines[0].strip()
        if not first_line.startswith(spec["title_prefix"]):
            errors.append(f"missing_heading:{path.as_posix()}")

        lowered = stripped.lower()
        for term in spec["required_terms"]:
            if term.lower() not in lowered:
                errors.append(f"missing_term:{path.as_posix()}::{term}")

    return {
        "ok": not errors,
        "docs_dir": DOCS_DIR.as_posix(),
        "checked_files": checked_files,
        "errors": errors,
    }


def main() -> int:
    result = validate_release_governance()
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
