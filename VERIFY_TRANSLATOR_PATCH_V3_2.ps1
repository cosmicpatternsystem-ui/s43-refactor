$ErrorActionPreference = "Stop"

function Info($m) { Write-Host "[INFO]  $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "[OK]    $m" -ForegroundColor Green }
function Warn($m) { Write-Host "[WARN]  $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "[FAIL]  $m" -ForegroundColor Red }

$Root = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = (Get-Location).Path
}

$TargetFile = Join-Path $Root "s43_instrumented_LATEST.py"
$TranslatorFile = Join-Path $Root "translator_module.py"

Info "Root: $Root"
Info "Target: $TargetFile"
Info "Translator: $TranslatorFile"

if (-not (Test-Path -LiteralPath $TargetFile)) {
    throw "TARGET_NOT_FOUND: $TargetFile"
}

if (-not (Test-Path -LiteralPath $TranslatorFile)) {
    throw "TRANSLATOR_NOT_FOUND: $TranslatorFile"
}

$content = [System.IO.File]::ReadAllText($TargetFile, [System.Text.Encoding]::UTF8)
if ([string]::IsNullOrWhiteSpace($content)) {
    throw "TARGET_FILE_EMPTY"
}

$checks = @(
    @{
        Name = "IMPORT"
        Needle = "from translator_module import translate_api_message"
    },
    @{
        Name = "HOOK1"
        Needle = "s = str(translate_api_message(s2))"
    },
    @{
        Name = "HOOK2"
        Needle = "msg = _pp200_redact(str(translate_api_message(msg)))"
    }
)

foreach ($check in $checks) {
    if ($content.Contains($check.Needle)) {
        Ok "$($check.Name) found"
    }
    else {
        throw "$($check.Name)_MISSING"
    }
}

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

Info "Running translation smoke test..."
& python -c "from translator_module import translate_api_message; assert translate_api_message('insufficient balance') == 'موجودی کافی نیست'; assert translate_api_message('Network error while calling endpoint') == 'خطای شبکه'; assert translate_api_message('unknown custom message') == 'unknown custom message'; print('VERIFY_SMOKE_TEST_OK')"
if ($LASTEXITCODE -ne 0) {
    throw "VERIFY_SMOKE_TEST_FAILED"
}
Ok "Smoke test passed"

Info "Calculating SHA256..."
$targetHash = Get-FileHash -Algorithm SHA256 -LiteralPath $TargetFile
$translatorHash = Get-FileHash -Algorithm SHA256 -LiteralPath $TranslatorFile

Ok "VERIFY COMPLETED SUCCESSFULLY"
Write-Host ""
Write-Host "TARGET_SHA256=$($targetHash.Hash)" -ForegroundColor Gray
Write-Host "TRANSLATOR_SHA256=$($translatorHash.Hash)" -ForegroundColor Gray
