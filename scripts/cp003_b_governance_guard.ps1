param()

$ErrorActionPreference = "Stop"

Write-Host "== CP003-B governance guard ==" -ForegroundColor Cyan

$currentBranch = git branch --show-current
Write-Host "Branch: $currentBranch"

$dirty = git status --short
if ($dirty) {
    Write-Host ""
    Write-Host "Working tree is dirty:" -ForegroundColor Yellow
    $dirty
    throw "Refusing to continue."
}

$requiredTags = @(
    "s43-cp003-a-locked",
    "s43-cp003-b-start",
    "s43-cp003-b-charter-v1",
    "s43-cp003-b-insertion-map-v1",
    "s43-cp003-b-impact-assessment-v1",
    "s43-cp003-b-safety-gate-review-v1",
    "s43-cp003-b-rollback-plan-v1",
    "s43-cp003-b-test-plan-v1",
    "s43-cp003-b-readiness-review-v1",
    "s43-cp003-b-mutation-proposal-v1",
    "s43-cp003-b-archival-checkpoint-v1",
    "s43-cp003-b-approval-gate-template-v1",
    "s43-cp003-b-approval-record-generator-v1"
)

Write-Host ""
Write-Host "Tag check:" -ForegroundColor Cyan
foreach ($tag in $requiredTags) {
    git rev-parse --verify "refs/tags/$tag" | Out-Null
    $target = git rev-list -n 1 $tag
    Write-Host "OK  $tag  $target"
}

$protectedFiles = @(
    "s43_instrumented_LATEST.py",
    "11029.py",
    "s43_latest_refactor.py",
    "MY_S43_LATEST.py"
)

Write-Host ""
Write-Host "Protected baseline diff:" -ForegroundColor Cyan
$baselineDiff = git diff --name-status s43-cp003-a-locked..HEAD -- $protectedFiles
if ($baselineDiff) {
    $baselineDiff
    throw "Protected baseline drift detected."
} else {
    Write-Host "OK  no protected baseline drift"
}

Write-Host ""
Write-Host "Protected baseline scaffold scan:" -ForegroundColor Cyan
$scanMatches = Select-String -Path $protectedFiles -Pattern "cp003_scaffold" -SimpleMatch
if ($scanMatches) {
    $scanMatches
    throw "Unexpected cp003_scaffold wiring detected."
} else {
    Write-Host "OK  no cp003_scaffold wiring in protected baseline files"
}

Write-Host ""
Write-Host "Approval gate document:" -ForegroundColor Cyan
if (Test-Path ".\governance\CP003_B_APPROVAL_GATE_TEMPLATE.md") {
    Write-Host "OK  governance\CP003_B_APPROVAL_GATE_TEMPLATE.md"
} else {
    throw "Missing governance\CP003_B_APPROVAL_GATE_TEMPLATE.md"
}

Write-Host ""
$validatorScript = ".\scripts\cp003_b_approval_record_validator.ps1"
if (Test-Path $validatorScript) {
    & $validatorScript
} else {
    throw "Missing .\scripts\cp003_b_approval_record_validator.ps1"
}
Write-Host "Current ruling:" -ForegroundColor Cyan
Write-Host "SAFE  governance chain intact"
Write-Host "SAFE  runtime mutation absent"
Write-Host "SAFE  deny-by-default preserved"
Write-Host "BLOCK  any future mutation requires a separate completed approval record"


