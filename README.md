# Bandhan
### Intelligent Loan Recovery Workflow Management System Using AI-Based Risk Prediction

---

## Project Name & Overview

**Bandhan** is a centralized, cloud-based software platform that digitizes and manages the entire loan recovery lifecycle for banks and financial institutions — from borrower and loan onboarding, through recovery case creation and field-officer assignment, to AI-assisted risk prioritization and manager-level reporting.

The project is built primarily as a **Software Engineering** exercise, demonstrating the full SDLC (requirements → design → implementation → testing → deployment → maintenance) using an Agile Scrum process across 6 sprints. Artificial Intelligence is used in a single, well-scoped capacity — borrower risk scoring — rather than as the core focus of the system.

---

## Problem It Solves

Loan recovery in most financial institutions today still relies on manual spreadsheets, phone calls, and disconnected systems. This creates several recurring problems:

- Case tracking is fragmented and error-prone
- Assigning recovery officers to cases is a manual, ad-hoc process
- Managers lack real-time visibility into recovery progress
- Generating reports is slow and time-consuming
- High-risk borrowers are difficult to identify early, delaying intervention

**Bandhan** addresses each of these by centralizing borrower, loan, and case data in one system, automating officer assignment and status tracking, and surfacing AI-generated risk scores so managers can prioritize the cases that matter most.

---

## Target Users (Personas)

| Persona | Role Summary | Key Needs |
|---|---|---|
| **Admin** | Manages the platform itself | Create/manage users, assign roles, view system logs |
| **Manager** | Oversees recovery operations | Create borrowers/loans/cases, assign officers, monitor progress, view AI risk scores, access dashboards & reports |
| **Recovery Officer** | Works cases in the field | View assigned cases, log visit details and remarks, update recovery status |
| **Borrower** | The individual with an outstanding loan | View loan details and current recovery status |

---

## Vision Statement

> To replace fragmented, manual loan-recovery processes with a single, centralized platform that gives every stakeholder — from field officer to manager — real-time visibility and AI-informed prioritization, while remaining simple, secure, and cloud-ready from day one.

---

## Key Features / Goals

- **Secure Authentication & RBAC** — JWT-based login with role-based access for Admin, Manager, Officer, and Borrower
- **User Management** — Admin-controlled creation and management of Manager and Officer accounts
- **Borrower Management** — Centralized borrower profiles (contact, address, employment, documents)
- **Loan Management** — Track loan amount, due dates, interest, and status
- **Recovery Case Management** — Create cases, assign officers, track status, log visit history and remarks
- **AI Risk Prediction** — ML-based risk scoring on borrower data to help managers prioritize recovery efforts
- **Dashboards** — Role-specific dashboards (Manager, Officer) surfacing recovery progress and high-risk borrowers
- **Reporting** — Recovery summaries, pending case reports, and officer performance reports
- **Containerized Deployment** — Docker-based packaging deployed to AWS EC2, with GitHub-based version control and CI/CD

---

## Success Metrics

- All **Must Have** MoSCoW features (auth, RBAC, borrower/loan/case management, officer assignment, dashboard, PostgreSQL, Docker setup) implemented and demonstrable by the end of Sprint 4
- End-to-end recovery workflow (create case → assign officer → update status → resolve) functions without manual workarounds
- AI risk prediction module returns a risk score for a borrower in under 2 seconds
- System successfully containerized and deployed to AWS EC2 with a working CI/CD pipeline via GitHub
- All 6 sprints completed on schedule with SRS, architecture diagrams, and test documentation delivered alongside working software

---

## Local Development Tools

To set up and run Bandhan locally, install the following tools:

| Tool | Purpose | Version |
|---|---|---|
| [Git](https://git-scm.com/downloads) | Version control | 2.40+ |
| [Node.js](https://nodejs.org/) + npm | Running/building the React frontend | Node 18+ |
| [Python](https://www.python.org/downloads/) | Running the FastAPI backend & AI risk model | 3.11+ |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Containerizing and running the full stack | Latest |
| [PostgreSQL](https://www.postgresql.org/download/) | Local database (optional if using the Dockerized DB) | 15+ |
| [GitHub CLI](https://cli.github.com/) | Managing issues/PRs from the terminal | Latest |
| Code editor — [VS Code](https://code.visualstudio.com/) (recommended) | Development environment | Latest |

### Recommended VS Code Extensions
- Python (Microsoft)
- ESLint
- Prettier
- Docker (Microsoft)
- PostgreSQL / SQLTools (optional, for querying the DB directly)

### Verifying Your Setup
Run the following to confirm each tool is installed correctly:
```bash
git --version
node --version
npm --version
python --version
docker --version
docker compose version
gh --version
```

### Environment Variables
Create a `.env` file in the project root (see `.env.example`) with the following:
```
DATABASE_URL=postgresql://user:password@localhost:5432/bandhan
JWT_SECRET=your-secret-key
AI_MODEL_PATH=./ai/models/risk_model.pkl
```

## Assumptions & Constraints

**Assumptions**
- Loan and borrower data used during development will be sample/synthetic data, not real customer data
- A single AI/ML model (trained on available sample data) is sufficient to demonstrate risk-scoring functionality — model accuracy is not the primary evaluation criterion for this Software Engineering course project
- Users (Admin, Manager, Officer) are internal staff with basic digital literacy; no extensive onboarding/training flow is required for v1

**Constraints**
- Project scope is limited to the **Must Have** and **Should Have** MoSCoW items for the current version; features under **Won't Have** (payment gateway, chatbot, OTP auth, mobile app, real-time chat, etc.) are explicitly out of scope
- Fixed academic timeline of 6 sprints
- Tech stack is fixed: React (frontend), FastAPI (backend), PostgreSQL (database), Python (AI), Docker + AWS EC2 (deployment), GitHub (version control)
- AI is scoped strictly to risk prediction — it does not drive any other part of the workflow (e.g., no automated decision-making or case assignment)

## Quick Start — Local Development

### Prerequisites
Make sure you've installed everything listed in [Local Development Tools](#local-development-tools) above, and that Docker Desktop is running.

### 1. Clone the repository
```bash
git clone https://github.com/your-username/bandhan.git
cd bandhan
```

### 2. Set up environment variables
```bash
cp .env.example .env
```
Then open `.env` and fill in any values specific to your machine (defaults work fine for local development).

### 3. Build and run the full stack with Docker
```bash
docker compose up --build
```
This starts three containers:
- `bandhan-db` — PostgreSQL database on port `5432`
- `bandhan-backend` — FastAPI backend on port `8000`
- `bandhan-frontend` — React frontend on port `3000`

### 4. Access the app
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API docs (FastAPI Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. Stopping the app
```bash
docker compose down
```
To also remove the database volume (fresh start):
```bash
docker compose down -v
```

### Running Without Docker (optional, for active development)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

**Database:** install PostgreSQL locally and update `DATABASE_URL` in `.env` to point to it, or keep using the Dockerized `db` service alone:
```bash
docker compose up db
```

## Branching Strategy

Bandhan uses a simplified Git Flow model with three levels of branches, keeping unstable work isolated from the code that's always deployable.

### `main`
- The production branch — always stable, always deployable
- This is what gets containerized and deployed to AWS EC2
- Nobody commits directly here; code only arrives after being tested and merged from `develop`

### `develop`
- The integration branch — where finished features come together before a release
- Once several features are merged in and stable, `develop` is merged into `main`
- Acts as a staging area — can be slightly rougher than `main`, but should still basically work

### `feature/<name>`
- One branch per user story or task — this is where day-to-day work happens
- Named after the user story it implements, e.g. `feature/us-08-create-recovery-case`
- Safe to experiment on since it's isolated from other work
- Merged into `develop` via a pull request once the feature is complete and tested

### Example structure by sprint

```
main
 └── develop
      ├── feature/us-01-secure-admin-login       (Sprint 2)
      ├── feature/us-06-create-borrower-profile   (Sprint 3)
      ├── feature/us-11-manager-dashboard         (Sprint 4)
      └── feature/us-24-containerize-app          (Sprint 6)
```

Each feature branch is merged into `develop` once done and tested. At the end of each sprint, `develop` is merged into `main` — that merge point represents the sprint's deliverable/demo state.

### Workflow

```bash
git checkout -b feature/your-feature-name
git add .
git commit -m "Add: short description of change"
git push origin feature/your-feature-name
```
Then open a pull request into `develop` on GitHub.

### Why this matters
- **Traceability** — branch names tied to user story IDs (e.g. `us-08`) let anyone reviewing the repo see exactly which branch implemented which requirement
- **Safe collaboration** — isolates in-progress work so it can't break `develop` or `main`
- **Demonstrates SDLC process** — reflects standard industry practice, showing the project follows a real development workflow rather than just producing working code