param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Install", "Remove")]
    [string]$Action
)

$ErrorActionPreference = "Stop"
$TaskName = "AamirPortfolioNaukriResumeUpdate"

if ($Action -eq "Remove") {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    exit 0
}

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$Runner = Join-Path $PSScriptRoot "naukri_task.py"
if (-not (Test-Path $Python)) {
    throw "The project Python interpreter was not found."
}
if (-not (Test-Path $Runner)) {
    throw "The Naukri update runner was not found."
}

$Identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$TaskAction = New-ScheduledTaskAction `
    -Execute $Python `
    -Argument "`"$Runner`"" `
    -WorkingDirectory $PSScriptRoot
$Trigger = New-ScheduledTaskTrigger -Daily -At "8:15AM"
$Trigger.RandomDelay = "PT15M"
$Principal = New-ScheduledTaskPrincipal `
    -UserId $Identity `
    -LogonType Interactive `
    -RunLevel Limited
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 25)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $TaskAction `
    -Trigger $Trigger `
    -Principal $Principal `
    -Settings $Settings `
    -Description "Run Aamir's portfolio-managed Naukri resume updater between 8:15 and 8:30 AM." `
    -Force | Out-Null
