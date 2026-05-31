## Context

### Background
当前诊断工具的分析流程是：日志 → AI 诊断 → 结果。用户面对大量原始异常日志时缺乏快速定位能力，且 AI 诊断耗时较长，无法即时给出方向性提示。

### Current State
- `log_aggregator.py`：已有按 Exception 类和消息模板聚类能力
- `keyword_search.py` / `rule_matcher.py`：已有历史案例检索能力（基于 metadata.yaml）
- `case.md`：历史案例正文，但尚未被检索系统利用
- 现有 Task 输出目录有 `progress.json` 进度追踪机制

### Constraints
- 日志可能很大（GB 级别），必须流式处理，不能全量加载
- 分析结果 Session 级，不持久化
- 案例经验持久化在 `data/cases/`，不依赖 Session

### Stakeholders
- 需要快速定位问题的运维/开发工程师
- 希望减少 AI 诊断等待时间的用户

---

## Goals / Non-Goals

**Goals:**
- 提供"异常聚类 + 历史匹配"的快速路径，不依赖 AI
- 前端可轮询进度，显示分析状态
- 每组异常展示：类名、次数、典型样本、时间分布、匹配案例
- 聚类结果 Session 级，分析过程不阻塞用户

**Non-Goals:**
- 不替代 AI 诊断，只是前置增强
- 不修改现有 case 持久化格式
- 不做实时流式聚类（批量分析场景）

---

## Decisions

### Decision 1: 异步任务架构

**Chosen**: 后台任务 + 前端轮询进度
**Rationale**: 日志分析耗时不确定，同步接口会导致超时。轮询方案简单可靠，已有的 `progress.json` 机制可复用。

**Alternative**: WebSocket 推送进度 → 复杂度高，需要额外基础设施

### Decision 2: 历史案例匹配双轨机制

**Chosen**: metadata.yaml 字段匹配 + case.md 正文提取并行
**Rationale**:
- metadata 丰富时优先用 metadata（快速、准确）
- metadata 简单时从 case.md 正文提取 root cause / solution / summary 补充
- 正文提取成本低，可作为兜底方案

**Alternative**: 只用 metadata → 案例少时效果差
**Alternative**: 只用正文 → 无法利用结构化信息优势

### Decision 3: 聚类输入源

**Chosen**: ERROR/WARN/WARNING 行提取作为聚类输入
**Rationale**: 用户通常关注异常事件，扫描全量日志成本高。ERROR/WARN/WARNING 是最直接的异常信号。

**Alternative**: 全量日志聚类 → 噪声多，计算量大

### Decision 4: 进度分段

**Chosen**: 四段进度 (20%/50%/80%/100%)
**Rationale**: 便于用户理解当前阶段，同时不过度细化（避免进度抖动）

```
[20%] 扫描日志，提取 ERROR/WARN
[50%] 异常聚类
[80%] 历史案例匹配
[100%] 完成
```

---

## Data Flow

```
POST /api/cluster
    │
    ├─→ 创建 task 目录 data/output/{task_id}/
    │       └─→ 写入 progress.json { status: "scanning", progress: 20 }
    │
    ├─→ 后台线程启动（异步）
    │       │
    │       ├─ [20%] scan_directory() 扫描日志文件
    │       │       └─→ 提取所有 ERROR/WARN 行
    │       │       └─→ 更新 progress.json { status: "scanning", progress: 20 }
    │       │
    │       ├─ [50%] aggregate_log_lines() 聚类
    │       │       └─→ 按 Exception 类分组
    │       │       └─→ 每组提取典型样本、时间分布
    │       │       └─→ 更新 progress.json { status: "aggregating", progress: 50 }
    │       │
    │       ├─ [80%] 匹配历史案例
    │       │       ├─ keyword_search() metadata 字段匹配
    │       │       ├─ rule_matcher() 规则匹配
    │       │       └─ case_text_extraction() 正文提取
    │       │       └─→ 更新 progress.json { status: "matching", progress: 80 }
    │       │
    │       └─ [100%] 输出结果
    │               └─→ 写入 cluster-result.json
    │               └─→ 更新 progress.json { status: "done", progress: 100 }
    │
    └← 返回 { task_id }

GET /api/cluster/{task_id}
    │
    ├─→ 读取 progress.json
    │
    ├─→ if status == "done":
    │       ├─ 读取 cluster-result.json
    │       └─→ 返回完整结果
    │
    └─→ if status in ("scanning", "aggregating", "matching"):
            └─→ 返回 { status, progress, current_step }
```

---

## API Design

### POST /api/cluster

**Request:**
```json
{ "source_path": "/path/to/logs" }
```

**Response:**
```json
{ "task_id": "cluster-20260523-001" }
```

### GET /api/cluster/{task_id}

**Response (running):**
```json
{
  "status": "aggregating",
  "progress": 50,
  "current_step": "异常聚类中..."
}
```

**Response (done):**
```json
{
  "status": "done",
  "progress": 100,
  "current_step": "分析完成",
  "clusters": [
    {
      "exception_class": "JedisConnectionException",
      "count": 127,
      "sample_messages": ["Connection refused: /127.0.0.1:6379", "...],
      "time_distribution": { "peak_hour": "14:00-15:00", "range": "13:30-15:30" },
      "matched_cases": [
        {
          "case_id": "case#42",
          "score": 0.85,
          "summary": "连接池耗尽，常见于高并发场景",
          "root_cause": "连接池配置过小",
          "solution": "调大连接池 maxTotal"
        }
      ]
    }
  ]
}
```

---

## Module Design

### ClusterAnalyzer (diagnose_tool/analyzer/cluster_analyzer.py)

```python
class ClusterAnalyzer:
    """异步聚类 + 历史匹配 orchestrator"""

    def run(self, task_id: str, source_path: str) -> ClusterResult:
        """主流程"""
        ...

    def _scan_and_extract_errors(self, ...)  # 20%
    def _aggregate_clusters(self, ...)       # 50%
    def _match_historical_cases(self, ...)    # 80%
    def _write_result(self, ...)             # 100%
```

### ClusterResult (dataclass)

```python
@dataclass
class ClusterGroup:
    exception_class: str
    count: int
    sample_messages: list[str]
    time_distribution: dict
    matched_cases: list[MatchedCase]

@dataclass
class MatchedCase:
    case_id: str
    score: float
    summary: str
    root_cause: str | None
    solution: str | None
```

### CaseTextExtractor

从 case.md 提取结构化信息：
- `## Root Cause` section → root_cause
- `## Solution` section → solution
- 首段/摘要段 → summary

---

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| 日志文件过大导致扫描慢 | 流式读取 + 采样上限 (默认 10w 行/组) |
| 历史案例为空时匹配无意义 | 展示"无匹配案例，建议 AI 诊断" |
| metadata 字段不丰富 | 正文提取兜底 |
| 进度轮询频率高 | 前端限制最小 2s 轮询间隔 |
| ZIP 内嵌 .gz 归档日志未解析 | `read_log_lines_in_archive()` 流式解析所有内嵌压缩文件 |
| 中文编码日志乱码 | 编码自动检测：采样前 4KB，高字节密度用 GB18030 |

---

## Open Questions

1. **采样上限**：每组异常最多保留多少条样本？默认 10 条够吗？
2. **case.md 正文提取的 section 名**：目前假设是 `## Root Cause` / `## Solution`，是否需要适配多种格式？
3. **Session 清理时机**：是前端主动通知后端清理，还是后台定时清理？