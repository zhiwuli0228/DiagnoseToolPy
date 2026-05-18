# Meeting Log

## Code Review Sync Meeting

**日期**：2026-05-18 09:17 GMT+8
**议题**：代码审查报告合理性确认 + 修改方案确定
**主持人**：chief

---

## 议程

1. 逐一 review 审查问题，确认归因是否正确
2. 确定修复优先级和负责角色
3. 明确哪些问题本次不处理及理由

---

## 议题 1：审查问题逐条确认

### 问题 1.1：test_diagnosis.py 未使用变量 `original_chart`

**报告原文**：第 98 行赋值但从未使用的 `original_chat` 变量

**coder 意见**：
```python
original_chat = diag_module.LLMClient.chat  # F841
```
这是 patch 测试前的旧代码遗留，应该直接删除。

**结论**：✅ 确认，修复方案：删除该行。负责：coder。

---

### 问题 1.2：test_diagnosis.py 未使用 import

**报告原文**：`DiagnosisError` F401 未使用

**coder 意见**：
`DiagnosisError` 和 `TaskNotFoundError`、`EvidenceNotFoundError` 都在 `except` 块中直接使用字符串匹配（`if "TaskNotFoundError" in str(type(exc))`），而不是用 `isinstance` 判断，因此这些异常类没有被实际引用，只是测试用的类被实例化了。

**结论**：⚠️ 需要进一步确认——实际上异常类有被 `pytest.raises()` 使用。请再确认。

**requester 补充**：实际上 `DiagnosisError` 确实被导入但未在代码中引用（raise/except 均无直接使用），删除是正确的。`TaskNotFoundError` 和 `EvidenceNotFoundError` 有在 `except` 块中被 `isinstance` 或类型名匹配引用，需要保留。

**结论**：✅ 确认，`DiagnosisError` 可删除，`TaskNotFoundError` 和 `EvidenceNotFoundError` 保留。负责：coder。

---

### 问题 1.3：test_diagnosis_api.py 未使用 import

**报告原文**：`DiagnosisOrchestrator`、`EvidenceNotFoundError` F401

**coder 意见**：需要确认是否真的未使用。

**结论**：待确认后决定是否清理。

---

### 问题 1.4：test_llm_client.py 未使用 `threading` import

**报告原文**：F401 `threading` 未使用

**coder 意见**：确认，LLMClient 使用 `Semaphore` 但 threading 模块确实未直接引用，删除即可。

**结论**：✅ 确认，删除 `import threading`。负责：coder。

---

### 问题 1.5：test_llm_config.py 未使用 `yaml` 和 `AppLLMConfig` import

**报告原文**：F401

**coder 意见**：确认，yaml 和 AppLLMConfig 确实未使用，直接删除。

**结论**：✅ 确认，负责：coder。

---

### 问题 1.6：case_service.py Bare except 静默吞异常

**报告原文**：
```python
try:
    fault_case = load_case(case_dir)
    cases.append(fault_case)
except Exception:
    continue  # 静默跳过，无日志
```

**solution-designer 意见**：
这在 `get_all_cases()` 中是故意的——遍历时某个 case 损坏不应该导致整个列表失败。但确实需要加日志记录被跳过的 case，以便排查。

**结论**：✅ 确认，修复方案：加 `logger.warning(f"Skipped case {case_dir}: {exc}")`。负责：coder。

---

### 问题 1.7：routes_source.py 重复调用 load_config()

**报告原文**：
```python
def _validate_source_path(path: str):
    config = load_config()  # 每次请求都重新加载
```

**solution-designer 意见**：
当前 `load_config()` 读取 YAML 文件，每次 HTTP 请求都读一次。生产环境中这是性能浪费。

**结论**：✅ 确认，修复方案：使用 `functools.lru_cache` 或在应用启动时缓存到 app state。负责：solution-designer（决策架构），coder（实现）。

---

### 问题 1.8：node_modules 未在 .gitignore

**报告原文**：git status 大量 node_modules 变更

**reviewer 意见**：
需要确认 `.gitignore` 内容。如果 `frontend/node_modules/` 已在 .gitignore 中，则不是问题；如果不在，需要添加。

**结论**：待查证 .gitignore 内容后决定。

---

### 问题 1.9：LLMClient 类级别共享 Semaphore 线程问题

**报告原文**：多进程模式下每个 worker 有独立 semaphore 初值

**solution-designer 意见**：
当前 FastAPI + uvicorn 使用线程模型，没问题。如果是 Gunicorn prefork 模式，每个 worker 进程有独立 semaphore，这是预期行为（每个 worker 独立限流）。文档中无需特别说明。

**结论**：✅ 不是 bug，维持现状，不需要修改。

---

### 问题 1.10：前端代码无测试

**报告原文**：frontend/src 无 .test.ts 文件

**coder 意见**：
MVP 阶段可接受，后续补充。当前应聚焦后端功能完整性。

**结论**：✅ 确认，本次不做，后续补充。

---

## 议题 2：修复方案汇总

### 本次会议决定修改的问题

| # | 问题 | 修复方案 | 负责 | 优先级 |
|---|---|---|---|---|
| 1.1 | test_diagnosis.py 无用变量 | 删除 `original_chat` 赋值行 | coder | P2 |
| 1.2 | test_diagnosis.py 未使用 import | 删除 `DiagnosisError` import | coder | P2 |
| 1.4 | test_llm_client.py 未使用 import | 删除 `threading` import | coder | P2 |
| 1.5 | test_llm_config.py 未使用 import | 删除 `yaml` 和 `AppLLMConfig` import | coder | P2 |
| 1.6 | case_service.py bare except | 加 `logger.warning` | coder | P2 |
| 1.7 | load_config() 重复调用 | 加 `lru_cache` 或启动时缓存 | solution-designer + coder | P1 |

### 待查证后决定

| # | 问题 | 待查 | 负责 |
|---|---|---|---|
| 1.3 | test_diagnosis_api.py import | 确认是否真的未使用 | coder |
| 1.8 | node_modules .gitignore | 查证 .gitignore 内容 | reviewer |

### 本次会议决定不改的问题

| # | 问题 | 理由 |
|---|---|---|
| 1.9 | LLMClient 线程问题 | 不是 bug，维持现状 |
| 1.10 | 前端无测试 | MVP 阶段可接受 |

---

## 决策摘要

1. ✅ 确认问题 1.1/1.2/1.4/1.5/1.6 归因正确，修复方案明确
2. ⚠️ 问题 1.3/1.8 待查证
3. ✅ 问题 1.7 确认为性能问题，优先级 P1
4. ❌ 问题 1.9/1.10 本次不改

## 下一步行动

1. **coder**：修复问题 1.1/1.2/1.4/1.5/1.6，合并后重新运行 `uv run ruff check .` 验证
2. **coder**：查证问题 1.3（test_diagnosis_api.py），确认后清理
3. **reviewer**：查证问题 1.8（.gitignore），确认 frontend/node_modules 是否被追踪
4. **solution-designer**：设计问题 1.7 的缓存方案（lru_cache vs app state）

---

## 会议结束

下次开会时间：修复完成后审查结果
