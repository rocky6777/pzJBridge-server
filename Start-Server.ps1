[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $GameDirectory,
    [string] $ServerName = 'servertest',
    [string] $CacheDirectory,
    [switch] $DryRun
)
$ErrorActionPreference = 'Stop'
$gamePath = (Resolve-Path -LiteralPath $GameDirectory).Path
$config = [IO.File]::ReadAllText((Join-Path $gamePath 'ProjectZomboid64.json')) | ConvertFrom-Json
if ($config.mainClass.Replace('/', '.') -ne 'zombie.network.GameServer') {
    throw 'This launcher requires the dedicated-server JSON, not the client JSON.'
}
$java = Join-Path $gamePath 'jre64\bin\java.exe'
if (-not (Test-Path -LiteralPath $java)) { throw 'Bundled server Java runtime was not found.' }
$vmArgs = @($config.vmArgs)
if (-not ($vmArgs | Where-Object { $_ -match '^-javaagent:.*zomboidjbridge.*=side=server(?:;|$)' })) {
    throw 'Run Install-ServerAgent.ps1 first. No server-mode agent option was found.'
}
if ($config.windows -and $config.windows.'10') { $vmArgs += @($config.windows.'10'.vmArgs) }
$classPath = $config.classpath -join [IO.Path]::PathSeparator
$launchArgs = $vmArgs + @('-cp', $classPath, $config.mainClass.Replace('/', '.'), '-servername', $ServerName)
if ($CacheDirectory) { $launchArgs += '-cachedir=' + [IO.Path]::GetFullPath($CacheDirectory) }
if ($DryRun) {
    # Only the constructed invocation is shown; no process or world is created.
    Write-Output ($java)
    $launchArgs | Write-Output
    return
}
Push-Location -LiteralPath $gamePath
try {
    # Keep an interactive console for the server's first-run account setup and quit command.
    & $java @launchArgs
    $serverExit = $LASTEXITCODE
} finally { Pop-Location }
exit $serverExit
