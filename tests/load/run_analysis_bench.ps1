param(
    [string]$Profile,
    [string]$BaseUrl = "http://127.0.0.1:18080",
    [string]$Config = "tests/load/analysis_benchmarks.yaml",
    [int]$SampleIntervalSeconds = 2
)

$ErrorActionPreference = "Stop"
$runId = Get-Date -Format "yyyyMMdd-HHmmss"
$artifactRoot = Join-Path "tests/load/artifacts" $runId
New-Item -ItemType Directory -Path $artifactRoot -Force | Out-Null

$healthUrl = "$($BaseUrl.TrimEnd('/'))/health"
Write-Host "preflight: GET $healthUrl"

try {
    $response = Invoke-WebRequest -Uri $healthUrl -TimeoutSec 5 -UseBasicParsing
} catch {
    Write-Error "preflight FAILED: $healthUrl did not return 200 within 5s. Start the backend and rerun."
    exit 3
}

if ($response.StatusCode -ne 200) {
    Write-Error "preflight FAILED: $healthUrl returned status $($response.StatusCode)"
    exit 3
}

Write-Host "preflight OK"

Write-Host "preparing benchmark datasets from $Config"
$prepareArgs = @("run", "python", "tests/load/prepare_analysis_datasets.py", "--config", $Config)
if ($Profile) {
    $prepareArgs += @("--profile", $Profile)
}
& uv @prepareArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "dataset preparation failed"
    exit $LASTEXITCODE
}

$statsPath = Join-Path $artifactRoot "process-stats.csv"
$stopFile = Join-Path $artifactRoot ".collector-stop"
$collectorScript = Resolve-Path "tests/load/collect_process_stats.ps1"

$collectorArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $collectorScript,
    "-OutputPath", $statsPath,
    "-StopFile", $stopFile,
    "-IntervalSeconds", $SampleIntervalSeconds
)

$collector = Start-Process -FilePath "pwsh" -ArgumentList $collectorArgs -WindowStyle Hidden -PassThru
Write-Host "collector started: PID=$($collector.Id)"

$args = @(
    "run",
    "python",
    "tests/load/analysis_benchmark.py",
    "--config", $Config,
    "--host", $BaseUrl,
    "--output-dir", $artifactRoot
)
if ($Profile) {
    $args += @("--profile", $Profile)
}

try {
    & uv @args
    $benchmarkExitCode = $LASTEXITCODE
} finally {
    New-Item -ItemType File -Path $stopFile -Force | Out-Null
    Start-Sleep -Seconds ([Math]::Max(1, $SampleIntervalSeconds))
    if (-not $collector.HasExited) {
        Stop-Process -Id $collector.Id -Force -ErrorAction SilentlyContinue
    }
}

$runMeta = [ordered]@{
    run_id = $runId
    host = $BaseUrl
    profile = $Profile
    config = $Config
    sample_interval_seconds = $SampleIntervalSeconds
    artifact_root = (Resolve-Path $artifactRoot).Path
    process_stats_csv = $statsPath
    benchmark_exit_code = $benchmarkExitCode
    generated_at = [DateTime]::UtcNow.ToString("o")
} | ConvertTo-Json -Depth 4

Set-Content -Path (Join-Path $artifactRoot "run-meta.json") -Value $runMeta -Encoding UTF8
Write-Host "artifacts: $artifactRoot"

exit $benchmarkExitCode
