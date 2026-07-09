from pathlib import Path
import json
import pytest
from aso_signing import sign_bytes, verify_bytes

def test_ledger_signing_logic(tmp_path):
    # Dummy keys using Ed25519
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
    except ImportError:
        pytest.skip("cryptography library not installed")

    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()

    priv_path = tmp_path / "private.pem"
    pub_path = tmp_path / "public.pem"

    priv_path.write_bytes(priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ))
    pub_path.write_bytes(pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))

    payload = b"ASO-X secure audit trail 50y validation"
    sig = sign_bytes(priv_path, payload)
    assert sig.startswith("base64:")

    assert verify_bytes(pub_path, payload, sig) is True
    assert verify_bytes(pub_path, payload + b"tampered", sig) is False
