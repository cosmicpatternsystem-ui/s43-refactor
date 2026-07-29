[CmdletBinding()]
param(
    [string]$RepoRoot = ".",
    [string]$ArtifactsRoot = "artifacts/authority-proof",
    [string]$PythonExe = "python",
    [string]$RunId = "",
    [string]$Commit = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

function Write-Utf8NoBomFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

function ConvertTo-JsonSafe {
    param(
        [Parameter(Mandatory = $true)]$Object,
        [int]$Depth = 8
    )
    return ($Object | ConvertTo-Json -Depth $Depth)
}

function Normalize-PathString {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return $Value }
    try {
        return [System.IO.Path]::GetFullPath($Value)
    }
    catch {
        return $Value
    }
}

$resolvedRepoRoot = Normalize-PathString $RepoRoot
Push-Location $resolvedRepoRoot

try {
    $artifactsDir = Join-Path (Get-Location) $ArtifactsRoot
    $artifactsDir = Normalize-PathString $artifactsDir

    if (Test-Path $artifactsDir) {
        Remove-Item -Recurse -Force $artifactsDir
    }
    New-Item -ItemType Directory -Path $artifactsDir -Force | Out-Null

    $pytestOutputPath = Join-Path $artifactsDir "pytest-output.txt"
    $summaryJsonPath  = Join-Path $artifactsDir "summary.json"
    $environmentPath  = Join-Path $artifactsDir "environment.txt"
    $junitXmlPath     = Join-Path $artifactsDir "junit.xml"

    $canonicalTests = @(
        "tests/test_resolve_next_action.py::test_first_pending_task_selected",
        "tests/test_resolve_next_action.py::test_missing_tasks_key_returns_insufficient_data",
        "tests/test_roadmap_governance.py::test_single_roadmap_authority_model_declared",
        "tests/test_roadmap_governance.py::test_requirement_ids_are_unique_and_valid",
        "tests/test_governance_bootstrap.py::test_roadmap_and_next_actions_exist_with_expected_markers"
    )

    $subsetCount = $canonicalTests.Count
    if ($subsetCount -ne 5) {
        throw "Canonical subset drift detected. Expected 5 tests, got $subsetCount."
    }

    $timestampUtc = [DateTime]::UtcNow.ToString("o")

    if ([string]::IsNullOrWhiteSpace($RunId)) {
        if ($env:GITHUB_RUN_ID) {
            $RunId = $env:GITHUB_RUN_ID
        }
        elseif ($env:BUILD_BUILDID) {
            $RunId = $env:BUILD_BUILDID
        }
        elseif ($env:CI_PIPELINE_ID) {
            $RunId = $env:CI_PIPELINE_ID
        }
        else {
            $RunId = "local-$([DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ'))"
        }
    }

    if ([string]::IsNullOrWhiteSpace($Commit)) {
        if ($env:GITHUB_SHA) {
            $Commit = $env:GITHUB_SHA
        }
        elseif ($env:BUILD_SOURCEVERSION) {
            $Commit = $env:BUILD_SOURCEVERSION
        }
        elseif ($env:CI_COMMIT_SHA) {
            $Commit = $env:CI_COMMIT_SHA
        }
        else {
            try {
                $Commit = (git rev-parse HEAD 2>$null).Trim()
            }
            catch {
                $Commit = ""
            }
        }
    }

    $pythonVersion = ""
    try {
        $pythonVersion = (& $PythonExe -c "import sys; print(sys.version.split()[0])" 2>$null | Out-String).Trim()
    }
    catch {
        $pythonVersion = ""
    }

    $commandParts = @(
        "-m", "pytest",
        "--maxfail=1",
        "--disable-warnings",
        "--junitxml", $junitXmlPath
    ) + $canonicalTests

    $commandDisplay = $PythonExe + " " + (($commandParts | ForEach-Object {
        if ($_ -match '\s') { '"' + $_ + '"' } else { $_ }
    }) -join " ")

    $environmentLines = @(
        "python: $pythonVersion",
        "cwd: $(Get-Location)",
        "runner: scripts/run_authority_proof.ps1",
        "command: $commandDisplay",
        "platform: $([System.Environment]::OSVersion.VersionString)",
        "run_id: $RunId",
        "commit: $Commit",
        "timestamp_utc: $timestampUtc"
    )
    Write-Utf8NoBomFile -Path $environmentPath -Content (($environmentLines -join "`n") + "`n")

    $exitCode = 999
    $status = "FAIL"
    $pytestRaw = ""

    try {
        $pytestRaw = & $PythonExe @commandParts 2>&1 | Out-String
        $exitCode = $LASTEXITCODE
    }
    catch {
        $pytestRaw = ($pytestRaw + "`n" + $_.Exception.Message).Trim()
        if (-not $pytestRaw) {
            $pytestRaw = $_ | Out-String
        }
        $exitCode = 1
    }

    if ([string]::IsNullOrWhiteSpace($pytestRaw)) {
        $pytestRaw = "[no pytest output captured]"
    }

    Write-Utf8NoBomFile -Path $pytestOutputPath -Content $pytestRaw

    if ($exitCode -eq 0) {
        $status = "PASS"
    }
    else {
        $status = "FAIL"
    }

    $summary = [ordered]@{
        gate          = "authority-proof"
        status        = $status
        commit        = $Commit
        run_id        = $RunId
        timestamp_utc = $timestampUtc
        python        = $pythonVersion
        runner        = "scripts/run_authority_proof.ps1"
        exit_code     = $exitCode
        subset_count  = $subsetCount
        tests         = $canonicalTests
        artifacts     = [ordered]@{
            pytest_output = "artifacts/authority-proof/pytest-output.txt"
            summary_json  = "artifacts/authority-proof/summary.json"
            environment   = "artifacts/authority-proof/environment.txt"
            junit_xml     = "artifacts/authority-proof/junit.xml"
        }
    }

    $summaryJson = ConvertTo-JsonSafe -Object $summary -Depth 8
    Write-Utf8NoBomFile -Path $summaryJsonPath -Content ($summaryJson + "`n")

    if (-not (Test-Path $pytestOutputPath)) {
        throw "Missing required artifact: pytest-output.txt"
    }
    if (-not (Test-Path $summaryJsonPath)) {
        throw "Missing required artifact: summary.json"
    }
    if (-not (Test-Path $environmentPath)) {
        throw "Missing required artifact: environment.txt"
    }

    if ($subsetCount -ne 5) {
        throw "subset_count validation failed."
    }

    if (($status -eq "PASS") -and ($exitCode -ne 0)) {
        throw "Integrity validation failed: PASS with non-zero exit code."
    }
    if (($status -eq "FAIL") -and ($exitCode -eq 0)) {
        throw "Integrity validation failed: FAIL with zero exit code."
    }

    if ($status -eq "PASS") {
        Write-Host "AUTHORITY_PROOF_RESULT=PASS"
        exit 0
    }
    else {
        Write-Host "AUTHORITY_PROOF_RESULT=FAIL"
        exit $exitCode
    }
}
finally {
    Pop-Location
}
