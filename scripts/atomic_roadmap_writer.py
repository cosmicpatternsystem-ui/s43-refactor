#!/usr/bin/env python3
"""Atomic Roadmap Writer — Phase B/D/E/F Durability"""
import json
import os
import shutil
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone

SOURCE_OF_TRUTH = "repository_files_only"
ROADMAP_PATH = Path("docs/governance/ROADMAP_CURRENT.json")
BACKUP_DIR = Path(".roadmap_backups")
JOURNAL_DIR = Path(".roadmap_journal")

def compute_hash(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def atomic_write(path: Path, content: str) -> None:
    temp_path = path.with_suffix(".tmp")
    journal_path = JOURNAL_DIR / f"{int(time.time())}.journal"
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    journal_entry = {
        "action": "write",
        "target": str(path),
        "temp_file": str(temp_path),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "content_hash": compute_hash(content)
    }
    journal_path.write_text(json.dumps(journal_entry, indent=2), encoding="utf-8")
    temp_path.write_text(content, encoding="utf-8")
    actual_hash = compute_hash(temp_path.read_text(encoding="utf-8"))
    if actual_hash != journal_entry["content_hash"]:
        temp_path.unlink()
        raise ValueError("Hash mismatch")
    temp_path.replace(path)
    journal_path.unlink()

def backup_roadmap() -> None:
    if not ROADMAP_PATH.exists():
        return
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"ROADMAP_CURRENT_{timestamp}.json"
    shutil.copy2(ROADMAP_PATH, backup_path)
    backups = sorted(BACKUP_DIR.glob("ROADMAP_CURRENT_*.json"))
    for old_backup in backups[:-30]:
        old_backup.unlink()

def load_roadmap() -> dict:
    if not ROADMAP_PATH.exists():
        raise FileNotFoundError(f"Roadmap not found: {ROADMAP_PATH}")
    data = json.loads(ROADMAP_PATH.read_text(encoding="utf-8"))
    required = ["schema_version", "roadmap_version", "authority", "lifecycle"]
    missing = [f for f in required if f not in data]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
    source = data.get("authority", {}).get("source")
    if source != SOURCE_OF_TRUTH:
        raise ValueError(f"source_of_truth mismatch: expected '{SOURCE_OF_TRUTH}', got '{source}'")
    return data

def save_roadmap(data: dict) -> None:
    data["authority"]["source"] = SOURCE_OF_TRUTH
    if "initiatives" in data:
        for init in data["initiatives"]:
            if "source_of_truth" in init:
                init["source_of_truth"] = SOURCE_OF_TRUTH
    data["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    data["lifecycle"]["last_updated"] = data["updated_at_utc"]
    backup_roadmap()
    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    atomic_write(ROADMAP_PATH, content)
    print(f"✓ Roadmap saved: {ROADMAP_PATH}")
    print(f"  Hash: {compute_hash(content)[:16]}...")
    print(f"  Backups: {len(list(BACKUP_DIR.glob('*.json')))} retained")

def recover_from_journal() -> None:
    if not JOURNAL_DIR.exists():
        return
    journals = sorted(JOURNAL_DIR.glob("*.journal"))
    for j in journals:
        entry = json.loads(j.read_text(encoding="utf-8"))
        temp = Path(entry["temp_file"])
        target = Path(entry["target"])
        if temp.exists():
            content = temp.read_text(encoding="utf-8")
            if compute_hash(content) == entry["content_hash"]:
                temp.replace(target)
                print(f"✓ Recovered: {target}")
            else:
                print(f"✗ Hash mismatch, discarding: {temp}")
                temp.unlink()
        j.unlink()

if __name__ == "__main__":
    recover_from_journal()
    roadmap = load_roadmap()
    print(f"Current source_of_truth: {roadmap['authority']['source']}")
    save_roadmap(roadmap)