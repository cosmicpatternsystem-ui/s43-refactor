import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
import jsonschema

class AtomicEvidenceWriter:
    """
    High-integrity atomic writer for ASO-X Evidence Records conforming to Policy P3.2/P3.3.
    Guarantees BOM-free UTF-8 LF serialization and prevention of partial writes.
    """
    def __init__(self, schema_path: Path):
        self.schema_path = Path(schema_path)
        if not self.schema_path.exists():
            raise FileNotFoundError(f"JSON Schema not found at {self.schema_path}")
        
        with open(self.schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

    def validate_record(self, record: dict) -> None:
        """Validates a record against the configured JSON schema."""
        jsonschema.validate(instance=record, schema=self.schema)

    def write_atomic(self, target_path: Path, record: dict) -> None:
        """
        Writes the validated record to target_path using atomic file replacement.
        Guarantees no partial file updates.
        """
        # Ensure schema compliance first
        self.validate_record(record)
        
        target_path = Path(target_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temporary file in the same directory to guarantee atomic move on most file systems
        temp_path = target_path.with_suffix(f".tmp_{uuid.uuid4().hex}")
        
        try:
            # Serialize to string ensuring LF format
            json_str = json.dumps(record, indent=2, ensure_ascii=False)
            normalized_str = json_str.replace("\r\n", "\n").replace("\r", "\n")
            
            # Atomic write execution
            with open(temp_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(normalized_str)
                f.flush()
                os.fsync(f.fileno())  # Force OS buffer flush to disk
            
            # Atomic replacement
            os.replace(temp_path, target_path)
        
        except Exception as e:
            # Cleanup temp file on failure
            if temp_path.exists():
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise IOError(f"Atomic write failed for {target_path}: {e}") from e