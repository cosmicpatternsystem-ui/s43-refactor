$ErrorActionPreference = "Stop"

function Info($m) { Write-Host "[INFO]  $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "[OK]    $m" -ForegroundColor Green }
function Warn($m) { Write-Host "[WARN]  $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "[FAIL]  $m" -ForegroundColor Red }

function CountLiteral($Text, $Needle) {
    if ([string]::IsNullOrEmpty($Needle)) { return 0 }

    $count = 0
    $pos = 0

    while ($true) {
        $idx = $Text.IndexOf($Needle, $pos, [System.StringComparison]::Ordinal)
        if ($idx -lt 0) { break }

        $count++
        $pos = $idx + $Needle.Length
    }

    return $count
}

function ReplaceLiteralOnce($Text, $Old, $New, $Label) {
    $newCount = CountLiteral $Text $New
    if ($newCount -gt 0) {
        Warn "$Label already patched"
        return $Text
    }

    $oldCount = CountLiteral $Text $Old

    if ($oldCount -eq 0) {
        throw "$($Label)_PATTERN_NOT_FOUND"
    }

    if ($oldCount -gt 1) {
        throw "$($Label)_PATTERN_NOT_UNIQUE_COUNT_$oldCount"
    }

    $idx = $Text.IndexOf($Old, [System.StringComparison]::Ordinal)
    if ($idx -lt 0) {
        throw "$($Label)_INDEX_NOT_FOUND"
    }

    $before = $Text.Substring(0, $idx)
    $after = $Text.Substring($idx + $Old.Length)

    Ok "$Label patched"
    return ($before + $New + $after)
}

$Root = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Get-Location).Path
}

$TargetFile = Join-Path $Root "s43_instrumented_LATEST.py"
$TranslatorFile = Join-Path $Root "translator_module.py"

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = "$TargetFile.bak_TRANSLATOR_PATCH_V3_1_FIXED_$Timestamp"
$TranslatorBackupFile = "$TranslatorFile.bak_TRANSLATOR_PATCH_V3_1_FIXED_$Timestamp"

Info "Root: $Root"
Info "Target: $TargetFile"
Info "Translator: $TranslatorFile"
Info "Backup: $BackupFile"

if (-not (Test-Path -LiteralPath $TargetFile)) {
    throw "TARGET_NOT_FOUND: $TargetFile"
}

Copy-Item -LiteralPath $TargetFile -Destination $BackupFile -Force
Ok "Target backup created"

$TranslatorExisted = Test-Path -LiteralPath $TranslatorFile

if ($TranslatorExisted) {
    Copy-Item -LiteralPath $TranslatorFile -Destination $TranslatorBackupFile -Force
    Ok "Existing translator_module.py backup created"
}
else {
    Info "translator_module.py did not exist before patch"
}

$translatorContent = @'
# -*- coding: utf-8 -*-
"""
translator_module.py

Defensive helper for translating selected API messages.
"""

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

try {
    [System.IO.File]::WriteAllText(
        $TranslatorFile,
        $translatorContent,
        (New-Object System.Text.UTF8Encoding($false))
    )
    Ok "translator_module.py written"

    $content = [System.IO.File]::ReadAllText(
        $TargetFile,
        [System.Text.Encoding]::UTF8
    )

    if ([string]::IsNullOrWhiteSpace($content)) {
        throw "TARGET_FILE_EMPTY"
    }

    # --------------------------------------------------
    # Import injection
    # --------------------------------------------------
    $importNeedle = 'from translator_module import translate_api_message'

    $importBlock = @'
try:
    from translator_module import translate_api_message
except Exception:
    def translate_api_message(message):
        return message
'@

    if ($content.Contains($importNeedle)) {
        Warn "Import block already exists"
    }
    else {
        $anchor = "from __future__ import annotations"

        if (-not $content.Contains($anchor)) {
            throw "IMPORT_ANCHOR_NOT_FOUND"
        }

        $anchorCount = CountLiteral $content $anchor

        if ($anchorCount -ne 1) {
            throw "IMPORT_ANCHOR_NOT_UNIQUE_COUNT_$anchorCount"
        }

        $replacement = $anchor + "`r`n" + $importBlock
        $content = ReplaceLiteralOnce $content $anchor $replacement "IMPORT_BLOCK"
        Ok "Import block inserted"
    }

    # --------------------------------------------------
    # Hook 1
    # --------------------------------------------------
    $hook1Old = '                    s = str(s2)'
    $hook1New = '                    s = str(translate_api_message(s2))'

    $content = ReplaceLiteralOnce $content $hook1Old $hook1New "HOOK1"

    # --------------------------------------------------
    # Hook 2
    # --------------------------------------------------
    $hook2Old = '                    msg = obj.get("msg") or obj.get("message") or obj.get("error") or ""'
    $hook2New = '                    msg = translate_api_message(obj.get("msg") or obj.get("message") or obj.get("error") or "")'

    $content = ReplaceLiteralOnce $content $hook2Old $hook2New "HOOK2"

    # --------------------------------------------------
    # Safety checks
    # --------------------------------------------------
    if (-not $content.Contains('from translator_module import translate_api_message')) {
        throw "VERIFY_IMPORT_MISSING"
    }

    if (-not $content.Contains('s = str(translate_api_message(s2))')) {
        throw "VERIFY_HOOK1_MISSING"
    }

    if (-not $content.Contains('msg = translate_api_message(obj.get("msg") or obj.get("message") or obj.get("error") or "")')) {
        throw "VERIFY_HOOK2_MISSING"
    }

    if (-not $content.Contains('_pp200_redact(str(msg))')) {
        throw "VERIFY_REDACTION_CALL_MISSING"
    }

    Ok "Pre-write safety verification passed"

    [System.IO.File]::WriteAllText(
        $TargetFile,
        $content,
        (New-Object System.Text.UTF8Encoding($false))
    )
    Ok "Patched target written"

    Info "Compiling translator_module.py..."
    & python -m py_compile $TranslatorFile
    if ($LASTEXITCODE -ne 0) {
        throw "PY_COMPILE_TRANSLATOR_FAILED"
    }
    Ok "translator_module.py compile OK"

    Info "Compiling s43_instrumented_LATEST.py..."
    & python -m py_compile $TargetFile
    if ($LASTEXITCODE -ne 0) {
        throw "PY_COMPILE_TARGET_FAILED"
    }
    Ok "s43_instrumented_LATEST.py compile OK"

    Info "Running smoke test..."
    & python -c "from translator_module import translate_api_message; assert translate_api_message('insufficient balance') == 'موجودی کافی نیست'; assert translate_api_message('Network error while calling endpoint') == 'خطای شبکه'; assert translate_api_message('unknown custom message') == 'unknown custom message'; print('SMOKE_TEST_OK')"
    if ($LASTEXITCODE -ne 0) {
        throw "SMOKE_TEST_FAILED"
    }
    Ok "Smoke test passed"

    Ok "PATCH V3.1 FIXED COMPLETED SUCCESSFULLY"

    Write-Host ""
    Write-Host "TARGET_FILE=$TargetFile" -ForegroundColor Gray
    Write-Host "BACKUP_FILE=$BackupFile" -ForegroundColor Gray
    Write-Host "TRANSLATOR_FILE=$TranslatorFile" -ForegroundColor Gray

    if ($TranslatorExisted) {
        Write-Host "TRANSLATOR_BACKUP_FILE=$TranslatorBackupFile" -ForegroundColor Gray
    }
}
catch {
    Fail $_.Exception.Message
    Warn "Rolling back..."

    if (Test-Path -LiteralPath $BackupFile) {
        Copy-Item -LiteralPath $BackupFile -Destination $TargetFile -Force
        Ok "Target rollback completed"
    }
    else {
        Fail "Target backup not found for rollback"
    }

    if ($TranslatorExisted) {
        if (Test-Path -LiteralPath $TranslatorBackupFile) {
            Copy-Item -LiteralPath $TranslatorBackupFile -Destination $TranslatorFile -Force
            Ok "translator_module.py rollback completed"
        }
        else {
            Fail "Translator backup not found for rollback"
        }
    }
    else {
        if (Test-Path -LiteralPath $TranslatorFile) {
            Remove-Item -LiteralPath $TranslatorFile -Force
            Ok "New translator_module.py removed during rollback"
        }
    }

    throw
}
