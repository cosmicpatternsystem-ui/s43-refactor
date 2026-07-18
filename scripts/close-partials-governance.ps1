[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$Owner = "cosmicpatternsystem-ui",
    [string]$Repo = "s43-refactor",
    [string]$MainBranch = "main",
    [switch]$ApplyProtection,
    [switch]$DeleteMarkedBranches,
    [switch]$IncludeMergedSignal
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Require-Command {
    param([string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Content
    )

    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
    }

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

function Save-TextSnapshot {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Content
    )

    if ($WhatIfPreference) {
        Write-Host "What if: Would write file $Path"
        return
    }

    Write-Utf8NoBom -Path $Path -Content $Content
}

Require-Command git
Require-Command gh

$repoSlug = "$Owner/$Repo"
$root = git rev-parse --show-toplevel 2>$null

if (-not $root) {
    throw "Not inside a git repository."
}

Set-Location $root

$artifactsDir = Join-Path $root "artifacts"
if (-not (Test-Path $artifactsDir)) {
    New-Item -ItemType Directory -Path $artifactsDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$inventoryCsv = Join-Path $artifactsDir "remote-branch-lifecycle-review.csv"
$protectionBefore = Join-Path $artifactsDir "main-branch-protection-before-$timestamp.json"
$protectionAfter = Join-Path $artifactsDir "main-branch-protection-after-$timestamp.json"
$protectionUpdateJson = Join-Path $artifactsDir "main-protection-update-$timestamp.json"

Write-Host "Repository: $repoSlug"
Write-Host "Root: $root"
Write-Host ""

Write-Host "Fetching latest remote refs..."
git fetch --all --prune | Out-Host

Write-Host "Capturing current branch protection..."
try {
    $beforeRaw = gh api "repos/$repoSlug/branches/$MainBranch/protection"
    Save-TextSnapshot -Path $protectionBefore -Content $beforeRaw
    Write-Host "Protection before snapshot: $protectionBefore"
} catch {
    Write-Warning "Could not capture current protection. Continuing. Error: $($_.Exception.Message)"
}

Write-Host ""
Write-Host "Collecting remote branches..."

$branchPagesRaw = gh api --paginate --slurp "repos/$repoSlug/branches?per_page=100"
$branchPages = $branchPagesRaw | ConvertFrom-Json
$branches = @()

foreach ($page in $branchPages) {
    foreach ($branch in $page) {
        $branches += $branch
    }
}

if (-not $branches -or $branches.Count -eq 0) {
    throw "No remote branches returned by GitHub API."
}

$openPrHeads = @{}

try {
    $openPrs = gh pr list --repo $repoSlug --state open --limit 200 --json headRefName,number,title | ConvertFrom-Json
    foreach ($pr in $openPrs) {
        $openPrHeads[$pr.headRefName] = $pr
    }
} catch {
    Write-Warning "Could not retrieve open PR list. Continuing without PR linkage. Error: $($_.Exception.Message)"
}

function Get-BranchClassification {
    param(
        [string]$BranchName,
        [bool]$Protected,
        [bool]$HasOpenPr,
        [Nullable[bool]]$MergedToMain
    )

    if ($BranchName -eq $MainBranch) {
        return @{
            Lifecycle = "keep"
            Reason = "primary protected branch"
        }
    }

    if ($Protected) {
        return @{
            Lifecycle = "keep"
            Reason = "protected remote branch"
        }
    }

    if ($HasOpenPr) {
        return @{
            Lifecycle = "keep"
            Reason = "has open pull request"
        }
    }

    if ($BranchName -match '^release/' -or
        $BranchName -match '^hotfix/' -or
        $BranchName -match '^support/' -or
        $BranchName -match '^phase\d+' -or
        $BranchName -match '^gov' -or
        $BranchName -match '^governance/' -or
        $BranchName -match '^baseline/' -or
        $BranchName -match '^roadmap') {

        if ($MergedToMain -eq $true) {
            return @{
                Lifecycle = "archive"
                Reason = "historical governance or release branch already merged"
            }
        }

        return @{
            Lifecycle = "keep"
            Reason = "named governance or release branch"
        }
    }

    if ($BranchName -match '^archive/' -or
        $BranchName -match '^backup/' -or
        $BranchName -match '^safety/') {
        return @{
            Lifecycle = "archive"
            Reason = "archive or safety branch"
        }
    }

    if ($BranchName -match '^feature/' -or
        $BranchName -match '^fix/' -or
        $BranchName -match '^chore/' -or
        $BranchName -match '^work/' -or
        $BranchName -match '^review/' -or
        $BranchName -match '^auto/' -or
        $BranchName -match '^docs/' -or
        $BranchName -match '^cp\d+' -or
        $BranchName -match '^mcp\d+') {

        if ($MergedToMain -eq $true) {
            return @{
                Lifecycle = "delete"
                Reason = "work branch already merged and no open PR"
            }
        }

        return @{
            Lifecycle = "archive"
            Reason = "unprotected work branch not yet confirmed obsolete"
        }
    }

    if ($MergedToMain -eq $true) {
        return @{
            Lifecycle = "delete"
            Reason = "merged to main and not matched by retention policy"
        }
    }

    return @{
        Lifecycle = "archive"
        Reason = "manual owner review needed"
    }
}

$results = @()

foreach ($branch in $branches) {
    $name = [string]$branch.name
    $protected = [bool]$branch.protected
    $hasOpenPr = $openPrHeads.ContainsKey($name)
    $prNumber = $null
    $prTitle = $null

    if ($hasOpenPr) {
        $prNumber = $openPrHeads[$name].number
        $prTitle = $openPrHeads[$name].title
    }

    $mergedToMain = $null

    if ($IncludeMergedSignal -and $name -ne $MainBranch) {
        git merge-base --is-ancestor "origin/$name" "origin/$MainBranch" 2>$null
        if ($LASTEXITCODE -eq 0) {
            $mergedToMain = $true
        } elseif ($LASTEXITCODE -eq 1) {
            $mergedToMain = $false
        } else {
            $mergedToMain = $null
        }
    }

    $classification = Get-BranchClassification `
        -BranchName $name `
        -Protected $protected `
        -HasOpenPr $hasOpenPr `
        -MergedToMain $mergedToMain

    $results += [pscustomobject]@{
        branch_name = $name
        protected = $protected
        has_open_pr = $hasOpenPr
        open_pr_number = $prNumber
        open_pr_title = $prTitle
        merged_to_main = $mergedToMain
        lifecycle = $classification.Lifecycle
        reason = $classification.Reason
    }
}

if ($WhatIfPreference) {
    Write-Host "What if: Would export CSV to $inventoryCsv"
} else {
    $results |
        Sort-Object lifecycle, branch_name |
        Export-Csv -Path $inventoryCsv -NoTypeInformation -Encoding utf8
}

Write-Host ""
Write-Host "Remote branch lifecycle review written to:"
Write-Host "  $inventoryCsv"
Write-Host ""

$grouped = $results | Group-Object lifecycle | Sort-Object Name
foreach ($group in $grouped) {
    Write-Host ("{0}: {1}" -f $group.Name, $group.Count)
}

Write-Host ""
Write-Host "Suggested lifecycle decisions:"
$results |
    Sort-Object lifecycle, branch_name |
    Format-Table branch_name, lifecycle, protected, has_open_pr, merged_to_main, reason -AutoSize

if ($DeleteMarkedBranches) {
    $deletions = $results | Where-Object {
        $_.lifecycle -eq "delete" -and $_.branch_name -ne $MainBranch
    }

    if (-not $deletions) {
        Write-Host ""
        Write-Host "No branches marked delete."
    } else {
        Write-Host ""
        Write-Host "Branches marked delete:"
        $deletions | Format-Table branch_name, reason -AutoSize

        foreach ($item in $deletions) {
            $ref = $item.branch_name
            if ($PSCmdlet.ShouldProcess("origin/$ref", "Delete remote branch")) {
                Write-Host "Deleting remote branch: $ref"
                git push origin --delete $ref
                if ($LASTEXITCODE -ne 0) {
                    throw "Failed to delete remote branch: $ref"
                }
            }
        }
    }
}

if ($ApplyProtection) {
    Write-Host ""
    Write-Host "Updating branch protection for $MainBranch..."

    $body = @{
        required_status_checks = @{
            strict = $true
            contexts = @(
                "policy-smokes",
                "hardening-tests",
                "Assert release readiness contract",
                "Assert operational roadmap contract",
                "Assert PR hygiene contract",
                "Roadmap generator and validator smoke test"
            )
        }
        enforce_admins = $true
        required_pull_request_reviews = @{
            dismiss_stale_reviews = $false
            require_code_owner_reviews = $true
            required_approving_review_count = 1
            require_last_push_approval = $false
        }
        restrictions = $null
        required_linear_history = $false
        allow_force_pushes = $false
        allow_deletions = $false
        block_creations = $false
        required_conversation_resolution = $true
        lock_branch = $false
        allow_fork_syncing = $false
    } | ConvertTo-Json -Depth 10

    Save-TextSnapshot -Path $protectionUpdateJson -Content $body

    if ($PSCmdlet.ShouldProcess("${repoSlug}:${MainBranch}", "Apply stricter pull request review protection")) {
        $applyOutput = gh api `
            --method PUT `
            -H "Accept: application/vnd.github+json" `
            "repos/$repoSlug/branches/$MainBranch/protection" `
            --input $protectionUpdateJson 2>&1

        if ($LASTEXITCODE -ne 0) {
            throw "Failed to update branch protection: $applyOutput"
        }

        $afterRaw = gh api "repos/$repoSlug/branches/$MainBranch/protection" 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Protection update may have succeeded, but verification fetch failed: $afterRaw"
        }

        Save-TextSnapshot -Path $protectionAfter -Content $afterRaw

        Write-Host "Updated branch protection."
        Write-Host "Before snapshot: $protectionBefore"
        Write-Host "Update body:      $protectionUpdateJson"
        Write-Host "After snapshot:   $protectionAfter"
    }
} else {
    Write-Host ""
    Write-Host "Protection update skipped. Re-run with -ApplyProtection to enforce:"
    Write-Host "  - required_approving_review_count = 1"
    Write-Host "  - require_code_owner_reviews = true"
}

Write-Host ""
Write-Host "Final verification:"
$protectionRaw = gh api "repos/$repoSlug/branches/$MainBranch/protection" 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Could not verify protection: $protectionRaw"
}

$protection = $protectionRaw | ConvertFrom-Json
$reviewCount = $protection.required_pull_request_reviews.required_approving_review_count
$codeOwner = $protection.required_pull_request_reviews.require_code_owner_reviews
$strict = $protection.required_status_checks.strict

Write-Host "  required_approving_review_count: $reviewCount"
Write-Host "  require_code_owner_reviews:      $codeOwner"
Write-Host "  required_status_checks.strict:   $strict"

Write-Host ""
Write-Host "Done."
