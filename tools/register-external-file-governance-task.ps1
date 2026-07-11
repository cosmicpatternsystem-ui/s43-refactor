[CmdletBinding()]
param(
    [string]$ProjectRoot = 'G:\s43_work\s43_g11_work',
    [string]$TaskName = 'S43 External File Governance',
    [string]$DailyAt = '21:00'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Runner = Join-Path $ProjectRoot 'tools\run-external-file-governance.ps1'
if (-not (Test-Path -LiteralPath $Runner)) {
    throw "Missing runner script: $Runner"
}

$Action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`" -ProjectRoot `"$ProjectRoot`""
$Trigger = New-ScheduledTaskTrigger -Daily -At $DailyAt
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description 'Audits, imports, and manifests project-related files found outside the official project root.' -Force | Out-Null
Write-Output $TaskName
