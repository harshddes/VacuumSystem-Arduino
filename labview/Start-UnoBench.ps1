[CmdletBinding()]
param(
    [ValidatePattern('^COM[1-9][0-9]*$')]
    [string]$Port,
    [switch]$Upload
)

$ErrorActionPreference = 'Stop'
$cli = Join-Path $env:ProgramFiles 'Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe'
if (-not (Test-Path -LiteralPath $cli)) {
    $command = Get-Command arduino-cli -ErrorAction SilentlyContinue
    if ($command) { $cli = $command.Source }
}
if (-not $Port) {
    if (-not (Test-Path -LiteralPath $cli)) { throw 'Pass -Port COMn for the USB port shown in Arduino IDE.' }
    $boards = & $cli board list --format json | ConvertFrom-Json
    $ports = @($boards.detected_ports | Where-Object {
        $_.port.address -match '^COM[1-9][0-9]*$' -and
        ($_.matching_boards.fqbn -contains 'arduino:avr:uno')
    } | ForEach-Object { $_.port.address })
    if ($ports.Count -ne 1) {
        throw 'Connect the Uno by USB and pass -Port COMn for its port in Arduino IDE.'
    }
    $Port = $ports[0]
}

if ($Upload) {
    if (-not (Test-Path -LiteralPath $cli)) { throw 'Arduino CLI is required for -Upload.' }
    & $cli compile --upload --port $Port --fqbn arduino:avr:uno (Join-Path $PSScriptRoot 'firmware\OptaTelemetry')
    if ($LASTEXITCODE -ne 0) { throw 'The Uno upload failed.' }
}

# Keep the installed Opta project's connection file intact.
$bench = Join-Path $env:TEMP ('maize-uno-' + [Guid]::NewGuid().ToString('N'))
$null = New-Item -Path $bench -ItemType Directory
$items = @(
    'MAIZE Vacuum.lvproj', 'MAIZE Vacuum Console.vi', 'Valve pilot lamp.vi',
    'Vacuum permissions.vi', 'Interlock messages.vi', 'MAIZE.Telemetry.exe',
    'Telemetry.cs', 'README.md', 'Start-UnoBench.ps1', 'firmware'
)
foreach ($item in $items) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $item) -Destination $bench -Recurse
}
Set-Content -LiteralPath (Join-Path $bench 'Opta.address') -Value 'uno' -Encoding ascii
$bridge = Start-Process -FilePath (Join-Path $bench 'MAIZE.Telemetry.exe') -ArgumentList '--uno-bridge', $Port -WindowStyle Hidden -PassThru
try {
    if (-not $bridge.WaitForExit(1200)) {
        Start-Process -FilePath (Join-Path $bench 'MAIZE Vacuum.lvproj')
        Write-Host "Uno bench on $Port. Run MAIZE Vacuum Console.vi in the opened LabVIEW project. Press Ctrl+C here to end USB acquisition."
        while (-not $bridge.WaitForExit(750)) {}
    }
    switch ($bridge.ExitCode) {
        2 { throw "Cannot open $Port. Close Arduino Serial Monitor and check that the board is connected." }
        3 { throw 'A bench bridge may already be running. Stop it before launching another.' }
        4 { throw "Lost $Port. Reconnect the Uno and rerun this command." }
        default { throw "The Uno bridge exited with code $($bridge.ExitCode)." }
    }
} finally {
    if (-not $bridge.HasExited) { Stop-Process -InputObject $bridge }
}
