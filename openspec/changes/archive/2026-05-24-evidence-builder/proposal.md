## Why

用户通过搜索或聚类分析得到日志结果后，无法在前台快速组织成可供大模型诊断的证据资料。现有流程要求必须通过已完成的任务生成 `evidence-pack.md`，无法支持用户手动选择和组织特定日志条目。用户需要一个"证据构建器"来选择、组织证据内容，然后发送给大模型诊断。

## What Changes

### Backend Changes

1. **Search 缓存扩展**: 搜索结果执行后，将 matched_lines（带前后5行逻辑事件上下文）存入 `data/output/search-{timestamp}-{uuid}/matched-lines.jsonl`，返回 `cache_key` 供后续引用

2. **Cluster 缓存扩展**: 聚类分析执行后，在现有 `task_id` 目录下额外存储 `matched-lines.jsonl`，包含每个聚类组的原始日志行

3. **新增 API**: `POST /api/diagnosis/search` — 接收 `cache_key`, `selections`, `options`，从缓存读取日志，智能压缩后发送给 LLM，返回诊断结果

4. **新增 API**: `POST /api/diagnosis/cluster` — 同上，处理聚类结果的诊断

5. **智能压缩模块**: 后端对选中的日志进行去重、堆栈模式分析、时间统计，确保 LLM 输入在 token 预算内

### Frontend Changes

1. **聚合组展开**: 搜索/聚类的聚合结果默认收起，用户可展开查看匹配的原始日志行

2. **单条日志选择**: 展开后可单独勾选日志条目，支持"选组内所有日志"快捷操作

3. **证据篮 UI**: 右上角徽章显示已选项数量，点击展开预览列表，支持移除单项

4. **诊断调用**: 调用新的 `/api/diagnosis/search` 或 `/api/diagnosis/cluster` API

### Data Structures

**selections 请求结构**:
```json
{ "type": "group", "group_key": "..." }
{ "type": "group_all", "group_key": "..." }
{ "type": "log", "id": "hash123" }
{ "type": "cluster", "cluster_index": 0 }
```

**matched-lines.jsonl 结构**:
```json
{
  "id": "hash123",
  "group_key": "NullPointerException at OrderService",
  "event": { "timestamp": "", "level": "", "thread": "", "message": "", "raw": "", "file_path": "", "line_no": 0 },
  "context_before": [/* 前5个逻辑事件 */],
  "context_after": [/* 后5个逻辑事件 */]
}
```

## Capabilities

### New Capabilities

- `evidence-builder`: 用户从搜索结果和聚类结果中选择和组织日志证据，传给大模型诊断的能力。包括：后端缓存机制、智能压缩、前端证据篮 UI、新的诊断 API

### Modified Capabilities

- `evidence-report-generation`: 现有自动生成 evidence-pack 的能力不受影响，但聚类结果需要扩展返回 `matched_lines` 以支持证据选择

## Impact

### Backend
- 新增 `diagnose_tool/api/routes_diagnosis.py` 中的 `/diagnosis/search` 和 `/diagnosis/cluster` endpoints
- 新增 `diagnose_tool/analyzer/evidence_cache.py` 处理 matched-lines 缓存读写
- 新增 `diagnose_tool/analyzer/evidence_compressor.py` 智能压缩逻辑
- 聚类分析需要扩展返回 `matched_lines`（修改 `cluster_analyzer.py` 和 `routes_cluster.py`）

### Frontend
- `AnalysisTasksPage` 聚合组展开显示 matched_lines 表格（带勾选）
- 新增 `EvidenceBasket` 组件（徽章 + 预览抽屉）
- 新增 `DiagnosisButton` 处理新的诊断 API 调用

### Storage
- `data/output/search-{timestamp}-{uuid}/matched-lines.jsonl` — 搜索结果缓存
- `data/output/{cluster-task-id}/matched-lines.jsonl` — 聚类结果缓存
- 缓存生命周期：同一 path 的新搜索会覆盖旧缓存
