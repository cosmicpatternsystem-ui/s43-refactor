param(
    [Parameter(Mandatory=$true)]
    [string]$Path,

    [Parameter(Mandatory=$true)]
    [string]$Content,

    [Parameter(Mandatory=$false)]
    [ValidateSet('update','restore','checkpoint','init')]
    [string]$Operation = 'update',

    [Parameter(Mandatory=$false)]
    [string]$Phase = ''
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$startTime = Get-Date

# Resolve target path using PowerShell provider semantics before using .NET file APIs.
# This prevents relative paths from being resolved against the process CWD (for example C:\Windows\system32).
$targetPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)
$targetParent = Split-Path -Path $targetPath -Parent
$targetName = Split-Path -Path $targetPath -Leaf

if ([string]::IsNullOrWhiteSpace($targetParent)) {
    $targetParent = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath('.')
}

if (-not (Test-Path -LiteralPath $targetParent)) {
    New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
}

# Calculate old state hash
$oldHash = 'none'
if (Test-Path -LiteralPath $targetPath) {
    $oldContent = Get-Content -LiteralPath $targetPath -Raw -Encoding UTF8
    $oldBytes = [System.Text.Encoding]::UTF8.GetBytes($oldContent)
    $oldHash = (Get-FileHash -InputStream ([System.IO.MemoryStream]::new($oldBytes)) -Algorithm SHA256).Hash
}

$tempFile = Join-Path $targetParent (".{0}.{1}.tmp" -f $targetName, [System.Guid]::NewGuid().ToString('N'))

try {
    # Write temp as UTF-8 no BOM
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($tempFile, $Content, $utf8NoBom)

    # Validate JSON before replace
    $null = Get-Content -LiteralPath $tempFile -Raw -Encoding UTF8 | ConvertFrom-Json

    # Calculate new state hash
    $newContent = Get-Content -LiteralPath $tempFile -Raw -Encoding UTF8
    $newBytes = [System.Text.Encoding]::UTF8.GetBytes($newContent)
    $newHash = (Get-FileHash -InputStream ([System.IO.MemoryStream]::new($newBytes)) -Algorithm SHA256).Hash

    # Replace target from temp file in the same directory.
    Move-Item -LiteralPath $tempFile -Destination $targetPath -Force

    $duration = [int]((Get-Date) - $startTime).TotalMilliseconds

    & "$PSScriptRoot/Write-Journal.ps1" `
        -Operation $Operation `
        -Phase $Phase `
        -OldStateHash $oldHash `
        -NewStateHash $newHash `
        -Status 'success' `
        -DurationMs $duration

    Write-Output "[OK] Atomic write completed: $targetPath"
} catch {
    if (Test-Path -LiteralPath $tempFile) {
        Remove-Item -LiteralPath $tempFile -Force
    }

    $duration = [int]((Get-Date) - $startTime).TotalMilliseconds

    & "$PSScriptRoot/Write-Journal.ps1" `
        -Operation $Operation `
        -Phase $Phase `
        -OldStateHash $oldHash `
        -NewStateHash 'failed' `
        -Status 'failed' `
        -DurationMs $duration -ErrorAction SilentlyContinue

    throw "Atomic write failed: $_"
}
