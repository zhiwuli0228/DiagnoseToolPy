## Purpose

Provide the React frontend shell, routing, and API proxy integration that form the UI foundation for DiagnoseToolPy without changing backend behavior.

## Requirements

### Requirement: Frontend Shell Application
The system SHALL provide a React-based frontend shell that serves as the UI foundation for DiagnoseToolPy.

#### Scenario: Frontend development server starts
- **WHEN** `npm run dev` is executed in the frontend directory
- **THEN** Vite starts on a development port (e.g., 3000)
- **AND** the application is accessible in a browser

#### Scenario: Frontend production build succeeds
- **WHEN** `npm run build` is executed in the frontend directory
- **THEN** a production build is generated in the `dist` directory
- **AND** the build completes without errors

### Requirement: API Proxy Configuration
The system SHALL configure the frontend development server to proxy API requests to the FastAPI backend.

#### Scenario: Frontend calls /api/health
- **WHEN** the frontend calls `GET /api/health`
- **THEN** the request is proxied to the FastAPI backend at localhost:18080
- **AND** the response is returned to the frontend

#### Scenario: Frontend calls /api/source/check
- **WHEN** the frontend calls `POST /api/source/check` with a directory path
- **THEN** the request is proxied to the FastAPI backend
- **AND** the response with directory validation result is returned

#### Scenario: Backend is unavailable
- **WHEN** the FastAPI backend is not running
- **THEN** the frontend receives a network error
- **AND** the UI displays an appropriate error state

### Requirement: Dashboard Page
The system SHALL provide a dashboard page as the entry point of the application.

#### Scenario: User opens the application root URL
- **WHEN** user navigates to the application URL
- **THEN** the dashboard page is displayed
- **AND** navigation cards are shown for main features (Directory Scan, Analysis Tasks, Casebase, Settings)

#### Scenario: User clicks a navigation card
- **WHEN** user clicks on a navigation card
- **THEN** the user is navigated to the corresponding page

### Requirement: Directory Scan Integration
The system SHALL provide UI integration for directory scanning that calls the existing backend APIs.

#### Scenario: User enters a directory path
- **WHEN** user enters a directory path in the analysis page input field
- **THEN** the frontend calls `POST /api/source/check` to validate the path
- **AND** displays whether the path is allowed

#### Scenario: User initiates a scan
- **WHEN** user clicks the scan button after path validation
- **THEN** the frontend calls `POST /api/source/scan`
- **AND** displays the scan results (file count, sizes, etc.)

#### Scenario: Scan is performed on invalid path
- **WHEN** user enters a path outside allowed roots
- **THEN** the backend returns a validation error
- **AND** the frontend displays the error message

### Requirement: Navigation and Routing
The system SHALL provide client-side routing for all main pages.

#### Scenario: User navigates to /analysis
- **WHEN** user navigates to `/analysis`
- **THEN** the AnalysisTasksPage component is rendered
- **AND** the sidebar navigation highlights the Analysis item

#### Scenario: User navigates to /settings
- **WHEN** user navigates to `/settings`
- **THEN** the SettingsPage component is rendered
- **AND** configured input roots are displayed (or placeholder if not configured)

#### Scenario: User navigates to /cases
- **WHEN** user navigates to `/cases`
- **THEN** the CasebasePage component is rendered
- **AND** displays placeholder content for future case list functionality

### Requirement: Page Placeholder States
The system SHALL display clear placeholder content for features not yet implemented.

#### Scenario: User opens Task Detail page
- **WHEN** user navigates to `/analysis/:taskId`
- **THEN** the TaskDetailPage shows placeholder content indicating this feature is under development

#### Scenario: User opens Case Detail page
- **WHEN** user navigates to `/cases/:caseId`
- **THEN** the CaseDetailPage shows placeholder content indicating this feature is under development

### Requirement: Error State Handling
The system SHALL display appropriate error states when backend API calls fail.

#### Scenario: API call returns an error response
- **WHEN** a backend API call returns a non-2xx status code
- **THEN** the frontend displays an error message to the user
- **AND** the error is logged for debugging

#### Scenario: Network request fails
- **WHEN** a network error occurs (backend unavailable, CORS, etc.)
- **THEN** the frontend displays a "Unable to connect to server" message
- **AND** suggests checking if the backend is running

### Requirement: Frontend Documentation
The system SHALL provide documentation for frontend development workflow.

#### Scenario: Developer reads frontend development guide
- **WHEN** a developer reads the frontend development documentation
- **THEN** they can find commands to install dependencies, start dev server, and build for production
- **AND** they can understand the proxy configuration
- **AND** they can understand how to run both frontend and backend
