import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def run_cmd(*args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)

def test_p34_ledger_record_and_verify():
    import shutil
    ledger_path = Path('artifacts/evidence/ledger')
    if ledger_path.exists(): shutil.rmtree(ledger_path)
    ledger_path.mkdir(parents=True, exist_ok=True)
    # ASO-X Isolation: Ensure ledger is clean before run
    ledger_path = Path("artifacts/evidence/ledger")
    if ledger_path.exists(): shutil.rmtree(ledger_path)
    ledger_path.mkdir(parents=True, exist_ok=True)
    record = run_cmd(sys.executable, "asoctl.py", "evidence", "ledger-record")
    assert record.returncode == 0, record.stdout + record.stderr
    data = json.loads(record.stdout)
    assert data["decision"] == "pass"
    assert data["status"] == "pass"

    ledger_entry = ROOT / data["ledger_entry_path"]
    assert ledger_entry.exists()

    verify = run_cmd(sys.executable, "asoctl.py", "evidence", "ledger-verify")
    assert verify.returncode == 0, verify.stdout + verify.stderr
    v = json.loads(verify.stdout)
    assert v["decision"] == "pass"
    assert v["status"] == "pass"
    assert v["verified_entries"] >= 1

def test_p34_ledger_verify_detects_tamper():
    bootstrap = run_cmd(sys.executable, "asoctl.py", "evidence", "ledger-record")
    assert bootstrap.returncode == 0, bootstrap.stdout + bootstrap.stderr

    ledger_dir = ROOT / "artifacts" / "evidence" / "ledger"
    entries = sorted(fp for fp in ledger_dir.glob("*.json") if fp.stat().st_size > 0)
    assert entries, "no ledger entries present for tamper test"

    target = entries[-1]
    original = target.read_text(encoding="utf-8-sig")
    data = json.loads(original)
    data["subject"] = "tampered-subject"
    target.write_text(
        json.dumps(data, ensure_ascii=True, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    try:
        verify = run_cmd(sys.executable, "asoctl.py", "evidence", "ledger-verify")
        assert verify.returncode == 1, verify.stdout + verify.stderr
        v = json.loads(verify.stdout)
        assert v["decision"] == "fail"
        assert v["status"] == "fail"
    finally:
        target.write_text(original, encoding="utf-8", newline="\n")
