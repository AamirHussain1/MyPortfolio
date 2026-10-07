param(
    [switch]$HiddenWorker,
    [switch]$Stop
)

$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Requirements = Join-Path $ProjectRoot "requirements.txt"
$Url = "http://127.0.0.1:5000/"
$StateDirectory = Join-Path $env:LOCALAPPDATA "AamirPortfolio"
$ProcessIdFile = Join-Path $StateDirectory "server.pid"
$StdoutLog = Join-Path $StateDirectory "server-output.log"
$StderrLog = Join-Path $StateDirectory "server-error.log"
$InstallLog = Join-Path $StateDirectory "install.log"
$InstallErrorLog = Join-Path $StateDirectory "install-error.log"
$LauncherLog = Join-Path $StateDirectory "launcher-error.log"

if (-not $HiddenWorker) {
    $PowerShell = Join-Path $PSHOME "powershell.exe"
    $WorkerArguments = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", "`"$PSCommandPath`"",
        "-HiddenWorker"
    )
    if ($Stop) {
        $WorkerArguments += "-Stop"
    }

    Start-Process -FilePath $PowerShell `
        -ArgumentList $WorkerArguments `
        -WindowStyle Hidden
    return
}

try {
    New-Item -ItemType Directory -Path $StateDirectory -Force | Out-Null

    if (-not (Test-Path $Python)) {
        throw "The virtual-environment Python was not found at $Python. Create the project's .venv first."
    }

    if (-not (Test-Path $Requirements)) {
        throw "The dependency file was not found at $Requirements."
    }

    if (-not $Stop) {
        try {
            $ExistingResponse = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($ExistingResponse.StatusCode -eq 200 -and $ExistingResponse.Content -like "*Aamir Hussain*") {
                Start-Process -FilePath $Url
                exit 0
            }
        }
        catch {
            # No portfolio server is responding yet; continue with startup.
        }
    }

    if ($Stop) {
        if (-not (Test-Path $ProcessIdFile)) {
            throw "No portfolio server process is recorded. It may already be stopped."
        }

        $ServerId = [int](Get-Content -Path $ProcessIdFile -Raw).Trim()
        $Server = Get-CimInstance Win32_Process -Filter "ProcessId = $ServerId"
        if (-not $Server -or $Server.ExecutablePath -ine $Python -or $Server.CommandLine -notlike "*$ProjectRoot\app.py*") {
            Remove-Item -Path $ProcessIdFile -Force
            throw "The recorded process is no longer this portfolio server. No process was stopped."
        }

        Stop-Process -Id $ServerId
        Remove-Item -Path $ProcessIdFile -Force
        exit 0
    }

    $InstallProcess = Start-Process -FilePath $Python `
        -ArgumentList @("-m", "pip", "install", "-r", "`"$Requirements`"") `
        -WorkingDirectory $ProjectRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $InstallLog `
        -RedirectStandardError $InstallErrorLog `
        -Wait `
        -PassThru
    if ($InstallProcess.ExitCode -ne 0) {
        throw "Installing dependencies failed. See $InstallLog and $InstallErrorLog for details."
    }

    $ServerProcess = Start-Process -FilePath $Python `
        -ArgumentList @("-u", "`"$ProjectRoot\app.py`"") `
        -WorkingDirectory $ProjectRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $StdoutLog `
        -RedirectStandardError $StderrLog `
        -PassThru
    Set-Content -Path $ProcessIdFile -Value $ServerProcess.Id

    $Ready = $false
    for ($Attempt = 0; $Attempt -lt 45; $Attempt++) {
        Start-Sleep -Seconds 1

        if ($ServerProcess.HasExited) {
            throw "The portfolio server stopped during startup. See $StderrLog for details."
        }

        try {
            $Response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($Response.StatusCode -eq 200 -and $Response.Content -like "*Aamir Hussain*") {
                $Ready = $true
                break
            }
        }
        catch {
            # The local server is not ready yet; keep waiting until the startup timeout.
        }
    }

    if (-not $Ready) {
        Stop-Process -Id $ServerProcess.Id -ErrorAction SilentlyContinue
        Remove-Item -Path $ProcessIdFile -Force -ErrorAction SilentlyContinue
        throw "The portfolio did not become ready within 45 seconds. See $StderrLog for details."
    }

    Start-Process -FilePath $Url
}
catch {
    $ErrorDetails = $_ | Format-List * -Force | Out-String
    $Message = "Portfolio launcher error:`r`n$ErrorDetails"
    Set-Content -Path $LauncherLog -Value $Message
    if (Test-Path $StderrLog) {
        $RecentErrors = Get-Content -Path $StderrLog -Tail 12
        if ($RecentErrors) {
            $Message += "`r`n`r`nRecent server output:`r`n$($RecentErrors -join "`r`n")"
        }
    }

    $Shell = New-Object -ComObject WScript.Shell
    $Shell.Popup($Message, 0, "Portfolio launcher", 16) | Out-Null
    exit 1
}
