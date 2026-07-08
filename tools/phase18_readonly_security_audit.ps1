[CmdletBinding()]
param(
    [string]$ExpectedBranch = "phase17-work-from-restore"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $RepoRoot

$CurrentBranch = (git branch --show-current).Trim()
if ($CurrentBranch -ne $ExpectedBranch) {
    throw "Invalid branch: $CurrentBranch"
}

git fetch origin $ExpectedBranch | Out-Null

$Head = (git rev-parse HEAD).Trim()
$Origin = (git rev-parse "origin/$ExpectedBranch").Trim()
if ($Head -ne $Origin) {
    throw "HEAD and origin differ. HEAD=$Head ORIGIN=$Origin"
}

$Status = @(git status --short)
if ($Status.Count -gt 0) {
    throw ("Working tree is not clean before read-only security audit: " + ($Status -join " | "))
}

$Patterns = @(
    @{ Name = "GenericPrivateKey"; Regex = "-----BEGIN (RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----" },
    @{ Name = "AwsAccessKeyId"; Regex = "AKIA[0-9A-Z]{16}" },
    @{ Name = "GithubToken"; Regex = "gh[pousr]_[A-Za-z0-9_]{20,}" },
    @{ Name = "SlackToken"; Regex = "xox[baprs]-[A-Za-z0-9-]{10,}" },
    @{ Name = "JwtToken"; Regex = "eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}" },
    @{ Name = "PasswordAssignment"; Regex = "(?i)(password|passwd|pwd)\s*[:=]\s*['""][^'""]{6,}['""]" },
    @{ Name = "SecretAssignment"; Regex = "(?i)(secret|token|api[_-]?key|client[_-]?secret)\s*[:=]\s*['""][^'""]{8,}['""]" },
    @{ Name = "EnvFileTracked"; Regex = "(^|/)\.env(\.|$|/)" },
    @{ Name = "CertificateOrKeyFile"; Regex = "\.(pem|p12|pfx|key|crt|cer)$" }
)

$TrackedFiles = @(git ls-files)
$Findings = New-Object System.Collections.Generic.List[object]

foreach ($File in $TrackedFiles) {
    foreach ($Pattern in $Patterns) {
        if ($Pattern.Name -eq "EnvFileTracked" -or $Pattern.Name -eq "CertificateOrKeyFile") {
            if ($File -match $Pattern.Regex) {
                $Findings.Add([pscustomobject]@{
                    Pattern = $Pattern.Name
                    File = $File
                    Line = 0
                    Detail = "Tracked sensitive file path pattern"
                })
            }
            continue
        }

        $Matches = @(Select-String -LiteralPath $File -Pattern $Pattern.Regex -AllMatches -ErrorAction SilentlyContinue)
        foreach ($Match in $Matches) {
            $Findings.Add([pscustomobject]@{
                Pattern = $Pattern.Name
                File = $File
                Line = $Match.LineNumber
                Detail = "Potential sensitive value pattern detected; value intentionally redacted"
            })
        }
    }
}

$ByPattern = $Findings | Group-Object Pattern | Sort-Object Name

Write-Host "PHASE18_READONLY_SECURITY_AUDIT_COMPLETE"
Write-Host "BRANCH=$CurrentBranch"
Write-Host "HEAD=$Head"
Write-Host "ORIGIN=$Origin"
Write-Host "TRACKED_FILES_SCANNED=$($TrackedFiles.Count)"
Write-Host "FINDINGS_TOTAL=$($Findings.Count)"

foreach ($Group in $ByPattern) {
    Write-Host ("FINDING_GROUP={0} COUNT={1}" -f $Group.Name, $Group.Count)
}

if ($Findings.Count -gt 0) {
    Write-Host "FINDINGS_REDACTED_LIST_BEGIN"
    foreach ($Finding in ($Findings | Sort-Object Pattern, File, Line)) {
        Write-Host ("{0} | {1}:{2} | {3}" -f $Finding.Pattern, $Finding.File, $Finding.Line, $Finding.Detail)
    }
    Write-Host "FINDINGS_REDACTED_LIST_END"
}

Write-Host "AUDIT_MODE=READ_ONLY"
Write-Host "SECRET_VALUES_PRINTED=NO"
