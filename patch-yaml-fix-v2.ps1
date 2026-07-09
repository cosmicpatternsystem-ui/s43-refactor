#Requires -Version 7.0
$ErrorActionPreference = "Stop"

$target = ".\scripts\update-roadmap.ps1"
$content = Get-Content $target -Raw -Encoding UTF8

# 1) Remove early return; continue to YAML parser
$old1 = @"
    if (-not `$match.Success) {
        return `$defaults
    }

    `$metadata = `$match.Groups[1].Value | ConvertFrom-Json

    foreach (`$key in @("owner", "priority", "depends_on", "acceptance_criteria", "evidence", "last_verified_at")) {
        if (`$metadata.PSObject.Properties.Name -contains `$key) {
            `$defaults[`$key] = `$metadata.`$key
        }
    }
"@

$new1 = @"
    if (`$match.Success) {
        `$metadata = `$match.Groups[1].Value | ConvertFrom-Json
        foreach (`$key in @("owner", "priority", "depends_on", "acceptance_criteria", "evidence", "last_verified_at")) {
            if (`$metadata.PSObject.Properties.Name -contains `$key) {
                `$defaults[`$key] = `$metadata.`$key
            }
        }
    }
"@

if ($content -notlike "*$old1*") {
    Write-Warning "Pattern 1 (early return) not found"
} else {
    $content = $content.Replace($old1, $new1)
    Write-Host "[OK] Removed early return" -ForegroundColor Green
}

# 2) Fix brace structure in quoted-scalar branch
$old2 = @"
            if (`$line -match '^(\w+):\s*"(.+)"`$') {
                # scalar string: owner: "value"
                if (`$currentKey -and `$isAray) {
                `$defaults[`$Matches[1]] = `$Matches[2]
                `$currentKey = `$null
                `$isArray = `$false
            }
"@

$new2 = @"
            if (`$line -match '^(\w+):\s*"(.+)"`$') {
                # scalar string: owner: "value"
                if (`$currentKey -and `$isArray) {
                    `$defaults[`$currentKey] = `$arayBuffer
                `$arrayBuffer = @()
                }
                `$defaults[`$Matches[1] = `$Matches[2]
                `$currentKey = `$null
                `$isArray = `$false
            }
"@

if ($content -notlike "*$old2*") {
    Write-Warning "Pattern 2 (quoted-scalar brace) not found"
} else {
    $content = $content.Replace($old2, $new2)
    Write-Host "[OK] Fixed quoted-scalar branch" -ForegroundColor Green
}

# Write back (BOM-free UTF8 LF)
$content = $content -replace "`r`n", "`n"
[System.IO.File]::WriteAllText((Resolve-Path $target).Path, $content, (New-Object System.Text.UTF8Encoding $false))
Write-Host "[DONE] Patch applied" -ForegroundColor Cyan
