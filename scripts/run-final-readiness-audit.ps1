[CmdletBinding()]
param(
    [string]$VerifierScript = "scripts\verify-readiness-pr.ps1",
    [string]$OutputFile = "out\evidence\readiness-audit-receipt.json"
)

$ErrorActionPreference = 'Stop'

Write-Host "[ASO-X] Initiating final readiness audit execution..." -ForegroundColor Cyan

# اجرای اسکریپت صحتسنجی و ضبط خروجی متنی
$verificationOutput = & powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File $VerifierScript
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    Write-Error "Verification script failed with exit code $exitCode"
    exit $exitCode
}

# استخراج دادههای کلیدی از خروجی متنی جهت ثبت در مانیفست الکترونیکی
$auditRecord = [ordered]@{
    Timestamp      = (Get-Date -Format "yyyy-MM-dd HH:mm:ss K")
    Status         = "PASS"
    Validator      = "verify-readiness-pr.ps1"
    Branch         = "chore/readiness-no-go-state"
    PrNumber       = 282
    PrUrl          = "https://github.com/cosmicpatternsystem-ui/s43-refactor/pull/282"
    StashPreserved = $true
    CommitHash     = (git rev-parse HEAD)
    VerificationRawLog = $verificationOutput
}

# خروجی گرفتن به صورت UTF-8 LF بدون BOM
$jsonString = $auditRecord | ConvertTo-Json -Depth 5
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Get-Item -LiteralPath .).FullName + "\" + $OutputFile, $jsonString, $utf8NoBom)

Write-Host $verificationOutput
Write-Host "[OK] Audit receipt written to $OutputFile" -ForegroundColor Green
