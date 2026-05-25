## Tasks

### Task 1: Create translation keys in zh.json
- Add all ~190 translation keys with Chinese values

### Task 2: Create translation keys in en.json
- Add all ~190 translation keys with English values

### Task 3: Replace strings in components
Files to update (in order):
1. `frontend/src/App.tsx` (~1 string)
2. `frontend/src/hooks/useResultDetection.ts` (~4 strings)
3. `frontend/src/components/EvidenceBasket.tsx` (~25 strings)
4. `frontend/src/components/AIDiagnosisButton.tsx` (~20 strings)
5. `frontend/src/components/ClusterProgress.tsx` (~4 strings)
6. `frontend/src/components/ClusterResult.tsx` (~15 strings)
7. `frontend/src/components/ConversationThread.tsx` (~10 strings)
8. `frontend/src/components/DiagnosisModeToggle.tsx` (~6 strings)
9. `frontend/src/components/DiagnosisActionBar.tsx` (~3 strings)
10. `frontend/src/components/AIQuestionCard.tsx` (~2 strings)
11. `frontend/src/components/UserContextInput.tsx` (~15 strings)
12. `frontend/src/components/SearchPanel.tsx` (~15 strings)
13. `frontend/src/components/layout/AppLayout.tsx` (~1 string)
14. `frontend/src/pages/DiagnosisStudioPage.tsx` (~60 strings)
15. `frontend/src/pages/AnalysisTasksPage.tsx` (~40 strings)

### Task 4: Verify
- [ ] All hardcoded Chinese strings replaced
- [ ] Both languages display correctly
- [ ] No runtime errors from missing keys
