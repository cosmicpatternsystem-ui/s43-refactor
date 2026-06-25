import json
import os
import hashlib

def generate_vault_export(audit_path, export_path):
    if not os.path.exists(audit_path): return
    
    with open(audit_path, 'r') as f:
        data = f.read()
    
    # ایجاد یک امضای دیجیتال برای کل فایل صادراتی
    file_signature = hashlib.sha256(data.encode()).hexdigest()
    
    export_package = {
        "export_id": "VAULT-EXTRACT-2026",
        "integrity_signature": file_signature,
        "raw_data": data.splitlines()
    }
    
    with open(export_path, 'w') as f:
        json.dump(export_package, f, indent=4)
    print(f"IMMUTABLE_EXPORT_CREATED: {export_path}")

generate_vault_export("runtime/audit/decision_audit.jsonl", "runtime/audit/final_vault_report.json")
