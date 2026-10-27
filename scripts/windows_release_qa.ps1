# Windows-native preflight for local AutoML delivery. Does not claim browser approval.
param([switch]$OpenBrowser)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONUTF8 = "1"

$launcher = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    $launcher = @("py","-3.11")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $launcher = @("python")
} else {
    throw "Python 3.11 not found. Install Python 3.11 and retry."
}
$exe = $launcher[0]
$argsPrefix = if ($launcher.Length -gt 1) { $launcher[1..($launcher.Length-1)] } else { @() }
& $exe @argsPrefix -c "import sys; assert sys.version_info[:2] == (3, 11), 'Python 3.11 required'"
if ($LASTEXITCODE -ne 0) { throw "Python 3.11 is required for this release gate." }

# No global pip writes. A dedicated, gitignored environment leaves the owner's
# other Python installations and their existing packages intact.
$venvRoot = Join-Path (Get-Location).Path ".venv-automl-qa"
$venvPython = Join-Path $venvRoot "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    & $exe @argsPrefix -m venv $venvRoot
    if ($LASTEXITCODE -ne 0) { throw "Failed to create the isolated project QA environment." }
}
$exe = $venvPython
$argsPrefix = @()
& $exe -c "import sys; assert sys.version_info[:2] == (3, 11), 'Python 3.11 required'"
if ($LASTEXITCODE -ne 0) { throw "Existing QA venv is not Python 3.11. Preserve it and investigate." }
$env:PATH = (Join-Path $venvRoot "Scripts") + ";" + $env:PATH

$font = @(
    "$env:WINDIR\Fonts\NanumGothic.ttf",
    "$env:LOCALAPPDATA\Microsoft\Windows\Fonts\NanumGothic.ttf"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $font) {
    throw "Install a properly licensed NanumGothic.ttf, then rerun. Do not bundle Microsoft fonts."
}
$env:AUTOML_KOREAN_FONT_PATH = $font

& $exe @argsPrefix -m pip install -r requirements-verified-py311.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }

# No Poppler required for these tests. P3 full PDF raster tests run in Linux CI.
& $exe @argsPrefix -m pytest -q tests/test_original_smoke.py tests/test_basic_mvp.py tests/test_p2_ml_validity.py tests/test_p4_standard_delivery.py tests/test_p5_premium.py tests/test_p6_security.py tests/test_p6_xlsx.py tests/test_p6_windows_compat.py tests/test_p6_chart_policy.py tests/test_p6e6_delivery_policy.py
if ($LASTEXITCODE -ne 0) { throw "Windows smoke tests failed; do not list product for sale." }

# Portable synthetic previews for browser upload + actual local PREMIUM replay.
# qa-preview is gitignored and uses a fresh run folder; no customer data.
& $exe @argsPrefix -m scripts.p6e5_windows_demo
if ($LASTEXITCODE -ne 0) { throw "Synthetic tier review pack failed; do not approve sale." }

Write-Host "Non-GUI checks passed. Owner browser clicks/downloads still require manual verification." -ForegroundColor Yellow
if ($OpenBrowser) {
    $serverArgs = @()
    if ($exe -eq "py") { $serverArgs += "-3.11" }
    $serverArgs += @("-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000")
    $server = Start-Process -FilePath $exe -ArgumentList $serverArgs -WorkingDirectory (Get-Location).Path -WindowStyle Hidden -PassThru
    $ready = $false
    for ($i = 0; $i -lt 25; $i++) {
        if ($server.HasExited) { throw "Local server exited during startup." }
        try {
            $response = Invoke-WebRequest "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 1
            if ($response.StatusCode -eq 200) { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 300 }
    }
    if (-not $ready) {
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
        throw "Local server did not pass health check."
    }
    Write-Host "Local server PID: $($server.Id). To stop later: Stop-Process -Id $($server.Id)" -ForegroundColor Green
    Write-Host "Manually test all three uploads, ZIP download/extraction, and PREMIUM predict.cmd."
    Start-Process "http://127.0.0.1:8000/basic-mvp"
    Start-Process "http://127.0.0.1:8000/standard-mvp"
    Start-Process "http://127.0.0.1:8000/premium-mvp"
}
