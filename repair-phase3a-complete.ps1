if (-not $PSVersionTable.PSEdition -or $PSVersionTable.PSEdition -ne 'Core') {
    throw 'This script must be run with PowerShell Core (pwsh).'
}
& {
    Set-StrictMode -Version Latest
    $ErrorActionPreference = 'Stop'
    $ProgressPreference = 'SilentlyContinue'

    $SourcePath = Join-Path (Get-Location) 'asox-autopilot-phase3a-incomplete.txt'
    $OutputPath = Join-Path (Get-Location) 'asox-autopilot-phase3a.audit-only.ps1'
    $LockPath = $OutputPath + '.repair.lock'
    $ExpectedSourceSha256 = '75E922D109CE085078921DAE9F609DB9309E69D3F981AE042AE79ACFCE4D4434'
    $Utf8NoBom = New-Object System.Text.UTF8Encoding($false, $true)
    $LockStream = $null
    $TemporaryPath = $null

    function Write-Status {
        param([Parameter(Mandatory = $true)][string]$Text)

        try {
            [Console]::Out.WriteLine($Text)
        }
        catch {
            Write-Output $Text
        }
    }

    function Stop-Repair {
        param([Parameter(Mandatory = $true)][string]$Message)

        throw ('PHASE3A_REPAIR_FAILED: ' + $Message)
    }

    try {
        Write-Status 'ASO-X Phase 3A complete audit-only reconstruction'
        Write-Status ('Source: ' + $SourcePath)
        Write-Status ('Output: ' + $OutputPath)

        if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) {
            Stop-Repair ('Source file not found: ' + $SourcePath)
        }

        $LockStream = New-Object System.IO.FileStream(
            $LockPath,
            [System.IO.FileMode]::CreateNew,
            [System.IO.FileAccess]::Write,
            [System.IO.FileShare]::None
        )

        $LockPayload = (
            'PID=' + [string]$PID + "`n" +
            'UTC=' + [DateTime]::UtcNow.ToString('o') + "`n"
        )
        $LockBytes = $Utf8NoBom.GetBytes($LockPayload)
        $LockStream.Write($LockBytes, 0, $LockBytes.Length)
        $LockStream.Flush($true)

        $SourceBytes = [System.IO.File]::ReadAllBytes($SourcePath)

        $Hasher = [System.Security.Cryptography.SHA256]::Create()
        try {
            $SourceDigestBytes = $Hasher.ComputeHash($SourceBytes)
        }
        finally {
            $Hasher.Dispose()
        }

        $SourceSha256 = (
            [System.BitConverter]::ToString($SourceDigestBytes)
        ).Replace('-', '').ToUpperInvariant()

        if ($SourceSha256 -ne $ExpectedSourceSha256) {
            Stop-Repair (
                'Source SHA-256 mismatch. Expected=' +
                $ExpectedSourceSha256 +
                ' Actual=' +
                $SourceSha256
            )
        }

        Write-Status ('PASS source SHA-256: ' + $SourceSha256)

        $Utf8Offset = 0
        if (
            $SourceBytes.Length -ge 3 -and
            $SourceBytes[0] -eq 0xEF -and
            $SourceBytes[1] -eq 0xBB -and
            $SourceBytes[2] -eq 0xBF
        ) {
            $Utf8Offset = 3
        }

        try {
            $SourceText = $Utf8NoBom.GetString(
                $SourceBytes,
                $Utf8Offset,
                $SourceBytes.Length - $Utf8Offset
            )
        }
        catch {
            Stop-Repair ('Source is not strict UTF-8: ' + $_.Exception.Message)
        }

        $SourceText = $SourceText.Replace("`r`n", "`n").Replace("`r", "`n")

        $ForbiddenPatterns = @(
            '(?im)^\s*git(?:\.exe)?\s+push(?:\s|$)',
            '(?im)^\s*git(?:\.exe)?\s+merge(?:\s|$)',
            '(?im)^\s*git(?:\.exe)?\s+rebase(?:\s|$)',
            '(?im)^\s*git(?:\.exe)?\s+reset(?:\s|$)',
            '(?im)^\s*git(?:\.exe)?\s+clean(?:\s|$)',
            '(?im)^\s*git(?:\.exe)?\s+commit(?:\s|$)',
            '(?im)^\s*git(?:\.exe)?\s+tag(?:\s|$)',
            '(?im)^\s*git(?:\.exe)?\s+branch\s+(?:-D|-d|--delete)(?:\s|$)',
            '(?im)^\s*gh(?:\.exe)?\s+pr\s+merge(?:\s|$)',
            '(?im)^\s*gh(?:\.exe)?\s+repo\s+(?:delete|archive)(?:\s|$)',
            '(?im)^\s*gh(?:\.exe)?\s+release\s+(?:create|delete|edit)(?:\s|$)',
            '(?im)^\s*gh(?:\.exe)?\s+workflow\s+run(?:\s|$)',
            '(?im)^\s*gh(?:\.exe)?\s+api\b[^\r\n]*(?:--method|-X)\s*(?:POST|PUT|PATCH|DELETE)\b',
            '(?im)^\s*Invoke-RestMethod\b[^\r\n]*-Method\s+(?:POST|PUT|PATCH|DELETE)\b',
            '(?im)^\s*Invoke-WebRequest\b[^\r\n]*-Method\s+(?:POST|PUT|PATCH|DELETE)\b'
        )

        foreach ($ForbiddenPattern in $ForbiddenPatterns) {
            if ([regex]::IsMatch($SourceText, $ForbiddenPattern)) {
                Stop-Repair (
                    'Potential repository mutation detected. Pattern=' +
                    $ForbiddenPattern
                )
            }
        }

        Write-Status 'PASS mutation-command scan'

        $Tokens = $null
        $ParseErrors = $null

        [void][System.Management.Automation.Language.Parser]::ParseInput(
            $SourceText,
            [ref]$Tokens,
            [ref]$ParseErrors
        )

        $UnexpectedParseErrors = @(
            $ParseErrors |
                Where-Object {
                    $_.ErrorId -ne 'MissingEndCurlyBrace' -and
                    $_.ErrorId -ne 'MissingCatchOrFinally'
                }
        )

        if ($UnexpectedParseErrors.Count -gt 0) {
            $ErrorSummary = (
                $UnexpectedParseErrors |
                    ForEach-Object {
                        $_.ErrorId + ': ' + $_.Message
                    }
            ) -join ' | '

            Stop-Repair (
                'Source contains unsupported syntax damage: ' +
                $ErrorSummary
            )
        }

        $OpenCurlyCount = @(
            $Tokens |
                Where-Object {
                    [string]$_.Kind -eq 'LCurly' -or
                    [string]$_.Kind -eq 'AtCurly'
                }
        ).Count

        $CloseCurlyCount = @(
            $Tokens |
                Where-Object {
                    [string]$_.Kind -eq 'RCurly'
                }
        ).Count

        $CurlyBalance = $OpenCurlyCount - $CloseCurlyCount

        if ($CurlyBalance -lt 1) {
            Stop-Repair (
                'Expected at least the outer "& {" block to remain open. Balance=' +
                [string]$CurlyBalance
            )
        }

        $InsertionMarker = '    [System.IO.Directory]::CreateDirectory($EvidenceDir) | Out-Null'
        $InsertionIndex = $SourceText.IndexOf(
            $InsertionMarker,
            [System.StringComparison]::Ordinal
        )

        if ($InsertionIndex -lt 0) {
            Stop-Repair (
                'Main-script insertion marker not found: "' +
                $InsertionMarker +
                '"'
            )
        }

        $Prefix = $SourceText.Substring(0, $InsertionIndex)
        $MainBody = $SourceText.Substring($InsertionIndex)

        $Reconstructed = (
            $Prefix.TrimEnd("`n") +
            "`n`n" +
            $MainBody.TrimEnd("`n") +
            "`n"
        )

        $InternalClosureCount = $CurlyBalance - 1

        for (
            $ClosureIndex = 0;
            $ClosureIndex -lt $InternalClosureCount;
            $ClosureIndex++
        ) {
            $Reconstructed += "        }`n"
        }

        $TailLines = @(
            '    }'
            '    catch {'
            '        $UnhandledMessage = $_.Exception.Message'
            '        try {'
            '            Add-Gap `'
            '                -Severity BLOCKER `'
            '                -Control ''Audit execution'' `'
            '                -Finding (''Unhandled audit failure: '' + $UnhandledMessage) `'
            '                -Remediation ''Resolve the reported local or GitHub API failure and rerun the audit.'' `'
            '                -Evidence ''audit-summary.json'''
            '        }'
            '        catch {'
            '            Write-AsciiStatus (''[BLOCKER] Unhandled audit failure: '' + $UnhandledMessage)'
            '        }'
            '        $script:ASOXAuditExitCode = 2'
            '    }'
            ''
            '    if ($null -eq (Get-Variable -Name ASOXAuditExitCode -Scope Script -ErrorAction SilentlyContinue)) {'
            '        $script:ASOXAuditExitCode = 0'
            '    }'
            ''
            '    function Write-FinalAtomicText {'
            '        param('
            '            [Parameter(Mandatory = $true)][string]$Path,'
            '            [Parameter(Mandatory = $true)][string]$Value'
            '        )'
            ''
            '        $Parent = Split-Path -Parent $Path'
            '        if (-not (Test-Path -LiteralPath $Parent -PathType Container)) {'
            '            [void](New-Item -Path $Parent -ItemType Directory -Force)'
            '        }'
            ''
            '        $Temporary = Join-Path $Parent ('
            '            ''.'' + [IO.Path]::GetFileName($Path) + ''.tmp.'' +'
            '            [Guid]::NewGuid().ToString(''N'')'
            '        )'
            ''
            '        try {'
            '            [IO.File]::WriteAllText($Temporary, $Value, $Utf8NoBom)'
            ''
            '            if (Test-Path -LiteralPath $Path -PathType Leaf) {'
            '                try { [IO.File]::Replace([IO.Path]::GetFullPath($Temporary), [IO.Path]::GetFullPath($Path), $null, $true) } catch { if (Test-Path -LiteralPath $Path -PathType Leaf) { Remove-Item -LiteralPath $Path -Force }; Move-Item -LiteralPath $Temporary -Destination $Path -Force }'
            '            }'
            '            else {'
            '                Move-Item -LiteralPath $Temporary -Destination $Path -Force'
            '            }'
            '        }'
            '        finally {'
            '            if (Test-Path -LiteralPath $Temporary -PathType Leaf) {'
            '                Remove-Item -LiteralPath $Temporary -Force'
            '            }'
            '        }'
            '    }'
            ''
            '    try {'
            '        if (-not (Test-Path -LiteralPath $EvidenceDir -PathType Container)) {'
            '            [void](New-Item -Path $EvidenceDir -ItemType Directory -Force)'
            '        }'
            ''
            '        $GapsPath = Join-Path $EvidenceDir ''audit-gaps.json'''
            '        $ApiResultsPath = Join-Path $EvidenceDir ''api-results.json'''
            '        $SummaryPath = Join-Path $EvidenceDir ''audit-summary.json'''
            '        $ManifestPath = Join-Path $EvidenceDir ''sha256-manifest.json'''
            ''
            '        $GapsJson = @($Gaps) | ConvertTo-Json -Depth 20'
            '        $ApiResultsJson = @($ApiResults) | ConvertTo-Json -Depth 20'
            ''
            '        Write-FinalAtomicText -Path $GapsPath -Value ($GapsJson + "`n")'
            '        Write-FinalAtomicText -Path $ApiResultsPath -Value ($ApiResultsJson + "`n")'
            ''
            '        $SeverityCounts = [ordered]@{}'
            '        foreach ($SeverityGroup in @($Gaps | Group-Object -Property Severity)) {'
            '            $SeverityCounts[[string]$SeverityGroup.Name] = [int]$SeverityGroup.Count'
            '        }'
            ''
            '        $Summary = [ordered]@{'
            '            SchemaVersion = 1'
            '            Audit = ''ASO-X Autopilot Phase 3A'''
            '            Mode = ''audit-only'''
            '            Repository = $Repository'
            '            Branch = $Branch'
            '            GeneratedUtc = [DateTime]::UtcNow.ToString(''o'')'
            '            EvidenceDirectory = $EvidenceDir'
            '            GapCount = @($Gaps).Count'
            '            SeverityCounts = $SeverityCounts'
            '            ApiRequestCount = @($ApiResults).Count'
            '            ApiSuccessCount = @($ApiResults | Where-Object { $_.Success }).Count'
            '            ExitCode = [int]$script:ASOXAuditExitCode'
            '            RepositoryMutationPerformed = $false'
            '        }'
            ''
            '        Write-FinalAtomicText `'
            '            -Path $SummaryPath `'
            '            -Value (($Summary | ConvertTo-Json -Depth 20) + "`n")'
            ''
            '        $ManifestEntries = @('
            '            Get-ChildItem -LiteralPath $EvidenceDir -File |'
            '                Where-Object { $_.Name -ne ''sha256-manifest.json'' } |'
            '                Sort-Object -Property Name |'
            '                ForEach-Object {'
            '                    $FileHash = Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256'
            '                    [PSCustomObject]@{'
            '                        Name = $_.Name'
            '                        Length = [Int64]$_.Length'
            '                        SHA256 = $FileHash.Hash.ToUpperInvariant()'
            '                    }'
            '                }'
            '        )'
            ''
            '        $Manifest = [ordered]@{'
            '            SchemaVersion = 1'
            '            Algorithm = ''SHA-256'''
            '            GeneratedUtc = [DateTime]::UtcNow.ToString(''o'')'
            '            Files = $ManifestEntries'
            '        }'
            ''
            '        Write-FinalAtomicText `'
            '            -Path $ManifestPath `'
            '            -Value (($Manifest | ConvertTo-Json -Depth 20) + "`n")'
            ''
            '        Write-AsciiStatus (''PASS evidence directory: '' + $EvidenceDir)'
            '        Write-AsciiStatus (''PASS gap count: '' + [string]@($Gaps).Count)'
            '        Write-AsciiStatus (''PASS exit code: '' + [string]$script:ASOXAuditExitCode)'
            '    }'
            '    catch {'
            '        $script:ASOXAuditExitCode = 3'
            '        Write-AsciiStatus (''[BLOCKER] Final evidence generation failed: '' + $_.Exception.Message)'
            '    }'
            '}'
            ''
            'exit [int]$script:ASOXAuditExitCode'
        )

        $Reconstructed += (($TailLines -join "`n") + "`n")

        $FinalTokens = $null
        $FinalParseErrors = $null

        [void][System.Management.Automation.Language.Parser]::ParseInput(
            $Reconstructed,
            [ref]$FinalTokens,
            [ref]$FinalParseErrors
        )

        if ($FinalParseErrors.Count -ne 0) {
            $FinalErrorSummary = (
                $FinalParseErrors |
                    ForEach-Object {
                        $_.ErrorId + ': ' + $_.Message
                    }
            ) -join ' | '

            Stop-Repair (
                'Reconstructed script did not pass the parser: ' +
                $FinalErrorSummary
            )
        }

        foreach ($ForbiddenPattern in $ForbiddenPatterns) {
            if ([regex]::IsMatch($Reconstructed, $ForbiddenPattern)) {
                Stop-Repair (
                    'Reconstructed output failed mutation scan. Pattern=' +
                    $ForbiddenPattern
                )
            }
        }

        $OutputDirectory = Split-Path -Parent $OutputPath
        $TemporaryPath = Join-Path $OutputDirectory (
            '.' +
            [IO.Path]::GetFileName($OutputPath) +
            '.tmp.' +
            [Guid]::NewGuid().ToString('N')
        )

        [IO.File]::WriteAllText(
            $TemporaryPath,
            $Reconstructed,
            $Utf8NoBom
        )

        $VerificationBytes = [IO.File]::ReadAllBytes($TemporaryPath)

        if (
            $VerificationBytes.Length -ge 3 -and
            $VerificationBytes[0] -eq 0xEF -and
            $VerificationBytes[1] -eq 0xBB -and
            $VerificationBytes[2] -eq 0xBF
        ) {
            Stop-Repair 'Temporary output unexpectedly contains a UTF-8 BOM.'
        }

        $VerificationText = $Utf8NoBom.GetString($VerificationBytes)

        if ($VerificationText.Contains("`r")) {
            Stop-Repair 'Temporary output contains non-LF line endings.'
        }

        if (Test-Path -LiteralPath $OutputPath -PathType Leaf) {
            $BackupPath = (
                $OutputPath +
                '.pre-complete-repair.' +
                (Get-Date -Format 'yyyyMMdd-HHmmss') +
                '.bak'
            )

            try {
                [IO.File]::Replace(
                    [IO.Path]::GetFullPath($TemporaryPath),
                    [IO.Path]::GetFullPath($OutputPath),
                    [IO.Path]::GetFullPath($BackupPath),
                    $true
                )
            }
            catch {
                if (Test-Path -LiteralPath $OutputPath -PathType Leaf) {
                    Copy-Item -LiteralPath $OutputPath -Destination $BackupPath -Force
                    Remove-Item -LiteralPath $OutputPath -Force
                }
                Move-Item -LiteralPath $TemporaryPath -Destination $OutputPath -Force
            }

            $TemporaryPath = $null
            Write-Status ('Previous output backup: ' + $BackupPath)
        }
        else {
            Move-Item -LiteralPath $TemporaryPath -Destination $OutputPath -Force
            $TemporaryPath = $null
        }

        $OutputHash = (
            Get-FileHash -LiteralPath $OutputPath -Algorithm SHA256
        ).Hash.ToUpperInvariant()

        $WrittenText = [IO.File]::ReadAllText($OutputPath, $Utf8NoBom)
        $WrittenTokens = $null
        $WrittenErrors = $null

        [void][System.Management.Automation.Language.Parser]::ParseInput(
            $WrittenText,
            [ref]$WrittenTokens,
            [ref]$WrittenErrors
        )

        if ($WrittenErrors.Count -ne 0) {
            Stop-Repair 'Post-write parser verification failed.'
        }

        Write-Status 'PASS reconstruction completed'
        Write-Status 'PASS PowerShell parser verification'
        Write-Status 'PASS UTF-8 without BOM'
        Write-Status 'PASS LF-only line endings'
        Write-Status 'PASS audit-only mutation scan'
        Write-Status ('OUTPUT=' + $OutputPath)
        Write-Status ('SHA256=' + $OutputHash)
        Write-Status 'NOTE: Output was generated and verified, but not executed.'
    }
    finally {
        if ($null -ne $LockStream) {
            $LockStream.Dispose()
        }

        if (
            $null -ne $TemporaryPath -and
            (Test-Path -LiteralPath $TemporaryPath -PathType Leaf)
        ) {
            Remove-Item -LiteralPath $TemporaryPath -Force
        }

        if (Test-Path -LiteralPath $LockPath -PathType Leaf) {
            Remove-Item -LiteralPath $LockPath -Force
        }
    }
}
