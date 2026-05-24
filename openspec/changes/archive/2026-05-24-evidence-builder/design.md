## Context

用户通过 `/api/source/search` 搜索日志或 `/api/cluster` 聚类分析后，得到聚合的异常组和样本消息。但用户无法选择特定日志条目组成证据包传给大模型诊断。现有 `/api/diagnosis` endpoint 只接受 `task_id`，从预生成的 `evidence-pack.md` 读取证据。

本设计引入"证据构建器"能力，允许用户：
1. 从搜索/聚类结果中选择日志条目或整组
2. 后端缓存选中的 matched_lines（带上下文）
3. 智能压缩后发送给 LLM
4. 返回诊断结果（暂不写盘）

## Goals / Non-Goals

**Goals:**
- 用户可从搜索结果的聚合组中选择日志条目
- 用户可从聚类结果的聚合组中选择日志条目
- 后端自动压缩选中日志（去重、堆栈模式分析）
- 支持"选组内所有日志"快捷操作
- 证据篮状态存储在内存/会话，页面刷新后清空
- 诊断结果仅返回文本，持久化按钮后续实现

**Non-Goals:**
- 不修改现有的 `evidence-pack.md` 生成逻辑
- 不改变聚类分析的核心算法
- 不实现案例持久化（诊断结果的 case 归档后续实现）
- 不支持多选时的拖拽排序

## Decisions

### 1. 缓存策略：Server-side cache with JSONL storage

**Decision**: 搜索/聚类的 matched_lines 存入 `data/output/{type}-{timestamp}-{uuid}/matched-lines.jsonl`，后端 API 读取缓存。

**Rationale**: 相比 Redis 等外部依赖，文件系统缓存无需额外服务，启动简单。JSONL 格式支持流式追加，内存友好。

**Alternative Considered**:
- **Memory-only cache**: 简单但无法跨请求共享，不适合 async 场景
- **Redis**: 需要额外依赖，增加部署复杂度

### 2. 上下文存储：按逻辑日志事件计算前后5行

**Decision**: 存储时按"逻辑日志事件"（主行+堆栈行）计算前后5个事件，而非物理行数。

**Rationale**: 日志分析以事件为单位，上下文应该围绕事件展开而非物理行。

**Alternative Considered**:
- **物理行数**: 堆栈跨越多行会导致上下文碎片化

### 3. 单条日志 ID：Hash-based stable ID

**Decision**: 每条 matched_lines 条目生成 `hash(sha256(file_path + line_no + timestamp))` 作为 stable ID。

**Rationale**: 相比自增索引，hash 更稳定，用户展开/收起后 ID 不变。

**Alternative Considered**:
- **自增索引**: 简单但不稳定，展开收起后可能变化
- **全局唯一 UUID**: 存储开销大，hash 足够定位

### 4. API 设计：分开 endpoints

**Decision**: `POST /api/diagnosis/search` 和 `POST /api/diagnosis/cluster` 分开。

**Rationale**: 搜索和聚类的缓存结构不同，分开避免 endpoint 内部判断逻辑。后续维护更清晰。

**Alternative Considered**:
- **统一 endpoint**: 传入 `type` 字段区分，增加内部分支判断

### 5. 智能压缩：按堆栈模式分组

**Decision**: 选中日志按堆栈模板归类，每类保留1条代表性日志+统计信息。

**Rationale**: 大量相似日志（如 NPE at OrderService x300）堆栈相同，只需一条+计数即可。

**压缩算法**:
1. 提取堆栈第一行（最可能区分不同代码路径）
2. 按堆栈模板分组
3. 每组保留1条+count+时间范围
4. 若 token 超限，进一步按组数采样

### 6. 诊断结果不写盘

**Decision**: `POST /api/diagnosis/search|cluster` 仅返回 diagnosis 文本，不写入 `data/cases/`。

**Rationale**: 简化本次迭代范围，持久化能力作为单独 feature。

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| 缓存文件积累占用磁盘 | 同一 path 新搜索覆盖旧缓存；可定期清理 `data/output/search-*/` |
| 大日志文件读取慢 | 使用流式读取 matched-lines.jsonl，不一次性加载 |
| LLM token 超限 | 压缩模块有 max_tokens 参数，默认 2000 |
| 用户选大量日志后卡顿 | 前端只展示，不做重计算；压缩在后端异步进行 |

## Open Questions

1. **缓存清理策略**: 是否需要后台任务定期清理？用户关闭页面后缓存保留多久？
2. **聚类 matched_lines 大小**: 聚类可能产生大量 matched_lines，是否需要限制每个 cluster 的存储数量？
3. **诊断结果预览**: 用户是否需要先预览压缩后的 evidence 再发送 LLM？
