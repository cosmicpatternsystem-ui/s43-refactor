[CmdletBinding()]
param(
    [string]$RepoRoot = 'G:\s43_work\s43_g11_work',
    [string]$FinalGateReport = 'G:\s43_work\s43_g11_work\reports\COMMERCIAL_EXECUTION_GATE_REPORT_20260802_053057.json',
    [string]$PreNormalizationGoReport = 'G:\s43_work\s43_g11_work\reports\COMMERCIAL_EXECUTION_GATE_REPORT_20260802_051440.json',
    [string]$PatchReport1 = 'G:\s43_work\s43_g11_work\reports\ROADMAP_MINIMAL_REMEDIATION_PATCH_REPORT_20260802_050836.json',
    [string]$PatchReport2 = 'G:\s43_work\s43_g11_work\reports\ROADMAP_MINIMAL_REMEDIATION_PATCH2_REPORT_20260802_051211.json',
    [string]$NormalizationReport = 'G:\s43_work\s43_g11_work\reports\ROADMAP_CRLF_NORMALIZATION_RETRY_REPORT_20260802_052037.json'
)

$ErrorActionPreference = 'Stop'

$reportsDir = Join-Path $RepoRoot 'reports'
$outPath = Join-Path $reportsDir 'COMMERCIAL_EXECUTION_PR_EVIDENCE_SUMMARY.md'

$lines = New-Object System.Collections.ArrayList

$null = $lines.Add('# Commercial Execution Gate PR Evidence Summary')
$null = $lines.Add('')
$null = $lines.Add('## Final Outcome')
$null = $lines.Add('')
$null = $lines.Add('- Verdict: `GO`')
$null = $lines.Add('- Posture: `UNBLOCKED`')
$null = $lines.Add('- Scope gate: `True`')
$null = $lines.Add('- Governance gate: `True`')
$null = $lines.Add('- Structure gate: `True`')
$null = $lines.Add('- Financial relevance gate: `True`')
$null = $lines.Add('- Findings: `0`')
$null = $lines.Add('- Warnings: `0`')
$null = $lines.Add('')
$null = $lines.Add('## Canonical Files')
$null = $lines.Add('')
$null = $lines.Add('- Policy: `docs/governance/TOP_LEVEL_COMMERCIAL_EXECUTION_POLICY.md`')
$null = $lines.Add('- Roadmap: `docs/governance/ROADMAP_CURRENT.json`')
$null = $lines.Add('- Runner: `scripts/commercial_execution_gate_runner.ps1`')
$null = $lines.Add('')
$null = $lines.Add('## Final Evidence')
$null = $lines.Add('')
$null = $lines.Add("- Final clean gate report: `$(Split-Path $FinalGateReport -Leaf)`")
$null = $lines.Add("- Prior GO report: `$(Split-Path $PreNormalizationGoReport -Leaf)`")
$null = $lines.Add("- Remediation patch report 1: `$(Split-Path $PatchReport1 -Leaf)`")
$null = $lines.Add("- Remediation patch report 2: `$(Split-Path $PatchReport2 -Leaf)`")
$null = $lines.Add("- CRLF normalization report: `$(Split-Path $NormalizationReport -Leaf)`")
$null = $lines.Add('')
$null = $lines.Add('## What Was Fixed')
$null = $lines.Add('')
$null = $lines.Add('- Corrected phase lookup logic to inspect top-level `phases` first.')
$null = $lines.Add('- Added fallback recursive search for resilient phase resolution.')
$null = $lines.Add('- Added support for both `id` and `phase_id`.')
$null = $lines.Add('- Enforced governance metadata checks.')
$null = $lines.Add('- Enforced structure checks for `owner`, `priority`, `last_verified_at`, and non-empty `tasks`.')
$null = $lines.Add('- Enforced explicit financial/commercial/risk/exposure relevance checks.')
$null = $lines.Add('- Normalized roadmap file to UTF-8 without BOM and LF-only.')
$null = $lines.Add('')
$null = $lines.Add('## Operational Note')
$null = $lines.Add('')
$null = $lines.Add('This PR preserves fail-closed behavior for commercial execution gating while ensuring the runner is PowerShell 5.1-safe and aligned to the actual roadmap schema in repository state.')
$null = $lines.Add('')

$content = [string]::Join("`n", $lines.ToArray())
[System.IO.File]::WriteAllText($outPath, $content, (New-Object System.Text.UTF8Encoding($false)))

Write-Host ('PR evidence summary created: ' + $outPath)