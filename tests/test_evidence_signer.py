import pytest
from src.security.evidence_signer import EvidenceSigner

@pytest.fixture
def secret_key():
    return b"super-secure-kms-mock-key-32bytes!!"

@pytest.fixture
def signer(secret_key):
    return EvidenceSigner(key_id="kms-key-prod-01", secret_key=secret_key)

@pytest.fixture
def sample_record():
    return {
        "version": "1.0.0",
        "uuid": "f81d4fae-7dec-11d0-a765-00a0c91e6bf6",
        "timestamp": "2026-07-14T16:00:00Z",
        "producer": "aso-x-policy-engine",
        "event_type": "ledger_rotation",
        "payload_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }

def test_sign_record_appends_signature(signer, sample_record):
    signed = signer.sign_record(sample_record)
    
    assert "signatures" in signed
    assert len(signed["signatures"]) == 1
    assert signed["signatures"][0]["key_id"] == "kms-key-prod-01"
    assert len(signed["signatures"][0]["signature"]) == 64  # Hex length of SHA256

def test_verify_record_success(signer, sample_record):
    signed = signer.sign_record(sample_record)
    assert signer.verify_record(signed) is True

def test_verify_record_tampered_fails(signer, sample_record):
    signed = signer.sign_record(sample_record)
    
    # Tamper with the data
    signed["event_type"] = "tampered_event"
    
    assert signer.verify_record(signed) is False