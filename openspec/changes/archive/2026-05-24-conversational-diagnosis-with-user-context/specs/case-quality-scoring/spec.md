# Spec: case-quality-scoring

## Spec ID

`case-quality-scoring`

## Change ID

`conversational-diagnosis-with-user-context`

## Overview

Case 质量评分能力。根据对话轮数、用户反馈、AI 置信度评估诊断质量，决定自动晋升或进入草稿箱。

---

## ADDED Requirements

### Requirement: 质量评分维度

系统 SHALL 根据以下维度评估诊断质量：
1. **对话轮数**：轮数 >= 2 得满分，1 轮得低分
2. **用户追问次数**：用户主动追问越多表示越有价值
3. **AI 置信度**：LLM 返回的置信度评分（如果支持）
4. **信息完整度**：用户是否提供了堆栈、现象、入参等关键信息

#### Scenario: 高质量诊断
- **WHEN** 对话 >= 3 轮且用户提供了堆栈信息
- **THEN** 系统判定为高质量，建议自动晋升为正式 case

#### Scenario: 低质量诊断
- **WHEN** 对话只有 1 轮且无堆栈信息
- **THEN** 系统判定为低质量，存入草稿箱

### Requirement: 自动晋升机制

高质量诊断（评分 >= 阈值）SHALL 自动晋升为正式 case。

#### Scenario: 高质量自动晋升
- **WHEN** 诊断结束且质量评分 >= 8（满分 10）
- **THEN** 系统自动创建正式 case 并存入 `data/cases/`

### Requirement: 草稿箱机制

低质量诊断（评分 < 阈值）SHALL 存入草稿箱。

#### Scenario: 低质量进入草稿箱
- **WHEN** 诊断结束且质量评分 < 8
- **THEN** 系统创建草稿 case 并存入 `data/cases/_drafts/`

### Requirement: 草稿晋升

用户 SHALL 能够将草稿箱中的 case 晋升为正式 case。

#### Scenario: 手动晋升草稿
- **WHEN** 用户查看草稿箱并点击「确认质量，晋升为正式 case」
- **THEN** 系统将 case 从 `_drafts/` 移动到正式目录

### Requirement: 草稿清理

超过 30 天未晋升的草稿 SHALL 被自动清理。

#### Scenario: 草稿自动过期
- **WHEN** 草稿 case 创建时间超过 30 天
- **THEN** 系统删除该草稿目录

### Requirement: 评分详情可见

用户 SHALL 能够查看诊断的质量评分和评分依据。

#### Scenario: 查看评分详情
- **WHEN** 用户在 case 详情页查看诊断
- **THEN** 系统展示质量评分和各维度得分

---

## Scoring Formula

```
total_score = (
  conversation_rounds_score * 0.3 +
  user_questions_score * 0.2 +
  completeness_score * 0.3 +
  ai_confidence_score * 0.2
)

其中：
- conversation_rounds_score: 1轮=2分, 2轮=6分, 3轮+=10分
- user_questions_score: (追问次数 / 5) * 10，上限10分
- completeness_score: 有堆栈=4分 + 有现象=3分 + 有入参=3分
- ai_confidence_score: LLM返回的置信度（0-1）* 10

阈值：
- >= 8: 自动晋升
- < 8: 进入草稿箱
```

---

## Data Formats

### `data/cases/_drafts/{draft_id}/quality-score.json`

```json
{
  "draft_id": "uuid",
  "total_score": 7.5,
  "breakdown": {
    "conversation_rounds": { "score": 10, "raw": 3 },
    "user_questions": { "score": 4, "raw": 2 },
    "completeness": { "score": 7, "has_stack": true, "has_phenomenon": true, "has_params": false },
    "ai_confidence": { "score": 8, "raw": 0.8 }
  },
  "recommendation": "auto-promote",
  "created_at": "2026-05-24T10:30:00Z"
}
```

---

## Acceptance Criteria

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC1 | 高质量诊断自动晋升 | 集成测试 |
| AC2 | 低质量诊断进入草稿箱 | 集成测试 |
| AC3 | 草稿可以手动晋升 | 集成测试 |
| AC4 | 30天草稿自动清理 | 定时任务测试 |
| AC5 | 评分详情正确展示 | 前端测试 |
| AC6 | 评分计算公式正确 | 单元测试 |
