#!/usr/bin/env python3
"""
verify_audit_chain.py — canonical verifier for runtime/audit/decision_audit.jsonl

Scheme is LOCKED to the empirically calibrated writer scheme:
    entry_hash = sha256( (prev_hash_hex + json.dumps(payload, sort_keys=True,
                          ensure_ascii=CANONICAL_ENSURE_ASCII)).encode("utf-8") ).hexdigest()
where:
    - payload = entry with "_hash" removed (and "_prev_hash" RETAINED, per calibration)
    - prev_hash_hex of the genesis record = "0" * 64
    - records are JSONL: one JSON object per line, in chain order

NOTE on ensure_ascii: the existing chain is pure-ASCII, so True/False are
indistinguishable from current data. Locked to False to match the repo
UTF-8/LF standard and to remain correct for future non-ASCII (e.g. Persian)
audit payloads. Do not "auto-detect" — that introduced silent ambiguity.
"""
import json
import hashlib
import sys
from pathlib import Path

AUDIT_PATH = Path("runtime/audit/decision_audit.jsonl")
GENESIS_PREV_HASH = "0" * 64
CANONICAL_ENSURE_ASCII = False  # LOCKED — see module docstring


def compute_entry_hash(prev_hash: str, payload: dict) -> str:
    body = json.dumps(payload, sort_keys=True, ensure_ascii=CANONICAL_ENSURE_ASCII)
    return hashlib.sha256((prev_hash + body).encode("utf-8")).hexdigest()


def load_chain(path: Path) -> list[dict]:
    entries = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {lineno}: invalid JSON: {exc}") from exc
    return entries


def verify(path: Path = AUDIT_PATH) -> dict:
    if not path.exists():
        return {"status": "missing", "path": str(path)}

    chain = load_chain(path)
    if not chain:
        return {"status": "empty", "path": str(path)}

    prev_hash = GENESIS_PREV_HASH
    for index, entry in enumerate(chain):
        stored_hash = entry.get("_hash")
        if stored_hash is None:
            return {"status": "malformed", "at_index": index,
                    "reason": "missing _hash"}

        if entry.get("_prev_hash") != prev_hash:
            return {"status": "broken_link", "at_index": index,
                    "expected_prev": prev_hash,
                    "found_prev": entry.get("_prev_hash")}

        payload = {k: v for k, v in entry.items() if k != "_hash"}
        recomputed = compute_entry_hash(prev_hash, payload)
        if recomputed != stored_hash:
            return {"status": "tampered", "at_index": index,
                    "expected_hash": recomputed,
                    "stored_hash": stored_hash}

        prev_hash = stored_hash

    return {"status": "verified", "entries": len(chain), "head_hash": prev_hash}


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "verified" else 1


if __name__ == "__main__":
    sys.exit(main())