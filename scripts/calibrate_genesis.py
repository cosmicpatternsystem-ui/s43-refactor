import json, hashlib, itertools
from pathlib import Path

AUDIT = Path("runtime/audit/decision_audit.jsonl")
rec = json.loads(AUDIT.read_bytes().split(b"\n", 1)[0])
target = rec["_hash"]
prev = rec["_prev_hash"]

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

# --- payload key-exclusion variants ---
def payload(exclude):
    return {k: v for k, v in rec.items() if k not in exclude}

exclusions = {
    "drop _hash only":            {"_hash"},
    "drop _hash + _prev_hash":    {"_hash", "_prev_hash"},
}

# --- serializers ---
serializers = {
    "compact no-ascii sort":   lambda p: json.dumps(p, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    "compact ascii sort":      lambda p: json.dumps(p, sort_keys=True, separators=(",", ":")),
    "compact no-ascii order":  lambda p: json.dumps(p, ensure_ascii=False, separators=(",", ":")),
    "compact ascii order":     lambda p: json.dumps(p, separators=(",", ":")),
    "defaultsep no-ascii sort":lambda p: json.dumps(p, ensure_ascii=False, sort_keys=True),
    "defaultsep ascii sort":   lambda p: json.dumps(p, sort_keys=True),
    "defaultsep ascii order":  lambda p: json.dumps(p),
}

# --- chain modes: how prev_hash is combined with the serialized body ---
def chain_variants(body: str):
    yield ("no-chain", body.encode("utf-8"))
    yield ("prev_str + body", (prev + body).encode("utf-8"))
    yield ("body + prev_str", (body + prev).encode("utf-8"))
    yield ("prev_bytes + body", bytes.fromhex(prev) + body.encode("utf-8"))
    yield ("body + prev_bytes", body.encode("utf-8") + bytes.fromhex(prev))
    yield ("prev_str + '\\n' + body", (prev + "\n" + body).encode("utf-8"))

newlines = {"no-nl": "", "trailing-nl": "\n"}

print(f"target _hash: {target}\n")

hits = []
total = 0
for (ex_name, ex), (ser_name, ser), (nl_name, nl) in itertools.product(
        exclusions.items(), serializers.items(), newlines.items()):
    body = ser(payload(ex)) + nl
    for chain_name, data in chain_variants(body):
        total += 1
        got = sha(data)
        if got == target:
            hits.append(f"{ex_name} | {ser_name} | {chain_name} | {nl_name}")

print(f"tested {total} combinations")
if hits:
    print("\nMATCH(es):")
    for h in hits:
        print("  <<< " + h)
else:
    print("\nNO MATCH across full matrix")