param()

$ErrorActionPreference = "Stop"

$files = git diff --cached --name-only --diff-filter=ACMR | Where-Object {
    $_ -match '\.(ps1|md|json|yml|yaml|txt)$'
}

if (-not $files) {
    exit 0
}

foreach ($file in $files) {
    if (-not (Test-Path -LiteralPath $file)) {
        continue
    }

    $raw = Get-Content -LiteralPath $file -Raw
    if ($null -eq $raw) {
        continue
    }

    $fixed = $raw -replace '(\r?\n)+\z', "`n"

    if ($fixed -ne $raw) {
        [System.IO.File]::WriteAllText((Resolve-Path -LiteralPath $file), $fixed, [System.Text.UTF8Encoding]::new($false))
        git add -- $file | Out-Null
        Write-Host "Fixed EOF whitespace: $file"
    }
}