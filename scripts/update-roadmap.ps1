param()

$ErrorActionPreference = "Stop"

$phaseFiles = Get-ChildItem -Path . -Filter "PHASE_*.md" -File | Sort-Object Name

$phases = @()
foreach ($file in $phaseFiles) {
  $content = Get-Content $file.FullName -Raw

  $status = "recorded"
  if ($content -match "(?i)\bCOMPLETE\b") {
    $status = "complete"
  }

  $noOperationalChange =
    ($content -match "(?i)documentation-only") -or
    ($content -match "(?i)no-op") -or
    (
      ($content -match "(?i)no code") -and
      ($content -match "(?i)no runtime") -and
      ($content -match "(?i)no deployment")
    )

  $phases += [ordered]@{
    file = $file.Name
    status = $status
    documentation_only = [bool]$noOperationalChange
  }
}

$roadmap = [ordered]@{
  schema_version = 1
  source_of_truth = "repository phase documents"
  generated_by = "scripts/update-roadmap.ps1"
  enforcement_model = "generated-and-diff-enforced-in-pr"
  updated_at_utc = "GENERATED"
  phase_count = $phases.Count
  phases = $phases
}

$json = $roadmap | ConvertTo-Json -Depth 20
$json = $json -replace "`r`n", "`n"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path (Get-Location) "ROADMAP_CURRENT.json"), $json + "`n", $utf8NoBom)

Write-Host "ROADMAP_CURRENT.json regenerated from PHASE_*.md files"
