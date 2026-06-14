param(
    [string]$ExpectedBranch = "phase17-work-from-restore",
    [string]$Mode = "AutoSnapshot"
)

$ErrorActionPreference = "Continue"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$ReportPath = Join-Path $RepoRoot "QUALITY_GATE_LAST_REPORT.md"
$StartedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$Failures = New-Object System.Collections.Generic.List[string]
$Warnings = New-Object System.Collections.Generic.List[string]

function Add-Failure {
    param([string]$Message)
    $Failures.Add($Message) | Out-Null
}

function Add-Warning {
    param([string]$Message)
    $Warnings.Add($Message) | Out-Null
}

function Write-Report {
    $endedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $lines = @()
    $lines += "# Phase 17 Quality Gate Last Report"
    $lines += ""
    $lines += "- Started: $StartedAt"
    $lines += "- Finished: $endedAt"
    $lines += "- Mode: $Mode"
    $lines += "- Expected branch: $ExpectedBranch"
    $lines += "- Result: " + $(if ($Failures.Count -eq 0) { "PASS" } else { "FAIL" })
    $lines += ""
    $lines += "## Failures"
    if ($Failures.Count -eq 0) {
        $lines += "- None"
    }
    else {
        foreach ($f in $Failures) { $lines += "- $f" }
    }
    $lines += ""
    $lines += "## Warnings"
    if ($Warnings.Count -eq 0) {
        $lines += "- None"
    }
    else {
        foreach ($w in $Warnings) { $lines += "- $w" }
    }
    Set-Content -Path $ReportPath -Value ($lines -join [Environment]::NewLine) -Encoding UTF8
}

function Test-CommandAvailable {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return ($null -ne (Get-Command $Command -ErrorAction SilentlyContinue))
}

function Get-PythonCommand {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { return @("py", "-3") }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) { return @("python") }

    return @()
}

function Get-ChangedFiles {
    $raw = git status --porcelain --untracked-files=all
    $files = New-Object System.Collections.Generic.List[string]

    foreach ($line in $raw) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }

        $path = $line.Substring(3).Trim()
        if ($path -match " -> ") {
            $path = ($path -split " -> ")[-1].Trim()
        }

        if (-not [string]::IsNullOrWhiteSpace($path)) {
            $files.Add($path) | Out-Null
        }
    }

    return $files
}

function Test-TextFileCandidate {
    param([string]$Path)

    if (-not (Test-Path $Path -PathType Leaf)) { return $false }

    try {
        $item = Get-Item $Path
        if ($item.Length -gt 5242880) { return $false }
    }
    catch {
        return $false
    }

    $binaryExtensions = @(
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".pdf", ".zip", ".rar",
        ".7z", ".exe", ".dll", ".pyd", ".so", ".db", ".sqlite", ".mp3", ".mp4",
        ".wav", ".avi", ".mov", ".webp"
    )

    $ext = [System.IO.Path]::GetExtension($Path).ToLowerInvariant()
    if ($binaryExtensions -contains $ext) { return $false }

    return $true
}

function Read-FileText {
    param([string]$Path)

    try {
        return Get-Content -Raw -Path $Path -Encoding UTF8 -ErrorAction Stop
    }
    catch {
        try {
            return Get-Content -Raw -Path $Path -ErrorAction Stop
        }
        catch {
            Add-Warning "Could not read text file: $Path"
            return $null
        }
    }
}

function Test-ForbiddenRuntimeFiles {
    param([System.Collections.Generic.List[string]]$Files)

    $forbiddenExact = @(
        "AUTO_SNAPSHOT_LOG.md",
        "AUTO_SNAPSHOT_SECURITY_BLOCK.md",
        ".auto_snapshot.lock",
        "QUALITY_GATE_LAST_REPORT.md",
        "AUTO_SNAPSHOT_LAST_STATUS.json"
    )

    foreach ($file in $Files) {
        $normalized = $file -replace "\\", "/"

        if ($forbiddenExact -contains $file) {
            Add-Failure "Runtime artifact must not be committed: $file"
        }

        if ($normalized -match "(^|/)__pycache__/") {
            Add-Failure "Python cache artifact must not be committed: $file"
        }

        if ($normalized -match "\.pyc$|\.tmp$|\.temp$|\.bak$|\.swp$") {
            Add-Failure "Temporary/generated artifact must not be committed: $file"
        }
    }
}

function Test-ConflictMarkers {
    param([System.Collections.Generic.List[string]]$Files)

    foreach ($file in $Files) {
        if (-not (Test-TextFileCandidate $file)) { continue }

        $content = Read-FileText $file
        if ($null -eq $content) { continue }

        if ($content -match "(?m)^(<<<<<<<|=======|>>>>>>>)") {
            Add-Failure "Merge conflict marker detected in: $file"
        }
    }
}

function Test-SecretRisk {
    param([System.Collections.Generic.List[string]]$Files)

    $rules = @(
        @{ Name = "AWS access key"; Pattern = "AKIA[0-9A-Z]{16}"; CaseInsensitive = $false },
        @{ Name = "AWS temporary access key"; Pattern = "ASIA[0-9A-Z]{16}"; CaseInsensitive = $false },
        @{ Name = "GitHub token"; Pattern = "gh[pousr]_[A-Za-z0-9_]{36,255}"; CaseInsensitive = $false },
        @{ Name = "GitHub fine-grained token"; Pattern = "github_pat_[A-Za-z0-9_]{20,255}"; CaseInsensitive = $false },
        @{ Name = "Slack token"; Pattern = "xox[baprs]-[A-Za-z0-9-]{10,}"; CaseInsensitive = $false },
        @{ Name = "OpenAI-style API key"; Pattern = "sk-[A-Za-z0-9]{20,}"; CaseInsensitive = $false },
        @{ Name = "Private key block"; Pattern = "-----BEGIN (RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"; CaseInsensitive = $false },
        @{ Name = "Generic password assignment"; Pattern = "(password|passwd|pwd)\s*[:=]\s*['""][^'""]{8,}['""]"; CaseInsensitive = $true },
        @{ Name = "Generic token/secret assignment"; Pattern = "(token|secret|api_key|apikey)\s*[:=]\s*['""][^'""]{12,}['""]"; CaseInsensitive = $true }
    )

    foreach ($file in $Files) {
        if (-not (Test-TextFileCandidate $file)) { continue }

        $content = Read-FileText $file
        if ($null -eq $content) { continue }

        foreach ($rule in $rules) {
            $options = [System.Text.RegularExpressions.RegexOptions]::Multiline
            if ($rule.CaseInsensitive) {
                $options = $options -bor [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
            }

            if ([regex]::IsMatch($content, $rule.Pattern, $options)) {
                Add-Failure "Possible secret detected: $($rule.Name) in $file"
            }
        }
    }
}

function Invoke-ExternalCheck {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$ArgumentList
    )

    $output = & $FilePath @ArgumentList 2>&1
    $exit = $LASTEXITCODE

    if ($exit -ne 0) {
        Add-Failure "$Name failed with exit code $exit. Output: $($output -join ' | ')"
    }
}

try {
    git --version *> $null
    if ($LASTEXITCODE -ne 0) {
        Add-Failure "git is not available."
    }

    $branch = (git branch --show-current).Trim()
    if ($branch -ne $ExpectedBranch) {
        Add-Failure "Wrong branch: '$branch'. Expected '$ExpectedBranch'."
    }

    git remote get-url origin *> $null
    if ($LASTEXITCODE -ne 0) {
        Add-Failure "origin remote is not configured."
    }

    if (Test-Path ".git\MERGE_HEAD") {
        Add-Failure "Repository is in a merge state."
    }

    if ((Test-Path ".git\rebase-merge") -or (Test-Path ".git\rebase-apply")) {
        Add-Failure "Repository is in a rebase state."
    }

    git diff --check *> $null
    if ($LASTEXITCODE -ne 0) {
        Add-Failure "git diff --check failed. Whitespace or conflict-marker style issue may exist."
    }

    $changedFiles = Get-ChangedFiles
    Test-ForbiddenRuntimeFiles -Files $changedFiles
    Test-ConflictMarkers -Files $changedFiles
    Test-SecretRisk -Files $changedFiles

    $pythonCommand = Get-PythonCommand
    if ($pythonCommand.Count -eq 0) {
        Add-Failure "Python is not available, cannot run syntax/governance checks."
    }
    else {
        $pythonExe = $pythonCommand[0]
        $pythonPrefixArgs = @()
        if ($pythonCommand.Count -gt 1) {
            $pythonPrefixArgs = $pythonCommand[1..($pythonCommand.Count - 1)]
        }

        if (Test-Path ".\s43.py") {
            Invoke-ExternalCheck -Name "Python syntax check for s43.py" -FilePath $pythonExe -ArgumentList ($pythonPrefixArgs + @("-m", "py_compile", "s43.py"))
        }
        else {
            Add-Failure "s43.py not found."
        }

        if (Test-Path ".\governance_audit.py") {
            Invoke-ExternalCheck -Name "governance_audit.py" -FilePath $pythonExe -ArgumentList ($pythonPrefixArgs + @("governance_audit.py"))
        }
        else {
            Add-Warning "governance_audit.py not found; governance audit skipped."
        }
    }
}
catch {
    Add-Failure "Unexpected quality gate exception: $($_.Exception.Message)"
}
finally {
    Write-Report
}

if ($Failures.Count -eq 0) {
    Write-Host "QUALITY_GATE_PASS"
    exit 0
}
else {
    Write-Host "QUALITY_GATE_FAIL"
    foreach ($f in $Failures) {
        Write-Host "- $f"
    }
    exit 1
}

