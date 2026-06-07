param(
    [string]$SuiteId = "current_large_log_cluster_requirement",
    [string]$BaseUrl = "http://127.0.0.1:18080",
    [string]$BenchmarkConfig = "tests/load/analysis_benchmarks.yaml",
    [string]$SuiteConfig = "tests/load/acceptance_suites.yaml",
    [int]$SampleIntervalSeconds = 2
)

$ErrorActionPreference = "Stop"
$runId = Get-Date -Format "yyyyMMdd-HHmmss"
$artifactRoot = Join-Path "tests/load/artifacts" "acceptance-$runId"
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

$suiteJson = & uv run python tests/load/requirement_acceptance.py suite-profiles --config $SuiteConfig --suite $SuiteId
if ($LASTEXITCODE -ne 0) {
    Write-Error "failed to resolve acceptance suite profiles"
    exit $LASTEXITCODE
}
$suiteInfo = $suiteJson | ConvertFrom-Json
$profiles = @($suiteInfo.profiles)

Write-Host "suite $SuiteId profiles: $($profiles -join ', ')"

$prepareArgs = @("run", "python", "tests/load/prepare_analysis_datasets.py", "--config", $BenchmarkConfig)
foreach ($profile in $profiles) {
    $prepareArgs += @("--profile", $profile)
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

$benchmarkArgs = @(
    "run",
    "python",
    "tests/load/analysis_benchmark.py",
    "--config", $BenchmarkConfig,
    "--host", $BaseUrl,
    "--output-dir", $artifactRoot
)
foreach ($profile in $profiles) {
    $benchmarkArgs += @("--profile", $profile)
}

try {
    & uv @benchmarkArgs
    $benchmarkExitCode = $LASTEXITCODE
} finally {
    New-Item -ItemType File -Path $stopFile -Force | Out-Null
    Start-Sleep -Seconds ([Math]::Max(1, $SampleIntervalSeconds))
    if (-not $collector.HasExited) {
        Stop-Process -Id $collector.Id -Force -ErrorAction SilentlyContinue
    }
}

$finalizeJson = & uv run python tests/load/requirement_acceptance.py finalize --config $SuiteConfig --suite $SuiteId --artifacts-dir $artifactRoot --benchmark-exit-code $benchmarkExitCode
$finalizeExitCode = $LASTEXITCODE
if ($finalizeExitCode -eq 0) {
    Write-Host "acceptance summary generated"
} elseif ($benchmarkExitCode -ne 0) {
    Write-Error "benchmark failed; acceptance summary was skipped"
} else {
    Write-Error "acceptance run did not pass"
}

$finalizeInfo = $null
if ($finalizeJson) {
    $finalizeInfo = $finalizeJson | ConvertFrom-Json
}

$runMeta = [ordered]@{
    run_id = "acceptance-$runId"
    suite_id = $SuiteId
    host = $BaseUrl
    benchmark_config = $BenchmarkConfig
    suite_config = $SuiteConfig
    profiles = $profiles
    sample_interval_seconds = $SampleIntervalSeconds
    artifact_root = (Resolve-Path $artifactRoot).Path
    process_stats_csv = $statsPath
    benchmark_exit_code = $benchmarkExitCode
    acceptance_exit_code = $finalizeExitCode
    summary_generated = [bool]($finalizeInfo.summary_written)
    acceptance_passed = [bool]($finalizeInfo.passed)
    generated_at = [DateTime]::UtcNow.ToString("o")
} | ConvertTo-Json -Depth 4

Set-Content -Path (Join-Path $artifactRoot "acceptance-run-meta.json") -Value $runMeta -Encoding UTF8
Write-Host "acceptance artifacts: $artifactRoot"

exit $finalizeExitCode
