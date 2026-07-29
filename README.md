# Bandhan

[![CI](https://github.com/your-organization/bandhan/actions/workflows/ci.yml/badge.svg)](https://github.com/your-organization/bandhan/actions/workflows/ci.yml)

## Project Overview

**Bandhan – Intelligent Loan Recovery Workflow Management System Using AI-Based Risk Prediction** is a cloud-based Software Engineering project. It is designed around enterprise loan-recovery workflow management, including authentication, role-based access, borrower and loan records, recovery-case handling, dashboards, and analytics.

AI-based risk prediction is one planned module, not the project’s primary focus. This Review 1 repository contains only initialization, DevOps configuration, documentation, and placeholders—no application implementation.

## Technology Stack

| Area | Technology |
| --- | --- |
| Frontend | React |
| Backend | FastAPI |
| Database | PostgreSQL |
| AI | Python |
| Containerization | Docker |
| Deployment | AWS EC2 |
| Version Control | Git + GitHub |

## Repository Structure

```text
bandhan/
├── frontend/             # Future React application
├── backend/              # Future FastAPI services
├── ai-model/             # Future AI risk-prediction assets
├── database/             # Future PostgreSQL schema and migrations
├── docs/                 # Architecture, UML, SRS, and testing documents
├── docker/               # Docker setup guidance
├── .github/workflows/    # GitHub Actions workflows
├── Dockerfile            # FastAPI-ready backend image definition
├── docker-compose.yml    # Backend and PostgreSQL local environment
├── .gitignore            # Generated files and local-secret exclusions
└── LICENSE               # MIT License
```

Each top-level module includes a README and `.gitkeep` placeholder where appropriate so the intended structure is tracked before implementation begins.

## Branching Strategy

Bandhan follows **GitHub Flow** with a structured branch naming convention:

- `main`: stable, reviewed code ready for release or academic review.
- `develop`: shared integration branch for completed features.
- `feature/*`: isolated work for a new capability, such as `feature/login`.
- `bugfix/*`: focused corrections for identified defects.
- `release/*`: release-preparation, final verification, and documentation updates.

Create a short-lived branch from `develop`, open a pull request for review, and merge only after CI succeeds. Promote approved work to `main` for review milestones and releases.

## Quick Start – Local Development

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/bandhan.git
   ```

2. Enter the project directory:

   ```bash
   cd bandhan
   ```

3. Build and start the local containers:

   ```bash
   docker compose up --build
   ```

4. Stop the containers when finished:

   ```bash
   docker compose down
   ```

### Expected URLs

- Backend (reserved for FastAPI): <http://localhost:8000>
- Frontend (reserved for React): <http://localhost:3000>

These URLs become active when the application is implemented. Review 1 deliberately includes no frontend or backend source code, so no application endpoint is currently served.

## Team Members

| Name | Role | GitHub |
| --- | --- | --- |
| _To be added_ | _To be added_ | _To be added_ |

## Documentation

- [Frontend placeholder](frontend/README.md)
- [Backend placeholder](backend/README.md)
- [AI model placeholder](ai-model/README.md)
- [Database placeholder](database/README.md)
- [Documentation index](docs/README.md)
- [Docker guide](docker/README.md)

## License

This project is licensed under the [MIT License](LICENSE).
