[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $RepairPath,

    [Parameter(Mandatory = $true)]
    [string] $TargetPath,

    [Parameter(Mandatory = $false)]
    [string[]] $ImagePaths = @(),

    [Parameter(Mandatory = $false)]
    [string] $OutDir = ""
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

function Write-AsciiStatus {
    param([Parameter(Mandatory = $true)][string] $Message)

    $chars = New-Object System.Collections.Generic.List[char]
    foreach ($ch in $Message.ToCharArray()) {
        $code = [int][char]$ch
        if ($code -ge 32 -and $code -le 126) {
            [void]$chars.Add($ch)
        } else {
            [void]$chars.Add('?')
        }
    }

    Write-Host ([string]::new($chars.ToArray()))
}

function New-Utf8NoBomEncoding {
    New-Object System.Text.UTF8Encoding($false)
}

function Write-TextAtomic {
    param(
        [Parameter(Mandatory = $true)][string] $Path,
        [Parameter(Mandatory = $true)][string] $Text
    )

    $dir = [System.IO.Path]::GetDirectoryName($Path)
    if ([string]::IsNullOrWhiteSpace($dir)) {
        $dir = "."
    }

    if (-not [System.IO.Directory]::Exists($dir)) {
        [System.IO.Directory]::CreateDirectory($dir) | Out-Null
    }

    $tmp = Join-Path $dir ([System.IO.Path]::GetFileName($Path) + ".tmp." + [System.Guid]::NewGuid().ToString("N"))
    $enc = New-Utf8NoBomEncoding

    try {
        [System.IO.File]::WriteAllText($tmp, $Text, $enc)

        if (Test-Path -LiteralPath $Path) {
            Remove-Item -LiteralPath $Path -Force
        }

        Move-Item -LiteralPath $tmp -Destination $Path -Force
    } catch {
        if (Test-Path -LiteralPath $tmp) {
            Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
        }
        throw
    }
}

function Resolve-RequiredFile {
    param([Parameter(Mandatory = $true)][string] $Path)

    $resolved = Resolve-Path -LiteralPath $Path -ErrorAction Stop
    $full = $resolved.ProviderPath

    if (-not [System.IO.File]::Exists($full)) {
        throw "Required file not found: $Path"
    }

    $full
}

function Get-HashSha256 {
    param([Parameter(Mandatory = $true)][string] $Path)

    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        try {
            $hash = $sha.ComputeHash($stream)
            (($hash | ForEach-Object { $_.ToString("x2") }) -join "")
        } finally {
            $stream.Dispose()
        }
    } finally {
        $sha.Dispose()
    }
}

function Get-FileEncodingAndNewlineFacts {
    param([Parameter(Mandatory = $true)][string] $Path)

    $bytes = [System.IO.File]::ReadAllBytes($Path)
    $bom = "None"

    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        $bom = "UTF-8 BOM"
    } elseif ($bytes.Length -ge 2 -and $bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) {
        $bom = "UTF-16 LE BOM"
    } elseif ($bytes.Length -ge 2 -and $bytes[0] -eq 0xFE -and $bytes[1] -eq 0xFF) {
        $bom = "UTF-16 BE BOM"
    }

    $lf = 0
    $crlf = 0
    $crOnly = 0
    $i = 0

    while ($i -lt $bytes.Length) {
        if ($bytes[$i] -eq 13) {
            if (($i + 1) -lt $bytes.Length -and $bytes[$i + 1] -eq 10) {
                $crlf++
                $lf++
                $i += 2
            } else {
                $crOnly++
                $i++
            }
        } elseif ($bytes[$i] -eq 10) {
            $lf++
            $i++
        } else {
            $i++
        }
    }

    $nul = 0
    foreach ($b in $bytes) {
        if ($b -eq 0) {
            $nul++
        }
    }

    [pscustomobject]@{
        Bom                = $bom
        LfCount            = $lf
        CrlfCount          = $crlf
        CrOnlyCount        = $crOnly
        ContainsNulBytes   = ($nul -gt 0)
        NulByteCount       = $nul
        IsLikelyLfOnly     = ($lf -gt 0 -and $crlf -eq 0 -and $crOnly -eq 0)
        IsLikelyUtf8NoBom  = ($bom -eq "None" -and $nul -eq 0)
    }
}

function Read-AllLinesSafe {
    param([Parameter(Mandatory = $true)][string] $Path)

    $reader = New-Object System.IO.StreamReader($Path, $true)
    try {
        $items = New-Object System.Collections.Generic.List[string]
        while (-not $reader.EndOfStream) {
            [void]$items.Add($reader.ReadLine())
        }
        $items.ToArray()
    } finally {
        $reader.Dispose()
    }
}

function Get-PreviewText {
    param(
        [Parameter(Mandatory = $true)][string] $Path,
        [Parameter(Mandatory = $true)][int] $HeadCount,
        [Parameter(Mandatory = $true)][int] $TailCount
    )

    $lines = Read-AllLinesSafe -Path $Path
    $sb = New-Object System.Text.StringBuilder

    [void]$sb.AppendLine("FILE: $Path")
    [void]$sb.AppendLine("TOTAL_LINES: $($lines.Count)")
    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("----- FIRST $HeadCount LINES -----")

    $headMax = [Math]::Min($HeadCount, $lines.Count)
    for ($i = 0; $i -lt $headMax; $i++) {
        [void]$sb.AppendLine(("{0,6}: {1}" -f ($i + 1), $lines[$i]))
    }

    [void]$sb.AppendLine("")
    [void]$sb.AppendLine("----- LAST $TailCount LINES -----")

    $start = [Math]::Max(0, $lines.Count - $TailCount)
    for ($i = $start; $i -lt $lines.Count; $i++) {
        [void]$sb.AppendLine(("{0,6}: {1}" -f ($i + 1), $lines[$i]))
    }

    $sb.ToString()
}

function Search-Symbols {
    param(
        [Parameter(Mandatory = $true)][string] $Path,
        [Parameter(Mandatory = $true)][string[]] $Symbols
    )

    $lines = Read-AllLinesSafe -Path $Path
    $hits = New-Object System.Collections.Generic.List[object]

    for ($i = 0; $i -lt $lines.Count; $i++) {
        foreach ($symbol in $Symbols) {
            if ($lines[$i].Contains($symbol)) {
                [void]$hits.Add([pscustomobject]@{
                    File   = $Path
                    Line   = ($i + 1)
                    Symbol = $symbol
                    Text   = $lines[$i]
                })
            }
        }
    }

    $hits.ToArray()
}

function Get-ParseFacts {
    param([Parameter(Mandatory = $true)][string] $Path)

    $tokens = $null
    $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors)

    $tryAsts = @($ast.FindAll({
        param($node)
        $node -is [System.Management.Automation.Language.TryStatementAst]
    }, $true))

    $tryFacts = New-Object System.Collections.Generic.List[object]
    foreach ($t in $tryAsts) {
        [void]$tryFacts.Add([pscustomobject]@{
            StartLine   = $t.Extent.StartLineNumber
            StartColumn = $t.Extent.StartColumnNumber
            EndLine     = $t.Extent.EndLineNumber
            EndColumn   = $t.Extent.EndColumnNumber
            CatchCount  = @($t.CatchClauses).Count
            HasFinally  = ($null -ne $t.Finally)
        })
    }

    $errorFacts = New-Object System.Collections.Generic.List[object]
    foreach ($e in @($errors)) {
        [void]$errorFacts.Add([pscustomobject]@{
            Message     = $e.Message
            ErrorId     = $e.ErrorId
            StartLine   = $e.Extent.StartLineNumber
            StartColumn = $e.Extent.StartColumnNumber
            EndLine     = $e.Extent.EndLineNumber
            EndColumn   = $e.Extent.EndColumnNumber
            Text        = $e.Extent.Text
        })
    }

    [pscustomobject]@{
        ParseErrorCount   = @($errors).Count
        TokenCount        = @($tokens).Count
        TryStatementCount = @($tryAsts).Count
        ParseErrors       = $errorFacts.ToArray()
        TryStatements     = $tryFacts.ToArray()
    }
}

function Get-FileFacts {
    param([Parameter(Mandatory = $true)][string] $Path)

    $item = Get-Item -LiteralPath $Path -ErrorAction Stop
    $enc = Get-FileEncodingAndNewlineFacts -Path $Path

    [pscustomobject]@{
        Path              = $Path
        Name              = $item.Name
        LengthBytes       = $item.Length
        LastWriteTimeUtc  = $item.LastWriteTimeUtc.ToString("o")
        Sha256            = Get-HashSha256 -Path $Path
        Bom               = $enc.Bom
        LfCount           = $enc.LfCount
        CrlfCount         = $enc.CrlfCount
        CrOnlyCount       = $enc.CrOnlyCount
        ContainsNulBytes  = $enc.ContainsNulBytes
        NulByteCount      = $enc.NulByteCount
        IsLikelyLfOnly    = $enc.IsLikelyLfOnly
        IsLikelyUtf8NoBom = $enc.IsLikelyUtf8NoBom
    }
}

function ConvertTo-JsonSafe {
    param([Parameter(Mandatory = $true)] $Object)
    $Object | ConvertTo-Json -Depth 20
}

function Invoke-OptionalOcr {
    param(
        [Parameter(Mandatory = $true)][string] $ImagePath,
        [Parameter(Mandatory = $true)][string] $OutputPath
    )

    $tesseract = Get-Command tesseract -ErrorAction SilentlyContinue
    if ($null -eq $tesseract) {
        Write-TextAtomic -Path $OutputPath -Text "OCR_NOT_RUN: tesseract command was not found on this machine.`n"
        return [pscustomobject]@{
            ImagePath = $ImagePath
            OcrRan    = $false
            Reason    = "tesseract not found"
            Output    = $OutputPath
        }
    }

    $ocrText = & $tesseract.Source $ImagePath stdout 2>&1
    $text = ($ocrText -join [Environment]::NewLine)
    Write-TextAtomic -Path $OutputPath -Text $text

    [pscustomobject]@{
        ImagePath = $ImagePath
        OcrRan    = $true
        Reason    = ""
        Output    = $OutputPath
    }
}

try {
    $repairFull = Resolve-RequiredFile -Path $RepairPath
    $targetFull = Resolve-RequiredFile -Path $TargetPath

    $imageFullPaths = New-Object System.Collections.Generic.List[string]
    foreach ($img in $ImagePaths) {
        if (-not [string]::IsNullOrWhiteSpace($img)) {
            [void]$imageFullPaths.Add((Resolve-RequiredFile -Path $img))
        }
    }

    if ([string]::IsNullOrWhiteSpace($OutDir)) {
        $stamp = [DateTime]::UtcNow.ToString("yyyyMMdd_HHmmss")
        $OutDir = Join-Path (Get-Location).Path ("phase3a_evidence_" + $stamp)
    }

    [System.IO.Directory]::CreateDirectory($OutDir) | Out-Null

    $symbols = @(
        "ParseInput",
        "InternalClosureCount",
        "TailLines",
        "FinalOutput",
        "Reconstructed",
        "WriteAllText",
        "Move-Item",
        "Set-Content",
        "Out-File",
        "StreamWriter",
        "UTF8Encoding",
        "try",
        "catch",
        "finally",
        "throw",
        "exit"
    )

    Write-AsciiStatus "Collecting file facts..."
    $repairFacts = Get-FileFacts -Path $repairFull
    $targetFacts = Get-FileFacts -Path $targetFull

    Write-AsciiStatus "Collecting parser facts..."
    $repairParse = Get-ParseFacts -Path $repairFull
    $targetParse = Get-ParseFacts -Path $targetFull

    Write-AsciiStatus "Collecting previews..."
    Write-TextAtomic -Path (Join-Path $OutDir "repair_first80_last160.txt") -Text (Get-PreviewText -Path $repairFull -HeadCount 80 -TailCount 160)
    Write-TextAtomic -Path (Join-Path $OutDir "target_first80_last160.txt") -Text (Get-PreviewText -Path $targetFull -HeadCount 80 -TailCount 160)

    Write-AsciiStatus "Searching symbols..."
    $repairHits = Search-Symbols -Path $repairFull -Symbols $symbols
    $targetHits = Search-Symbols -Path $targetFull -Symbols $symbols

    $imageFacts = New-Object System.Collections.Generic.List[object]
    $ocrFacts = New-Object System.Collections.Generic.List[object]

    foreach ($imgPath in $imageFullPaths.ToArray()) {
        [void]$imageFacts.Add((Get-FileFacts -Path $imgPath))
        $ocrOut = Join-Path $OutDir (([System.IO.Path]::GetFileNameWithoutExtension($imgPath)) + ".ocr.txt")
        [void]$ocrFacts.Add((Invoke-OptionalOcr -ImagePath $imgPath -OutputPath $ocrOut))
    }

    $manifest = [pscustomobject]@{
        ToolName          = "collect-phase3a-evidence.ps1"
        ToolVersion       = "1.0.0"
        CollectedAtUtc    = [DateTime]::UtcNow.ToString("o")
        PowerShellVersion = $PSVersionTable.PSVersion.ToString()
        Platform          = [Environment]::OSVersion.VersionString
        RepairFile        = $repairFacts
        TargetFile        = $targetFacts
        ImageFiles        = $imageFacts.ToArray()
        RepairParse       = $repairParse
        TargetParse       = $targetParse
        RepairSymbolHits  = $repairHits
        TargetSymbolHits  = $targetHits
        OcrResults        = $ocrFacts.ToArray()
    }

    Write-TextAtomic -Path (Join-Path $OutDir "manifest.json") -Text ((ConvertTo-JsonSafe -Object $manifest) + [Environment]::NewLine)
    Write-TextAtomic -Path (Join-Path $OutDir "repair_symbol_hits.json") -Text ((ConvertTo-JsonSafe -Object $repairHits) + [Environment]::NewLine)
    Write-TextAtomic -Path (Join-Path $OutDir "target_symbol_hits.json") -Text ((ConvertTo-JsonSafe -Object $targetHits) + [Environment]::NewLine)
    Write-TextAtomic -Path (Join-Path $OutDir "repair_parse.json") -Text ((ConvertTo-JsonSafe -Object $repairParse) + [Environment]::NewLine)
    Write-TextAtomic -Path (Join-Path $OutDir "target_parse.json") -Text ((ConvertTo-JsonSafe -Object $targetParse) + [Environment]::NewLine)

    $report = New-Object System.Text.StringBuilder
    [void]$report.AppendLine("PHASE 3A EVIDENCE REPORT")
    [void]$report.AppendLine("CollectedAtUtc: $([DateTime]::UtcNow.ToString("o"))")
    [void]$report.AppendLine("")
    [void]$report.AppendLine("RepairPath: $repairFull")
    [void]$report.AppendLine("RepairSha256: $($repairFacts.Sha256)")
    [void]$report.AppendLine("RepairLengthBytes: $($repairFacts.LengthBytes)")
    [void]$report.AppendLine("RepairBom: $($repairFacts.Bom)")
    [void]$report.AppendLine("RepairLfCount: $($repairFacts.LfCount)")
    [void]$report.AppendLine("RepairCrlfCount: $($repairFacts.CrlfCount)")
    [void]$report.AppendLine("RepairCrOnlyCount: $($repairFacts.CrOnlyCount)")
    [void]$report.AppendLine("RepairParseErrorCount: $($repairParse.ParseErrorCount)")
    [void]$report.AppendLine("RepairTryStatementCount: $($repairParse.TryStatementCount)")
    [void]$report.AppendLine("")
    [void]$report.AppendLine("TargetPath: $targetFull")
    [void]$report.AppendLine("TargetSha256: $($targetFacts.Sha256)")
    [void]$report.AppendLine("TargetLengthBytes: $($targetFacts.LengthBytes)")
    [void]$report.AppendLine("TargetBom: $($targetFacts.Bom)")
    [void]$report.AppendLine("TargetLfCount: $($targetFacts.LfCount)")
    [void]$report.AppendLine("TargetCrlfCount: $($targetFacts.CrlfCount)")
    [void]$report.AppendLine("TargetCrOnlyCount: $($targetFacts.CrOnlyCount)")
    [void]$report.AppendLine("TargetParseErrorCount: $($targetParse.ParseErrorCount)")
    [void]$report.AppendLine("TargetTryStatementCount: $($targetParse.TryStatementCount)")
    [void]$report.AppendLine("")
    [void]$report.AppendLine("ImageCount: $($imageFacts.Count)")

    Write-TextAtomic -Path (Join-Path $OutDir "report.txt") -Text $report.ToString()

    $zipPath = $OutDir.TrimEnd('\', '/') + ".zip"
    $compress = Get-Command Compress-Archive -ErrorAction SilentlyContinue

    if ($null -ne $compress) {
        if (Test-Path -LiteralPath $zipPath) {
            Remove-Item -LiteralPath $zipPath -Force
        }
        Compress-Archive -Path (Join-Path $OutDir "*") -DestinationPath $zipPath -Force -ErrorAction Stop

        if (-not (Test-Path -LiteralPath $zipPath)) {
            throw "Evidence zip was reported as created, but does not exist: $zipPath"
        }

        $zipItem = Get-Item -LiteralPath $zipPath -ErrorAction Stop
        if ($zipItem.Length -le 0) {
            throw "Evidence zip is empty: $zipPath"
        }

        Write-AsciiStatus "Evidence zip created:"
        Write-AsciiStatus $zipItem.FullName
    } else {
        Write-AsciiStatus "Compress-Archive not available. Evidence directory created:"
        Write-AsciiStatus $OutDir
    }

    Write-AsciiStatus "Done. Upload the evidence zip or directory contents."
} catch {
    Write-AsciiStatus "FAILED"
    Write-AsciiStatus $_.Exception.Message
    throw
}

