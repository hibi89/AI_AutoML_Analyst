# One command for local, synthetic-only AI AutoML release verification.
# Full is the default: tests, ZIP/PDF review pack, and real headless browser.
# Quick reuses only the existing short smoke subset. No deletes or real data.
[CmdletBinding()]
param(
    [switch]$Quick,
    [switch]$SkipBrowser,
    [switch]$CheckOnly
)
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Push-Location -LiteralPath $root
try {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw "Git is required to identify the exact tested source revision."
    }
    $sha = [string](& git rev-parse --verify HEAD 2>$null)
    if ($LASTEXITCODE -ne 0 -or $sha -notmatch '^[0-9a-f]{40}$') {
        throw "Run this command inside a Git checkout; source SHA unavailable."
    }
    if ($CheckOnly) {
        Write-Output "AUTOML_LOCAL_VERIFIER=READY SHA=$sha"
        return
    }

    $folder = Join-Path $root "qa-preview"
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
    $stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssfffZ")
    $logPath = Join-Path $folder "verify-local-$stamp.log"
    $resultPath = Join-Path $folder "verify-local-$stamp.json"
    $mode = if ($Quick) { "QUICK" } else { "FULL" }
    $browserResult = "NOT RUN"
    $errorMessage = $null
    $status = "FAIL"
    $transcript = $false
    try {
        Start-Transcript -Path $logPath -ErrorAction Stop | Out-Null
        $transcript = $true
        Write-Output "VERIFY_MODE=$mode SOURCE_SHA=$sha"
        $fullSuite = -not $Quick
        # Reuse the hardened Windows bootstrap once. It preserves preexisting
        # venvs/files, checks pinned fonts and builds a synthetic 3-tier pack.
        & (Join-Path $root "scripts\windows_release_qa.ps1") -AllTests:$fullSuite
        $venvPython = Join-Path $root ".venv-automl-qa\Scripts\python.exe"
        if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
            throw "Windows QA helper did not prepare expected isolated Python."
        }
        if (-not $Quick -and -not $SkipBrowser) {
            # A disposable localhost-only browser session, 6 exact SKU/encoding
            # flows. No existing listener is killed; only its own server stops.
            & $venvPython -m pip install -r requirements-browser.txt
            if ($LASTEXITCODE -ne 0) { throw "Pinned local browser installation failed." }
            & $venvPython -m playwright install chromium
            if ($LASTEXITCODE -ne 0) { throw "Headless Chromium setup failed." }
            & $venvPython -m scripts.p6_browser_smoke
            if ($LASTEXITCODE -ne 0) { throw "Real browser/ZIP integration failed." }
            $browserResult = "PASS"
        } elseif ($SkipBrowser) {
            $browserResult = "SKIP (explicit)"
        } else {
            $browserResult = "SKIP (quick mode)"
        }
        $status = "PASS"
    } catch {
        $errorMessage = [string]$_.Exception.Message
        Write-Output "VERIFY_ERROR=$errorMessage"
    } finally {
        if ($transcript) {
            Stop-Transcript | Out-Null
        }
    }

    # Extract ONLY an actually printed pytest summary; absence is NOT RUN,
    # never a fabricated zero-pass or green result. Transcript stays local.
    $passed = $null
    $skipped = $null
    $failed = $null
    if (Test-Path -LiteralPath $logPath -PathType Leaf) {
        $rawLog = Get-Content -LiteralPath $logPath -Raw
        $matchesFound = [regex]::Matches(
            $rawLog, '(\d+) passed(?:, (\d+) failed)?(?:, (\d+) skipped)?'
        )
        if ($matchesFound.Count -gt 0) {
            $match = $matchesFound[$matchesFound.Count - 1]
            $passed = [int]$match.Groups[1].Value
            if ($match.Groups[2].Success) { $failed = [int]$match.Groups[2].Value }
            if ($match.Groups[3].Success) { $skipped = [int]$match.Groups[3].Value }
        }
    }
    $record = [ordered]@{
        source_sha = $sha
        mode = $mode
        result = $status
        pytest_pass = $passed
        pytest_fail = $failed
        pytest_skip = $skipped
        browser = $browserResult
        human_pdf_zip_review = "NOT RUN"
        font_and_software_license_approval = "PENDING OWNER"
        sku_commercial_approval = "NO-GO"
        error = $errorMessage
        log_file = $logPath
        generated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    }
    $record | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $resultPath -Encoding UTF8
    Write-Output "VERIFICATION=$status MODE=$mode SHA=$sha"
    Write-Output "TESTS_PASS=$passed TESTS_FAIL=$failed TESTS_SKIP=$skipped BROWSER=$browserResult"
    Write-Output "LOG=$logPath"
    Write-Output "SUMMARY=$resultPath"
    if ($status -ne "PASS") {
        throw "Local verification failed: $errorMessage. See $resultPath"
    }
} finally {
    Pop-Location
}
