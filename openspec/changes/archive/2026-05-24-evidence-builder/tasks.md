## 1. Backend: Cache Storage

- [x] 1.1 Create `diagnose_tool/analyzer/evidence_cache.py` for matched-lines JSONL read/write
- [x] 1.2 Modify `diagnose_tool/api/routes_source.py` search endpoint to store matched-lines.jsonl after search
- [x] 1.3 Modify `diagnose_tool/api/routes_cluster.py` to store matched-lines.jsonl after cluster analysis
- [x] 1.4 Implement `EvidenceCacheManager` class with get/put/list operations
- [x] 1.5 Implement logical event context calculation (5 events before/after)

## 2. Backend: Smart Compression Module

- [x] 2.1 Create `diagnose_tool/analyzer/evidence_compressor.py`
- [x] 2.2 Implement stack trace pattern extraction and grouping
- [x] 2.3 Implement compression with statistics (count, time range, peak window)
- [x] 2.4 Implement max_tokens budget enforcement
- [x] 2.5 Support include_stack and include_timeline options

## 3. Backend: Diagnosis API Endpoints

- [x] 3.1 Create `POST /api/diagnosis/search` endpoint in `routes_diagnosis.py`
- [x] 3.2 Create `POST /api/diagnosis/cluster` endpoint in `routes_diagnosis.py`
- [x] 3.3 Implement request validation (cache_key, selections, options)
- [x] 3.4 Implement cache retrieval and selection resolution
- [x] 3.5 Integrate compression module with LLM client
- [x] 3.6 Return diagnosis response without persisting to disk

## 4. Frontend: Evidence Basket Component

- [x] 4.1 Create `frontend/src/components/EvidenceBasket.tsx` with badge and preview
- [x] 4.2 Implement in-memory selection state management
- [x] 4.3 Implement add/remove selection operations
- [x] 4.4 Implement "select all in group" operation
- [x] 4.5 Implement clear basket operation

## 5. Frontend: Group Expansion UI

- [x] 5.1 Modify AnalysisTasksPage search results to show collapsible groups (default collapsed)
- [x] 5.2 Implement matched lines table within expanded group
- [x] 5.3 Add checkboxes for individual log entry selection
- [x] 5.4 Add "Select All" option per expanded group
- [x] 5.5 Connect selection state to EvidenceBasket component

## 6. Frontend: Cluster Result Expansion

- [x] 6.1 Modify ClusterResult component to support expansion
- [x] 6.2 Display matched_lines table when cluster group is expanded (pending backend matched_lines return)
- [x] 6.3 Add checkboxes for cluster group selection
- [x] 6.4 Connect selection state to EvidenceBasket component

## 7. Frontend: Diagnosis Integration

- [x] 7.1 Add diagnosis API calls for search results in `diagnosisApi.ts`
- [x] 7.2 Add diagnosis API calls for cluster results in `diagnosisApi.ts`
- [x] 7.3 Connect EvidenceBasket "Diagnose" button to new API
- [x] 7.4 Display diagnosis result in a modal or new section
- [x] 7.5 Handle loading and error states

## 8. Frontend: Cluster API Extension

- [x] 8.1 Extend `ClusterStatusResponse` to include `matched_lines` for each cluster
- [x] 8.2 Update `pollClusterTask` to return matched_lines when status is done
- [x] 8.3 Store matched_lines in cluster cache for later retrieval (done in cluster_analyzer.py)

## 9. Testing

- [x] 9.1 Write unit tests for evidence_cache.py
- [x] 9.2 Write unit tests for evidence_compressor.py
- [x] 9.3 Write integration tests for diagnosis endpoints
- [x] 9.4 Test frontend selection flow manually

## 10. Documentation

- [x] 10.1 Update API documentation for new endpoints
- [x] 10.2 Add frontend usage guide for evidence basket
