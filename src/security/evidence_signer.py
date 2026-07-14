import hmac
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

class EvidenceSigner:
    """
    Cryptographic Signer for ASO-X Evidence Records.
    Provides secure signatures using HMAC-SHA256 over canonical record data.
    """
    def __init__(self, key_id: str, secret_key: bytes):
        if not key_id:
            raise ValueError("key_id cannot be empty")
        if not secret_key or len(secret_key) < 16:
            raise ValueError("secret_key must be at least 16 bytes long")
        
        self.key_id = key_id
        self.secret_key = secret_key

    def _canonical_data(self, record: dict) -> bytes:
        """
        Creates a deterministic byte representation of the target record fields.
        Excludes existing signatures for signing validation.
        """
        # Create a copy and strip signatures to get the signable body
        signable_part = {k: v for k, v in record.items() if k != "signatures"}
        # Serialize deterministically (sorted keys, no-BOM UTF-8, LF endings)
        serialized = json.dumps(signable_part, sort_keys=True, ensure_ascii=False)
        normalized = serialized.replace("\r\n", "\n").replace("\r", "\n")
        return normalized.encode("utf-8")

    def sign_record(self, record: dict) -> dict:
        """
        Signs the given record and appends the signature to its 'signatures' array.
        Returns the mutated or new dictionary.
        """
        signed_record = record.copy()
        
        # Calculate HMAC-SHA256 signature
        data_to_sign = self._canonical_data(signed_record)
        signature_hash = hmac.new(self.secret_key, data_to_sign, hashlib.sha256).hexdigest()
        
        # Initialize signatures array if not exists
        if "signatures" not in signed_record or not isinstance(signed_record["signatures"], list):
            signed_record["signatures"] = []
            
        # Append new signature block
        signed_record["signatures"].append({
            "key_id": self.key_id,
            "signature": signature_hash
        })
        
        return signed_record

    def verify_record(self, record: dict) -> bool:
        """
        Verifies if there is a valid signature matching this signer's key_id and secret_key.
        """
        if "signatures" not in record or not isinstance(record["signatures"], list):
            return False
            
        # Find matching signature for our key_id
        matching_sig = None
        for sig in record["signatures"]:
            if sig.get("key_id") == self.key_id:
                matching_sig = sig.get("signature")
                break
                
        if not matching_sig:
            return False
            
        # Re-calculate and verify
        data_to_verify = self._canonical_data(record)
        expected_sig = hmac.new(self.secret_key, data_to_verify, hashlib.sha256).hexdigest()
        
        return hmac.compare_digest(matching_sig, expected_sig)