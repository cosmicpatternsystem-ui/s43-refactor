param(
    [Parameter(Mandatory=$true)]
    [string]$Path,
    
    [Parameter(Mandatory=$true)]
    [string]$Content,
    
    [Parameter(Mandatory=$false)]
    [string]$Operation = 'update',
    
    [Parameter(Mandatory=$false)]
    [string]$Phase = ''
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$startTime = Get-Date

# Calculate old state hash
$oldHash = 'init'
if (Test-Path $Path) {
    $oldContent = Get-Content -Path $Path -Raw -Encoding UTF8
    $oldHash = (Get-FileHash -InputStream ([System.IO.MemoryStream]::new([System.Text.Encoding]::UTF8.GetBytes($oldContent))) -Algorithm SHA256).Hash
}

$tempFile = "$Path.tmp"
try {
    # Write to temp
    Set-Content -Path $tempFile -Value $Content -Encoding UTF8 -NoNewline
    
    # Validate JSON
    $null = Get-Content -Path $tempFile -Raw -Encoding UTF8 | ConvertFrom-Json
    
    # Calculate new state hash
    $newContent = Get-Content -Path $tempFile -Raw -Encoding UTF8
    $newHash = (Get-FileHash -InputStream ([System.IO.MemoryStream]::new([System.Text.Encoding]::UTF8.GetBytes($newContent))) -Algorithm SHA256).Hash
    
    # Atomic rename
    Move-Item -Path $tempFile -Destination $Path -Force
    
    # Calculate duration
    $duration = [int]((Get-Date) - $startTime).TotalMilliseconds
    
    # Write journal entry
    & "$PSScriptRoot/Write-Journal.ps1" `
        -Operation $Operation `
        -Phase $Phase `
        -OldStateHash $oldHash `
        -NewStateHash $newHash `
        -Status 'success' `
        -DurationMs $duration
    
    Write-Output "[OK] Atomic write completed: $Path"
} catch {
    if (Test-Path $tempFile) { Remove-Item -Path $tempFile -Force }
    
    # Log failure to journal
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
