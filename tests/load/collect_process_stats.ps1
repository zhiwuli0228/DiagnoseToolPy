param(
    [string]$OutputPath,
    [string]$StopFile,
    [int]$IntervalSeconds = 2
)

$ErrorActionPreference = "Stop"

if (-not $OutputPath) {
    throw "OutputPath is required."
}
if (-not $StopFile) {
    throw "StopFile is required."
}

$outputDir = Split-Path -Parent $OutputPath
if ($outputDir) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

"timestamp_utc,pid,name,cpu_seconds,working_set_mb,private_memory_mb,start_time,command_line" | Set-Content -Path $OutputPath -Encoding UTF8

while (-not (Test-Path -LiteralPath $StopFile)) {
    $timestamp = [DateTime]::UtcNow.ToString("o")

    $processes = Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match '^(python|python3|pythonw|uvicorn)(\.exe)?$' -or
        $_.CommandLine -match 'uvicorn' -or
        $_.CommandLine -match 'diagnose_tool\.main:app'
    }

    foreach ($proc in $processes) {
        try {
            $runtimeProc = Get-Process -Id $proc.ProcessId -ErrorAction Stop
            $cpu = if ($null -ne $runtimeProc.CPU) { [Math]::Round([double]$runtimeProc.CPU, 2) } else { 0.0 }
            $workingSetMb = [Math]::Round($runtimeProc.WorkingSet64 / 1MB, 2)
            $privateMemMb = [Math]::Round($runtimeProc.PrivateMemorySize64 / 1MB, 2)
            $startTime = if ($runtimeProc.StartTime) { $runtimeProc.StartTime.ToUniversalTime().ToString("o") } else { "" }
            $commandLine = ($proc.CommandLine -replace '"', '""')
            Add-Content -Path $OutputPath -Encoding UTF8 -Value (
                '{0},{1},{2},{3},{4},{5},"{6}","{7}"' -f
                $timestamp,
                $proc.ProcessId,
                $runtimeProc.ProcessName,
                $cpu,
                $workingSetMb,
                $privateMemMb,
                $startTime,
                $commandLine
            )
        } catch {
            continue
        }
    }

    Start-Sleep -Seconds $IntervalSeconds
}
