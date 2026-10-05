[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)] [string] $GameDirectory,
    [string] $InstallDirectory = (Join-Path $env:LOCALAPPDATA 'ZomboidJBridgeServer'),
    [switch] $EnableMcp,
    [string] $McpFile,
    [string] $WorkshopDirectory,
    [switch] $DisableWorkshop,
    [switch] $Uninstall
)

$ErrorActionPreference = 'Stop'
$gamePath = (Resolve-Path -LiteralPath $GameDirectory).Path
$launcherPath = Join-Path $gamePath 'ProjectZomboid64.json'
$gameJarPath = Join-Path $gamePath 'java\projectzomboid.jar'
if (-not (Test-Path -LiteralPath $launcherPath) -or -not (Test-Path -LiteralPath $gameJarPath)) {
    throw 'Expected the dedicated-server folder, containing ProjectZomboid64.json and java/projectzomboid.jar.'
}
$runningServer = Get-CimInstance Win32_Process | Where-Object {
    $_.ExecutablePath -and $_.ExecutablePath.StartsWith($gamePath + '\', [StringComparison]::OrdinalIgnoreCase) -and
    ($_.Name -eq 'ProjectZomboid64.exe' -or ($_.Name -eq 'java.exe' -and $_.CommandLine -match 'zombie[./]network[./]GameServer'))
}
if ($runningServer) { throw 'Stop the dedicated server normally before installing or uninstalling the agent.' }

$original = [IO.File]::ReadAllText($launcherPath)
$config = $original | ConvertFrom-Json
if ($config.mainClass.Replace('/', '.') -ne 'zombie.network.GameServer') {
    throw 'Expected a dedicated-server launcher JSON, not the client JSON.'
}
if (-not ($config.PSObject.Properties.Name -contains 'vmArgs')) { throw 'Launcher JSON has no vmArgs array.' }
$existingArgs = @($config.vmArgs)
$preservedArgs = @($existingArgs | Where-Object { -not ($_ -match '^-javaagent:.*zomboidjbridge.*\.jar(?:=|$)') })
$config.vmArgs = $preservedArgs

if (-not $Uninstall) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [IO.Compression.ZipFile]::OpenRead($gameJarPath)
    try {
        $entry = $archive.GetEntry('zombie/network/packets/connection/LoginPacket.class')
        if (-not $entry) { throw 'The expected B42 login class is missing.' }
        $stream = $entry.Open()
        $sha = [Security.Cryptography.SHA256]::Create()
        try { $gameHash = [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() }
        finally { $stream.Dispose(); $sha.Dispose() }
    } finally { $archive.Dispose() }
    if ($gameHash -ne '5ea931e8d251517d6566eaac9a220d3d722959951581e6cc6bb7a104fe4519d9') {
        throw 'This game build does not match the verified 42.21 agent profile. No launcher settings were changed.'
    }
    $bundledJar = Join-Path $PSScriptRoot 'java\zomboidjbridge-0.7.1.jar'
    $checksumFile = Join-Path $PSScriptRoot 'java\zomboidjbridge-0.7.1.jar.sha256'
    if (-not (Test-Path -LiteralPath $bundledJar) -or -not (Test-Path -LiteralPath $checksumFile)) {
        throw 'The packaged agent or checksum is missing. Use the generated Workshop package, not the source template.'
    }
    $expectedHash = ([IO.File]::ReadAllText($checksumFile)).Trim()
    $bundleStream = [IO.File]::OpenRead($bundledJar)
    $bundleSha = [Security.Cryptography.SHA256]::Create()
    try { $bundleHash = [BitConverter]::ToString($bundleSha.ComputeHash($bundleStream)).Replace('-', '').ToLowerInvariant() }
    finally { $bundleStream.Dispose(); $bundleSha.Dispose() }
    if ($bundleHash -ne $expectedHash) {
        throw 'Bundled agent checksum mismatch. No launcher settings were changed.'
    }
    $stableDirectory = [IO.Path]::GetFullPath($InstallDirectory)
    $stableJar = Join-Path $stableDirectory 'zomboidjbridge-0.7.1.jar'
    if (@($stableJar, $gameJarPath, $McpFile) | Where-Object { $_ -and $_.Contains(';') }) {
        throw 'Agent option paths cannot contain semicolons.'
    }
    $agentOption = '-javaagent:' + $stableJar.Replace('\', '/') + '=side=server;gameJar=' + $gameJarPath.Replace('\', '/')
    if ($DisableWorkshop) { $agentOption += ';workshop=false' }
    if ($WorkshopDirectory) {
        $workshopPath = (Resolve-Path -LiteralPath $WorkshopDirectory).Path
        if ($workshopPath.Contains(';')) { throw 'Workshop paths cannot contain semicolons.' }
        $agentOption += ';workshopDir=' + $workshopPath.Replace('\', '/')
    }
    if ($EnableMcp) {
        if (-not $McpFile) { $McpFile = Join-Path $stableDirectory 'mcp\server.json' }
        $McpFile = [IO.Path]::GetFullPath($McpFile)
        if ($McpFile.Contains(';')) { throw 'MCP path cannot contain semicolons.' }
        $agentOption += ';mcpPort=0;mcpFile=' + $McpFile.Replace('\', '/')
    }
    $config.vmArgs = @($agentOption) + $preservedArgs
}

$newJson = $config | ConvertTo-Json -Depth 32
$null = $newJson | ConvertFrom-Json
if ($PSCmdlet.ShouldProcess($launcherPath, $(if ($Uninstall) { 'Remove ZomboidJBridge startup option' } else { 'Back up launcher and install ZomboidJBridge startup option' }))) {
    $backupPath = $launcherPath + '.zjb-' + (Get-Date -Format 'yyyyMMdd-HHmmss-ffff') + '.bak'
    Copy-Item -LiteralPath $launcherPath -Destination $backupPath
    if (-not $Uninstall) {
        New-Item -ItemType Directory -Path $stableDirectory -Force | Out-Null
        Copy-Item -LiteralPath $bundledJar -Destination $stableJar -Force
    }
    [IO.File]::WriteAllText($launcherPath, $newJson + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
    Write-Host ('Launcher backup: ' + $backupPath)
    Write-Host $(if ($Uninstall) { 'Agent startup option removed. Use Start-Server.ps1 to launch the server.' } else { 'Agent installed. Use Start-Server.ps1 to launch the server; stock StartServer batch files ignore this JSON.' })
    if (-not $Uninstall -and $EnableMcp) { Write-Host ('Developer MCP connection file: ' + $McpFile) }
}
