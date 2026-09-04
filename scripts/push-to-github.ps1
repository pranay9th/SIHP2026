<#
    push-to-github.ps1
    ------------------
    Commits everything in this project and pushes it to
    git@github.com:pranay9th/SIHP2026.git

    Run it from Windows PowerShell, from the project folder:

        cd D:\pranay\SIHP2026
        powershell -ExecutionPolicy Bypass -File scripts\push-to-github.ps1

    Optional custom commit message:

        powershell -ExecutionPolicy Bypass -File scripts\push-to-github.ps1 -Message "Add rule pack"

    Why this script exists: the repository was initialised from a sandboxed
    environment that cannot delete files, so a stale .git\index.lock may be
    left behind. This script clears it, then does a normal commit and push.

    NOTE: this file is deliberately plain ASCII and saved with a UTF-8 BOM,
    so Windows PowerShell 5.1 parses it correctly.
#>

param(
    [string]$Message = "Add SIH26034 problem analysis, project roadmap, presentation guide and idea-submission deck",
    [string]$Remote  = "git@github.com:pranay9th/SIHP2026.git",
    [string]$Branch  = "main"
)

# Deliberately NOT "Stop": git writes normal progress messages to stderr,
# which "Stop" would turn into fatal errors. Exit codes are checked instead.
$ErrorActionPreference = "Continue"

function Step($text) { Write-Host ""; Write-Host "==> $text" -ForegroundColor Cyan }
function Ok($text)   { Write-Host "    $text" -ForegroundColor Green }
function Warn($text) { Write-Host "    $text" -ForegroundColor Yellow }
function Fail($text) { Write-Host "    $text" -ForegroundColor Red }

# --- locate the repo root (parent of the scripts folder) -------------------
if ($PSScriptRoot) {
    $repoRoot = Split-Path -Parent $PSScriptRoot
} else {
    $repoRoot = (Get-Location).Path
}
if (-not $repoRoot -or -not (Test-Path $repoRoot)) {
    $repoRoot = (Get-Location).Path
}
Set-Location $repoRoot
Write-Host "Repository: $repoRoot"

# --- 0. is git installed? --------------------------------------------------
Step "Checking git"
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Fail "git is not installed, or not on PATH."
    Write-Host "    Install it from https://git-scm.com/download/win then run this again."
    exit 1
}
Ok (git --version)

# --- 1. clear stale lock files --------------------------------------------
Step "Clearing stale lock files"
$cleared = 0
$locks = @(
    ".git\index.lock",
    ".git\HEAD.lock",
    ".git\config.lock",
    ".git\refs\heads\$Branch.lock"
)
foreach ($l in $locks) {
    if (Test-Path $l) {
        Remove-Item $l -Force -ErrorAction SilentlyContinue
        if (-not (Test-Path $l)) { $cleared++; Ok "removed $l" }
    }
}
if (Test-Path ".git\objects") {
    Get-ChildItem ".git\objects" -Recurse -Filter "tmp_obj_*" -ErrorAction SilentlyContinue |
        ForEach-Object {
            Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
            $cleared++
        }
}
if ($cleared -eq 0) { Ok "nothing to clear" } else { Ok "$cleared item(s) cleared" }

# --- 2. repository ---------------------------------------------------------
Step "Checking repository"
if (-not (Test-Path ".git")) {
    git init -b $Branch | Out-Null
    Ok "initialised a new repository"
} else {
    Ok "repository already initialised"
}

$current = git rev-parse --abbrev-ref HEAD 2>$null
if ($LASTEXITCODE -ne 0 -or $current -eq "HEAD" -or -not $current) {
    git checkout -B $Branch 2>&1 | Out-Null
    Ok "on branch $Branch"
} elseif ($current -ne $Branch) {
    git branch -M $Branch 2>&1 | Out-Null
    Ok "renamed branch $current to $Branch"
} else {
    Ok "on branch $Branch"
}

# --- 3. identity -----------------------------------------------------------
Step "Checking git identity"
$name  = git config user.name
$email = git config user.email
if (-not $name)  { git config user.name  "pranay9th"                | Out-Null; $name  = "pranay9th" }
if (-not $email) { git config user.email "pranaykumarcse@gmail.com" | Out-Null; $email = "pranaykumarcse@gmail.com" }
Ok "$name <$email>"

# --- 4. remote -------------------------------------------------------------
Step "Configuring remote"
$existing = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0 -or -not $existing) {
    git remote add origin $Remote
    Ok "added origin -> $Remote"
} elseif ($existing.Trim() -ne $Remote) {
    git remote set-url origin $Remote
    Ok "updated origin -> $Remote"
} else {
    Ok "origin already set to $Remote"
}

# --- 5. commit -------------------------------------------------------------
Step "Staging and committing"
git add -A
$pending = git status --porcelain
if (-not $pending) {
    Warn "nothing to commit, working tree is clean"
} else {
    git commit -m $Message
    if ($LASTEXITCODE -ne 0) {
        Fail "commit failed, see the message above"
        exit 1
    }
    Ok "committed"
}

# --- 6. push ---------------------------------------------------------------
Step "Pushing to GitHub"
Write-Host "    (if this pauses asking for a passphrase, that is your SSH key - type it)"
git push -u origin $Branch
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Fail "Push failed."
    Write-Host "Most likely causes:"
    Write-Host ""
    Write-Host "  1. No SSH key set up for GitHub. Test it with:"
    Write-Host "         ssh -T git@github.com"
    Write-Host "     Set one up: https://docs.github.com/authentication/connecting-to-github-with-ssh"
    Write-Host ""
    Write-Host "  2. The remote already has commits. Then run:"
    Write-Host "         git pull --rebase origin $Branch"
    Write-Host "         git push -u origin $Branch"
    Write-Host ""
    Write-Host "  3. To use HTTPS instead of SSH (browser sign-in, no key needed):"
    Write-Host "         git remote set-url origin https://github.com/pranay9th/SIHP2026.git"
    Write-Host "         git push -u origin $Branch"
    exit 1
}

Write-Host ""
Write-Host "Done. https://github.com/pranay9th/SIHP2026" -ForegroundColor Green
