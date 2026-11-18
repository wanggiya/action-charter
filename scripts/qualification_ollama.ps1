param(
  [ValidateSet('Start','Stop')][string]$Action = 'Start',
  [Parameter(Mandatory=$true)][string]$PrivateHome,
  [string]$Executable,
  [string]$Models,
  [int]$Port,
  [int]$LifetimeSeconds = 420
)
$ErrorActionPreference = 'Stop'
$record = Join-Path $PrivateHome 'owned-process.json'
function Stop-OwnedProcess {
  if (Test-Path $record) {
    $owned = Get-Content -Raw $record | ConvertFrom-Json
    $target = Get-Process -Id $owned.pid -ErrorAction SilentlyContinue
    if ($target -and $target.ProcessName -eq 'ollama' -and $target.StartTime.ToUniversalTime().Ticks.ToString() -eq $owned.started_ticks) {
      & "$env:SystemRoot\System32\taskkill.exe" /PID $target.Id /T /F | Out-Null
    }
  }
}
if ($Action -eq 'Stop') { Stop-OwnedProcess; exit 0 }
if (($Port -ne 0 -and $Port -lt 1024) -or $Port -gt 65535 -or $LifetimeSeconds -gt 420 -or $LifetimeSeconds -lt 1) { throw 'Invalid qualification limits' }
if ($Port -eq 0) {
  $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, 0)
  $listener.Start(); $Port = $listener.LocalEndpoint.Port; $listener.Stop()
}
New-Item -ItemType Directory -Force -Path $PrivateHome | Out-Null
$stream = [System.IO.File]::OpenRead($Executable)
try { $binaryHash = [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($stream)).Replace('-','').ToLower() } finally { $stream.Dispose() }
$start = New-Object System.Diagnostics.ProcessStartInfo
$start.FileName = $Executable
$start.Arguments = 'serve'
$start.UseShellExecute = $false
$start.EnvironmentVariables.Clear()
$start.EnvironmentVariables['SystemRoot'] = $env:SystemRoot
$start.EnvironmentVariables['PATH'] = "$env:SystemRoot\System32"
foreach ($name in @('USERPROFILE','HOME','TEMP','TMP','APPDATA','LOCALAPPDATA')) { $start.EnvironmentVariables[$name] = $PrivateHome }
$start.EnvironmentVariables['OLLAMA_HOST'] = "127.0.0.1:$Port"
$start.EnvironmentVariables['OLLAMA_MODELS'] = $Models
$start.EnvironmentVariables['OLLAMA_KEEP_ALIVE'] = '2m'
$start.EnvironmentVariables['OLLAMA_MAX_LOADED_MODELS'] = '1'
$start.EnvironmentVariables['OLLAMA_NUM_PARALLEL'] = '1'
$start.EnvironmentVariables['OLLAMA_NOPRUNE'] = '1'
$start.EnvironmentVariables['OLLAMA_NO_CLOUD'] = '1'
$process = [System.Diagnostics.Process]::Start($start)
try {
  @{ pid=$process.Id; started_ticks=$process.StartTime.ToUniversalTime().Ticks.ToString(); binary_sha256=$binaryHash; port=$Port } | ConvertTo-Json | Set-Content -Encoding UTF8 $record
  if (-not $process.WaitForExit($LifetimeSeconds * 1000)) { Stop-OwnedProcess }
} finally {
  if (-not $process.HasExited) { & "$env:SystemRoot\System32\taskkill.exe" /PID $process.Id /T /F | Out-Null }
}
