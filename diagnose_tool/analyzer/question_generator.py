"""LLM-based question generator for conversational diagnosis.

Two-phase approach:
  Phase 1: Evaluate whether user context is sufficient for diagnosis
  Phase 2A: Generate diagnosis if sufficient
  Phase 2B: Generate follow-up question if insufficient
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from diagnose_tool.core.llm_client import LLMClient, LLMClientError
from diagnose_tool.core.llm_config import AppLLMConfig

logger = logging.getLogger(__name__)


# --- Data Models --------------------------------------------------------


@dataclass
class SufficiencyResult:
    """Result of information sufficiency evaluation."""
    sufficient: bool
    missing: list[str]
    confidence: float
    reasoning: str


@dataclass
class DiagnosisResult:
    """Result of diagnosis generation."""
    diagnosis: str
    confidence: float | None = None
    from_incomplete: bool = False


@dataclass
class QuestionResult:
    """Result of follow-up question generation."""
    question: str
    topic: str


# --- Question Generator -------------------------------------------------


class QuestionGenerator:
    """Generates follow-up questions and diagnoses using LLM."""

    EVALUATION_SYSTEM_PROMPT = """你是一个诊断助手。你的任务是评估用户提供的上下文信息是否足以支撑一次有价值的诊断。

请根据以下标准评估：
1. 是否有问题现象描述（错误信息、异常行为、响应时间等）
2. 是否有堆栈信息（异常堆栈、调用栈）
3. 是否有关键入参（请求参数、环境信息）

请以JSON格式返回评估结果：
{
  "sufficient": true/false,
  "missing": ["缺失项1", "缺失项2"],
  "confidence": 0.0-1.0,
  "reasoning": "简要说明判断理由"
}"""

    EVALUATION_USER_PROMPT = """请评估以下用户上下文信息是否充分：

{user_context}

证据信息：
{evidence}

请判断是否足以支撑一次有价值的诊断。"""

    DIAGNOSIS_SYSTEM_PROMPT = """你是一个资深后端稳定性工程师。

根据提供的信息，分析问题并给出诊断结论。
- 如果信息充分，给出明确的根因分析和解决建议
- 如果信息不足但被强制要求诊断，明确标注"基于有限信息"
- 优先考虑常见问题：OOM、GC停顿、连接池耗尽、超时、并发问题

诊断结论应包含：
1. 最可能的根因
2. 支持证据
3. 可能的一连串影响
4. 立即缓解措施
5. 长期修复建议"""

    DIAGNOSIS_USER_PROMPT = """# 用户上下文

{user_context}

# 日志证据

{evidence}

# 诊断要求

{diagnosis_requirement}

{similar_cases}"""

    QUESTION_SYSTEM_PROMPT = """你是一个诊断助手。当用户上下文信息不足时，生成针对性的追问问题。

规则：
- 每次只问1-2个最关键的问题
- 问题要具体、可操作
- 不要重复用户已经提供的信息
- 优先询问对诊断最有价值的信息"""

    QUESTION_USER_PROMPT = """用户已提供了以下上下文信息：

{user_context}

以下信息仍然缺失：
{missing}

请生成1-2个针对性的追问问题，帮助用户补充最关键的信息。"""

    def __init__(
        self,
        llm_config: AppLLMConfig,
        data_dir: Path,
        max_follow_up_rounds: int = 3,
    ) -> None:
        self._llm = LLMClient(llm_config)
        self._data_dir = Path(data_dir)
        self._max_follow_up_rounds = max_follow_up_rounds

    def evaluate_sufficiency(
        self,
        user_context: dict[str, str],
        evidence: str,
    ) -> SufficiencyResult:
        """Evaluate if the provided context is sufficient for diagnosis.

        Args:
            user_context: Parsed user context dict with phenomenon, stack, params.
            evidence: Log evidence as formatted string.

        Returns:
            SufficiencyResult with evaluation details.
        """
        context_str = self._format_context(user_context)

        messages = [
            {"role": "system", "content": self.EVALUATION_SYSTEM_PROMPT},
            {"role": "user", "content": self.EVALUATION_USER_PROMPT.format(
                user_context=context_str,
                evidence=evidence or "无",
            )},
        ]

        try:
            response = self._llm.chat(messages=messages)
            return self._parse_evaluation_response(response)
        except LLMClientError:
            raise
        except Exception as exc:
            logger.warning("LLM evaluation failed: %s, assuming sufficient", exc)
            return SufficiencyResult(
                sufficient=True,
                missing=[],
                confidence=0.5,
                reasoning=f"评估失败，假设充分: {exc}",
            )

    def generate_diagnosis(
        self,
        user_context: dict[str, str],
        evidence: str,
        similar_cases: str,
        from_incomplete: bool = False,
    ) -> DiagnosisResult:
        """Generate a diagnosis based on provided context.

        Args:
            user_context: Parsed user context dict.
            evidence: Log evidence as formatted string.
            similar_cases: Similar historical cases context.
            from_incomplete: Whether diagnosis is forced from incomplete info.

        Returns:
            DiagnosisResult with diagnosis text and optional confidence.
        """
        context_str = self._format_context(user_context)
        requirement = (
            "结论可能不完整，仅供参考。"
            if from_incomplete
            else "请给出详细的诊断结论。"
        )

        messages = [
            {"role": "system", "content": self.DIAGNOSIS_SYSTEM_PROMPT},
            {"role": "user", "content": self.DIAGNOSIS_USER_PROMPT.format(
                user_context=context_str,
                evidence=evidence or "无日志证据",
                diagnosis_requirement=requirement,
                similar_cases=similar_cases,
            )},
        ]

        try:
            diagnosis = self._llm.chat(messages=messages)
            return DiagnosisResult(
                diagnosis=diagnosis,
                confidence=None,
                from_incomplete=from_incomplete,
            )
        except LLMClientError:
            raise
        except Exception as exc:
            logger.error("LLM diagnosis failed: %s", exc)
            return DiagnosisResult(
                diagnosis=f"诊断生成失败: {exc}",
                confidence=0.0,
                from_incomplete=True,
            )

    def generate_question(
        self,
        user_context: dict[str, str],
        missing: list[str],
    ) -> QuestionResult:
        """Generate a follow-up question based on missing information.

        Args:
            user_context: Parsed user context dict.
            missing: List of missing information types.

        Returns:
            QuestionResult with question text and topic.
        """
        context_str = self._format_context(user_context)

        messages = [
            {"role": "system", "content": self.QUESTION_SYSTEM_PROMPT},
            {"role": "user", "content": self.QUESTION_USER_PROMPT.format(
                user_context=context_str,
                missing="\n".join(f"- {m}" for m in missing),
            )},
        ]

        try:
            question = self._llm.chat(messages=messages)
            return QuestionResult(
                question=question,
                topic=missing[0] if missing else "general",
            )
        except LLMClientError:
            raise
        except Exception as exc:
            logger.error("LLM question generation failed: %s", exc)
            return QuestionResult(
                question="为了更好地诊断，请提供更多关于问题的详细信息。",
                topic="general",
            )

    def _format_context(self, user_context: dict[str, str]) -> str:
        """Format user context as a readable string."""
        parts = []

        if user_context.get("phenomenon"):
            parts.append(f"## 问题现象\n{user_context['phenomenon']}")
        if user_context.get("stack"):
            parts.append(f"## 堆栈信息\n{user_context['stack']}")
        if user_context.get("params"):
            parts.append(f"## 关键入参\n{user_context['params']}")

        return "\n\n".join(parts) if parts else "（用户未提供额外上下文）"

    def _parse_evaluation_response(self, response: str) -> SufficiencyResult:
        """Parse JSON response from LLM evaluation."""
        try:
            data = json.loads(response)
            return SufficiencyResult(
                sufficient=data.get("sufficient", True),
                missing=data.get("missing", []),
                confidence=data.get("confidence", 0.5),
                reasoning=data.get("reasoning", ""),
            )
        except json.JSONDecodeError:
            if match := re.search(r'"sufficient":\s*(true|false)', response, re.IGNORECASE):
                return SufficiencyResult(
                    sufficient=match.group(1).lower() == "true",
                    missing=[],
                    confidence=0.5,
                    reasoning="无法解析LLM响应",
                )
            return SufficiencyResult(
                sufficient=True,
                missing=[],
                confidence=0.5,
                reasoning=f"JSON解析失败: {response[:100]}",
            )
