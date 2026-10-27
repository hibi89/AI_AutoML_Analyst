# Windows-native preflight for local AutoML delivery. Does not claim browser approval.
param(
    [switch]$OpenBrowser,
    [switch]$ProbeOnly,
    [switch]$PortProbeOnly,
    [switch]$IdentityProbeOnly,
    [switch]$VenvOnly,
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

# An unrelated process can reply to /health even if it acquires the port
# after the initial free-port check. The root JSON must match this application's
# existing public root contract before opening browsers.
function Test-AutoMLServerIdentity {
    param([int]$ListenPort)
    try {
        $response = Invoke-WebRequest "http://127.0.0.1:$ListenPort/" -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -ne 200) { return $false }
        $identity = $response.Content | ConvertFrom-Json -ErrorAction Stop
        return ($identity.message -ceq "AI AutoML Analyst API" -and
                $identity.health -ceq "/health" -and
                $identity.analyze_upload -ceq "/api/analyze")
    } catch {
        return $false
    }
}
if ($IdentityProbeOnly) {
    if (-not (Test-AutoMLServerIdentity -ListenPort $Port)) {
        throw "Local port $Port is not serving the expected AI AutoML Analyst API."
    }
    Write-Output "AUTOML_SERVER_IDENTITY=PASS"
    return
}

# Always use the actual, verified Python 3.11 executable for venv creation.
# On a real Windows owner machine a py launcher passed a version probe but
# unexpectedly dropped into the Python REPL for '-m venv'; its exit code was 0.
# The old script then tried to execute a nonexistent venv interpreter.
$probe = "import sys; sys.exit(0 if sys.version_info[:2] == (3, 11) else 1)"
$exe = $null
$launcherLabel = $null

# Prefer a direct Python 3.11 executable; unlike the 'py' wrapper it has no
# intermediary argument forwarding for '-m venv' or path-with-spaces values.
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd) {
    try {
        & $pythonCmd.Source -c $probe 2>$null
        if ($LASTEXITCODE -eq 0) {
            $exe = $pythonCmd.Source
            $launcherLabel = "python"
        }
    } catch { }
}
if (-not $exe -and (Get-Command py -ErrorAction SilentlyContinue)) {
    try {
        # py is only used to resolve the actual registered Python binary.
        $candidate = @(& py -3.11 -c "import sys; print(sys.executable)" 2>$null)
        if ($LASTEXITCODE -eq 0 -and $candidate.Count -eq 1) {
            $candidatePath = [string]$candidate[0]
            if ((Test-Path -LiteralPath $candidatePath -PathType Leaf)) {
                & $candidatePath -c $probe 2>$null
                if ($LASTEXITCODE -eq 0) {
                    $exe = $candidatePath
                    $launcherLabel = "py -3.11"
                }
            }
        }
    } catch { }
}
if (-not $exe) {
    throw "Python 3.11 not found via python or py -3.11. Install Python 3.11 and retry."
}
if ($ProbeOnly) {
    Write-Output ("PYTHON311_LAUNCHER=" + $launcherLabel)
    Write-Output ("PYTHON311_EXECUTABLE=" + $exe)
    return
}

# No global pip writes. Never remove an existing environment automatically.
# If venv creation exits 0 but does not create python.exe, fail closed.
$venvRoot = Join-Path (Get-Location).Path ".venv-automl-qa"
$venvPython = Join-Path $venvRoot "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    & $exe -m venv $venvRoot
    if ($LASTEXITCODE -ne 0) { throw "Failed to create the isolated project QA environment." }
    if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
        throw "Python venv creation returned success but Scripts\\python.exe is missing in $venvRoot. Existing files were preserved; check Python launcher/venv installation."
    }
}
$exe = $venvPython
& $exe -c "import sys; assert sys.version_info[:2] == (3, 11), 'Python 3.11 required'"
if ($LASTEXITCODE -ne 0) { throw "Existing QA venv is not Python 3.11. Preserve it and investigate." }
if ($VenvOnly) {
    Write-Output ("VENV_PYTHON311_OK=" + $venvPython)
    return
}
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
    $serverArgs += @("-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "$Port")
    $server = Start-Process -FilePath $exe -ArgumentList $serverArgs -WorkingDirectory (Get-Location).Path -WindowStyle Hidden -PassThru
    $ready = $false
    for ($i = 0; $i -lt 25; $i++) {
        if ($server.HasExited) { throw "Local server exited during startup." }
        try {
            $response = Invoke-WebRequest "http://127.0.0.1:$Port/health" -UseBasicParsing -TimeoutSec 1
            if ($response.StatusCode -eq 200 -and
                (Test-AutoMLServerIdentity -ListenPort $Port) -and
                (-not $server.HasExited)) {
                $ready = $true
                break
            }
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
