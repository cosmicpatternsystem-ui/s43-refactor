$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root
$target = Join-Path $root "s43_instrumented_LATEST.py"
if (!(Test-Path -LiteralPath $target)) { throw "TARGET_NOT_FOUND" }
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backup = Join-Path $root ("s43_instrumented_LATEST.py.bak_translate_" + $timestamp)
Copy-Item -LiteralPath $target -Destination $backup -Force
$content = Get-Content -LiteralPath $target -Raw -Encoding UTF8
if ($content -match 'API_MESSAGE_TRANSLATIONS\s*=\s*\{') {
    Write-Host "SKIP_ALREADY_PATCHED"
    Write-Host $backup
    exit 0
}
$translationBlock = ""
$translationBlock += "`r`nAPI_MESSAGE_TRANSLATIONS = {`r`n"
$translationBlock += '    "\u062A\u0648\u06A9\u0646 \u0646\u0627\u0645\u0639\u062A\u0628\u0631": "Invalid token",`r`n'
$translationBlock += '    "\u062F\u0633\u062A\u0631\u0633\u06CC \u063A\u06CC\u0631\u0645\u062C\u0627\u0632": "Unauthorized access",`r`n'
$translationBlock += '    "\u062E\u0637\u0627\u06CC \u0633\u0631\u0648\u0631": "Server error",`r`n'
$translationBlock += '    "\u0627\u0637\u0644\u0627\u0639\u0627\u062A \u06CC\u0627\u0641\u062A \u0646\u0634\u062F": "No data found",`r`n'
$translationBlock += '    "\u062F\u0631\u062E\u0648\u0627\u0633\u062A \u0646\u0627\u0645\u0639\u062A\u0628\u0631": "Invalid request",`r`n'
$translationBlock += '    "\u0646\u0634\u0633\u062A \u0645\u0646\u0642\u0636\u06CC \u0634\u062F\u0647 \u0627\u0633\u062A": "Session expired",`r`n'
$translationBlock += '    "\u0644\u0637\u0641\u0627\u064B \u062F\u0648\u0628\u0627\u0631\u0647 \u0648\u0627\u0631\u062F \u0634\u0648\u06CC\u062F": "Please sign in again",`r`n'
$translationBlock += '    "\u06A9\u0627\u0631\u0628\u0631 \u06CC\u0627\u0641\u062A \u0646\u0634\u062F": "User not found",`r`n'
$translationBlock += '    "\u06A9\u062F \u062A\u0623\u06CC\u06CC\u062F \u0646\u0627\u0645\u0639\u062A\u0628\u0631 \u0627\u0633\u062A": "Invalid verification code",`r`n'
$translationBlock += '    "\u0645\u0648\u062C\u0648\u062F\u06CC \u06A9\u0627\u0641\u06CC \u0646\u06CC\u0633\u062A": "Insufficient balance"`r`n'
$translationBlock += '}`r`n`r`ndef translate_api_message(message):`r`n    if not isinstance(message, str):`r`n        return message`r`n    normalized = message.strip()`r`n    for fa_text, en_text in API_MESSAGE_TRANSLATIONS.items():`r`n        if fa_text in normalized:`r`n            normalized = normalized.replace(fa_text, en_text)`r`n    return normalized`r`n'
$importPattern = '(?ms)\A((?:[ \t]*(?:from|import)\b.*\r?\n)+)'
if ([regex]::IsMatch($content, $importPattern)) {
    $content = [regex]::Replace($content, $importPattern, { param($m) $m.Groups[1].Value + "`r`n" + $translationBlock }, 1)
} else {
    $content = $translationBlock + "`r`n" + $content
}
$patterns = @(
    '(?<expr>\bresponse_json\.get\(\s*["'']message["'']\s*,\s*["'']{0,1}["'']{0,1}\s*\))',
    '(?<expr>\bresponse\.get\(\s*["'']message["'']\s*,\s*["'']{0,1}["'']{0,1}\s*\))',
    '(?<expr>\bdata\.get\(\s*["'']message["'']\s*,\s*["'']{0,1}["'']{0,1}\s*\))',
    '(?<expr>\berror\.get\(\s*["'']message["'']\s*,\s*["'']{0,1}["'']{0,1}\s*\))',
    '(?<expr>\bresponse_json\.get\(\s*["'']error["'']\s*,\s*\{\s*\}\s*\)\.get\(\s*["'']message["'']\s*,\s*["'']{0,1}["'']{0,1}\s*\))',
    '(?<expr>\bresponse\.get\(\s*["'']error["'']\s*,\s*\{\s*\}\s*\)\.get\(\s*["'']message["'']\s*,\s*["'']{0,1}["'']{0,1}\s*\))',
    '(?<expr>\bdata\.get\(\s*["'']error["'']\s*,\s*\{\s*\}\s*\)\.get\(\s*["'']message["'']\s*,\s*["'']{0,1}["'']{0,1}\s*\))'
)
foreach ($pattern in $patterns) {
    $content = [regex]::Replace($content, $pattern, {
        param($m)
        $expr = $m.Groups["expr"].Value
        if ($expr -match 'translate_api_message\s*\(') { return $expr }
        return "translate_api_message($expr)"
    })
}
Set-Content -LiteralPath $target -Value $content -Encoding UTF8
$report = Join-Path $root ("PATCH_TRANSLATE_REPORT_" + $timestamp + ".txt")
$reportLines = @(
    "PATCH_APPLIED",
    ("Target: " + $target),
    ("Backup: " + $backup),
    ("Timestamp: " + $timestamp)
)
Set-Content -LiteralPath $report -Value $reportLines -Encoding UTF8
Write-Host "PATCH_APPLIED"
Write-Host ("Target: " + $target)
Write-Host ("Backup: " + $backup)
Write-Host ("Report: " + $report)
