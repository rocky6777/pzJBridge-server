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
if ($ServerName -notmatch '^[a-zA-Z0-9_-]+$') { throw 'ServerName must contain only letters, digits, underscore or hyphen.' }
$cachePath = if ($CacheDirectory) { [IO.Path]::GetFullPath($CacheDirectory) } else { Join-Path $env:USERPROFILE 'Zomboid' }
$profilePath = Join-Path $cachePath ('Server\' + $ServerName + '.ini')
$workshopItems = @()
$foundWorkshopSetting = $false
if (Test-Path -LiteralPath $profilePath) {
    foreach ($line in [IO.File]::ReadAllLines($profilePath)) {
        if ($line -match '^\s*WorkshopItems\s*=(.*)$') {
            if ($foundWorkshopSetting) { throw 'Duplicate WorkshopItems settings in the server profile.' }
            $foundWorkshopSetting = $true
            $workshopItems = @($Matches[1].Split(';') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
            foreach ($item in $workshopItems) {
                if ($item -notmatch '^[1-9][0-9]*$') { throw 'WorkshopItems must contain semicolon-separated numeric IDs.' }
            }
        }
    }
}
for ($index = 0; $index -lt $vmArgs.Count; $index++) {
    if ($vmArgs[$index] -match '^-javaagent:.*zomboidjbridge.*=side=server(?:;|$)') {
        $vmArgs[$index] = $vmArgs[$index] -replace ';workshopItems=[^;]*', ''
        if ($workshopItems.Count -gt 0) { $vmArgs[$index] += ';workshopItems=' + ($workshopItems -join ',') }
    }
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
$previousSteamAppId = $env:SteamAppId
$previousSteamGameId = $env:SteamGameId
try {
    # Steam distributes the dedicated tool as 380870, but client connections use
    # the game's 108600 identity. Scope this override to the server process.
    $env:SteamAppId = '108600'
    $env:SteamGameId = '108600'
    # Keep an interactive console for the server's first-run account setup and quit command.
    & $java @launchArgs
    $serverExit = $LASTEXITCODE
} finally {
    $env:SteamAppId = $previousSteamAppId
    $env:SteamGameId = $previousSteamGameId
    Pop-Location
}
exit $serverExit
