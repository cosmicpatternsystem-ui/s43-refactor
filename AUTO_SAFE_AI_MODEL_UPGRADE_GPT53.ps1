$ErrorActionPreference = "Stop"

$NewModel = "gpt-5.3-chat-latest"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$Root = Get-Location
$MainConfig = Join-Path $Root "11029.py"
$TargetFile = Join-Path $Root "s43_instrumented_LATEST.py"
$ReleaseDir = Join-Path $Root "release_v3_2"
$ReleaseZip = Join-Path $Root "release_v3_2.zip"
$ZipHashFile = Join-Path $Root "release_v3_2.zip.sha256.txt"

Write-Host "=== AI MODEL UPGRADE PATCH START ===" -ForegroundColor Cyan
Write-Host "Target model: $NewModel"
Write-Host "Working dir : $Root"

function Assert-FileExists {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        throw "Required file not found: $Path"
    }
}

function Backup-File {
    param([string]$Path)
    Assert-FileExists $Path
    $BackupPath = "$Path.bak_AI_MODEL_GPT53_$Stamp"
    Copy-Item $Path $BackupPath -Force
    Write-Host "Backup created: $BackupPath" -ForegroundColor Green
    return $BackupPath
}

function Read-TextUtf8 {
    param([string]$Path)
    return [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
}

function Write-TextUtf8 {
    param([string]$Path, [string]$Text)
    [System.IO.File]::WriteAllText($Path, $Text, [System.Text.Encoding]::UTF8)
}

function Patch-11029 {
    param([string]$Path)

    Write-Host ""
    Write-Host "Patching 11029.py..." -ForegroundColor Cyan

    $Text = Read-TextUtf8 $Path
    $Original = $Text

    $Pattern = 'DEFAULT_AI_MODEL\s*:\s*str\s*=\s*["''][^"'']+["'']'
    $Replacement = 'DEFAULT_AI_MODEL: str = "' + $NewModel + '"'

    if ($Text -notmatch $Pattern) {
        throw "DEFAULT_AI_MODEL pattern not found in $Path"
    }

    $Text = [regex]::Replace($Text, $Pattern, $Replacement, 1)

    if ($Text -eq $Original) {
        throw "No change applied to $Path"
    }

    Write-TextUtf8 $Path $Text
    Write-Host "Updated DEFAULT_AI_MODEL -> $NewModel" -ForegroundColor Green
}

function Patch-S43Fallback {
    param([string]$Path)

    Write-Host ""
    Write-Host "Patching s43 fallback model..." -ForegroundColor Cyan

    $Text = Read-TextUtf8 $Path
    $Original = $Text

    $Pattern = 'model_name\s*=\s*obj\.get\("model"\)\s*or\s*["''][^"'']+["'']'
    $Replacement = 'model_name = obj.get("model") or "' + $NewModel + '"'

    if ($Text -match $Pattern) {
        $Text = [regex]::Replace($Text, $Pattern, $Replacement, 1)
        Write-Host "Updated fallback model_name -> $NewModel" -ForegroundColor Green
    }
    else {
        Write-Host "Fallback pattern not found in $Path; skipping this hook." -ForegroundColor Yellow
    }

    if ($Text -ne $Original) {
        Write-TextUtf8 $Path $Text
    }
}

function Verify-ModelPatch {
    param([string]$ConfigPath, [string]$TargetPath)

    Write-Host ""
    Write-Host "Verifying model patch..." -ForegroundColor Cyan

    $ConfigText = Read-TextUtf8 $ConfigPath
    $TargetText = Read-TextUtf8 $TargetPath

    $ConfigPattern = 'DEFAULT_AI_MODEL\s*:\s*str\s*=\s*["'']' + [regex]::Escape($NewModel) + '["'']'
    $FallbackAny = 'model_name\s*=\s*obj\.get\("model"\)\s*or\s*["'']'
    $FallbackExpected = 'model_name\s*=\s*obj\.get\("model"\)\s*or\s*["'']' + [regex]::Escape($NewModel) + '["'']'

    if ($ConfigText -notmatch $ConfigPattern) {
        throw "Verification failed: DEFAULT_AI_MODEL is not set to $NewModel"
    }

    if (($TargetText -match $FallbackAny) -and ($TargetText -notmatch $FallbackExpected)) {
        throw "Verification failed: fallback model_name exists but is not set to $NewModel"
    }

    Write-Host "VERIFY_MODEL_PATCH_OK" -ForegroundColor Green
}

function Compile-Python {
    param([string]$Path)

    Write-Host "Compiling: $Path"
    python -m py_compile $Path

    if ($LASTEXITCODE -ne 0) {
        throw "Python compile failed: $Path"
    }

    Write-Host "Compile OK: $Path" -ForegroundColor Green
}

function Update-ReleaseDocs {
    param([string]$ReleasePath)

    if (-not (Test-Path $ReleasePath)) {
        Write-Host ""
        Write-Host "Release folder not found; skipping release sync." -ForegroundColor Yellow
        return
    }

    Write-Host ""
    Write-Host "Syncing release folder..." -ForegroundColor Cyan

    Copy-Item $MainConfig $ReleasePath -Force
    Copy-Item $TargetFile $ReleasePath -Force

    $NotePath = Join-Path $ReleasePath "AI_MODEL_UPGRADE_GPT53.md"

    $DocLines = @(
        "# AI Model Upgrade",
        "",
        "Status: Applied safely.",
        "New Model: $NewModel",
        "Timestamp: $Stamp",
        "",
        "Files Updated:",
        "- 11029.py",
        "- s43_instrumented_LATEST.py",
        "",
        "Purpose:",
        "Upgrade default OpenAI-compatible chat model to $NewModel.",
        "",
        "Verification:",
        "python -m py_compile .\11029.py",
        "python -m py_compile .\s43_instrumented_LATEST.py",
        "",
        "Compatibility Note:",
        "This model name must be supported by the configured API provider and SDK.",
        "If the provider rejects the model name, rollback using the generated backups."
    )

    $Doc = $DocLines -join [Environment]::NewLine
    Write-TextUtf8 $NotePath $Doc
    Write-Host "Release doc added: $NotePath" -ForegroundColor Green

    $HashPath = Join-Path $ReleasePath "SHA256SUMS_AI_MODEL_GPT53.txt"
    Get-FileHash -Algorithm SHA256 $MainConfig, $TargetFile | Format-List | Out-File $HashPath -Encoding UTF8
    Write-Host "Release hash file added: $HashPath" -ForegroundColor Green
}

function Rebuild-ReleaseZip {
    if (-not (Test-Path $ReleaseDir)) {
        return
    }

    Write-Host ""
    Write-Host "Rebuilding release ZIP..." -ForegroundColor Cyan

    Compress-Archive -Path (Join-Path $ReleaseDir "*") -DestinationPath $ReleaseZip -Force
    Get-FileHash -Algorithm SHA256 $ReleaseZip | Format-List | Out-File $ZipHashFile -Encoding UTF8

    $ZipHash = (Get-FileHash -Algorithm SHA256 $ReleaseZip).Hash

    Write-Host "Release ZIP rebuilt: $ReleaseZip" -ForegroundColor Green
    Write-Host "Release ZIP SHA256: $ZipHash" -ForegroundColor Green
}

try {
    Assert-FileExists $MainConfig
    Assert-FileExists $TargetFile

    $Backup11029 = Backup-File $MainConfig
    $BackupS43 = Backup-File $TargetFile

    Patch-11029 $MainConfig
    Patch-S43Fallback $TargetFile

    Verify-ModelPatch $MainConfig $TargetFile

    Write-Host ""
    Write-Host "Running compile tests..." -ForegroundColor Cyan
    Compile-Python $MainConfig
    Compile-Python $TargetFile

    Update-ReleaseDocs $ReleaseDir
    Rebuild-ReleaseZip

    Write-Host ""
    Write-Host "=== AI MODEL UPGRADE PATCH COMPLETED SUCCESSFULLY ===" -ForegroundColor Green
    Write-Host "New model: $NewModel"
    Write-Host "Backup 11029: $Backup11029"
    Write-Host "Backup S43  : $BackupS43"
}
catch {
    Write-Host ""
    Write-Host "=== PATCH FAILED ===" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
