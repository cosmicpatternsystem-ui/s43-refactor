import importlib.util
import json
from pathlib import Path

REPO = Path(r"G:\s43_work\s43_g11_work")
MODULE_PATH = REPO / "src" / "evidence" / "ingest" / "ingestor.py"

spec = importlib.util.spec_from_file_location("ingestor", str(MODULE_PATH))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def test_ingest_evidence_smoke():
    payload = {"data": "test_content"}
    evidence_id = "evidence-2026-001" 
    producer = "engineer-smoke-test"
    subject = "smoke_verification"

    result = mod.ingest_evidence(
        payload=payload,
        evidence_id=evidence_id,
        producer=producer,
        subject=subject
    )

    # اصلاح: استفاده از record_path مطابق خروجی واقعی سیستم
    output_path = result.get("record_path") if isinstance(result, dict) else str(result)
    
    assert output_path, f"Could not extract record_path from result: {result}"
    
    evidence_file = REPO / output_path
    assert evidence_file.exists(), f"Evidence file not found: {evidence_file}"

    data = json.loads(evidence_file.read_text(encoding="utf-8"))

    # اعتبارسنجی نهایی: نبودن فیلد ممنوعه
    assert "redaction_status" not in data, "FAILURE: redaction_status detected in output!"
    
    print(f"\nSUCCESS: Evidence record stored at {output_path}")
    # اگر مایل بودی فایل تست را پاک نکنی این خط را کامنت کن:
    # evidence_file.unlink()