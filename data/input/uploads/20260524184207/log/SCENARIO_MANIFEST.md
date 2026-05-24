# Thread Doctor Log Scenario Manifest

This archive is generated for basic functional testing of log scanning, stacktrace merging, clustering, timeline building, evidence pack generation, Codex task generation, and OpenSpec change draft generation.

## Expected scenarios

1. Redis pool exhaustion + Redis IO timeout + lock amplification
   - TraceId: TD-REDIS-20260505-0001
   - Main files: log/myservice1/log/collect/collect.log, log/myservice1/log/diagnostic/jstack-20260505-102120.log
   - Expected clusters: JedisConnectionException, SocketTimeoutException, TimeoutException
   - Suspected classes: RedisCacheClient, CacheRefreshService, CacheRefreshTask, DeviceQueryService

2. DB connection pool exhaustion + slow SQL + ingestion backlog
   - TraceId: TD-DB-20260505-0002
   - Main file: log/myservice1/log/ingestion/ingestrion.log
   - Expected clusters: SQLTransientConnectionException, HikariPool timeout, Slow SQL
   - Suspected classes: DynamicDataRepository, BatchInsertService, BatchInsertWorker

3. Kafka lag increase + rebalance + producer timeout
   - TraceId: TD-KAFKA-20260505-0003
   - Main file: log/myservice2/log/collect/collect.log
   - Expected clusters: consumer lag increased, TimeoutException
   - Suspected classes: CacheSyncConsumer, CacheSyncProducer

4. Thread pool queue full + rejected execution
   - TraceId: TD-THREADPOOL-20260505-0004
   - Main file: log/myservice2/log/common.log
   - Expected clusters: RejectedExecutionException, Worker pool pressure high
   - Suspected classes: TaskSubmitter, DispatchMonitor

5. JVM Full GC pressure + OOM
   - TraceId: TD-JVM-20260505-0005
   - Main file: log/myservice3/log/root.log
   - Expected clusters: Full GC pause, OutOfMemoryError
   - Suspected classes: ReportExportService, ReportController

## Normal logs
Each service also contains normal INFO logs for health checks, collect, ingestion, and common processing. These are intended to test noise filtering.
