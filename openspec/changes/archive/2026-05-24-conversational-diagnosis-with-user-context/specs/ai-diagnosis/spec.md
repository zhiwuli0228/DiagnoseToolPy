# Spec: ai-diagnosis

## Spec ID

`ai-diagnosis`

## Change ID

`conversational-diagnosis-with-user-context`

## Overview

> **Delta Spec** — This file modifies the requirements from the original `ai-diagnosis` capability defined in change `add-ai-diagnosis-module`.

---

## MODIFIED Requirements

### Requirement: Diagnosis Orchestrator (F3)

**Original Behavior**: `DiagnosisOrchestrator` performs one-shot diagnosis, reads `evidence-pack.md`, builds prompt from template, calls LLM, saves result to `ai-diagnosis.md`.

**New Behavior**: `DiagnosisOrchestrator` supports conversational diagnosis mode. It SHALL accept user context with structured markers (`##现象`, `##堆栈`, `##入参`), maintain conversation state across turns, support active follow-up questioning when information is insufficient, and evaluate case quality after conversation ends.

#### Scenario: 单轮诊断（向后兼容）
- **WHEN** 用户只提供 task_id，无 session_id，且不提供 user_context
- **THEN** 系统执行单轮诊断（向后兼容原有行为）

#### Scenario: 多轮对话诊断
- **WHEN** 用户提供 session_id 和 user_context
- **THEN** 系统维护对话状态，支持多轮交互

### Requirement: Prompt 构建（F3，原 F7 移除/修改）

**Original Behavior**: Prompt built from `docs/05-domain/prompt-template.md` with `{evidence_pack}` and `{similar_cases}` placeholders.

**New Behavior**: Prompt 构建支持两种模式：
- **用户输入优先模式**: 用户上下文 → 日志证据 → 相似案例
- **日志优先模式**: 日志证据 → 用户上下文 → 相似案例

当信息不足时，Prompt 末尾附加追问指令，引导 LLM 生成追问问题。

#### Scenario: 用户输入优先模式
- **WHEN** mode = "user-priority"
- **THEN** prompt 结构为：用户上下文 → 日志证据 → 相似案例

#### Scenario: 日志优先模式
- **WHEN** mode = "log-priority"
- **THEN** prompt 结构为：日志证据 → 用户上下文 → 相似案例

### Requirement: 诊断结论存储（F3，新增存储结构）

**Original Behavior**: 诊断结果保存为 `data/cases/{case_id}/ai-diagnosis.md`。

**New Behavior**: 对话式诊断的完整对话历史保存到 `data/cases/{case_id}/conversation/` 目录，每个轮次保存为 `{turn_id}.json`。最终诊断结论保存为 `ai-diagnosis.md`。

---

## REMOVED Requirements

### Requirement: 一次性诊断结果格式（F9，原 ai-diagnosis.md 格式要求部分保留）

**Reason**: 对话式诊断的输出格式与单轮诊断不同，对话历史采用 JSON 格式，按轮次存储。最终诊断报告仍使用 markdown 格式，但结构有所调整。

**Migration**: 单轮诊断场景仍使用原有 `ai-diagnosis.md` 格式；多轮诊断场景使用新的目录结构存储对话历史，最终报告仍为 markdown。

---

## ADDED Requirements

### Requirement: 追问触发逻辑

系统 SHALL 在以下条件满足时触发追问：
1. 用户上下文缺少堆栈信息
2. 用户上下文缺少时间模式描述
3. 用户上下文缺少依赖服务信息
4. AI 置信度低于阈值（0.6）

#### Scenario: 触发追问
- **WHEN** 用户只提供了现象描述，无堆栈
- **THEN** LLM 在回复中包含追问问题

### Requirement: 追问轮数控制

系统 SHALL 支持配置最大追问轮数（默认 3 轮）。当达到最大轮数时，强制生成诊断结论。

#### Scenario: 追问轮数上限
- **WHEN** 当前轮次 >= max_follow_up_rounds（默认 3）
- **THEN** 系统不再生成追问，直接给出最终诊断结论

### Requirement: Case 质量评估触发

诊断会话结束后（用户主动结束或达到追问上限），系统 SHALL 触发 case 质量评估流程。

#### Scenario: 会话结束触发质量评估
- **WHEN** 用户点击「结束诊断」或达到最大追问轮数
- **THEN** 系统调用 case-quality-scoring 模块评估质量

### Requirement: 跳过追问

用户 SHALL 有权跳过追问，系统 SHALL 在收到 skip 请求后直接生成最终诊断结论，并在结论前添加「以下结论基于不完整信息」免责声明。

#### Scenario: 用户跳过追问
- **WHEN** 用户点击「跳过，直接给出诊断」
- **THEN** 系统生成最终诊断结论，结论前包含免责声明
