from __future__ import annotations

import base64
from pathlib import Path

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
    from cryptography.hazmat.primitives import serialization
except Exception as exc:
    Ed25519PrivateKey = None
    Ed25519PublicKey = None
    serialization = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

def _require_crypto():
    if _IMPORT_ERROR is not None:
        raise RuntimeError(
            "cryptography is required for ledger signing. Install it first."
        ) from _IMPORT_ERROR

def load_private_key(path: Path):
    _require_crypto()
    data = Path(path).read_bytes()
    return serialization.load_pem_private_key(data, password=None)

def load_public_key(path: Path):
    _require_crypto()
    data = Path(path).read_bytes()
    return serialization.load_pem_public_key(data)

def sign_bytes(private_key_path: Path, payload: bytes) -> str:
    _require_crypto()
    key = load_private_key(private_key_path)
    sig = key.sign(payload)
    return "base64:" + base64.b64encode(sig).decode("ascii")

def verify_bytes(public_key_path: Path, payload: bytes, signature_text: str) -> bool:
    _require_crypto()
    if not signature_text or not signature_text.startswith("base64:"):
        return False
    sig = base64.b64decode(signature_text[len("base64:"):])
    key = load_public_key(public_key_path)
    try:
        key.verify(sig, payload)
        return True
    except Exception:
        return False
