## 1. Backend - Cluster Analyzer Module

- [x] 1.1 Create `diagnose_tool/analyzer/cluster_analyzer.py` with `ClusterAnalyzer` class
- [x] 1.2 Implement `ClusterResult` and `ClusterGroup` dataclasses
- [x] 1.3 Implement `CaseTextExtractor` for extracting root_cause/solution/summary from case.md
- [x] 1.4 Implement `_scan_and_extract_errors()` method - extract ERROR/WARN lines
- [x] 1.5 Implement `_aggregate_clusters()` method - reuse log_aggregator, add time distribution
- [x] 1.6 Implement `_match_historical_cases()` method - dual track matching
- [x] 1.7 Implement `_write_result()` method - write cluster-result.json
- [x] 1.8 Implement progress tracking via progress.json updates at each phase

## 2. Backend - API Routes

- [x] 2.1 Create `diagnose_tool/api/routes_cluster.py`
- [x] 2.2 Implement `POST /api/cluster` - create task, return task_id, start async job
- [x] 2.3 Implement `GET /api/cluster/{task_id}` - return progress or full results
- [x] 2.4 Add task not found HTTP 404 handling
- [x] 2.5 Register router in FastAPI app

## 3. Backend - Async Job Management

- [x] 3.1 Implement background task runner (use threading or FastAPI BackgroundTasks)
- [x] 3.2 Ensure task directory creation under data/output/{task_id}/
- [x] 3.3 Ensure progress.json is written before returning POST response

## 4. Frontend - API Client

- [x] 4.1 Create `frontend/src/api/cluster.ts` with API call functions
- [x] 4.2 Implement `createClusterTask(source_path)` → task_id
- [x] 4.3 Implement `pollClusterTask(task_id)` → ClusterStatus

## 5. Frontend - Components

- [x] 5.1 Create `frontend/src/components/ClusterProgress.tsx` - progress bar component
- [x] 5.2 Create `frontend/src/components/ClusterResult.tsx` - cluster display component
- [x] 5.3 Create `frontend/src/components/MatchedCaseCard.tsx` - matched case info card (integrated in ClusterResult.tsx)
- [x] 5.4 Create `frontend/src/pages/ClusterResult.tsx` - full result page (integrated in AnalysisTasksPage)

## 6. Frontend - Integration

- [x] 6.1 Add clustering trigger button in analysis options UI
- [x] 6.2 Connect progress polling on task creation
- [x] 6.3 Display cluster results with matched historical cases
- [x] 6.4 Handle "无匹配案例，建议 AI 诊断" case

## 7. Testing

- [x] 7.1 Write unit tests for ClusterAnalyzer._aggregate_clusters()
- [x] 7.2 Write unit tests for CaseTextExtractor
- [x] 7.3 Write unit tests for dual-track matching scoring
- [x] 7.4 Write integration tests for POST /api/cluster
- [x] 7.5 Write integration tests for GET /api/cluster/{task_id} polling
- [x] 7.6 Write frontend tests for ClusterProgress component

## 8. Documentation

- [x] 8.1 Update CLAUDE.md if architecture decisions change
- [x] 8.2 Add API documentation for cluster endpoints