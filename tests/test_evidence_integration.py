import os
import json
import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519
from src.security.evidence_writer import EvidenceSigner, EvidencePipeline

def test_full_evidence_pipeline_integration(tmp_path):
    private_key, public_key = EvidenceSigner.generate_keypair()
    evidence_payload = {
        "version": "1.0.0",
        "timestamp": "2026-07-14T12:00:00Z",
        "event_type": "transaction_checkpoint",
        "payload": {
            "transaction_id": "tx_99999",
            "amount": 15000.50,
            "currency": "USD"
        }
    }
    filepath = os.path.join(tmp_path, "evidence_record_secured.json")
    pipeline = EvidencePipeline()
    signed_record = pipeline.process_and_save(
        evidence=evidence_payload,
        private_key=private_key,
        public_key=public_key,
        dest_filepath=filepath
    )
    assert os.path.exists(filepath)
    assert "signature" in signed_record["metadata"]
    assert "public_key" in signed_record["metadata"]
    
    with open(filepath, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)
        
    raw_data_to_verify = saved_data.copy()
    sig_hex = raw_data_to_verify["metadata"].pop("signature")
    raw_data_to_verify["metadata"].pop("public_key")
    if not raw_data_to_verify["metadata"]:
        raw_data_to_verify.pop("metadata")
        
    is_signature_valid = EvidenceSigner.verify_signature(
        raw_data_to_verify,
        sig_hex,
        public_key
    )
    assert is_signature_valid is True

def test_pipeline_validation_failure():
    pipeline = EvidencePipeline()
    private_key, public_key = EvidenceSigner.generate_keypair()
    invalid_payload = {
        "event_type": "malformed_data",
        "payload": {}
    }
    with pytest.raises(Exception):
        pipeline.process_and_save(
            evidence=invalid_payload,
            private_key=private_key,
            public_key=public_key,
            dest_filepath="dummy.json"
        )
