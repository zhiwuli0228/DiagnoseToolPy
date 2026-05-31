"""Conversation state machine — pure Python, FastAPI-independent."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from diagnose_tool.analyzer.session_store import SessionMetadata, SessionStore, TurnRecord

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Conversation lifecycle states."""
    WAITING_FOR_INPUT = "waiting_for_input"
    AWAITING_USER_REPLY = "awaiting_user_reply"
    DIAGNOSIS_COMPLETE = "diagnosis_complete"
    SKIPPED = "skipped"


@dataclass
class UserContext:
    """Parsed user input with structured markers."""
    phenomenon: str = ""
    stack: str = ""
    params: str = ""

    @classmethod
    def parse(cls, text: str) -> UserContext:
        """Parse user input with ##现象, ##堆栈, ##入参 markers."""
        parts = cls._extract_sections(text)
        return cls(
            phenomenon=parts.get("现象", "").strip(),
            stack=parts.get("堆栈", "").strip(),
            params=parts.get("入参", "").strip(),
        )

    @classmethod
    def _extract_sections(cls, text: str) -> dict[str, str]:
        """Extract sections by ##marker headers."""
        sections: dict[str, str] = {}
        current_section = None
        current_content: list[str] = []

        for line in text.splitlines():
            header_match = re.match(r"^##\s*(\S+)\s*$", line.strip())
            if header_match:
                if current_section is not None:
                    sections[current_section] = "\n".join(current_content)
                current_section = header_match.group(1)
                current_content = []
            else:
                current_content.append(line)

        if current_section is not None:
            sections[current_section] = "\n".join(current_content)

        return sections

    def to_dict(self) -> dict[str, str]:
        return {
            "phenomenon": self.phenomenon,
            "stack": self.stack,
            "params": self.params,
        }

    def is_complete(self) -> bool:
        """Check if context has sufficient information."""
        return bool(self.phenomenon or self.stack or self.params)

    def missing_fields(self) -> list[str]:
        """Return list of missing context fields."""
        missing = []
        if not self.phenomenon:
            missing.append("问题现象")
        if not self.stack:
            missing.append("堆栈信息")
        if not self.params:
            missing.append("关键入参")
        return missing


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation."""
    turn_number: int
    user_context: UserContext
    evidence_refs: list[str]
    mode: str
    ai_question: str | None = None
    ai_diagnosis: str | None = None
    state: ConversationState = ConversationState.WAITING_FOR_INPUT
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_record(self) -> TurnRecord:
        return TurnRecord(
            turn_id=f"{self.turn_number:03d}",
            user_context=self.user_context.to_dict(),
            evidence_refs=self.evidence_refs,
            ai_question=self.ai_question,
            ai_diagnosis=self.ai_diagnosis,
            mode=self.mode,
            timestamp=self.timestamp,
        )

    @classmethod
    def from_record(cls, record: TurnRecord) -> ConversationTurn:
        ctx = UserContext(
            phenomenon=record.user_context.get("phenomenon", ""),
            stack=record.user_context.get("stack", ""),
            params=record.user_context.get("params", ""),
        )
        return cls(
            turn_number=int(record.turn_id),
            user_context=ctx,
            evidence_refs=record.evidence_refs,
            mode=record.mode,
            ai_question=record.ai_question,
            ai_diagnosis=record.ai_diagnosis,
            state=ConversationState.DIAGNOSIS_COMPLETE if record.ai_diagnosis else ConversationState.AWAITING_USER_REPLY,
            timestamp=record.timestamp,
        )


class ConversationManager:
    """Manages the conversation state machine."""

    def __init__(
        self,
        session_store: SessionStore,
        data_dir: Path,
        max_follow_up_rounds: int = 3,
    ) -> None:
        self._store = session_store
        self._data_dir = Path(data_dir)
        self._max_follow_up_rounds = max_follow_up_rounds

    def create_or_continue(
        self,
        session_id: str | None,
        user_context: UserContext,
        evidence_refs: list[str],
        mode: str = "user-priority",
    ) -> tuple[SessionMetadata, ConversationTurn, bool]:
        """Create a new session or continue an existing one.

        Args:
            session_id: Existing session_id or None to create new.
            user_context: Parsed user input.
            evidence_refs: Selected log evidence IDs.
            mode: Diagnosis priority mode.

        Returns:
            Tuple of (session_metadata, current_turn, is_new_session).
        """
        is_new = False

        if session_id:
            try:
                metadata = self._store.get_session(session_id)
                history = self._store.get_conversation_history(session_id)
                if history:
                    last_turn = ConversationTurn.from_record(history[-1])
                    if last_turn.state == ConversationState.AWAITING_USER_REPLY:
                        # Continue the existing session
                        pass
            except Exception:
                # Session not found, create new
                session_id = None

        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            metadata = self._store.create_session(session_id, mode)
            is_new = True

        # Create new turn
        turn_number = len(self._store.get_session(session_id).turns) + 1
        turn = ConversationTurn(
            turn_number=turn_number,
            user_context=user_context,
            evidence_refs=evidence_refs,
            mode=mode,
            state=ConversationState.WAITING_FOR_INPUT,
        )

        return metadata, turn, is_new

    def process_turn(
        self,
        session_id: str,
        turn: ConversationTurn,
    ) -> tuple[ConversationState, str | None, str | None]:
        """Process a conversation turn.

        Evaluates whether to generate a diagnosis or ask a follow-up question.

        Args:
            session_id: Session identifier.
            turn: Current turn to process.

        Returns:
            Tuple of (new_state, ai_question, ai_diagnosis).
        """
        missing = turn.user_context.missing_fields()

        if not missing or turn.turn_number > self._max_follow_up_rounds:
            # Sufficient information or max rounds reached
            state = ConversationState.DIAGNOSIS_COMPLETE
            if turn.turn_number > self._max_follow_up_rounds:
                state = ConversationState.SKIPPED
            return state, None, "基于提供的信息生成了诊断结论。"

        # Need more information
        question = self._generate_follow_up_question(missing, turn.user_context)
        turn.ai_question = question
        turn.state = ConversationState.AWAITING_USER_REPLY

        return ConversationState.AWAITING_USER_REPLY, question, None

    def continue_conversation(
        self,
        session_id: str,
        turn_id: str,
        user_reply: str,
    ) -> tuple[ConversationTurn, ConversationState]:
        """Process a user reply to a follow-up question.

        Args:
            session_id: Session identifier.
            turn_id: Turn being continued.
            user_reply: User's reply to the question.

        Returns:
            Tuple of (updated_turn, new_state).
        """
        record = self._store.get_turn(session_id, turn_id)
        current_turn = ConversationTurn.from_record(record)

        # Append reply to the appropriate context field
        # This is simplified - in production, might need smarter merging
        reply_ctx = UserContext.parse(user_reply)
        if reply_ctx.phenomenon:
            if current_turn.user_context.phenomenon:
                current_turn.user_context.phenomenon += "\n" + reply_ctx.phenomenon
            else:
                current_turn.user_context.phenomenon = reply_ctx.phenomenon
        if reply_ctx.stack:
            if current_turn.user_context.stack:
                current_turn.user_context.stack += "\n" + reply_ctx.stack
            else:
                current_turn.user_context.stack = reply_ctx.stack
        if reply_ctx.params:
            if current_turn.user_context.params:
                current_turn.user_context.params += "\n" + reply_ctx.params
            else:
                current_turn.user_context.params = reply_ctx.params

        current_turn.turn_number += 1
        current_turn.timestamp = datetime.now(timezone.utc).isoformat()

        return current_turn, ConversationState.WAITING_FOR_INPUT

    def skip_follow_up(self, session_id: str, turn_id: str) -> ConversationTurn:
        """Skip follow-up questions and force diagnosis.

        Args:
            session_id: Session identifier.
            turn_id: Turn to skip.

        Returns:
            Updated turn with SKIPPED state.
        """
        record = self._store.get_turn(session_id, turn_id)
        current_turn = ConversationTurn.from_record(record)
        current_turn.state = ConversationState.SKIPPED
        current_turn.ai_diagnosis = (
            "以下结论基于不完整信息，仅供参考。\n\n"
            "系统在您跳过追问后基于现有信息给出诊断。"
        )
        return current_turn

    def end_conversation(self, session_id: str) -> SessionMetadata:
        """End a conversation session.

        Args:
            session_id: Session to end.

        Returns:
            Updated session metadata.
        """
        metadata = self._store.get_session(session_id)
        metadata.status = "completed"
        self._store.update_session(metadata)
        return metadata

    def save_turn(self, session_id: str, turn: ConversationTurn) -> None:
        """Persist a turn to storage.

        Args:
            session_id: Session identifier.
            turn: Turn to save.
        """
        record = turn.to_record()
        self._store.add_turn(session_id, record)

    def _generate_follow_up_question(
        self,
        missing_fields: list[str],
        ctx: UserContext,
    ) -> str:
        """Generate a follow-up question based on missing fields."""
        questions = []

        if "堆栈信息" in missing_fields:
            questions.append("请提供异常堆栈信息（如有），这有助于定位问题根因。")
        if "问题现象" in missing_fields:
            questions.append("请描述具体的问题现象，例如错误信息、响应时间异常等。")
        if "关键入参" in missing_fields:
            questions.append("请提供相关的关键入参或调用参数。")

        if not questions:
            questions.append("请问还有什么其他信息可以补充？")

        return "为了更准确诊断，请您补充以下信息：\n\n" + "\n".join(
            f"{i}. {q}" for i, q in enumerate(questions, 1)
        )
