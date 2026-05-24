## Why

当前诊断工具在日志分析后直接交由 AI 生成诊断结果，缺少对异常模式的预聚类和历史案例参考。用户面对大量原始异常日志时难以快速定位问题根因，且 AI 诊断耗时较长，无法即时给出方向性提示。

通过增加异常聚类 + 历史案例匹配功能，可在 AI 诊断之前先呈现"哪些异常最频繁、历史类似问题的经验是什么"，帮助工程师快速缩小排查范围，即使在案例库不丰富时也能通过正文提取获得有用参考。

## What Changes

### Backend
- 新增 `POST /api/cluster` 接口：接收日志路径，触发异步聚类任务
- 新增 `GET /api/cluster/{task_id}` 接口：轮询聚类进度和结果
- 新增 `diagnose_tool/analyzer/cluster_analyzer.py`：聚类 + 历史匹配的核心逻辑
- 进度追踪：基于现有 `data/output/{task_id}/progress.json` 机制

### Frontend
- 新增聚类触发入口（分析选项）
- 新增进度展示组件
- 新增聚类结果展示页（异常分组 + 历史案例匹配 + 元信息）

### 分析流程
1. 扫描日志，提取 ERROR/WARN/WARNING 行（包括 ZIP 内嵌 .gz 归档日志）
2. 按 Exception 类和归一化消息模板聚类
3. 对每组异常匹配历史案例（metadata.yaml 字段 + case.md 正文双轨）
4. 每组输出：异常类名、次数、典型样本、时间分布、匹配案例
5. 编码自动检测（UTF-8/GB18030）

### 生命周期
- 分析结果 Session 级（关页即清理）
- 案例/经验沉淀到 `data/cases/`，持久化不依赖 Session

## Capabilities

### New Capabilities
- `anomaly-clustering`: 异常聚类分析能力，支持按 Exception 类和消息模板分组，输出元信息
- `case-text-extraction`: 从 case.md 正文提取关键信息（root cause、solution、summary），辅助历史匹配
- `cluster-progress-tracking`: 异步任务进度追踪，支持前端轮询

### Modified Capabilities
- `log-reader-and-multiline`: 扩展日志扫描能力，支持 ERROR/WARN 行提取（聚类输入）
- `basic-case-retrieval`: 扩展检索能力，支持 metadata + case.md 正文双轨匹配

## Impact

### Backend
- `diagnose_tool/analyzer/` 新增 `cluster_analyzer.py`
- `diagnose_tool/api/` 新增 `routes_cluster.py`
- 不影响现有 `diagnosis` 流程，聚类为独立并行路径

### Frontend
- `src/pages/` 新增聚类结果展示组件
- `src/components/` 新增进度条组件
- `src/api/` 新增 cluster API 调用

### 数据
- 分析结果写入 `data/output/{task_id}/cluster-result.json`
- Session 级存储，前端关闭后不保留
- 案例持久化在 `data/cases/`，不受 Session 影响

### 依赖
- 复用现有 `log_aggregator.py`（聚类）
- 复用现有 `keyword_search.py`、`rule_matcher.py`（历史匹配）
- case.md 正文提取复用现有 reader 模块