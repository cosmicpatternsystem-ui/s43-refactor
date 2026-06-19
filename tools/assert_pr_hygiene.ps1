$ErrorActionPreference = "Stop"

$requiredFiles = @(
  ".github/CODEOWNERS",
  ".github/pull_request_template.md",
  ".github/ISSUE_TEMPLATE/bug_report.yml",
  ".github/ISSUE_TEMPLATE/automation_request.yml",
  ".github/ISSUE_TEMPLATE/documentation_request.yml",
  ".github/ISSUE_TEMPLATE/config.yml"
)

$requiredPhrases = @(
  @{
    File = ".github/CODEOWNERS"
    Phrase = "* @cosmicpatternsystem-ui"
  },
  @{
    File = ".github/pull_request_template.md"
    Phrase = "## Summary"
  },
  @{
    File = ".github/pull_request_template.md"
    Phrase = "## Change Type"
  },
  @{
    File = ".github/pull_request_template.md"
    Phrase = "## Safety Checklist"
  },
  @{
    File = ".github/pull_request_template.md"
    Phrase = "## Validation Evidence"
  },
  @{
    File = ".github/pull_request_template.md"
    Phrase = "## Risk Assessment"
  },
  @{
    File = ".github/ISSUE_TEMPLATE/bug_report.yml"
    Phrase = "name: Bug report"
  },
  @{
    File = ".github/ISSUE_TEMPLATE/automation_request.yml"
    Phrase = "name: Automation request"
  },
  @{
    File = ".github/ISSUE_TEMPLATE/documentation_request.yml"
    Phrase = "name: Documentation or policy request"
  },
  @{
    File = ".github/ISSUE_TEMPLATE/config.yml"
    Phrase = "blank_issues_enabled: true"
  }
)

foreach ($file in $requiredFiles) {
  if (-not (Test-Path -LiteralPath $file)) {
    Write-Host "FAIL: Missing required PR hygiene file: $file"
    exit 1
  }

  Write-Host "PASS: Required file exists: $file"
}

foreach ($check in $requiredPhrases) {
  $file = $check.File
  $phrase = $check.Phrase

  $content = Get-Content -LiteralPath $file -Raw

  if ($content -notlike "*$phrase*") {
    Write-Host "FAIL: Missing required phrase in $file"
    Write-Host "Phrase: $phrase"
    exit 1
  }

  Write-Host "PASS: Required phrase exists in $file"
}

Write-Host "PR HYGIENE GATE: PASS"
