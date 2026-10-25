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
& $exe @argsPrefix --version
if ($LASTEXITCODE -ne 0) { throw "Python failed." }

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
& $exe @argsPrefix -m pytest -q tests/test_original_smoke.py tests/test_basic_mvp.py tests/test_p2_ml_validity.py tests/test_p4_standard_delivery.py tests/test_p5_premium.py tests/test_p6_security.py tests/test_p6_xlsx.py tests/test_p6_windows_compat.py tests/test_p6_chart_policy.py
if ($LASTEXITCODE -ne 0) { throw "Windows smoke tests failed; do not list product for sale." }

Write-Host "Windows non-GUI tests passed. Browser click/download and actual predict.cmd are STILL unverified." -ForegroundColor Yellow
if ($OpenBrowser) {
    Write-Host "Start the server separately: py -3.11 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"
    Start-Process "http://127.0.0.1:8000/basic-mvp"
    Start-Process "http://127.0.0.1:8000/standard-mvp"
    Start-Process "http://127.0.0.1:8000/premium-mvp"
}
