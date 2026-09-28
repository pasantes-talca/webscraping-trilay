param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^([01]\d|2[0-3]):[0-5]\d$')]
    [string]$Hora
)

$ErrorActionPreference = 'Stop'
$raizProyecto = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonProyecto = Join-Path $raizProyecto '.venv\Scripts\python.exe'
$mainProyecto = Join-Path $raizProyecto 'main.py'

if (-not (Test-Path -LiteralPath $pythonProyecto -PathType Leaf)) {
    throw "No se encontró Python en $pythonProyecto"
}
if (-not (Test-Path -LiteralPath $mainProyecto -PathType Leaf)) {
    throw "No se encontró main.py en $mainProyecto"
}

$horaInicio = [datetime]::ParseExact(
    $Hora, 'HH:mm', [System.Globalization.CultureInfo]::InvariantCulture
)
$accion = New-ScheduledTaskAction `
    -Execute $pythonProyecto `
    -Argument 'main.py' `
    -WorkingDirectory $raizProyecto
$disparador = New-ScheduledTaskTrigger -Daily -At $horaInicio
$opciones = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 4)

$usuarioActual = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$credencial = Get-Credential `
    -UserName $usuarioActual `
    -Message 'Ingresá la contraseña de Windows para ejecutar la tarea con la sesión cerrada.'

Register-ScheduledTask `
    -TaskName 'Trilay Krikos Diario' `
    -Action $accion `
    -Trigger $disparador `
    -Settings $opciones `
    -User $credencial.UserName `
    -Password $credencial.GetNetworkCredential().Password `
    -Force | Out-Null

Write-Output "Tarea 'Trilay Krikos Diario' programada todos los días a las $Hora."
