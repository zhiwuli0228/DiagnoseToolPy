## ADDED Requirements

### Requirement: Frontend route components MUST be lazy-loaded

The application MUST load each of the 6 top-level page components
(Dashboard, Analysis Tasks, Casebase, AI Diagnosis, Diagnosis Studio,
Settings) via `React.lazy`, so the initial bundle does not contain
their code.

#### Scenario: First-screen bundle excludes page components

- **WHEN** `npm run build` produces `dist/assets/`
- **THEN** `DashboardPage` and the other 5 page files MUST appear only
  in dynamically-imported chunks, not in the main `index-*.js` chunk.

#### Scenario: Suspense fallback renders during route transition

- **WHEN** the user navigates to a route whose chunk is still loading
- **THEN** an Ant Design `<Spin />` MUST be visible as the fallback.
