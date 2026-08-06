[CmdletBinding()]
param(
    [string]$CanonicalPath = ".\docs\governance\ROADMAP_CANONICAL.md",
    [string]$RoadmapJsonPath = ".\docs\governance\ROADMAP_CURRENT.json",
    [string]$EvidencePackPath = ".\docs\governance\ROADMAP_EVIDENCE_PACK.txt",
    [string]$OutJsonPath = ".\artifacts\gov_drift_gate_result.json"
)

$ScriptBase = if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
    $PSScriptRoot
} else {
    (Get-Location).Path
}
$ErrorActionPreference = 'Stop'

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host ('=' * 78)
    Write-Host $Title
    Write-Host ('=' * 78)
}

function Resolve-FirstExistingPath {
    param(
        [Parameter(Mandatory = $true)][string[]]$Candidates
    )

    foreach ($candidate in $Candidates) {
        # Skip null/empty candidates defensively
        if ([string]::IsNullOrWhiteSpace($candidate)) {
            continue
        }
        $resolved = Resolve-Path -LiteralPath $candidate -ErrorAction SilentlyContinue
        if ($resolved) {
            return $resolved.Path
        }
    }

    return $null
}

function Test-ContainsLiteral {
    param(
        [string]$Text,
        [string]$Pattern
    )
    if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
    return ($Text -match [regex]::Escape($Pattern))
}

function Test-ContainsRegex {
    param(
        [string]$Text,
        [string]$Pattern
    )
    if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
    return ($Text -match $Pattern)
}

function Get-StringProp {
    param(
        [object]$Object,
        [string[]]$CandidateNames
    )

    if ($null -eq $Object) { return $null }

    foreach ($name in $CandidateNames) {
        $prop = $Object.PSObject.Properties[$name]
        if ($null -ne $prop -and $null -ne $prop.Value) {
            $s = [string]$prop.Value
            if (-not [string]::IsNullOrWhiteSpace($s)) {
                return $s.Trim()
            }
        }
    }

    return $null
}

function Get-ArrayProp {
    param(
        [object]$Object,
        [string[]]$CandidateNames
    )

    if ($null -eq $Object) { return @() }

    foreach ($name in $CandidateNames) {
        $prop = $Object.PSObject.Properties[$name]
        if ($null -ne $prop -and $null -ne $prop.Value) {
            $items = @()
            foreach ($item in $prop.Value) {
                $items += $item
            }
            if ($items.Count -gt 0) {
                return $items
            }
        }
    }

    return @()
}

function Get-BoolPropValue {
    param(
        [object]$Object,
        [string[]]$CandidateNames
    )

    if ($null -eq $Object) { return $null }

    foreach ($name in $CandidateNames) {
        $prop = $Object.PSObject.Properties[$name]
        if ($null -ne $prop -and $null -ne $prop.Value) {
            try {
                return [bool]$prop.Value
            }
            catch {
            }
        }
    }

    return $null
}

function Get-PhaseStatusCandidate {
    param(
        [object[]]$Phases
    )

    $result = [ordered]@{
        phase             = $null
        status            = $null
        task              = $null
        phase_found       = $false
        status_found      = $false
        task_found        = $false
        phases_found      = $false
        selected_strategy = $null
        phase_count       = 0
        active_flags_seen = $false
    }

    if ($null -eq $Phases -or $Phases.Count -eq 0) {
        return $result
    }

    $result.phases_found = $true
    $result.phase_count  = $Phases.Count

    foreach ($phaseObj in $Phases) {
        $isCurrent = Get-BoolPropValue -Object $phaseObj -CandidateNames @('is_current','current','active')
        if ($null -ne $isCurrent) {
            $result.active_flags_seen = $true
            if ($isCurrent) {
                $phaseName   = Get-StringProp -Object $phaseObj -CandidateNames @('phase','name','id','title')
                $phaseStatus = Get-StringProp -Object $phaseObj -CandidateNames @('status','state','phase_status')
                $phaseTask   = Get-StringProp -Object $phaseObj -CandidateNames @('task','task_name','workstream','focus','title')

                $result.phase             = $phaseName
                $result.status            = $phaseStatus
                $result.task              = $phaseTask
                $result.phase_found       = -not [string]::IsNullOrWhiteSpace($phaseName)
                $result.status_found      = -not [string]::IsNullOrWhiteSpace($phaseStatus)
                $result.task_found        = -not [string]::IsNullOrWhiteSpace($phaseTask)
                $result.selected_strategy = "explicit_current_flag"
                return $result
            }
        }
    }

    $preferredStatuses = @(
        'active',
        'in_progress',
        'in-progress',
        'current',
        'open',
        'working'
    )

    foreach ($phaseObj in $Phases) {
        $phaseName   = Get-StringProp -Object $phaseObj -CandidateNames @('phase','name','id','title')
        $phaseStatus = Get-StringProp -Object $phaseObj -CandidateNames @('status','state','phase_status')
        $phaseTask   = Get-StringProp -Object $phaseObj -CandidateNames @('task','task_name','workstream','focus','title')

        if ($phaseStatus) {
            foreach ($s in $preferredStatuses) {
                if ($phaseStatus.ToLowerInvariant() -eq $s) {
                    $result.phase             = $phaseName
                    $result.status            = $phaseStatus
                    $result.task              = $phaseTask
                    $result.phase_found       = -not [string]::IsNullOrWhiteSpace($phaseName)
                    $result.status_found      = $true
                    $result.task_found        = -not [string]::IsNullOrWhiteSpace($phaseTask)
                    $result.selected_strategy = "preferred_active_status"
                    return $result
                }
            }
        }
    }

    $terminalStatuses = @(
        'complete',
        'completed',
        'done',
        'closed',
        'recorded',
        'archived',
        'cancelled',
        'canceled'
    )

    foreach ($phaseObj in $Phases) {
        $phaseName   = Get-StringProp -Object $phaseObj -CandidateNames @('phase','name','id','title')
        $phaseStatus = Get-StringProp -Object $phaseObj -CandidateNames @('status','state','phase_status')
        $phaseTask   = Get-StringProp -Object $phaseObj -CandidateNames @('task','task_name','workstream','focus','title')

        if ($phaseStatus) {
            $isTerminal = $false
            foreach ($term in $terminalStatuses) {
                if ($phaseStatus.ToLowerInvariant() -eq $term) {
                    $isTerminal = $true
                    break
                }
            }

            if (-not $isTerminal) {
                $result.phase             = $phaseName
                $result.status            = $phaseStatus
                $result.task              = $phaseTask
                $result.phase_found       = -not [string]::IsNullOrWhiteSpace($phaseName)
                $result.status_found      = $true
                $result.task_found        = -not [string]::IsNullOrWhiteSpace($phaseTask)
                $result.selected_strategy = "first_non_terminal_status"
                return $result
            }
        }
    }

    foreach ($phaseObj in $Phases) {
        $phaseName   = Get-StringProp -Object $phaseObj -CandidateNames @('phase','name','id','title')
        $phaseStatus = Get-StringProp -Object $phaseObj -CandidateNames @('status','state','phase_status')
        $phaseTask   = Get-StringProp -Object $phaseObj -CandidateNames @('task','task_name','workstream','focus','title')

        if ($phaseName -or $phaseStatus -or $phaseTask) {
            $result.phase             = $phaseName
            $result.status            = $phaseStatus
            $result.task              = $phaseTask
            $result.phase_found       = -not [string]::IsNullOrWhiteSpace($phaseName)
            $result.status_found      = -not [string]::IsNullOrWhiteSpace($phaseStatus)
            $result.task_found        = -not [string]::IsNullOrWhiteSpace($phaseTask)
            $result.selected_strategy = "first_observed_phase"
            return $result
        }
    }

    return $result
}

function New-ResultObject {
    param(
        [hashtable]$Files,
        [string]$Reason
    )

    return [ordered]@{
        timestamp_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        files = [ordered]@{
            canonical_path     = $Files.canonical_path
            roadmap_json_path  = $Files.roadmap_json_path
            evidence_pack_path = $Files.evidence_pack_path
            out_json_path      = $Files.out_json_path
            comparator_path    = $Files.comparator_path
        }
        authority = [ordered]@{
            authority_confirmed                 = $false
            canonical_human_phrase              = $false
            canonical_governed_authority_phrase = $false
            roadmap_authority_phrase            = $false
            mcp03_present                       = $false
        }
        evidence = [ordered]@{
            rule_confirmed = $false
            decision_rule  = $null
        }
        observed_roadmap = [ordered]@{
            exists         = $false
            parse_ok       = $false
            schema_version = $null
            version        = $null
            phase          = $null
            status         = $null
            task           = $null
            lifecycle = [ordered]@{
                status = $null
            }
            extraction = [ordered]@{
                phase_selection_strategy = $null
                phase_count              = 0
                active_flags_seen        = $false
            }
            field_presence = [ordered]@{
                version_found          = $false
                schema_version_found   = $false
                lifecycle_status_found = $false
                phase_found            = $false
                status_found           = $false
                task_found             = $false
                phases_found           = $false
            }
        }
        drift = [ordered]@{
            has_drift_issues        = $false
            has_semver_drift        = $false
            has_authority_drift     = $false
            has_lifecycle_drift     = $false
            has_phase_status_drift  = $false
            has_content_drift       = $false

            comparator_available    = $script:comparatorAvailable
            drift_proven            = $false
            note                    = "Fail-closed due to missing or insufficient validated comparator evidence."
        }
        governance_gate     = "HOLD"
        operational_posture = "FAIL-CLOSED"
        drift_status        = "NOT PROVEN AS GOVERNANCE-SIGNIFICANT"
        overall_verdict     = "HOLD"
        reason              = $Reason
    }
}

function Save-ResultJson {
    param(
        [object]$Result,
        [string]$Path
    )

    $parent = Split-Path -Parent $Path
    if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    $json = $Result | ConvertTo-Json -Depth 12
    Set-Content -LiteralPath $Path -Value $json -Encoding UTF8
    Write-Host ("Result artifact written: {0}" -f $Path)
}

function Emit-AndExit {
    param(
        [object]$Result,
        [string]$OutPath,
        [int]$ExitCode = 1
    )

    try {
        Save-ResultJson -Result $Result -Path $OutPath
    }
    catch {
        Write-Warning ("Could not write result artifact: {0}" -f $_.Exception.Message)
    }

    $Result | ConvertTo-Json -Depth 12 | Write-Output
    exit $ExitCode
}

$script:comparatorAvailable = $false
$script:comparatorEvaluationStatus = $null
$script:comparatorGovernanceSignificance = $null
$script:comparatorSupportsControlled = $false

Write-Section "Locating governance files"

function Resolve-SafePath {
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) { return $null }
    try {
        return (Resolve-Path -LiteralPath $Path -ErrorAction SilentlyContinue)
    } catch {
        return $null
    }
}

if ([string]::IsNullOrWhiteSpace($CanonicalPath))    { $CanonicalPath = '.\ROADMAP_CANONICAL.md' }
if ([string]::IsNullOrWhiteSpace($RoadmapJsonPath))   { $RoadmapJsonPath = '.\ROADMAP_CURRENT.json' }
if ([string]::IsNullOrWhiteSpace($EvidencePackPath))  { $EvidencePackPath = '.\ROADMAP_EVIDENCE_PACK.txt' }
if ([string]::IsNullOrWhiteSpace($OutJsonPath))       { $OutJsonPath = '.\gov_drift_gate_result.json' }

$resolvedCanonical  = Resolve-SafePath $CanonicalPath
$resolvedRoadmap    = Resolve-SafePath $RoadmapJsonPath
$resolvedEvidence   = Resolve-SafePath $EvidencePackPath
$resolvedComparator = Resolve-SafePath '.\roadmap_comparator_result.json'

$filesInfo = [ordered]@{
    canonical_path    = if ($resolvedCanonical)  { $resolvedCanonical.Path }  else { $CanonicalPath }
    roadmap_json_path = if ($resolvedRoadmap)    { $resolvedRoadmap.Path }    else { $RoadmapJsonPath }
    evidence_pack_path= if ($resolvedEvidence)   { $resolvedEvidence.Path }   else { $EvidencePackPath }
    comparator_path   = if ($resolvedComparator) { $resolvedComparator.Path } else { '.\roadmap_comparator_result.json' }
    out_json_path     = $OutJsonPath
}

Write-Host ("Canonical  : {0}" -f $filesInfo.canonical_path)
Write-Host ("Current    : {0}" -f $filesInfo.roadmap_json_path)
Write-Host ("Evidence   : {0}" -f $filesInfo.evidence_pack_path)
Write-Host ("Comparator : {0}" -f $filesInfo.comparator_path)
Write-Host ("Output     : {0}" -f $filesInfo.out_json_path)

Write-Section "Reading governance files"

$canonicalText = Get-Content -LiteralPath ([string]$resolvedCanonical) -Raw -Encoding UTF8
$roadmapText   = Get-Content -LiteralPath ([string]$resolvedRoadmap) -Raw -Encoding UTF8
$evidenceText  = Get-Content -LiteralPath ([string]$resolvedEvidence) -Raw -Encoding UTF8

Write-Section "Validating authority and evidence rule"

$canonicalHumanPhrase = (
    (Test-ContainsLiteral -Text $canonicalText -Pattern "human-readable canonical roadmap") -or
    (Test-ContainsLiteral -Text $canonicalText -Pattern "human-readable")
)

$canonicalGovernedAuthorityPhrase = (
    (Test-ContainsRegex -Text $canonicalText -Pattern 'canonical\s+human-governed\s+roadmap\s+authority') -or
    (Test-ContainsRegex -Text $canonicalText -Pattern 'human-governed\s+roadmap\s+authority') -or
    (Test-ContainsRegex -Text $canonicalText -Pattern 'govern(ed|ing)\s+authority')
)

$roadmapAuthorityPhrase = (
    (Test-ContainsLiteral -Text $canonicalText -Pattern "ROADMAP_CURRENT.json") -or
    (Test-ContainsRegex -Text $canonicalText -Pattern 'machine-readable\s+roadmap\s+authority') -or
    (Test-ContainsLiteral -Text $evidenceText -Pattern "ROADMAP_CURRENT.json")
)

$mcp03Present = (
    (Test-ContainsLiteral -Text $canonicalText -Pattern "MCP03") -or
    (Test-ContainsLiteral -Text $canonicalText -Pattern "MCP-03") -or
    (Test-ContainsLiteral -Text $evidenceText -Pattern "MCP03") -or
    (Test-ContainsLiteral -Text $evidenceText -Pattern "MCP-03")
)

$authorityConfirmed = (
    $canonicalHumanPhrase -and
    $canonicalGovernedAuthorityPhrase -and
    $roadmapAuthorityPhrase -and
    $mcp03Present
)

$decisionRule = $null
if (Test-ContainsRegex -Text $evidenceText -Pattern 'No evidence,\s+no DONE\.') {
    $decisionRule = "No evidence, no DONE."
}

$ruleConfirmed = -not [string]::IsNullOrWhiteSpace($decisionRule)

$preParseResult = New-ResultObject -Files $filesInfo -Reason "Pre-parse evaluation completed."
$preParseResult.authority.canonical_human_phrase = $canonicalHumanPhrase
$preParseResult.authority.canonical_governed_authority_phrase = $canonicalGovernedAuthorityPhrase
$preParseResult.authority.roadmap_authority_phrase = $roadmapAuthorityPhrase
$preParseResult.authority.mcp03_present = $mcp03Present
$preParseResult.authority.authority_confirmed = $authorityConfirmed
$preParseResult.evidence.rule_confirmed = $ruleConfirmed
$preParseResult.evidence.decision_rule = $decisionRule
$preParseResult.observed_roadmap.exists = ($null -ne $resolvedRoadmap)
$preParseResult.observed_roadmap.parse_ok = $false

if (-not $authorityConfirmed) {
    $preParseResult.reason = "Governance authority could not be fully confirmed from canonical artifacts."
    Emit-AndExit -Result $preParseResult -OutPath $OutJsonPath -ExitCode 1
}

if (-not $ruleConfirmed) {
    $preParseResult.reason = "Decision rule was not confirmed from ROADMAP_EVIDENCE_PACK.txt."
    Emit-AndExit -Result $preParseResult -OutPath $OutJsonPath -ExitCode 1
}

Write-Section "Parsing roadmap JSON"

try {
    $roadmap = $roadmapText | ConvertFrom-Json
}
catch {
    $preParseResult.reason = "ROADMAP_CURRENT.json could not be parsed: $($_.Exception.Message)"
    Emit-AndExit -Result $preParseResult -OutPath $OutJsonPath -ExitCode 1
}

$version = Get-StringProp -Object $roadmap -CandidateNames @(
    'roadmap_version',
    'version'
)

$schemaVersion = Get-StringProp -Object $roadmap -CandidateNames @(
    'schema_version'
)

$lifecycleStatus = $null
$lifecycleProp = $roadmap.PSObject.Properties['lifecycle']
if ($null -ne $lifecycleProp -and $null -ne $lifecycleProp.Value) {
    $lifecycleStatus = Get-StringProp -Object $lifecycleProp.Value -CandidateNames @(
        'status',
        'state'
    )
}

$phases = Get-ArrayProp -Object $roadmap -CandidateNames @('phases')
$phaseCandidate = Get-PhaseStatusCandidate -Phases $phases

$topLevelPhase = Get-StringProp -Object $roadmap -CandidateNames @(
    'phase',
    'current_phase'
)

$topLevelStatus = Get-StringProp -Object $roadmap -CandidateNames @(
    'status',
    'current_status'
)

$topLevelTask = Get-StringProp -Object $roadmap -CandidateNames @(
    'task',
    'current_task',
    'focus',
    'workstream',
    'title'
)

$observedPhase = if ($phaseCandidate.phase_found) { $phaseCandidate.phase } else { $topLevelPhase }
$observedStatus = if ($phaseCandidate.status_found) { $phaseCandidate.status } elseif ($lifecycleStatus) { $lifecycleStatus } else { $topLevelStatus }
$observedTask = if ($phaseCandidate.task_found) { $phaseCandidate.task } else { $topLevelTask }

Write-Section "Computing governance result"


# Comparator capability (fail-closed, low-risk)
$comparatorPayload = $null
$comparatorPathEffective = $null

if ($resolvedComparator -and -not [string]::IsNullOrWhiteSpace($resolvedComparator.Path)) {
    $comparatorPathEffective = $resolvedComparator.Path
} elseif (-not [string]::IsNullOrWhiteSpace($filesInfo.comparator_path)) {
    $comparatorPathEffective = $filesInfo.comparator_path
}

if (-not [string]::IsNullOrWhiteSpace($comparatorPathEffective) -and (Test-Path -LiteralPath $comparatorPathEffective)) {
    try {
        $rawComparator = Get-Content -LiteralPath $comparatorPathEffective -Raw -ErrorAction Stop
        if (-not [string]::IsNullOrWhiteSpace($rawComparator)) {
            try {
                $comparatorPayload = $rawComparator | ConvertFrom-Json -ErrorAction Stop
                $script:comparatorAvailable = $true
                $script:comparatorEvaluationStatus = [string]$comparatorPayload.evaluation_status
                $script:comparatorGovernanceSignificance = [string]$comparatorPayload.governance_significance
                $script:comparatorSupportsControlled = (
                    $script:comparatorEvaluationStatus -eq 'EVALUATED' -and
                    $script:comparatorGovernanceSignificance -eq 'NON_SIGNIFICANT'
                )
            } catch {
            }
        }
    } catch {
    }
}
$result = New-ResultObject -Files $filesInfo -Reason "Authority and evidence rule confirmed; roadmap fields extracted with best-effort logic; governance-significant drift is not proven from validated comparator evidence."
$result.observed_roadmap.exists = $true
$result.observed_roadmap.parse_ok = $true
$result.observed_roadmap.schema_version = $schemaVersion

$result.authority.canonical_human_phrase = $canonicalHumanPhrase
$result.authority.canonical_governed_authority_phrase = $canonicalGovernedAuthorityPhrase
$result.authority.roadmap_authority_phrase = $roadmapAuthorityPhrase
$result.authority.mcp03_present = $mcp03Present
$result.authority.authority_confirmed = $authorityConfirmed

$result.evidence.rule_confirmed = $ruleConfirmed
$result.evidence.decision_rule = $decisionRule

$result.observed_roadmap.version = $version
$result.observed_roadmap.phase = $observedPhase
$result.observed_roadmap.status = $observedStatus
$result.observed_roadmap.task = $observedTask
$result.observed_roadmap.lifecycle.status = $lifecycleStatus
$result.observed_roadmap.extraction.phase_selection_strategy = $phaseCandidate.selected_strategy
$result.observed_roadmap.extraction.phase_count = $phaseCandidate.phase_count
$result.observed_roadmap.extraction.active_flags_seen = $phaseCandidate.active_flags_seen

$result.observed_roadmap.field_presence.version_found = -not [string]::IsNullOrWhiteSpace($version)
$result.observed_roadmap.field_presence.schema_version_found = -not [string]::IsNullOrWhiteSpace($schemaVersion)
$result.observed_roadmap.field_presence.lifecycle_status_found = -not [string]::IsNullOrWhiteSpace($lifecycleStatus)
$result.observed_roadmap.field_presence.phase_found = -not [string]::IsNullOrWhiteSpace($observedPhase)
$result.observed_roadmap.field_presence.status_found = -not [string]::IsNullOrWhiteSpace($observedStatus)
$result.observed_roadmap.field_presence.task_found = -not [string]::IsNullOrWhiteSpace($observedTask)
$result.observed_roadmap.field_presence.phases_found = $phaseCandidate.phases_found

$result.drift.has_drift_issues = $false
$result.drift.has_semver_drift = $false
$result.drift.has_authority_drift = $false
$result.drift.has_lifecycle_drift = $false
$result.drift.has_phase_status_drift = $false
$result.drift.has_content_drift = $false
$result.drift.comparator_available = $script:comparatorAvailable
$result.drift.comparator_evaluation_status = $script:comparatorEvaluationStatus
$result.drift.comparator_governance_significance = $script:comparatorGovernanceSignificance
$holdObserved = (
    ($result.observed_roadmap.status -and ([string]$result.observed_roadmap.status -match 'HOLD')) -or
    ($result.observed_roadmap.PSObject.Properties['lifecycle_status'] -and $result.observed_roadmap.lifecycle_status -and ([string]$result.observed_roadmap.lifecycle_status -match 'HOLD')) -or
    ($result.observed_roadmap.lifecycle -and $result.observed_roadmap.lifecycle.status -and ([string]$result.observed_roadmap.lifecycle.status -match 'HOLD'))
)
if (-not $holdObserved -and $script:comparatorSupportsControlled) {
    $result.governance_gate = 'GO'
    $result.operational_posture = 'CONTROLLED'
    $result.drift_status = 'NON_SIGNIFICANT'
    $result.overall_verdict = 'GO'
    $result.reason = 'Validated comparator evidence shows EVALUATED / NON_SIGNIFICANT.'
    $result.drift.drift_proven = $true
}
$result.drift.note = "Comparator evidence was evaluated with fail-closed semantics. If no valid comparator artifact is available or parseable, governance-significant drift is not proven and the result must remain HOLD / FAIL-CLOSED. This is not a green or no-drift certification."

try {
    Save-ResultJson -Result $result -Path $OutJsonPath
}
catch {
    Write-Warning ("Could not write result artifact: {0}" -f $_.Exception.Message)
}

$result | ConvertTo-Json -Depth 12 | Write-Output

Write-Section "Ready-to-paste PR summary"
Write-Host "Governance Gate Decision: $($result.governance_gate)"
Write-Host "Operational Posture: $($result.operational_posture)"
Write-Host "Drift Status: $($result.drift_status)"
Write-Host ""
Write-Host "Authority confirmation:"
Write-Host "- human-readable canonical roadmap: $($result.authority.canonical_human_phrase)"
Write-Host "- human-governed roadmap authority: $($result.authority.canonical_governed_authority_phrase)"
Write-Host "- ROADMAP_CURRENT.json authority linkage: $($result.authority.roadmap_authority_phrase)"
Write-Host "- MCP03/MCP-03 presence: $($result.authority.mcp03_present)"
Write-Host "- evidence rule confirmed: $($result.evidence.rule_confirmed)"
Write-Host ""
Write-Host "Observed roadmap:"
Write-Host "- Version: $($result.observed_roadmap.version)"
Write-Host "- Lifecycle.Status: $($result.observed_roadmap.lifecycle.status)"
Write-Host "- Selected Phase: $($result.observed_roadmap.phase)"
Write-Host "- Selected Status: $($result.observed_roadmap.status)"
Write-Host "- Selected Task: $($result.observed_roadmap.task)"
Write-Host "- Phase selection strategy: $($result.observed_roadmap.extraction.phase_selection_strategy)"
Write-Host ""
Write-Host "Reason:"
Write-Host $result.reason
Write-Host ""
Write-Host "Key rule:"
Write-Host $result.evidence.decision_rule
Write-Host ""
Write-Host "Disposition:"
if ($result.governance_gate -eq 'GO') {
    Write-Host "- PR is authorized to proceed under controlled governance posture"
    Write-Host "- Comparator evidence validated as NON_SIGNIFICANT"
} else {
    Write-Host "- PR remains on HOLD"
    Write-Host "- No green/go decision is authorized"
    Write-Host "- Restore authoritative drift producer or execute a validated replacement comparator"
}







