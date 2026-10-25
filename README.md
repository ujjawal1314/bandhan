# Bandhan

Bandhan is an AI-powered early warning and recovery platform for Indian Bank's MSME and government-scheme loan portfolios. The system is designed to identify borrower financial stress before loan default occurs by combining behavioral signals, peer benchmarking, and regional stress indicators into a contextual risk view.

This repository packages the MVP as a Python and Streamlit application with supporting backend services, datasets, and documentation. The goal is to help developers, judges, and collaborators understand how the platform works end to end and how the current codebase maps to that architecture.

## Project Overview

Bandhan introduces the Continuous Borrower Health Model (CBHM), a custom intelligence layer that estimates borrower health using repayment behavior, balance trends, transaction stability, cohort comparisons, and geographic loan stress signals.

The platform is built to help banks:

- Monitor borrower financial health in near real time
- Detect early stress signals before EMI default
- Compare borrower performance against similar peers
- Adjust risk interpretation using regional NPA pressure
- Prioritize recovery actions using contextual intelligence
- Provide transparent health insights to borrowers

Bandhan shifts loan recovery from reactive enforcement to proactive financial assistance.

## Technology Stack

### Frontend and UI

- Streamlit powers the primary bank monitoring dashboard
- Interactive views present borrower health, risk levels, and recommendations
- Charts and visual indicators highlight borrower score, peer score, and regional stress
- Dashboard copy is oriented toward explainable borrower-risk monitoring

### Backend

- Python 3.x handles application logic and orchestration
- Pandas and NumPy support feature preparation and scoring workflows
- FastAPI provides service endpoints for analysis, account state, and demo operations
- Risk processing is structured around borrower-level scoring and monitoring flows

### Data Layer

- Structured CSV datasets are used in the MVP for local development and demos
- The design can be extended to PostgreSQL or another operational data store
- The platform expects borrower profile data, transaction history, and regional performance context

### AI and Intelligence Layer

- CBHM is the conceptual scoring engine for borrower health evaluation
- Behavioral risk inference focuses on financial stress rather than static credit history alone
- Contextual risk adjustments use peer and geographic signals to refine interpretation
- AI-generated explanations can convert raw score outputs into understandable action guidance

### Infrastructure

- Git and GitHub support collaboration and version control
- Environment variables configure AI integrations and service connectivity
- Docker artifacts are available for containerized deployment

## System Architecture

Bandhan can be understood as a layered system.

### 1. Data Layer

This layer stores or loads the inputs required for borrower evaluation:

- Borrower profiles
- Loan metadata
- Repayment and transaction behavior
- Regional loan performance or NPA context

In the current MVP, sample datasets are loaded from local CSV files. In production, the same structure can be backed by PostgreSQL or another bank-controlled data source.

### 2. Feature Processing Layer

This layer transforms raw borrower activity into model-ready signals. Typical derived features include:

- Repayment consistency
- Transaction inflow and outflow stability
- Account balance trends
- Missed or delayed payment patterns
- Loan scheme cohort statistics
- Regional stress indicators

This is where raw operational data becomes a borrower-health representation.

### 3. AI Intelligence Layer

The Continuous Borrower Health Model (CBHM) estimates base borrower health. The model is intended to prioritize behavioral evidence over static credit labels by asking whether the borrower is becoming financially stressed, how quickly that change is happening, and whether that change is unusual for the borrower's context.

### 4. Contextual Risk Layer

The contextual layer refines the base health estimate using:

- Peer comparison for similar borrowers
- Loan-scheme benchmarking
- Regional NPA or economic-stress context

This layer prevents simplistic scoring by distinguishing a borrower-specific deterioration from broader regional pressure.

### 5. Backend Processing Layer

Python services coordinate data loading, feature extraction, score generation, risk classification, and API responses. The backend is responsible for turning datasets into dashboard-ready analysis and exposing analysis endpoints to other interfaces.

### 6. Presentation Layer

The Streamlit dashboard surfaces:

- Portfolio health summaries
- Borrower-level drilldowns
- Peer comparison metrics
- Regional stress context
- Recommended intervention actions

The presentation layer is intended for both bank-side monitoring and borrower-facing transparency flows.

## Data Flow

The intended data flow is:

1. Borrower, loan, transaction, and regional context data are loaded
2. Behavioral and contextual features are extracted
3. CBHM computes a base borrower health score
4. Peer comparison adjusts the score relative to a borrower cohort
5. Regional stress modifies interpretation of borrower deterioration
6. A final contextual risk score and category are assigned
7. Recovery recommendations are generated
8. Dashboards and APIs present the results

## Borrower Data Model

The core entity is `Borrower`.

Recommended properties:

- `borrower_id`
- `name`
- `loan_scheme`
- `region`
- `loan_amount`
- `health_score`
- `peer_score`
- `regional_stress_factor`
- `risk_level`

Why these attributes matter:

- `borrower_id` provides a stable reference for analysis and tracking
- `name` supports operational review and borrower communication
- `loan_scheme` enables cohort comparisons across Mudra, PMEGP, MSME, and related portfolios
- `region` enables contextual interpretation using district or state-level loan stress
- `loan_amount` helps normalize peer comparisons by exposure size
- `health_score` stores the direct model view of borrower condition
- `peer_score` shows how the borrower compares to similar borrowers
- `regional_stress_factor` helps separate borrower-specific weakness from systemic pressure
- `risk_level` converts the score into operational action categories

## Continuous Borrower Health Model (CBHM)

CBHM estimates borrower financial health using behavior-first signals instead of relying only on static credit history.

### Inputs

Behavioral financial signals:

- Repayment timing patterns
- Account balance trends
- Transaction inflow and outflow stability

Peer benchmarking:

- Average health of borrowers with similar schemes
- Comparison against similar loan amounts
- Cohort-based deviation analysis

Regional context:

- Regional NPA levels
- Geographic economic stress indicators

### Conceptual Scoring Logic

A simple conceptual version is:

`Adjusted Score = Base Health Score + Regional Factor - Peer Deviation Adjustment`

This supports a more accurate interpretation of risk:

- A borrower deteriorating faster than peers may require proactive action
- A weak score in a highly stressed region may call for assisted recovery instead of immediate escalation
- A borrower performing above a weak regional baseline may be less urgent than raw score alone suggests

## Contextual Risk Intelligence

### Peer Comparison

Borrowers are compared against peers with:

- Similar loan schemes
- Similar loan sizes
- Similar borrower categories

This helps determine whether a borrower is an outlier or simply tracking normal cohort behavior.

### Regional Risk Context

Regional NPA trends and economic pressure indicators adjust interpretation of borrower risk. For example, if one state shows structurally higher MSME loan stress than another, Bandhan can avoid over-penalizing borrowers whose weaker patterns reflect regional conditions rather than borrower-specific breakdown.

This reduces false alarms and improves recovery prioritization.

## Backend Processing Logic

The intended borrower-risk evaluation pipeline is:

1. Borrower data is loaded from the dataset or service layer
2. Behavioral features are extracted from transactions and repayment patterns
3. CBHM computes a base health score
4. Peer comparison adjusts the score relative to the cohort
5. Regional context modifies the result using geographic stress
6. The final score is classified into a risk category
7. A recovery recommendation is generated
8. Results are displayed through dashboards and APIs

## Risk Classification

The platform uses a 0-100 score range.

- High Risk: high probability of borrower default or urgent stress
- Moderate Risk: meaningful stress signals, but still manageable with intervention
- Low Risk: stable borrower behavior with no major early-warning indicators

Recommendations are driven by the category:

- High Risk: urgent outreach, restructuring review, manual monitoring, recovery prioritization
- Moderate Risk: assisted follow-up, repayment reminders, watchlist monitoring, borrower counseling
- Low Risk: routine monitoring and preventive nudges

## Dashboards

### Bank Dashboard

The bank dashboard is designed for portfolio monitoring and intervention planning. Typical elements include:

- Borrower table
- Risk indicators
- Peer comparison metrics
- Regional stress context
- Recommended intervention actions

The goal is to help officers prioritize recovery based on contextual intelligence rather than isolated alerts.

### Borrower Transparency Dashboard

The borrower-facing view is intended to show:

- Loan health score
- Peer comparison
- Regional context indicators
- Repayment guidance

This supports proactive repayment behavior and reduces the stigma of opaque risk labeling.

## Visualization Logic

Key metrics include:

- Borrower health score
- Peer average comparison
- Regional stress indicator

Color cues:

- Green for healthy borrowers
- Yellow for moderate stress
- Red for high-risk borrowers

These visual signals let bank officers identify deterioration quickly and consistently.

## Demo Workflow

The demo story for Bandhan is:

1. Load the borrower portfolio dashboard
2. Select a borrower from a stressed region or scheme
3. Run CBHM-based contextual scoring
4. Compare the borrower against peers
5. Adjust interpretation using regional NPA context
6. Generate a recovery recommendation
7. Show a borrower-side health summary view

This demonstrates explainable and contextual borrower-risk intelligence.

## Deployment

### Local Development

- Python environment
- Streamlit application
- CSV-backed sample dataset

Typical commands:

```bash
pip install -r requirements.txt
streamlit run dashboard_enhanced.py
```

Environment variables can be used for:

- AI provider API keys
- Backend service URLs
- Optional graph or database connectivity

### Containerization

Docker assets are included for teams that want a packaged local or demo deployment.

## Project Structure

```text
bandhan/
├── backend/                 # Service and processing logic
├── dashboard/               # Streamlit UI and presentation components
├── data/                    # Borrower and regional datasets
├── config/                  # Environment and configuration files
├── docs/                    # Technical documentation
└── tests/                   # Validation and regression coverage
```

The current repository contains legacy hackathon implementation files as well as the newer Bandhan positioning and documentation. As the product evolves, the folder layout can be normalized toward the structure above.

## Goal of the System

Bandhan aims to:

- Detect loan repayment stress early
- Reduce NPAs in PSU banking portfolios
- Enable proactive borrower support
- Improve recovery efficiency through contextual intelligence
- Provide transparent borrower financial health insights

The system reframes loan recovery as a data-driven early warning workflow for financial risk management.

---

## Software Design

Bandhan follows a layered three-tier architecture consisting of a React frontend, FastAPI backend, and PostgreSQL database. The backend is organized into modular business components, while the AI Risk Prediction module is kept separate through a defined service interface to maintain abstraction, cohesion, and low coupling. The design supports maintainability by allowing individual modules, database implementation, or the AI model to be changed with minimal impact on other parts of the system.

### Design Documentation

The complete Software Design Document is available here:

- [Software Design Document](design/Software_Design_Document.pdf)

### Architecture Diagram

![Bandhan Software Architecture](design/bandhan_architecture.png)

### UI Design

The six main UI screens designed for Bandhan are available in the Software Design Document and Figma prototype.

- Login
- Loan Management
- Recovery Case Management
- AI Risk Prediction
- Analytics & Reports
- Action Center

The revised user interface follows a consistent Bandhan visual identity using a warm colour scheme, structured navigation, clear typography, and modular interface components across all six screens. Each screen focuses on a specific responsibility, improving cohesion and removing irrelevant information or actions. The interfaces apply abstraction by presenting meaningful business information without exposing technical implementation details, while consistent module boundaries support modularity and low coupling.
