# Deployment Verification Guide
## Translator Patch V3.2

### Purpose
This document provides a quick operational checklist to confirm that the translator patch is correctly deployed and remains intact.

---

## Files Expected
- `s43_instrumented_LATEST.py`
- `translator_module.py`
- `VERIFY_TRANSLATOR_PATCH_V3_2.ps1`
- `SHA256SUMS.txt`

---

## Verification Steps

### Step 1: Run verify script
```powershell
powershell -ExecutionPolicy Bypass -File .\VERIFY_TRANSLATOR_PATCH_V3_2.ps1

Expected indicators:
- `IMPORT found`
- `HOOK1 found`
- `HOOK2 found`
- `translator_module.py compile OK`
- `s43_instrumented_LATEST.py compile OK`
- `VERIFY_SMOKE_TEST_OK`
- `VERIFY COMPLETED SUCCESSFULLY`

---

### Step 2: Confirm file hashes
Run:

powershell
Get-FileHash -Algorithm SHA256 .\s43_instrumented_LATEST.py
Get-FileHash -Algorithm SHA256 .\translator_module.py

Expected values:

#### Target
`7011FCE59D2ECDEFA429AE38E398F047539BBA659C732B85ABA63F99D1C77774`

#### Translator
`F00DA199147A23E20D746CA6FA5BCA4E12B93B84F8E1E18625DC610458E3751D`

---

## Functional Expectations
The system should now:
- translate selected known API messages
- preserve original unknown messages
- keep existing redaction behavior intact
- remain syntactically valid

---

## Rollback Reference
If rollback is required, restore these backups:

- `s43_instrumented_LATEST.py.bak_TRANSLATOR_PATCH_V3_2_20260609_233753`
- `translator_module.py.bak_TRANSLATOR_PATCH_V3_2_20260609_233753`

Example:

powershell
Copy-Item .\s43_instrumented_LATEST.py.bak_TRANSLATOR_PATCH_V3_2_20260609_233753 .\s43_instrumented_LATEST.py -Force
Copy-Item .\translator_module.py.bak_TRANSLATOR_PATCH_V3_2_20260609_233753 .\translator_module.py -Force

Then re-run:

powershell
python -m py_compile .\s43_instrumented_LATEST.py
python -m py_compile .\translator_module.py

---

## Release State
Current deployment state: **Verified / Ready**


---

## 2) فایل را به پوشه release اضافه کن

```powershell
copy .\DEPLOYMENT_VERIFY.md .\release_v3_2\
