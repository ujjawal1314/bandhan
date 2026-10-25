# Bandhan Technical Architecture

## Purpose

This document explains the Bandhan architecture from end to end for developers, judges, and collaborators. It is written as a high-level technical reference for the current MVP direction: borrower health monitoring, contextual risk scoring, and early loan-stress detection.

## 1. Project Overview

Bandhan is an AI-powered early warning and recovery platform for Indian Bank's MSME and government-scheme loan portfolios. The system focuses on borrower distress detection before default rather than post-default enforcement. It combines behavioral signals, peer context, and regional stress information to produce a more useful operational risk view.

The central intelligence concept is the Continuous Borrower Health Model (CBHM).

## 2. Layered Architecture

### Data Layer

The data layer contains:

- Borrower profiles
- Loan metadata
- Repayment and transaction history
- Regional performance or NPA context

For the MVP, these inputs can be loaded from CSV. In a production deployment, the same contract can be served from PostgreSQL or another internal banking data source.

### Feature Processing Layer

The feature layer derives:

- Repayment consistency
- Payment delays or skips
- Balance trend direction
- Inflow and outflow stability
- Cohort averages
- Regional stress factors

These features transform raw transaction history into borrower-health indicators.

### AI Intelligence Layer

CBHM estimates a base borrower health score using borrower behavior. The model is intended to answer whether the borrower is stable, deteriorating, or deviating from normal patterns.

### Contextual Risk Layer

The contextual layer adjusts the base score using:

- Peer benchmarks for similar borrowers
- Loan-scheme comparisons
- Regional NPA and economic-stress conditions

This avoids overreacting to systemic external pressure while still surfacing borrower-specific deterioration.

### Backend Processing Layer

The backend handles:

- Data loading
- Feature extraction
- Score generation
- Risk classification
- Recommendation generation
- API responses for dashboards and integrations

### Presentation Layer

The presentation layer is implemented with Streamlit and is intended to support:

- Bank-side monitoring
- Borrower-level drilldowns
- Peer comparison visualization
- Regional stress awareness
- Recovery recommendation visibility

## 3. Data Flow

1. Borrower and transaction data are loaded
2. Behavioral features are extracted
3. CBHM computes base borrower health
4. Peer benchmarking adjusts the score
5. Regional context modifies interpretation
6. Risk is classified into operational levels
7. A recommended action is produced
8. Dashboards visualize the result

## 4. Borrower Data Model

Primary entity: `Borrower`

Core properties:

- `borrower_id`
- `name`
- `loan_scheme`
- `region`
- `loan_amount`
- `health_score`
- `peer_score`
- `regional_stress_factor`
- `risk_level`

These attributes support identity, cohort grouping, exposure normalization, contextual risk interpretation, and operational actioning.

## 5. Continuous Borrower Health Model (CBHM)

CBHM is a conceptual model for borrower health estimation.

### Input Families

Behavioral financial signals:

- Repayment timing
- Balance trends
- Inflow and outflow stability

Peer benchmarking:

- Average score for similar schemes
- Average score for similar loan amounts
- Cohort deviation

Regional context:

- NPA intensity
- Economic stress conditions

### Conceptual Formula

`Adjusted Score = Base Health Score + Regional Factor - Peer Deviation Adjustment`

The formula is conceptual rather than implementation-specific, but it captures the intended logic: borrower risk should be interpreted relative to peer performance and regional conditions, not only in isolation.

## 6. Contextual Risk Intelligence

### Peer Comparison

Borrowers are compared against peers with similar:

- Loan schemes
- Loan amounts
- Borrower categories

This helps determine whether a borrower is materially underperforming the relevant cohort.

### Geographic Context

Regional NPA and economic stress data are used to contextualize borrower weakness. A borrower in a structurally stressed district may deserve a different operational response from a similarly scored borrower in a strong region.

This improves prioritization and reduces false alarms.

## 7. Risk Classification

Score range: `0-100`

- High Risk
- Moderate Risk
- Low Risk

Expected actioning:

- High Risk: urgent intervention and recovery review
- Moderate Risk: active monitoring and borrower support
- Low Risk: routine monitoring

## 8. Dashboard Design

### Bank Dashboard

Expected components:

- Borrower table
- Risk-level indicators
- Peer comparison visuals
- Regional stress insights
- Intervention recommendations

### Borrower Dashboard

Expected components:

- Loan health score
- Peer comparison summary
- Regional context signal
- Repayment guidance

## 9. Visualization Logic

The visual language should remain simple and operational:

- Green: healthy
- Yellow: moderate stress
- Red: high risk

Core visual metrics:

- Borrower health score
- Peer average
- Regional stress factor

## 10. Demo Workflow

1. Open the bank dashboard
2. Select a borrower from a stressed scheme or region
3. Run contextual scoring
4. Compare borrower vs cohort
5. Apply regional interpretation
6. Generate a recovery recommendation
7. Display borrower-facing health transparency

## 11. Deployment Model

### MVP

- Python runtime
- Streamlit dashboard
- CSV-backed demo dataset

### Configuration

Use environment variables for:

- AI integration credentials
- Service URLs
- Optional database endpoints

### Packaging

Docker can be used to package the dashboard and backend for demos or internal review environments.

## 12. System Goal

Bandhan is intended to:

- Detect repayment stress early
- Reduce NPAs in PSU loan portfolios
- Improve recovery efficiency
- Encourage proactive borrower support
- Provide transparent, explainable loan-health insights

The broader objective is to turn loan recovery into a contextual early-warning system rather than a purely reactive process.
