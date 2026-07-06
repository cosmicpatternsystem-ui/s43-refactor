$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location -LiteralPath $Repo

$Matrix = Join-Path $Repo "repo\contracts\AUTHORITY_CLASSIFICATION_MATRIX.yaml"
$Queue = Join-Path $Repo "repo\contracts\AUTHORITY_REVIEW_QUEUE.json"
if (-not (Test-Path -LiteralPath $Matrix)) { throw "Missing matrix: $Matrix" }
if (-not (Test-Path -LiteralPath $Queue)) { throw "Missing review queue: $Queue" }

$Warnings = New-Object System.Collections.Generic.List[string]
$Errors = New-Object System.Collections.Generic.List[string]

$Required = @(
  "repo\contracts\CANONICAL_SOURCES.yaml",
  "repo\contracts\PROJECT_CONSTITUTION.yaml",
  "repo\contracts\AUTHORITY_CLASSIFICATION_MATRIX.yaml",
  "repo\contracts\AUTHORITY_REVIEW_QUEUE.json",
  "docs\governance\SOURCE_OF_TRUTH_HIERARCHY.md",
  "docs\governance\SOURCE_OF_TRUTH_POLICY.md",
  "docs\governance\REPOSITORY_TRUTH.md",
  "docs\governance\ROADMAP_CONSTITUTION.md",
  "docs\governance\CANONICAL_ROADMAP_DECLARATION.md"
)

foreach ($Rel in $Required) {
    if (-not (Test-Path -LiteralPath (Join-Path $Repo $Rel))) {
        $Warnings.Add("MISSING_REQUIRED_CANDIDATE $Rel")
    }
}

$CanonicalRoadmap = "ROADMAP\ROADMAP_CANONICAL.md"
if (-not (Test-Path -LiteralPath (Join-Path $Repo $CanonicalRoadmap))) {
    $Errors.Add("MISSING_HUMAN_CANONICAL_ROADMAP $CanonicalRoadmap")
}

$RoadmapCandidates = @(
  "ROADMAP\ROADMAP_CANONICAL.md",
  "ROADMAP_CANONICAL.md",
  "docs\strategy\CANONICAL_ROADMAP.md",
  "docs\governance\CANONICAL_ROADMAP_DECLARATION.md",
  "docs\governance\ROADMAP_CONSTITUTION.md",
  "ROADMAP_CURRENT.json"
) | Where-Object { Test-Path -LiteralPath (Join-Path $Repo $_) }

if ($RoadmapCandidates.Count -gt 1) {
    $Warnings.Add("ROADMAP_AUTHORITY_REVIEW_RESOLVED_BY_MATRIX " + ($RoadmapCandidates -join " | "))
}

$ForbiddenPolicyPatterns = @(
  "AUDIT",
  "TRACEABILITY_",
  "BASELINE_PROTECTION_SNAPSHOT_",
  ".roadmap_archive",
  ".roadmap_backups",
  "backups",
  "runtime\backups",
  "_LOCAL_DEFERRED_AI_ARTIFACTS",
  "patch_log_"
)

$EvidenceWarnings = New-Object System.Collections.Generic.List[string]
$ScanFiles = Get-ChildItem -LiteralPath $Repo -Recurse -File -Force -ErrorAction SilentlyContinue |
    Where-Object {
        $_.FullName -notmatch "\\\.git\\" -and
        $_.FullName -notmatch "\\artifacts\\audits\\"
    }

foreach ($File in $ScanFiles) {
    $Rel = $File.FullName.Substring($Repo.Length).TrimStart("\")
    foreach ($Pat in $ForbiddenPolicyPatterns) {
        if ($Rel.StartsWith($Pat, [System.StringComparison]::OrdinalIgnoreCase) -or $Rel.Contains("\" + $Pat)) {
            $Text = ""
            try {
                if ($File.Length -lt 5242880) {
                    $Text = [System.IO.File]::ReadAllText($File.FullName)
                }
            } catch {
                $Text = ""
            }
            if ($Text -match "(?i)\b(canonical|constitution|source of truth|must override|authoritative|policy source)\b") {
                $EvidenceWarnings.Add("EVIDENCE_OR_ARCHIVE_AUTHORITY_LANGUAGE_CLASSIFIED $Rel")
            }
            break
        }
    }
}

foreach ($Warning in $EvidenceWarnings) {
    $Warnings.Add($Warning)
}

$Structured = [ordered]@{
    roadmap = @($Warnings | Where-Object { $_ -like "ROADMAP_AUTHORITY_REVIEW*" })
    evidence_or_archive = @($Warnings | Where-Object { $_ -like "EVIDENCE_OR_ARCHIVE_AUTHORITY_LANGUAGE*" })
    missing_candidates = @($Warnings | Where-Object { $_ -like "MISSING_REQUIRED_CANDIDATE*" })
    other = @($Warnings | Where-Object {
        $_ -notlike "ROADMAP_AUTHORITY_REVIEW*" -and
        $_ -notlike "EVIDENCE_OR_ARCHIVE_AUTHORITY_LANGUAGE*" -and
        $_ -notlike "MISSING_REQUIRED_CANDIDATE*"
    })
}

$Out = [ordered]@{
    matrix = "repo/contracts/AUTHORITY_CLASSIFICATION_MATRIX.yaml"
    review_queue = "repo/contracts/AUTHORITY_REVIEW_QUEUE.json"
    status = if ($Errors.Count -eq 0) { "PASS" } else { "FAIL" }
    errors = @($Errors)
    warnings = @($Warnings)
    structured_warnings = $Structured
    checked_at_utc = [DateTime]::UtcNow.ToString("o")
}

$Json = $Out | ConvertTo-Json -Depth 12
$ReportDir = Join-Path $Repo ("artifacts\audits\" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$ReportPath = Join-Path $ReportDir "authority_matrix_check.json"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($ReportPath, ($Json -replace "`r`n","`n" -replace "`r","`n"), $Utf8NoBom)

if ($Errors.Count -gt 0) {
    Write-Output "AUTHORITY_MATRIX_CHECK FAIL"
    Write-Output $ReportPath
    exit 1
}

Write-Output "AUTHORITY_MATRIX_CHECK PASS"
Write-Output $ReportPath
Write-Output ("WARNINGS " + $Warnings.Count)
Write-Output ("ROADMAP_WARNINGS " + @($Structured.roadmap).Count)
Write-Output ("EVIDENCE_ARCHIVE_WARNINGS " + @($Structured.evidence_or_archive).Count)
Write-Output ("MISSING_CANDIDATE_WARNINGS " + @($Structured.missing_candidates).Count)
Write-Output ("OTHER_WARNINGS " + @($Structured.other).Count)
exit 0