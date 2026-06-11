$ErrorActionPreference = "Stop"

function Info($m)  { Write-Host "[INFO]  $m" -ForegroundColor Cyan }
function Ok($m)    { Write-Host "[OK]    $m" -ForegroundColor Green }
function Warn($m)  { Write-Host "[WARN]  $m" -ForegroundColor Yellow }
function Fail($m)  { Write-Host "[FAIL]  $m" -ForegroundColor Red }

$TargetFile = Join-Path (Get-Location) "s43_instrumented_LATEST.py"
$TranslatorFile = Join-Path (Get-Location) "translator_module.py"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = "$TargetFile.bak_TRANSLATOR_PATCH_V3_$Timestamp"

if (-not (Test-Path -LiteralPath $TargetFile)) {
    throw "TARGET_NOT_FOUND: $TargetFile"
}

Info "Target: $TargetFile"
Info "Backup: $BackupFile"

Copy-Item -LiteralPath $TargetFile -Destination $BackupFile -Force
Ok "Backup created"

$translatorContent = @'
# -*- coding: utf-8 -*-

from typing import Optional

_EXACT_TRANSLATIONS = {
    "insufficient balance": "موجودی کافی نیست",
    "invalid address": "آدرس نامعتبر است",
    "network error": "خطای شبکه",
    "timeout": "اتمام زمان درخواست",
    "forbidden": "دسترسی مجاز نیست",
    "unauthorized": "احراز هویت انجام نشده است",
    "too many requests": "تعداد درخواست‌ها بیش از حد مجاز است",
    "internal server error": "خطای داخلی سرور",
    "service unavailable": "سرویس در دسترس نیست",
    "bad request": "درخواست نامعتبر است",
    "not found": "موردی یافت نشد",
}

_PARTIAL_TRANSLATIONS = {
    "insufficient balance": "موجودی کافی نیست",
    "invalid address": "آدرس نامعتبر است",
    "network error": "خطای شبکه",
    "timeout": "اتمام زمان درخواست",
    "forbidden": "دسترسی مجاز نیست",
    "unauthorized": "احراز هویت انجام نشده است",
    "too many requests": "تعداد درخواست‌ها بیش از حد مجاز است",
    "internal server error": "خطای داخلی سرور",
    "service unavailable": "سرویس در دسترس نیست",
    "bad request": "درخواست نامعتبر است",
    "not found": "موردی یافت نشد",
}

def translate_api_message(message: Optional[str]) -> Optional[str]:
    if message is None:
        return None

    original = str(message)
    normalized = original.strip()
    if not normalized:
        return original

    lowered = normalized.lower()

    exact = _EXACT_TRANSLATIONS.get(lowered)
    if exact is not None:
        return exact

    for key, value in _PARTIAL_TRANSLATIONS.items():
        if key in lowered:
            return value

    return original
'@

Set-Content -LiteralPath $TranslatorFile -Value $translatorContent -Encoding UTF8
Ok "translator_module.py written"

try {
    $content = Get-Content -LiteralPath $TargetFile -Raw -Encoding UTF8

    if ([string]::IsNullOrWhiteSpace($content)) {
        throw "TARGET_FILE_EMPTY"
    }

    # --------------------------------------------------
    # Insert import block after: from __future__ import annotations
    # --------------------------------------------------
    $importNeedle = 'from translator_module import translate_api_message'
    $importBlock = @'
try:
    from translator_module import translate_api_message
except Exception:
    def translate_api_message(message):
        return message
'@

    if ($content -match [regex]::Escape($importNeedle)) {
        Warn "Import already exists"
    }
    else {
        $anchor = "from __future__ import annotations"
        if ($content.Contains($anchor)) {
            $replacement = $anchor + "`r`n" + $importBlock
            $content = $content.Replace($anchor, $replacement)
            Ok "Import block inserted"
        }
        else {
            throw "IMPORT_ANCHOR_NOT_FOUND"
        }
    }

    # --------------------------------------------------
    # Hook 1
    # --------------------------------------------------
    $hook1Old = @'
                s2 = obj.get("detail") or obj.get("message") or obj.get("error") or ""
                if s2:
                    s = str(s2)
'@.Trim()

    $hook1New = @'
                s2 = obj.get("detail") or obj.get("message") or obj.get("error") or ""
                if s2:
                    s = str(translate_api_message(s2))
'@.Trim()

    if ($content.Contains($hook1New)) {
        Warn "Hook1 already patched"
    }
    elseif ($content.Contains($hook1Old)) {
        $content = $content.Replace($hook1Old, $hook1New)
        Ok "Hook1 patched"
    }
    else {
        throw "HOOK1_PATTERN_NOT_FOUND"
    }

    # --------------------------------------------------
    # Hook 2
    # --------------------------------------------------
    $hook2Old = '                    msg = obj.get("msg") or obj.get("message") or obj.get("error") or ""'
    $hook2New = '                    msg = translate_api_message(obj.get("msg") or obj.get("message") or obj.get("error") or "")'

    if ($content.Contains($hook2New)) {
        Warn "Hook2 already patched"
    }
    elseif ($content.Contains($hook2Old)) {
        $content = $content.Replace($hook2Old, $hook2New)
        Ok "Hook2 patched"
    }
    else {
        throw "HOOK2_PATTERN_NOT_FOUND"
    }

    if ($content -notmatch '_pp200_redact\(str\(msg\)\)') {
        throw "REDACT_SAFETY_CHECK_FAILED"
    }
    Ok "Redaction safety check passed"

    [System.IO.File]::WriteAllText(
        $TargetFile,
        $content,
        (New-Object System.Text.UTF8Encoding($false))
    )
    Ok "Patched target written"

    & python -m py_compile $TranslatorFile
    if ($LASTEXITCODE -ne 0) {
        throw "PY_COMPILE_TRANSLATOR_FAILED"
    }
    Ok "translator_module.py compile OK"

    & python -m py_compile $TargetFile
    if ($LASTEXITCODE -ne 0) {
        throw "PY_COMPILE_TARGET_FAILED"
    }
    Ok "s43_instrumented_LATEST.py compile OK"

    & python -c "from translator_module import translate_api_message; print(translate_api_message('insufficient balance')); print(translate_api_message('Network error while calling endpoint'))"
    if ($LASTEXITCODE -ne 0) {
        throw "SMOKE_TEST_FAILED"
    }
    Ok "Smoke test passed"

    Ok "PATCH COMPLETED SUCCESSFULLY"
    Write-Host "BACKUP_FILE=$BackupFile" -ForegroundColor Gray
}
catch {
    Fail $_.Exception.Message
    Warn "Rolling back..."
    if (Test-Path -LiteralPath $BackupFile) {
        Copy-Item -LiteralPath $BackupFile -Destination $TargetFile -Force
        Ok "Rollback completed"
    }
    else {
        Fail "Backup not found for rollback"
    }
    throw
}
