# Bandhan

## Project Overview

**Bandhan – Intelligent Loan Recovery Workflow Management System Using AI-Based Risk Prediction** is a cloud-based Software Engineering project. It is designed around enterprise loan-recovery workflow management, including authentication, role-based access, borrower and loan records, recovery-case handling, dashboards, and analytics.

AI-based risk prediction is one planned module, not the project’s primary focus. This Review 1 repository contains only initialization, DevOps configuration, documentation, and placeholders—no application implementation.
# Vision Document

## Project Name

**Bandhan – Intelligent Loan Recovery Workflow Management System Using AI-Based Risk Prediction**

---

## Project Overview

Bandhan is a cloud-based Loan Recovery Workflow Management System designed to help financial institutions efficiently manage loan recovery operations. The platform centralizes borrower information, loan records, recovery cases, and operational workflows into a secure application while using AI-based risk prediction to identify high-risk borrowers and support proactive recovery decisions.

The system enables recovery teams to prioritize critical cases, monitor recovery progress through dashboards, and improve collaboration across departments using role-based access control and workflow automation.

---

## Problem It Solves

Financial institutions often rely on fragmented systems and manual processes for loan recovery, making it difficult to identify high-risk borrowers, prioritize recovery cases, and track recovery performance efficiently.

Bandhan addresses these challenges by:

- Centralizing loan recovery operations
- Automating recovery workflows
- Predicting borrower risk using AI
- Providing real-time dashboards and analytics
- Improving collaboration among recovery teams
- Reducing manual effort and operational delays

---

## Target Users (Personas)

### Administrator
- Manages users and system configuration
- Assigns roles and permissions
- Monitors overall system health

### Recovery Manager
- Assigns recovery cases
- Monitors team performance
- Reviews recovery analytics

### Recovery Officer
- Handles assigned recovery cases
- Updates borrower interactions
- Tracks case progress

### Bank Management
- Reviews reports and recovery performance
- Makes strategic decisions based on analytics

---

## Vision Statement

To build an intelligent, secure, and scalable Loan Recovery Workflow Management System that empowers financial institutions to improve recovery efficiency, reduce non-performing assets (NPAs), and make informed decisions through AI-assisted risk prediction and workflow automation.

---

## Key Features / Goals

- Secure Role-Based Access Control (RBAC)
- Borrower and Loan Management
- Recovery Case Management
- AI-Based Borrower Risk Prediction
- Interactive Dashboards and Analytics
- Workflow Automation
- Centralized Data Management
- Docker-based Development Environment
- Cloud Deployment on AWS
- Modular and Scalable Software Architecture

---

## Success Metrics

The success of Bandhan will be evaluated using:

- Reduced manual effort in recovery workflows
- Faster identification of high-risk borrowers
- Improved recovery case tracking
- Better recovery prioritization using AI predictions
- Increased operational efficiency
- Secure and reliable access through RBAC
- Successful deployment using Docker and cloud infrastructure

---

## Assumptions

- Loan and borrower data is available and accurate.
- Authorized users have appropriate access permissions.
- AI predictions assist decision-making and do not replace human judgment.
- Users have basic technical knowledge of the application.

---

## Constraints

- Initial version focuses on loan recovery workflows only.
- AI prediction accuracy depends on data quality.
- Cloud deployment assumes internet connectivity.
- Integration with external banking systems is outside the scope of Review 1.
- Mobile application support is not included in the initial release.
- 
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
Sumedha Ganguli 24BAI 1630
Ujjawal Singh 24BRS1410
## Documentation

- [Frontend placeholder](frontend/README.md)
- [Backend placeholder](backend/README.md)
- [AI model placeholder](ai-model/README.md)
- [Database placeholder](database/README.md)
- [Documentation index](docs/README.md)
- [Docker guide](docker/README.md)

## License

This project is licensed under the [MIT License](LICENSE).
