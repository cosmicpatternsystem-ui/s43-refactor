import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

import jsonschema
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


class AtomicEvidenceWriter:
    """Atomic write operations for evidence files with schema validation."""

    def __init__(self, schema_path):
        self.schema_path = Path(schema_path)
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

        with self.schema_path.open("r", encoding="utf-8") as f:
            self.schema = json.load(f)

    def validate_record(self, record: dict) -> None:
        jsonschema.validate(instance=record, schema=self.schema)

    def write_atomic(self, target_path, record: dict) -> None:
        self.validate_record(record)

        target_path = Path(target_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(
            dir=str(target_path.parent),
            prefix=".tmp_evidence_",
            suffix=".json",
        )

        tmp_file = Path(tmp_path)

        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                json.dump(record, f, indent=2, ensure_ascii=False)
                f.write("\n")

            os.replace(tmp_file, target_path)
        except Exception:
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except Exception:
                    pass
            raise


class EvidenceSigner:
    """Ed25519 signing and verification logic."""

    @staticmethod
    def generate_keypair():
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def _normalize_for_signing(payload: dict) -> bytes:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

    @staticmethod
    def sign_payload(payload: dict, private_key) -> str:
        data_to_sign = EvidenceSigner._normalize_for_signing(payload)
        signature = private_key.sign(data_to_sign)
        return signature.hex()

    @staticmethod
    def verify_signature(payload: dict, signature, public_key) -> bool:
        try:
            signature_bytes = bytes.fromhex(signature) if isinstance(signature, str) else signature
            data_to_verify = EvidenceSigner._normalize_for_signing(payload)
            public_key.verify(signature_bytes, data_to_verify)
            return True
        except Exception:
            return False


class EvidencePipeline:
    """Integrates validation, signing, and atomic writing."""

    REQUIRED_FIELDS = ("version", "timestamp", "event_type", "payload")

    def __init__(self, schema_path=None):
        self.writer = AtomicEvidenceWriter(schema_path) if schema_path else None

    @staticmethod
    def _validate_evidence(evidence: Dict[str, Any]) -> None:
        if not isinstance(evidence, dict):
            raise ValueError("Evidence must be a dictionary.")

        missing = [k for k in EvidencePipeline.REQUIRED_FIELDS if k not in evidence]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        if not isinstance(evidence["version"], str) or not evidence["version"].strip():
            raise ValueError("version must be a non-empty string.")

        if not isinstance(evidence["timestamp"], str) or not evidence["timestamp"].strip():
            raise ValueError("timestamp must be a non-empty string.")

        if not isinstance(evidence["event_type"], str) or not evidence["event_type"].strip():
            raise ValueError("event_type must be a non-empty string.")

        if not isinstance(evidence["payload"], dict):
            raise ValueError("payload must be a dictionary.")

    @staticmethod
    def _public_key_to_hex(public_key) -> str:
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return public_bytes.hex()

    @staticmethod
    def _write_without_schema_validation(target_path, record: dict) -> None:
        target_path = Path(target_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(
            dir=str(target_path.parent),
            prefix=".tmp_evidence_",
            suffix=".json",
        )

        tmp_file = Path(tmp_path)

        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                json.dump(record, f, indent=2, ensure_ascii=False)
                f.write("\n")

            os.replace(tmp_file, target_path)
        except Exception:
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except Exception:
                    pass
            raise

    def process_and_save(self, evidence: Dict[str, Any], private_key, public_key, dest_filepath: str):
        self._validate_evidence(evidence)

        base_record = {
            "version": evidence["version"],
            "timestamp": evidence["timestamp"],
            "event_type": evidence["event_type"],
            "payload": evidence["payload"],
        }

        signable_record = {
            **base_record,
            "metadata": {
                "algorithm": "Ed25519",
            },
        }

        signature = EvidenceSigner.sign_payload(signable_record, private_key)
        public_key_hex = self._public_key_to_hex(public_key)

        secured_record = {
            **base_record,
            "metadata": {
                "signature": signature,
                "public_key": public_key_hex,
                "algorithm": "Ed25519",
            },
        }

        if self.writer is not None:
            self.writer.write_atomic(dest_filepath, secured_record)
        else:
            self._write_without_schema_validation(dest_filepath, secured_record)

        return secured_record

