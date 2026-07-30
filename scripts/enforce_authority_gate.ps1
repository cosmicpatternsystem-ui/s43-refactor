[CmdletBinding()]
param(
    [string]$RepoRoot = ".",
    [string]$WaiverFile = "governance/authority_waivers.json",
    [string]$ArtifactPolicyFile = "governance/artifact_policy.json",
    [string]$AuthorityProofScript = "scripts/run_authority_proof.ps1",
    [string]$AuthorityProofSummary = "artifacts/authority-proof/summary.json",
    [switch]$SkipArtifactPolicy,
    [switch]$EmitJsonOnly
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

function Write-Log {
    param(
        [ValidateSet("INFO","WARN","ERROR")]
        [string]$Level,
        [string]$Message
    )
    $timestamp = (Get-Date).ToString("s")
    if (-not $EmitJsonOnly) {
        Write-Host ("[{0}][{1}] {2}" -f $timestamp, $Level, $Message)
    }
}

function New-Result {
    return [ordered]@{
        gate                  = "authority-proof"
        status                = "UNKNOWN"
        decision              = "UNDECIDED"
        exit_code             = 99
        timestamp_utc         = [DateTime]::UtcNow.ToString("o")
        repo_root             = $null
        waiver_check          = [ordered]@{
            status            = "UNKNOWN"
            active_waivers    = @()
            expired_waivers   = @()
            blocking_waivers  = @()
        }
        proof_check           = [ordered]@{
            status            = "UNKNOWN"
            exit_code         = $null
            summary_path      = $null
            proof_result      = $null
        }
        artifact_policy_check = [ordered]@{
            status             = "SKIPPED"
            missing_required   = @()
            disallowed_present = @()
            tracked_files_scan = @()
        }
        failures              = @()
    }
}

function Add-Failure {
    param(
        [hashtable]$Result,
        [string]$Code,
        [string]$Message
    )
    $Result.failures += [ordered]@{
        code    = $Code
        message = $Message
    }
}

function Resolve-FullPathSafe {
    param(
        [string]$Base,
        [string]$Relative
    )
    $combined = Join-Path $Base $Relative
    return [System.IO.Path]::GetFullPath($combined)
}

function Load-JsonFile {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "JSON file not found: $Path"
    }

    $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    if ([string]::IsNullOrWhiteSpace($raw)) {
        throw "JSON file is empty: $Path"
    }

    return ($raw | ConvertFrom-Json)
}

function Test-Waivers {
    param(
        [string]$FullWaiverPath,
        [hashtable]$Result
    )

    $Result.waiver_check.status = "PASS"

    $doc = Load-JsonFile -Path $FullWaiverPath
    if ($null -eq $doc.waivers) {
        Add-Failure -Result $Result -Code "CONTRACT_MISMATCH" -Message "Waiver file does not contain waivers."
        $Result.waiver_check.status = "FAIL"
        return
    }

    $today = (Get-Date).Date

    foreach ($w in $doc.waivers) {
        if ($null -eq $w.id -or $null -eq $w.scope -or $null -eq $w.status -or $null -eq $w.expires_on) {
            Add-Failure -Result $Result -Code "CONTRACT_MISMATCH" -Message "Waiver entry missing required fields."
            $Result.waiver_check.status = "FAIL"
            continue
        }

        if ([string]$w.status -ne "active") {
            continue
        }

        $waiverInfo = [ordered]@{
            id               = [string]$w.id
            scope            = [string]$w.scope
            expires_on       = [string]$w.expires_on
            action_on_expiry = [string]$w.action_on_expiry
        }

        $Result.waiver_check.active_waivers += $waiverInfo

        try {
            $expiryDate = ([datetime]::ParseExact([string]$w.expires_on, "yyyy-MM-dd", [System.Globalization.CultureInfo]::InvariantCulture)).Date
        }
        catch {
            Add-Failure -Result $Result -Code "CONTRACT_MISMATCH" -Message ("Invalid waiver expiry date format for waiver {0}." -f [string]$w.id)
            $Result.waiver_check.status = "FAIL"
            continue
        }

        if ($expiryDate -lt $today) {
            $Result.waiver_check.expired_waivers += $waiverInfo

            if ([string]$w.action_on_expiry -eq "block") {
                $Result.waiver_check.blocking_waivers += $waiverInfo
                Add-Failure -Result $Result -Code "EXPIRED_WAIVER" -Message ("Waiver {0} is expired and configured to block." -f [string]$w.id)
                $Result.waiver_check.status = "FAIL"
            }
        }
    }
}

function Invoke-AuthorityProof {
    param(
        [string]$RepoRootFull,
        [string]$AuthorityProofScriptPath,
        [string]$AuthorityProofSummaryPath,
        [hashtable]$Result
    )

    if (-not (Test-Path -LiteralPath $AuthorityProofScriptPath)) {
        Add-Failure -Result $Result -Code "INSUFFICIENT_DATA" -Message ("Authority proof script not found: {0}" -f $AuthorityProofScriptPath)
        $Result.proof_check.status = "FAIL"
        return
    }

    $proofExit = $null

    Push-Location $RepoRootFull
    try {
        Write-Log -Level INFO -Message "Running authority proof script."
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $AuthorityProofScriptPath
        $proofExit = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }

    $Result.proof_check.exit_code = $proofExit
    $Result.proof_check.summary_path = $AuthorityProofSummaryPath

    if ($proofExit -ne 0) {
        Add-Failure -Result $Result -Code "CONTROLLED_BLOCK" -Message ("Authority proof returned non-zero exit code: {0}" -f $proofExit)
        $Result.proof_check.status = "FAIL"
        return
    }

    if (-not (Test-Path -LiteralPath $AuthorityProofSummaryPath)) {
        Add-Failure -Result $Result -Code "INSUFFICIENT_DATA" -Message ("Authority proof summary not found: {0}" -f $AuthorityProofSummaryPath)
        $Result.proof_check.status = "FAIL"
        return
    }

    try {
        $summary = Load-JsonFile -Path $AuthorityProofSummaryPath
    }
    catch {
        Add-Failure -Result $Result -Code "CONTRACT_MISMATCH" -Message "Authority proof summary is unreadable or invalid JSON."
        $Result.proof_check.status = "FAIL"
        return
    }

    if ($null -eq $summary.status) {
        Add-Failure -Result $Result -Code "CONTRACT_MISMATCH" -Message "Authority proof summary does not contain status."
        $Result.proof_check.status = "FAIL"
        return
    }

    $Result.proof_check.proof_result = [string]$summary.status

    if ([string]$summary.status -ne "PASS") {
        Add-Failure -Result $Result -Code "CONTROLLED_BLOCK" -Message ("Authority proof summary status is {0}, expected PASS." -f [string]$summary.status)
        $Result.proof_check.status = "FAIL"
        return
    }

    $Result.proof_check.status = "PASS"
}

function Convert-GlobToRegex {
    param([string]$Pattern)

    $escaped = [Regex]::Escape($Pattern)
    $escaped = $escaped.Replace("\*", ".*")
    $escaped = $escaped.Replace("\?", ".")
    return ("^" + $escaped + "$")
}

function Get-GitTrackedFiles {
    param([string]$RepoRootFull)

    $gitCmd = Get-Command git -ErrorAction SilentlyContinue
    if ($null -eq $gitCmd) {
        throw "git executable not found in PATH."
    }

    $output = & git -C $RepoRootFull ls-files
    if ($LASTEXITCODE -ne 0) {
        throw "git ls-files failed."
    }

    $files = @()
    foreach ($line in $output) {
        if (-not [string]::IsNullOrWhiteSpace($line)) {
            $normalized = ([string]$line).Trim() -replace '\\','/'
            $files += [ordered]@{
                Full     = (Join-Path $RepoRootFull $normalized)
                Relative = $normalized
            }
        }
    }

    return ,$files
}

function Test-ArtifactPolicy {
    param(
        [string]$RepoRootFull,
        [string]$PolicyPath,
        [hashtable]$Result
    )

    $Result.artifact_policy_check.status = "PASS"
    $policy = Load-JsonFile -Path $PolicyPath

    if ($null -eq $policy.required_files -or $null -eq $policy.repo_disallowed_patterns) {
        Add-Failure -Result $Result -Code "CONTRACT_MISMATCH" -Message "Artifact policy missing required arrays."
        $Result.artifact_policy_check.status = "FAIL"
        return
    }

    foreach ($required in $policy.required_files) {
        $full = Resolve-FullPathSafe -Base $RepoRootFull -Relative ([string]$required)
        if (-not (Test-Path -LiteralPath $full)) {
            $Result.artifact_policy_check.missing_required += [string]$required
            Add-Failure -Result $Result -Code "INSUFFICIENT_DATA" -Message ("Required artifact missing: {0}" -f [string]$required)
            $Result.artifact_policy_check.status = "FAIL"
        }
    }

    $trackedFiles = Get-GitTrackedFiles -RepoRootFull $RepoRootFull
    $Result.artifact_policy_check.tracked_files_scan = @($trackedFiles | ForEach-Object { $_.Relative })

    foreach ($disallowed in $policy.repo_disallowed_patterns) {
        $regex = Convert-GlobToRegex -Pattern ([string]$disallowed)
        $matches = $trackedFiles | Where-Object { $_.Relative -match $regex }
        foreach ($m in $matches) {
            $Result.artifact_policy_check.disallowed_present += [string]$m.Relative
            Add-Failure -Result $Result -Code "CONTROLLED_BLOCK" -Message ("Disallowed tracked repository artifact present: {0}" -f [string]$m.Relative)
            $Result.artifact_policy_check.status = "FAIL"
        }
    }
}

function Finalize-Decision {
    param([hashtable]$Result)

    if ($Result.failures.Count -gt 0) {
        $Result.status = "FAIL"
        $Result.decision = "BLOCK"
        $Result.exit_code = 1
    }
    else {
        $Result.status = "PASS"
        $Result.decision = "ALLOW"
        $Result.exit_code = 0
    }
}

$result = New-Result
$repoRootFull = [System.IO.Path]::GetFullPath($RepoRoot)
$result.repo_root = $repoRootFull

$waiverPathFull         = Resolve-FullPathSafe -Base $repoRootFull -Relative $WaiverFile
$artifactPolicyPathFull = Resolve-FullPathSafe -Base $repoRootFull -Relative $ArtifactPolicyFile
$proofScriptPathFull    = Resolve-FullPathSafe -Base $repoRootFull -Relative $AuthorityProofScript
$proofSummaryPathFull   = Resolve-FullPathSafe -Base $repoRootFull -Relative $AuthorityProofSummary

try {
    Write-Log -Level INFO -Message "Starting authority gate enforcement."
    Write-Log -Level INFO -Message ("Repository root: {0}" -f $repoRootFull)

    Test-Waivers -FullWaiverPath $waiverPathFull -Result $result
    Invoke-AuthorityProof -RepoRootFull $repoRootFull -AuthorityProofScriptPath $proofScriptPathFull -AuthorityProofSummaryPath $proofSummaryPathFull -Result $result

    if (-not $SkipArtifactPolicy) {
        Test-ArtifactPolicy -RepoRootFull $repoRootFull -PolicyPath $artifactPolicyPathFull -Result $result
    }

    Finalize-Decision -Result $result
}
catch {
    Add-Failure -Result $result -Code "CONTROLLED_BLOCK" -Message $_.Exception.Message
    $result.status = "FAIL"
    $result.decision = "BLOCK"
    $result.exit_code = 1
}

$json = $result | ConvertTo-Json -Depth 20

if (-not $EmitJsonOnly) {
    Write-Host ""
    Write-Host "===== AUTHORITY GATE RESULT ====="
    Write-Host $json
    Write-Host "================================="
}
else {
    Write-Output $json
}

exit $result.exit_code