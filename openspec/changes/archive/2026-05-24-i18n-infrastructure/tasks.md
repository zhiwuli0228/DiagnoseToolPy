## Tasks

### Task 1: Install i18n dependencies
- Run: `cd frontend && npm install react-i18next i18next i18next-browser-languagedetector`

### Task 2: Create i18n configuration
- File: `frontend/src/i18n/index.ts`
- Configure i18next with react-i18next
- Enable browser language detector
- Set default language to Chinese

### Task 3: Create translation files
- File: `frontend/src/locales/en.json` (empty structure)
- File: `frontend/src/locales/zh.json` (with Chinese translations)

### Task 4: Integrate i18n in main.tsx
- File: `frontend/src/main.tsx`
- Import i18n configuration
- Wrap App with I18nextProvider

### Task 5: Verify
- [ ] npm install succeeds
- [ ] i18n configuration loads without error
- [ ] t() function works in components
