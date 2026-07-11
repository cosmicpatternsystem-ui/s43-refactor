$ErrorActionPreference = "Stop"

param(
    [switch]$Push,
    [switch]$OpenPR
)

function Exec-And-Capture {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )

    $escapedArgs = @()
    foreach ($arg in $Arguments) {
        if ($null -eq $arg) {
            $escapedArgs += '""'
        } elseif ($arg -match '[\s"]') {
            $escapedArgs += '"' + ($arg -replace '"', '\"') + '"'
        } else {
            $escapedArgs += $arg
        }
    }

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.Arguments = ($escapedArgs -join ' ')
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    [void]$process.Start()

    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()

    $combined = New-Object System.Collections.Generic.List[string]
    if (-not [string]::IsNullOrWhiteSpace($stdout)) {
        foreach ($line in ($stdout -split "`r?`n")) {
            if ($line -ne "") { [void]$combined.Add($line) }
        }
    }
    if (-not [string]::IsNullOrWhiteSpace($stderr)) {
        foreach ($line in ($stderr -split "`r?`n")) {
            if ($line -ne "") { [void]$combined.Add($line) }
        }
    }

    return @{
        Output = $combined
        ExitCode = $process.ExitCode
    }
}

function Exec-Or-Throw {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )

    $result = Exec-And-Capture -FilePath $FilePath -Arguments $Arguments
    foreach ($line in $result.Output) {
        Write-Host $line
    }

    if ($result.ExitCode -ne 0) {
        throw ("Command failed: {0} {1}" -f $FilePath, ($Arguments -join ' '))
    }

    return $result
}

Write-Host "==> Check current branch" -ForegroundColor Cyan
$branchResult = Exec-Or-Throw "git" @("rev-parse", "--abbrev-ref", "HEAD")
$currentBranch = $branchResult.Output[0]

Write-Host "==> Run governance validation" -ForegroundColor Cyan
python .\asoctl.py validate
if ($LASTEXITCODE -ne 0) {
    throw "governance validation failed"
}

Write-Host ""
Write-Host "==> Stage persistent state files" -ForegroundColor Cyan
$persistFiles = @(
    "out/governance-state.json",
    "out/governance-manifest.json",
    "out/governance-audit.csv"
)
Exec-Or-Throw "git" (@("add", "-f", "--") + $persistFiles)

Write-Host "==> Commit if staged changes exist" -ForegroundColor Cyan
& git diff --cached --quiet --exit-code
$hasStagedChanges = ($LASTEXITCODE -ne 0)

if ($hasStagedChanges) {
    & git commit -m "docs(governance): persist verified repository state"
    if ($LASTEXITCODE -ne 0) {
        throw "git commit failed"
    }
} else {
    Write-Host "No staged changes to commit." -ForegroundColor Yellow
}

if ($Push) {
    Write-Host "==> Push current branch" -ForegroundColor Cyan
    Exec-Or-Throw "git" @("push", "origin", $currentBranch)
}

if ($OpenPR) {
    Write-Host "==> Create/Check PR" -ForegroundColor Cyan
    $prCheck = Exec-And-Capture "gh" @("pr", "view", "--json", "url")
    if ($prCheck.ExitCode -eq 0) {
        Write-Host ("PR already exists: " + ($prCheck.Output -join "`n")) -ForegroundColor Green
    } else {
        & gh pr create --title "Governance State Update" --body "Automated persistence of governance artifacts."
        if ($LASTEXITCODE -ne 0) {
            throw "gh pr create failed"
        }
    }
}