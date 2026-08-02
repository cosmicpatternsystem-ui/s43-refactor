[CmdletBinding()]
param(
    [string]$RepoRoot = 'G:\s43_work\s43_g11_work',
    [string]$TargetPhaseId = 'P0-PHASE-32-02-OPERATIONAL-INTELLIGENCE-RUNTIME-CONTRACT',
    [string]$ExpectedPolicySha256 = '039FD1B8D3E18CF4FDE3824E8A5A37E83CE0011B403E00B20BC0E2E34D95E157',
    [string]$ExpectedSchemaVersion = '2.0',
    [string]$ExpectedSourceOfTruth = 'repository_files_only',
    [string]$ExpectedEnforcementModel = 'generated-and-diff-enforced-in-pr',
    [string]$ExpectedCanonicalRoadmap = 'docs/governance/ROADMAP_CANONICAL.md'
)

$ErrorActionPreference = 'Stop'

$policyPath = Join-Path $RepoRoot 'docs\governance\TOP_LEVEL_COMMERCIAL_EXECUTION_POLICY.md'
$roadmapPath = Join-Path $RepoRoot 'docs\governance\ROADMAP_CURRENT.json'
$reportsDir = Join-Path $RepoRoot 'reports'
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$reportPath = Join-Path $reportsDir ("COMMERCIAL_EXECUTION_GATE_REPORT_{0}.json" -f $timestamp)

$script:findings = New-Object System.Collections.ArrayList
$script:warnings = New-Object System.Collections.ArrayList

function Add-Finding {
    param([string]$Code,[string]$Message)
    $null = $script:findings.Add([pscustomobject]@{
        code = $Code
        message = $Message
    })
}

function Add-Warning {
    param([string]$Code,[string]$Message)
    $null = $script:warnings.Add([pscustomobject]@{
        code = $Code
        message = $Message
    })
}

function Get-StringArray {
    param($Value)

    $items = New-Object System.Collections.ArrayList

    if ($null -eq $Value) {
        return ,@($items.ToArray())
    }

    foreach ($item in @($Value)) {
        if ($null -eq $item) { continue }
        $text = [string]$item
        if (-not [string]::IsNullOrWhiteSpace($text)) {
            $null = $items.Add($text)
        }
    }

    return ,@($items.ToArray())
}

function Test-HasFinancialSignals {
    param([string[]]$Texts)

    $signals = @(
        'financial',
        'real-money',
        'money',
        'cash',
        'revenue',
        'p&l',
        'pnl',
        'risk',
        'exposure',
        'commercial'
    )

    foreach ($text in @($Texts)) {
        if ([string]::IsNullOrWhiteSpace($text)) { continue }
        $normalized = $text.ToLowerInvariant()
        foreach ($signal in $signals) {
            if ($normalized.Contains($signal)) {
                return $true
            }
        }
    }

    return $false
}

function Test-PhaseIdentityMatch {
    param(
        $Item,
        [string]$PhaseId
    )

    if ($null -eq $Item) { return $false }

    if ($Item.PSObject.Properties['id']) {
        if ([string]$Item.id -eq $PhaseId) {
            return $true
        }
    }

    if ($Item.PSObject.Properties['phase_id']) {
        if ([string]$Item.phase_id -eq $PhaseId) {
            return $true
        }
    }

    return $false
}

function Find-PhaseInTopLevelPhases {
    param(
        $Roadmap,
        [string]$PhaseId
    )

    if ($null -eq $Roadmap) { return $null }
    if (-not $Roadmap.PSObject.Properties['phases']) { return $null }

    foreach ($phase in @($Roadmap.phases)) {
        if (Test-PhaseIdentityMatch -Item $phase -PhaseId $PhaseId) {
            return $phase
        }
    }

    return $null
}

function Find-PhaseRecursive {
    param(
        $Node,
        [string]$PhaseId
    )

    if ($null -eq $Node) { return $null }

    foreach ($item in @($Node)) {
        if ($null -eq $item) { continue }

        if (Test-PhaseIdentityMatch -Item $item -PhaseId $PhaseId) {
            return $item
        }

        foreach ($prop in $item.PSObject.Properties) {
            $value = $prop.Value
            if ($null -eq $value) { continue }

            $isEnumerable = ($value -is [System.Collections.IEnumerable]) -and -not ($value -is [string])
            $isObjectLike = ($value.PSObject -and $value.PSObject.Properties.Count -gt 0)

            if ($isEnumerable -or $isObjectLike) {
                $found = Find-PhaseRecursive -Node $value -PhaseId $PhaseId
                if ($null -ne $found) {
                    return $found
                }
            }
        }
    }

    return $null
}

try {
    if (-not (Test-Path $reportsDir)) {
        New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null
    }

    if (-not (Test-Path $policyPath)) {
        throw "Policy file not found: $policyPath"
    }

    if (-not (Test-Path $roadmapPath)) {
        throw "Roadmap file not found: $roadmapPath"
    }

    $policyHash = (Get-FileHash -Path $policyPath -Algorithm SHA256).Hash.ToUpperInvariant()

    if ($policyHash -ne $ExpectedPolicySha256) {
        Add-Finding 'policy_hash_mismatch' ("Expected SHA256 {0} but got {1}" -f $ExpectedPolicySha256, $policyHash)
    }

    [byte[]]$roadmapBytes = [System.IO.File]::ReadAllBytes($roadmapPath)

    $bomDetected = $false
    if ($roadmapBytes.Length -ge 3) {
        if ($roadmapBytes[0] -eq 239 -and $roadmapBytes[1] -eq 187 -and $roadmapBytes[2] -eq 191) {
            $bomDetected = $true
        }
    }

    if ($bomDetected) {
        Add-Warning 'roadmap_bom_detected' 'ROADMAP_CURRENT.json has UTF-8 BOM.'
    }

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $roadmapText = $utf8NoBom.GetString($roadmapBytes)

    if ($roadmapText.Contains("`r`n")) {
        Add-Warning 'roadmap_crlf_detected' 'ROADMAP_CURRENT.json contains CRLF line endings.'
    }

    $roadmap = $roadmapText | ConvertFrom-Json

    if ([string]$roadmap.schema_version -ne $ExpectedSchemaVersion) {
        Add-Finding 'schema_version_mismatch' ("Expected schema_version={0}" -f $ExpectedSchemaVersion)
    }

    if ([string]$roadmap.source_of_truth -ne $ExpectedSourceOfTruth) {
        Add-Finding 'source_of_truth_mismatch' ("Expected source_of_truth={0}" -f $ExpectedSourceOfTruth)
    }

    if ([string]$roadmap.enforcement_model -ne $ExpectedEnforcementModel) {
        Add-Finding 'enforcement_model_mismatch' ("Expected enforcement_model={0}" -f $ExpectedEnforcementModel)
    }

    if ([string]$roadmap.canonical_roadmap -ne $ExpectedCanonicalRoadmap) {
        Add-Finding 'canonical_roadmap_mismatch' ("Expected canonical_roadmap={0}" -f $ExpectedCanonicalRoadmap)
    }

    $targetPhase = Find-PhaseInTopLevelPhases -Roadmap $roadmap -PhaseId $TargetPhaseId

    if ($null -eq $targetPhase) {
        $targetPhase = Find-PhaseRecursive -Node $roadmap -PhaseId $TargetPhaseId
    }

    if ($null -eq $targetPhase) {
        Add-Finding 'target_phase_missing' ("Target phase not found: {0}" -f $TargetPhaseId)
    }

    $scopePass = $false
    $governancePass = $false
    $structurePass = $false
    $financialPass = $false

    if ($null -ne $targetPhase) {
        $scopePass = $true

        $governancePass = `
            ($policyHash -eq $ExpectedPolicySha256) -and `
            ([string]$roadmap.schema_version -eq $ExpectedSchemaVersion) -and `
            ([string]$roadmap.source_of_truth -eq $ExpectedSourceOfTruth) -and `
            ([string]$roadmap.enforcement_model -eq $ExpectedEnforcementModel) -and `
            ([string]$roadmap.canonical_roadmap -eq $ExpectedCanonicalRoadmap)

        $owner = ''
        $priority = ''
        $lastVerifiedAt = ''

        if ($targetPhase.PSObject.Properties['owner']) {
            $owner = [string]$targetPhase.owner
        }

        if ($targetPhase.PSObject.Properties['priority']) {
            $priority = [string]$targetPhase.priority
        }

        if ($targetPhase.PSObject.Properties['last_verified_at']) {
            $lastVerifiedAt = [string]$targetPhase.last_verified_at
        }

        $tasks = @()
        if ($targetPhase.PSObject.Properties['tasks']) {
            $tasks = Get-StringArray $targetPhase.tasks
        }

        if ([string]::IsNullOrWhiteSpace($owner)) {
            Add-Finding 'owner_missing' 'Target phase owner is missing.'
        }

        if ([string]::IsNullOrWhiteSpace($priority)) {
            Add-Finding 'priority_missing' 'Target phase priority is missing.'
        }

        if ([string]::IsNullOrWhiteSpace($lastVerifiedAt)) {
            Add-Finding 'last_verified_at_missing' 'Target phase last_verified_at is missing.'
        }

        if ($tasks.Count -eq 0) {
            Add-Finding 'tasks_missing' 'Target phase tasks are missing or empty.'
        }

        $structurePass = `
            (-not [string]::IsNullOrWhiteSpace($owner)) -and `
            (-not [string]::IsNullOrWhiteSpace($priority)) -and `
            (-not [string]::IsNullOrWhiteSpace($lastVerifiedAt)) -and `
            ($tasks.Count -gt 0)

        $acceptanceCriteria = @()
        if ($targetPhase.PSObject.Properties['acceptance_criteria']) {
            $acceptanceCriteria = Get-StringArray $targetPhase.acceptance_criteria
        }

        $evidence = @()
        if ($targetPhase.PSObject.Properties['evidence']) {
            $evidence = Get-StringArray $targetPhase.evidence
        }

        $texts = @()
        $texts += @($tasks)
        $texts += @($acceptanceCriteria)
        $texts += @($evidence)

        $financialPass = Test-HasFinancialSignals -Texts $texts

        if (-not $financialPass) {
            Add-Finding 'financial_relevance_missing' 'No explicit financial/commercial/risk/exposure signal found in target phase.'
        }
    }

    $blockingCount = $script:findings.Count
    $verdict = 'NO-GO'
    $posture = 'CONTROLLED_BLOCKED'

    if ($scopePass -and $governancePass -and $structurePass -and $financialPass -and $blockingCount -eq 0) {
        $verdict = 'GO'
        $posture = 'UNBLOCKED'
    }

    $result = [pscustomobject]@{
        generated_at_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        verdict = $verdict
        posture = $posture
        repo_root = $RepoRoot
        policy_path = $policyPath
        roadmap_path = $roadmapPath
        report_path = $reportPath
        target_phase_id = $TargetPhaseId
        gates = [pscustomobject]@{
            scope = $scopePass
            governance = $governancePass
            structure = $structurePass
            financial_relevance = $financialPass
        }
        policy_sha256_expected = $ExpectedPolicySha256
        policy_sha256_actual = $policyHash
        roadmap_metadata = [pscustomobject]@{
            schema_version = [string]$roadmap.schema_version
            source_of_truth = [string]$roadmap.source_of_truth
            enforcement_model = [string]$roadmap.enforcement_model
            canonical_roadmap = [string]$roadmap.canonical_roadmap
        }
        warnings = @($script:warnings)
        findings = @($script:findings)
    }

    $json = $result | ConvertTo-Json -Depth 100
    [System.IO.File]::WriteAllText($reportPath, $json, $utf8NoBom)

    Write-Host ''
    Write-Host ('Report: ' + $reportPath)
    Write-Host ('Verdict: ' + $verdict)
    Write-Host ('Posture: ' + $posture)
    Write-Host ('scope=' + $scopePass)
    Write-Host ('governance=' + $governancePass)
    Write-Host ('structure=' + $structurePass)
    Write-Host ('financial_relevance=' + $financialPass)
    Write-Host ('findings=' + $script:findings.Count)
    Write-Host ('warnings=' + $script:warnings.Count)

    if ($script:warnings.Count -gt 0) {
        Write-Host 'Warning codes:'
        foreach ($warning in $script:warnings) {
            Write-Host (' - ' + [string]$warning.code)
        }
    }

    if ($script:findings.Count -gt 0) {
        Write-Host 'Finding codes:'
        foreach ($finding in $script:findings) {
            Write-Host (' - ' + [string]$finding.code)
        }
    }
}
catch {
    $errorMessage = $_.Exception.Message

    try {
        if (-not (Test-Path $reportsDir)) {
            New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null
        }

        $failResult = [pscustomobject]@{
            generated_at_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
            verdict = 'NO-GO'
            posture = 'CONTROLLED_BLOCKED'
            status = 'FAILED'
            repo_root = $RepoRoot
            policy_path = $policyPath
            roadmap_path = $roadmapPath
            report_path = $reportPath
            error = $errorMessage
        }

        $failJson = $failResult | ConvertTo-Json -Depth 20
        [System.IO.File]::WriteAllText($reportPath, $failJson, (New-Object System.Text.UTF8Encoding($false)))
    }
    catch {
    }

    Write-Host ''
    Write-Host ('Report: ' + $reportPath)
    Write-Host 'Status: FAILED'
    Write-Host ('Error: ' + $errorMessage)
}