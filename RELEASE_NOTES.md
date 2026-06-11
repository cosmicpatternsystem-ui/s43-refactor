# Release Notes
## Translator Patch V3.2

### Release Date
2026-06-09

### Scope
This release applies a defensive and minimal translator patch to `s43_instrumented_LATEST.py` and introduces `translator_module.py` for selected API message translation.

### Objectives
- Add a safe translation layer for selected API-facing messages
- Preserve existing redaction behavior
- Keep the patch minimal and rollback-safe
- Verify syntax and runtime behavior using compile checks and smoke tests

---

## Delivered Files
- `s43_instrumented_LATEST.py`
- `translator_module.py`
- `AUTO_SAFE_TRANSLATOR_PATCH_V3_2.ps1`
- `VERIFY_TRANSLATOR_PATCH_V3_2.ps1`
- `SHA256SUMS.txt`

---

## Functional Changes

### 1. Defensive import injection
A defensive import block was inserted after:
```python
from __future__ import annotations

Behavior:
- Prefer importing `translate_api_message` from `translator_module`
- Fall back to a no-op translator if import fails

### 2. Hook 1 patch
Changed:

python
s = str(s2)

To:

python
s = str(translate_api_message(s2))

### 3. Hook 2 patch
Changed:

python
msg = _pp200_redact(str(msg))

To:

python
msg = _pp200_redact(str(translate_api_message(msg)))

This preserves the existing redaction chain while enabling translation before redaction output formatting.

---

## Safety Characteristics
- Minimal surface-area patch
- Automatic backup creation
- Automatic rollback on patch failure
- Compile verification for both Python files
- Runtime smoke test verification
- Hash-based artifact verification

---

## Validation Results
The following checks completed successfully:

- Import block detected
- Hook1 detected
- Hook2 detected
- `translator_module.py` compiled successfully
- `s43_instrumented_LATEST.py` compiled successfully
- Translation smoke test passed
- SHA256 hashes generated

---

## Final SHA256
- `s43_instrumented_LATEST.py`
  - `7011FCE59D2ECDEFA429AE38E398F047539BBA659C732B85ABA63F99D1C77774`

- `translator_module.py`
  - `F00DA199147A23E20D746CA6FA5BCA4E12B93B84F8E1E18625DC610458E3751D`

---

## Backup Artifacts
- `s43_instrumented_LATEST.py.bak_TRANSLATOR_PATCH_V3_2_20260609_233753`
- `translator_module.py.bak_TRANSLATOR_PATCH_V3_2_20260609_233753`

---

## Operational Status
Release status: **SUCCESSFUL**

Patch status:
- Applied
- Verified
- Compile-safe
- Smoke-tested
- Rollback-capable

---

## Recommended Retention
Keep the following files together:

- patched target file
- translator module
- patch script
- verify script
- both backup files
- SHA256 manifest
- this release note

---

## Notes
If future upstream changes alter the exact hook lines, patch anchors must be revalidated before reapplying this release logic.


---

# 3) فایل `DEPLOYMENT_VERIFY.md`

فایل زیر را بساز:

```powershell
notepad .\DEPLOYMENT_VERIFY.md
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

# 4) پیشنهاد ساخت پوشه release

برای نظم بهتر، این ساختار را پیشنهاد می‌کنم:

```powershell
mkdir .\release_v3_2
copy .\s43_instrumented_LATEST.py .\release_v3_2\
copy .\translator_module.py .\release_v3_2\
copy .\AUTO_SAFE_TRANSLATOR_PATCH_V3_2.ps1 .\release_v3_2\
copy .\VERIFY_TRANSLATOR_PATCH_V3_2.ps1 .\release_v3_2\
copy .\SHA256SUMS.txt .\release_v3_2\
copy .\RELEASE_NOTES.md .\release_v3_2\
copy .\DEPLOYMENT_VERIFY.md .\release_v3_2\
