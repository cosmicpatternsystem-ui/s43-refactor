param(
    [switch]$AllowDirty
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Failures = New-Object System.Collections.Generic.List[string]

function Add-Failure {
    param([string]$Message)
    $script:Failures.Add($Message) | Out-Null
    Write-Host "FAIL: $Message"
}

function Add-Pass {
    param([string]$Message)
    Write-Host "PASS: $Message"
}

function Test-RepoPath {
    param([string]$RelativePath)
    return Test-Path (Join-Path $RepoRoot $RelativePath)
}

$PolicyPath = Join-Path $RepoRoot "AUDIT/OPERATIONAL_RELEASE_POLICY.json"

if (-not (Test-Path $PolicyPath)) {
    Add-Failure "Operational release policy exists"
} else {
    Add-Pass "Operational release policy exists"
}

if (Test-Path $PolicyPath) {
    $Policy = Get-Content $PolicyPath -Raw | ConvertFrom-Json

    foreach ($RequiredFile in $Policy.required_files) {
        if (Test-RepoPath $RequiredFile) {
            Add-Pass "Required file exists: $RequiredFile"
        } else {
            Add-Failure "Required file missing: $RequiredFile"
        }
    }

    $RoadmapPath = Join-Path $RepoRoot "AUDIT/OPERATIONAL_ROADMAP.md"
    if (Test-Path $RoadmapPath) {
        $Roadmap = Get-Content $RoadmapPath -Raw
        foreach ($Phrase in $Policy.required_roadmap_phrases) {
            if ($Roadmap.Contains($Phrase)) {
                Add-Pass "Roadmap contains required phrase: $Phrase"
            } else {
                Add-Failure "Roadmap missing required phrase: $Phrase"
            }
        }
    }

    $DecisionPath = Join-Path $RepoRoot "AUDIT/PHASE19_OPERATIONAL_ROADMAP_DECISION.md"
    if (Test-Path $DecisionPath) {
        $Decision = Get-Content $DecisionPath -Raw
        foreach ($Phrase in $Policy.required_decision_phrases) {
            if ($Decision.Contains($Phrase)) {
                Add-Pass "Decision contains required phrase: $Phrase"
            } else {
                Add-Failure "Decision missing required phrase: $Phrase"
            }
        }
    }

    if ($Policy.commercial_automation.full_end_to_end_automation_claim_allowed -eq $false) {
        Add-Pass "Commercial automation is correctly classified as backlog"
    } else {
        Add-Failure "Commercial automation must not be claimed complete in Phase 19"
    }

    if ($Policy.branch_protection.required -eq $true) {
        Add-Pass "Branch protection requirement is recorded"
    } else {
        Add-Failure "Branch protection requirement is not recorded"
    }
}

if (-not $AllowDirty) {
    $GitStatus = git -C $RepoRoot status --short
    if ($LASTEXITCODE -ne 0) {
        Add-Failure "Git status command failed"
    } elseif ($GitStatus) {
        Add-Failure "Repository has uncommitted changes"
    } else {
        Add-Pass "Repository state is clean"
    }
} else {
    Add-Pass "Repository dirty state allowed"
}

if ($Failures.Count -gt 0) {
    Write-Host ""
    Write-Host "OPERATIONAL ROADMAP GATE: FAIL"
    foreach ($Failure in $Failures) {
        Write-Host "- $Failure"
    }
    exit 1
}

Write-Host ""
Write-Host "OPERATIONAL ROADMAP GATE: PASS"
exit 0