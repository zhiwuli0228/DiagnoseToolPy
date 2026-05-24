## 1. Backend: Session & Storage Foundation

- [x] 1.1 Create `diagnose_tool/analyzer/session_store.py` — session filesystem storage with metadata.yaml
- [x] 1.2 Create `diagnose_tool/analyzer/conversation_manager.py` — conversation state machine (create, continue, skip, end)
- [x] 1.3 Add session cleanup logic — remove sessions inactive > 7 days

## 2. Backend: JVM Stack Parser

- [x] 2.1 Create `diagnose_tool/analyzer/stack_parser.py` — core stack parsing (HotSpot, OpenJDK formats)
- [x] 2.2 Implement repeat frame detection and merging
- [x] 2.3 Implement same-package prefix merging
- [x] 2.4 Implement line count limit and truncation (default 50 lines)
- [x] 2.5 Add exception type and entry point extraction

## 3. Backend: LLM Integration & Question Generation

- [x] 3.1 Create `diagnose_tool/analyzer/question_generator.py` — two-phase LLM (evaluate sufficiency → generate question/diagnosis)
- [x] 3.2 Add max_follow_up_rounds configuration (default 3)
- [x] 3.3 Implement skip mechanism — force diagnosis with disclaimer

## 4. Backend: Case Quality Scorer

- [x] 4.1 Create `diagnose_tool/analyzer/case_quality_scorer.py` — scoring formula implementation
- [x] 4.2 Add auto-promote threshold (>= 8.0) logic
- [x] 4.3 Add draft case creation in `data/cases/_drafts/`
- [x] 4.4 Create draft cleanup cron job — remove drafts > 30 days

## 5. Backend: Conversation API Endpoints

- [x] 5.1 Create `diagnose_tool/api/routes_conversation.py` — new API endpoints
- [x] 5.2 Implement `POST /api/diagnosis/conversation` — create/continue session
- [x] 5.3 Implement `GET /api/diagnosis/conversation/{session_id}` — get session state and history
- [x] 5.4 Implement `POST /api/diagnosis/conversation/{session_id}/continue` — user responds to question
- [x] 5.5 Implement `POST /api/diagnosis/conversation/{session_id}/skip` — skip question, force diagnosis
- [x] 5.6 Implement `POST /api/diagnosis/conversation/{session_id}/end` — end session, trigger case quality scoring
- [x] 5.7 Update `diagnose_tool/main.py` to register new router

## 6. Backend: Modified Diagnosis Module

- [x] 6.1 Modify `diagnose_tool/analyzer/diagnosis.py` — DiagnosisOrchestrator to support user_context injection
- [x] 6.2 Add context priority mode (user-priority vs log-priority) to prompt building
- [x] 6.3 Update prompt templates to support structured markers (##现象, ##堆栈, ##入参)

## 7. Frontend: Session Management

- [x] 7.1 Create `frontend/src/hooks/useSession.ts` — session ID management (localStorage get/set)
- [x] 7.2 Add X-Session-ID header to all conversation API calls

## 8. Frontend: Diagnosis Studio Page

- [x] 8.1 Create `frontend/src/pages/DiagnosisStudioPage.tsx` — main diagnosis page (B2 layout)
- [x] 8.2 Add route in `frontend/src/App.tsx` for `/diagnosis-studio`
- [x] 8.3 Create `frontend/src/components/UserContextInput.tsx` — ##现象/##堆栈/##入参 input
- [x] 8.4 Create `frontend/src/components/DiagnosisModeToggle.tsx` — user-priority / log-priority toggle
- [x] 8.5 Create `frontend/src/components/ConversationThread.tsx` — conversation history display
- [x] 8.6 Create `frontend/src/components/AIQuestionCard.tsx` — AI question display with skip option
- [x] 8.7 Create `frontend/src/components/DiagnosisActionBar.tsx` — continue/skip/end buttons

## 9. Frontend: API Client

- [x] 9.1 Create `frontend/src/api/conversationApi.ts` — API client for conversation endpoints
- [x] 9.2 Add TypeScript types for conversation request/response

## 10. Frontend: Integration with Existing Components

- [x] 10.1 Integrate EvidenceBasket into DiagnosisStudio left panel
- [x] 10.2 Connect SearchLogsPanel to DiagnosisStudio
- [x] 10.3 Add "开始诊断" button to trigger first conversation turn

## 11. Storage & Cleanup

- [x] 11.1 Create `data/sessions/` directory structure
- [x] 11.2 Create `data/cases/_drafts/` directory structure
- [x] 11.3 Add backend cleanup jobs for sessions and drafts

## 12. Testing

- [x] 12.1 Add backend tests for session_store
- [x] 12.2 Add backend tests for stack_parser
- [x] 12.3 Add backend tests for case_quality_scorer
- [x] 12.4 Add backend tests for conversation endpoints (mock LLM)
- [x] 12.5 Add frontend tests for useSession hook
- [x] 12.6 Add frontend tests for ConversationThread component

## 13. Cleanup & Documentation

- [x] 13.1 Update CLAUDE.md with new API endpoints
- [x] 13.2 Consider deprecating or redirecting old AIDiagnosisPage
- [x] 13.3 Run `uv run ruff check` and fix any lint issues
- [x] 13.4 Run frontend `npm run build` to verify no build errors
