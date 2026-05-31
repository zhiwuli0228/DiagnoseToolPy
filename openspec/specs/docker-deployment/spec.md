## Purpose

Provide a containerized deployment path for DiagnoseToolPy with documented volume mounts and environment configuration, without changing the application behavior.

## Requirements

### Requirement: Docker Image Build
The system SHALL provide a Dockerfile that builds a working Python application image.

#### Scenario: Dockerfile builds successfully
- **WHEN** `docker build` is run in the project root
- **THEN** a container image is created with the DiagnoseToolPy application
- **AND** the image includes all dependencies from pyproject.toml
- **AND** the image uses Python 3.12

#### Scenario: Application runs in container
- **WHEN** the container is started
- **THEN** uvicorn starts serving on port 18080
- **AND** the health endpoint is accessible

### Requirement: Docker Compose Configuration
The system SHALL provide a docker-compose.yml that configures the application service with proper volume mounts.

#### Scenario: docker-compose starts the service
- **WHEN** `docker compose up -d` is run
- **THEN** the diagnose-tool container starts
- **AND** port 18080 is exposed to the host

#### Scenario: Input directories mounted read-only
- **WHEN** docker-compose is configured with input directories
- **THEN** `/data/diagnose/input` is mounted read-only (`:ro`)
- **AND** `/mnt/log-share` (if configured) is mounted read-only (`:ro`)

#### Scenario: Data directories mounted read-write
- **WHEN** docker-compose is configured with data directories
- **THEN** `/data/diagnose/output` is mounted read-write (`:rw`)
- **AND** `/data/diagnose/cases` is mounted read-write (`:rw`)
- **AND** `/data/diagnose/indexes` is mounted read-write (`:rw`)
- **AND** `/data/diagnose/runtime` is mounted read-write (`:rw`)

### Requirement: Environment Configuration
The system SHALL allow configuration via environment variables in docker-compose.

#### Scenario: DIAGNOSE_CONFIG environment variable is set
- **WHEN** docker-compose is configured with `DIAGNOSE_CONFIG` environment variable
- **THEN** the application reads configuration from that path inside the container
- **AND** the config directory is mounted read-only

#### Scenario: Application uses default config when env not set
- **WHEN** `DIAGNOSE_CONFIG` is not set in docker-compose
- **THEN** the application falls back to default config loading behavior

### Requirement: Deployment Documentation
The system SHALL provide documentation for Docker-based deployment.

#### Scenario: Deployment guide documents startup commands
- **WHEN** an operator reads the deployment guide
- **THEN** they can find commands to build and start the application with Docker Compose
- **AND** they can find commands to stop and clean up the deployment

#### Scenario: Docker-compose guide documents volume mount strategy
- **WHEN** an operator reads the docker-compose guide
- **THEN** they understand which directories are read-only and which are read-write
- **AND** they can configure their own volume mounts

#### Scenario: Deployment verification steps exist
- **WHEN** an operator follows the deployment verification steps
- **THEN** they can confirm the application is running correctly
- **AND** they can verify the volume mounts are working as expected
