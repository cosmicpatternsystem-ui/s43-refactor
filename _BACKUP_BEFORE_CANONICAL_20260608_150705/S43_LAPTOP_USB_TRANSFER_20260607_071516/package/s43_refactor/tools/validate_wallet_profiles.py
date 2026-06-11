#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ALLOWED_TOP_LEVEL_KEYS = {"version", "default_profile", "wallets"}
REQUIRED_TOP_LEVEL_KEYS = {"version", "default_profile", "wallets"}
ALLOWED_WALLET_KEYS = {"label", "network", "address", "enabled"}
REQUIRED_WALLET_KEYS = {"label", "network", "address", "enabled"}
ALLOWED_NETWORKS = {"TRX"}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"ERROR: file not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: invalid JSON in {path}: {exc}")


def ensure(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_wallet(name: str, payload: Any, errors: list[str]) -> None:
    ensure(isinstance(payload, dict), f"wallet '{name}' must be an object", errors)
    if not isinstance(payload, dict):
        return

    unknown = sorted(set(payload.keys()) - ALLOWED_WALLET_KEYS)
    missing = sorted(REQUIRED_WALLET_KEYS - set(payload.keys()))

    if unknown:
        errors.append(f"wallet '{name}' has unknown keys: {', '.join(unknown)}")
    if missing:
        errors.append(f"wallet '{name}' is missing keys: {', '.join(missing)}")

    label = payload.get("label")
    network = payload.get("network")
    address = payload.get("address")
    enabled = payload.get("enabled")

    ensure(
        isinstance(label, str) and label.strip() != "",
        f"wallet '{name}' label must be a non-empty string",
        errors,
    )
    ensure(
        network in ALLOWED_NETWORKS,
        f"wallet '{name}' network must be one of: {', '.join(sorted(ALLOWED_NETWORKS))}",
        errors,
    )
    ensure(
        isinstance(address, str) and address.strip() != "",
        f"wallet '{name}' address must be a non-empty string",
        errors,
    )
    ensure(
        isinstance(enabled, bool),
        f"wallet '{name}' enabled must be a boolean",
        errors,
    )


def validate_profile(payload: Any) -> dict[str, Any]:
    errors: list[str] = []

    ensure(isinstance(payload, dict), "top-level JSON value must be an object", errors)
    if not isinstance(payload, dict):
        return {"ok": False, "errors": errors}

    unknown = sorted(set(payload.keys()) - ALLOWED_TOP_LEVEL_KEYS)
    missing = sorted(REQUIRED_TOP_LEVEL_KEYS - set(payload.keys()))

    if unknown:
        errors.append(f"unknown top-level keys: {', '.join(unknown)}")
    if missing:
        errors.append(f"missing top-level keys: {', '.join(missing)}")

    version = payload.get("version")
    default_profile = payload.get("default_profile")
    wallets = payload.get("wallets")

    ensure(version == 1, "version must be exactly 1", errors)
    ensure(
        isinstance(default_profile, str) and default_profile.strip() != "",
        "default_profile must be a non-empty string",
        errors,
    )
    ensure(
        isinstance(wallets, dict) and len(wallets) > 0,
        "wallets must be a non-empty object",
        errors,
    )

    if isinstance(wallets, dict) and wallets:
        for wallet_name, wallet_payload in wallets.items():
            ensure(
                isinstance(wallet_name, str) and wallet_name.strip() != "",
                "wallet names must be non-empty strings",
                errors,
            )
            validate_wallet(str(wallet_name), wallet_payload, errors)

        if isinstance(default_profile, str) and default_profile.strip():
            ensure(
                default_profile in wallets,
                "default_profile must match one of the wallet names",
                errors,
            )

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "wallet_count": len(wallets) if isinstance(wallets, dict) else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate TriWallet profile JSON in read-only mode."
    )
    parser.add_argument("json_file", help="Path to wallet profile JSON file")
    parser.add_argument(
        "--report-json",
        dest="report_json",
        help="Optional path to write JSON validation report",
    )
    args = parser.parse_args()

    path = Path(args.json_file)
    payload = load_json(path)
    report = validate_profile(payload)
    report["file"] = str(path)

    rendered = json.dumps(report, indent=2, ensure_ascii=True)
    print(rendered)

    if args.report_json:
        Path(args.report_json).write_text(rendered + "\n", encoding="utf-8")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
