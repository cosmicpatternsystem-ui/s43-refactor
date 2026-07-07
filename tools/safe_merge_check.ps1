$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$specPath = Join-Path $repoRoot "repo/contracts/SAFE_MERGE_AUTOMATION_SPEC.yaml"

$warnings = @()
$errors = @()

if (-not (Test-Path $specPath)) {
    $errors += "Missing SAFE_MERGE_AUTOMATION_SPEC.yaml"
} else {
    $spec = Get-Content -Raw -Encoding UTF8 $specPath

    $requiredTerms = @(
        "pr_only_mutation",
        "required_checks_green",
        "post_merge_audit_retained",
        "immutable_traceability",
        "artifacts/audits/"
    )

    foreach ($term in $requiredTerms) {
        if ($spec -notmatch [regex]::Escape($term)) {
            $errors += "Missing required safe-merge term: $term"
        }
    }
}

$result = [ordered]@{
    check = "SAFE_MERGE_AUTOMATION_CHECK"
    status = if ($errors.Count -eq 0) { "PASS" } else { "FAIL" }
    errors = $errors
    warnings = $warnings
    spec_path = "repo/contracts/SAFE_MERGE_AUTOMATION_SPEC.yaml"
}

$result | ConvertTo-Json -Depth 8

if ($errors.Count -gt 0) {
    exit 1
}

exit 0