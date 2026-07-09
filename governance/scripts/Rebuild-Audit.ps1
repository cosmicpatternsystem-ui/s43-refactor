[CmdletBinding()]
param(
    [string]$RepoRoot = 'G:\s43_work\s43_g11_work',
    [string]$JsonPath,
    [switch]$Commit,
    [switch]$Push,
    [int]$MaxDepth = 6,
    [int]$MaxArrayItems = 25,
    [int]$MaxObjectProperties = 40,
    [int]$MaxStringLength = 300,
    [int]$MaxInlineProperties = 12
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-RepoRoot {
    param([string]$Candidate)
    if ([string]::IsNullOrWhiteSpace($Candidate)) {
        $Candidate = (Get-Location).Path
    }
    return [System.IO.Path]::GetFullPath($Candidate)
}

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Write-Utf8NoBomLfAtomic {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )

    $directory = Split-Path -Parent $Path
    Ensure-Directory -Path $directory

    $tempPath = [System.IO.Path]::Combine(
        $directory,
        ([System.IO.Path]::GetRandomFileName() + '.tmp')
    )

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $normalized = $Content -replace "`r`n", "`n"
    [System.IO.File]::WriteAllText($tempPath, $normalized, $utf8NoBom)

    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Force
    }

    Move-Item -LiteralPath $tempPath -Destination $Path -Force
}

function Get-ObjectProperties {
    param([object]$Value)

    if ($null -eq $Value) { return @() }

    if ($Value -is [System.Collections.IDictionary]) {
        $list = New-Object System.Collections.Generic.List[object]
        foreach ($key in $Value.Keys) {
            $list.Add([pscustomobject]@{
                Name  = [string]$key
                Value = $Value[$key]
            })
        }
        return @($list.ToArray())
    }

    if ($Value -is [string]) { return @() }
    if ($Value -is [System.Array]) { return @() }
    if ($Value -is [System.Collections.IEnumerable]) { return @() }

    if ($null -ne $Value.PSObject -and $null -ne $Value.PSObject.Properties) {
        $props = @(
            $Value.PSObject.Properties |
                Where-Object {
                    $_.MemberType -in @('NoteProperty', 'Property', 'AliasProperty', 'ScriptProperty')
                }
        )
        return $props
    }

    return @()
}

function Get-EnumerableItems {
    param([object]$Value)

    if ($null -eq $Value) { return @() }
    if ($Value -is [string]) { return @() }
    if ($Value -is [System.Collections.IDictionary]) { return @() }

    if ($Value -is [System.Array]) {
        return @($Value)
    }

    if ($Value -is [System.Collections.IEnumerable]) {
        $items = New-Object System.Collections.Generic.List[object]
        foreach ($item in $Value) {
            $items.Add($item)
        }
        return @($items.ToArray())
    }

    return @()
}

function Test-IsScalar {
    param([object]$Value)

    if ($null -eq $Value) { return $true }

    return (
        $Value -is [string] -or
        $Value -is [char] -or
        $Value -is [bool] -or
        $Value -is [byte] -or
        $Value -is [sbyte] -or
        $Value -is [int16] -or
        $Value -is [int32] -or
        $Value -is [int64] -or
        $Value -is [uint16] -or
        $Value -is [uint32] -or
        $Value -is [uint64] -or
        $Value -is [single] -or
        $Value -is [double] -or
        $Value -is [decimal] -or
        $Value -is [datetime] -or
        $Value -is [guid]
    )
}

function Format-Scalar {
    param(
        [object]$Value,
        [int]$MaxLength
    )

    if ($null -eq $Value) { return 'null' }

    if ($Value -is [datetime]) {
        return $Value.ToString('o')
    }

    $text = [string]$Value
    $text = $text -replace '\s+', ' '

    if ($text.Length -gt $MaxLength) {
        return $text.Substring(0, $MaxLength) + '...'
    }

    return $text
}

function Add-Line {
    param(
        [System.Collections.Generic.List[string]]$Lines,
        [string]$Text = ''
    )
    $Lines.Add($Text) | Out-Null
}

function Add-ScalarBullets {
    param(
        [System.Collections.Generic.List[string]]$Lines,
        [object[]]$Properties,
        [int]$MaxStringLength
    )

    if (@($Properties).Count -eq 0) { return }

    Add-Line -Lines $Lines -Text 'Scalar properties:'
    foreach ($prop in @($Properties)) {
        $valueText = Format-Scalar -Value $prop.Value -MaxLength $MaxStringLength
        Add-Line -Lines $Lines -Text ('- **{0}**: {1}' -f $prop.Name, $valueText)
    }
    Add-Line -Lines $Lines
}

function Render-Node {
    param(
        [string]$Name,
        [object]$Value,
        [int]$Depth,
        [System.Collections.Generic.List[string]]$Lines
    )

    if ($Depth -gt $MaxDepth) {
        Add-Line -Lines $Lines -Text ('- **{0}**: depth limit reached' -f $Name)
        return
    }

    if (Test-IsScalar -Value $Value) {
        Add-Line -Lines $Lines -Text ('- **{0}**: {1}' -f $Name, (Format-Scalar -Value $Value -MaxLength $MaxStringLength))
        return
    }

    $items = @(Get-EnumerableItems -Value $Value)
    if ($items.Count -gt 0) {
        Add-Line -Lines $Lines -Text ('## {0}' -f $Name)
        Add-Line -Lines $Lines
        Add-Line -Lines $Lines -Text '- **Kind**: Array'
        Add-Line -Lines $Lines -Text ('- **Count**: {0}' -f $items.Count)
        $sampleCount = [Math]::Min($items.Count, $MaxArrayItems)
        Add-Line -Lines $Lines -Text ('- **Sampled Items**: {0}' -f $sampleCount)
        Add-Line -Lines $Lines

        for ($i = 0; $i -lt $sampleCount; $i++) {
            $item = $items[$i]
            Add-Line -Lines $Lines -Text ('### Item {0}' -f $i)
            Add-Line -Lines $Lines

            if (Test-IsScalar -Value $item) {
                Add-Line -Lines $Lines -Text ('- **Value**: {0}' -f (Format-Scalar -Value $item -MaxLength $MaxStringLength))
                Add-Line -Lines $Lines
                continue
            }

            $itemProps = @(Get-ObjectProperties -Value $item)
            if ($itemProps.Count -gt 0) {
                Add-Line -Lines $Lines -Text '- **Kind**: Object'
                Add-Line -Lines $Lines -Text ('- **Property Count**: {0}' -f $itemProps.Count)
                Add-Line -Lines $Lines

                $scalarProps = @($itemProps | Where-Object { Test-IsScalar -Value $_.Value } | Select-Object -First $MaxInlineProperties)
                Add-ScalarBullets -Lines $Lines -Properties $scalarProps -MaxStringLength $MaxStringLength

                $nestedProps = @($itemProps | Where-Object { -not (Test-IsScalar -Value $_.Value) } | Select-Object -First $MaxInlineProperties)
                if ($nestedProps.Count -gt 0 -and $Depth -lt $MaxDepth) {
                    Add-Line -Lines $Lines -Text 'Nested properties sampled:'
                    foreach ($nested in $nestedProps) {
                        $kind = if (@(Get-EnumerableItems -Value $nested.Value).Count -gt 0) { 'array' } else { 'object' }
                        Add-Line -Lines $Lines -Text ('- `{0}` ({1})' -f $nested.Name, $kind)
                    }
                    Add-Line -Lines $Lines
                }
            }
            else {
                Add-Line -Lines $Lines -Text ('- **Value**: {0}' -f (Format-Scalar -Value $item -MaxLength $MaxStringLength))
                Add-Line -Lines $Lines
            }
        }

        if ($items.Count -gt $sampleCount) {
            Add-Line -Lines $Lines -Text ('- ... {0} additional items omitted' -f ($items.Count - $sampleCount))
            Add-Line -Lines $Lines
        }

        return
    }

    $props = @(Get-ObjectProperties -Value $Value)
    if ($props.Count -gt 0) {
        Add-Line -Lines $Lines -Text ('## {0}' -f $Name)
        Add-Line -Lines $Lines
        Add-Line -Lines $Lines -Text '- **Kind**: Object'
        Add-Line -Lines $Lines -Text ('- **Property Count**: {0}' -f $props.Count)
        Add-Line -Lines $Lines

        $scalarProps = @($props | Where-Object { Test-IsScalar -Value $_.Value } | Select-Object -First $MaxObjectProperties)
        Add-ScalarBullets -Lines $Lines -Properties $scalarProps -MaxStringLength $MaxStringLength

        $nestedProps = @($props | Where-Object { -not (Test-IsScalar -Value $_.Value) } | Select-Object -First $MaxObjectProperties)
        if ($nestedProps.Count -gt 0) {
            Add-Line -Lines $Lines -Text 'Nested sections:'
            foreach ($nested in $nestedProps) {
                Add-Line -Lines $Lines -Text ('- `{0}` ({1})' -f $nested.Name, $(if (@(Get-EnumerableItems -Value $nested.Value).Count -gt 0) { 'array' } else { 'object' }))
            }
            Add-Line -Lines $Lines

            foreach ($nested in $nestedProps) {
                if ($Depth + 1 -gt $MaxDepth) { continue }
                Render-Node -Name $nested.Name -Value $nested.Value -Depth ($Depth + 1) -Lines $Lines
            }
        }

        return
    }

    Add-Line -Lines $Lines -Text ('- **{0}**: {1}' -f $Name, (Format-Scalar -Value $Value -MaxLength $MaxStringLength))
}

function Invoke-Git {
    param(
        [string]$RepoRoot,
        [string[]]$Arguments
    )

    Push-Location $RepoRoot
    try {
        & git @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "git $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }
}

$RepoRoot = Resolve-RepoRoot -Candidate $RepoRoot
$reportsDir = Join-Path $RepoRoot 'governance\reports'

if (-not $JsonPath) {
    $candidate = Get-ChildItem -LiteralPath $reportsDir -Filter 'authority_audit_*.json' -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTimeUtc -Descending |
        Select-Object -First 1

    if (-not $candidate) {
        throw "No audit JSON file found in $reportsDir"
    }

    $JsonPath = $candidate.FullName
}

if (-not (Test-Path -LiteralPath $JsonPath)) {
    throw "JSON file not found: $JsonPath"
}

$jsonFile = Get-Item -LiteralPath $JsonPath
$raw = Get-Content -LiteralPath $jsonFile.FullName -Raw -Encoding UTF8
$data = $raw | ConvertFrom-Json

$timestamp = [DateTime]::UtcNow.ToString('yyyyMMdd_HHmmss')
$outPath = Join-Path $reportsDir ("authority_audit_{0}.md" -f $timestamp)

$lines = New-Object 'System.Collections.Generic.List[string]'
Add-Line -Lines $lines -Text '# Authority Audit Report'
Add-Line -Lines $lines
Add-Line -Lines $lines -Text ('- **Source JSON**: `{0}`' -f $jsonFile.Name)
Add-Line -Lines $lines -Text ('- **Generated UTC**: `{0}`' -f ([DateTime]::UtcNow.ToString('yyyy-MM-dd HH:mm:ss')))
Add-Line -Lines $lines -Text ('- **Source Size Bytes**: {0}' -f $jsonFile.Length)
Add-Line -Lines $lines -Text ('- **Max Depth**: {0}' -f $MaxDepth)
Add-Line -Lines $lines -Text ('- **Max Array Items**: {0}' -f $MaxArrayItems)
Add-Line -Lines $lines -Text ('- **Max Object Properties**: {0}' -f $MaxObjectProperties)
Add-Line -Lines $lines
Add-Line -Lines $lines -Text '## Top-Level Summary'
Add-Line -Lines $lines

$rootProps = @(Get-ObjectProperties -Value $data)
$rootScalarProps = @($rootProps | Where-Object { Test-IsScalar -Value $_.Value } | Select-Object -First $MaxInlineProperties)
foreach ($prop in $rootScalarProps) {
    Add-Line -Lines $lines -Text ('- **{0}**: {1}' -f $prop.Name, (Format-Scalar -Value $prop.Value -MaxLength $MaxStringLength))
}
Add-Line -Lines $lines

$rootNestedProps = @($rootProps | Where-Object { -not (Test-IsScalar -Value $_.Value) } | Select-Object -First $MaxObjectProperties)
foreach ($prop in $rootNestedProps) {
    Render-Node -Name $prop.Name -Value $prop.Value -Depth 1 -Lines $lines
    Add-Line -Lines $lines
}

Write-Utf8NoBomLfAtomic -Path $outPath -Content ($lines -join "`n")

Write-Host ("Generated report: {0}" -f $outPath)

if ($Commit -or $Push) {
    Invoke-Git -RepoRoot $RepoRoot -Arguments @('add', '--', $outPath)

    $statusOutput = & git -C $RepoRoot status --porcelain
    if ($LASTEXITCODE -ne 0) {
        throw 'git status --porcelain failed'
    }

    if ($statusOutput) {
        Invoke-Git -RepoRoot $RepoRoot -Arguments @('commit', '-m', ("governance: rebuild audit markdown {0}" -f $timestamp))
    }
    else {
        Write-Host 'No git changes detected; skipping commit.'
    }
}

if ($Push) {
    Invoke-Git -RepoRoot $RepoRoot -Arguments @('push')
}