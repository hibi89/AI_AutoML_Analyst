# Windows-native preflight for local AutoML delivery. Does not claim browser approval.
param(
    [switch]$OpenBrowser,
    [switch]$ProbeOnly,
    [switch]$PortProbeOnly,
    [ValidateRange(1024, 65535)][int]$Port = 8000
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONUTF8 = "1"

# Do not mistake another process's /health response for our server.
# A busy port must never trigger a forced kill of an unrelated process.
function Test-LoopbackPortOccupied {
    param([int]$ListenPort)
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        try {
            $client.Connect([System.Net.IPAddress]::Loopback, $ListenPort)
            return $true
        } catch [System.Net.Sockets.SocketException] {
            return $false
        }
    } finally {
        $client.Dispose()
    }
}
if ($PortProbeOnly) {
    if (Test-LoopbackPortOccupied -ListenPort $Port) {
        throw "Local port $Port is already occupied. Existing services are never stopped by this check."
    }
    Write-Output "LOCAL_PORT_AVAILABLE=$Port"
    return
}

# A stale Windows 'py' launcher can exist even when only 'python' points to
# an installed Python 3.11. Probe both commands before altering environments.
$probe = "import sys; sys.exit(0 if sys.version_info[:2] == (3, 11) else 1)"
$launcher = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    try {
        & py -3.11 -c $probe 2>$null
        if ($LASTEXITCODE -eq 0) { $launcher = @("py", "-3.11") }
    } catch { }  # py may exist but have no registered 3.11 runtime
}
if ($launcher.Count -eq 0 -and (Get-Command python -ErrorAction SilentlyContinue)) {
    try {
        & python -c $probe 2>$null
        if ($LASTEXITCODE -eq 0) { $launcher = @("python") }
    } catch { }
}
if ($launcher.Count -eq 0) {
    throw "Python 3.11 not found via py -3.11 or python. Install Python 3.11 and retry."
}
$exe = $launcher[0]
$argsPrefix = if ($launcher.Length -gt 1) { $launcher[1..($launcher.Length-1)] } else { @() }
if ($ProbeOnly) {
    # CI-only dry probe: no venv, font checks, pip installs, or app start.
    Write-Output ("PYTHON311_LAUNCHER=" + ($launcher -join " "))
    return
}

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
    if (Test-LoopbackPortOccupied -ListenPort $Port) {
        throw "Local port $Port is already occupied. Stop or relocate that service yourself before starting this app."
    }
    $serverArgs = @()
    if ($exe -eq "py") { $serverArgs += "-3.11" }
    $serverArgs += @("-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "$Port")
    $server = Start-Process -FilePath $exe -ArgumentList $serverArgs -WorkingDirectory (Get-Location).Path -WindowStyle Hidden -PassThru
    $ready = $false
    for ($i = 0; $i -lt 25; $i++) {
        if ($server.HasExited) { throw "Local server exited during startup." }
        try {
            $response = Invoke-WebRequest "http://127.0.0.1:$Port/health" -UseBasicParsing -TimeoutSec 1
            if ($response.StatusCode -eq 200) { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 300 }
    }
    if (-not $ready) {
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
        throw "Local server did not pass health check."
    }
    Write-Host "Local server PID: $($server.Id). To stop later: Stop-Process -Id $($server.Id)" -ForegroundColor Green
    Write-Host "Manually test all three uploads, ZIP download/extraction, and PREMIUM predict.cmd."
    Start-Process "http://127.0.0.1:$Port/basic-mvp"
    Start-Process "http://127.0.0.1:$Port/standard-mvp"
    Start-Process "http://127.0.0.1:$Port/premium-mvp"
}
