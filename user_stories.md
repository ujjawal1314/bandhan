# Bandhan — User Stories (25)

Format: **US-##** | Role | MoSCoW | Suggested Sprint

Each story below is written ready to paste into a GitHub Issue (title + body). See `create_github_issues.sh` to create all 25 as real GitHub Issues automatically.

---

### Admin

**US-01 — Secure Admin Login** | Must | Sprint 2
As an Admin, I want to log in securely so that I can access the system with appropriate permissions.
- [ ] Login form validates credentials against the backend
- [ ] JWT issued on successful login
- [ ] Invalid credentials show a clear error message

**US-02 — Manage User Accounts** | Must | Sprint 2
As an Admin, I want to create and manage user accounts for Managers and Officers so that I can control who has system access.
- [ ] Admin can create a new user with name, email, and role
- [ ] Admin can edit or remove an existing user
- [ ] New users receive the correct role on creation

**US-03 — Assign Roles (RBAC)** | Must | Sprint 2
As an Admin, I want to assign roles to users so that access is limited to their responsibilities.
- [ ] Roles available: Admin, Manager, Recovery Officer, Borrower
- [ ] Role changes take effect immediately
- [ ] Unauthorized role/endpoint access returns a 403

**US-04 — View System Logs** | Should | Sprint 5
As an Admin, I want to view system logs so that I can audit user actions.
- [ ] Logs capture login attempts and key data changes
- [ ] Logs are filterable by user and date

**US-05 — Deactivate/Reactivate Accounts** | Should | Sprint 2
As an Admin, I want to deactivate or reactivate a user account so that former staff immediately lose access.
- [ ] Deactivated users cannot log in
- [ ] Deactivation is reversible by an Admin

---

### Manager

**US-06 — Create Borrower Profile** | Must | Sprint 3
As a Manager, I want to create a new borrower profile so that borrower details are recorded in the system.
- [ ] Form captures contact, address, employment, and documents
- [ ] Borrower appears in the Borrowers List after creation

**US-07 — Create Loan Record** | Must | Sprint 3
As a Manager, I want to create a loan record linked to a borrower so that loan details are tracked.
- [ ] Loan captures amount, due date, interest, and status
- [ ] Loan is linked to an existing borrower

**US-08 — Create Recovery Case** | Must | Sprint 3
As a Manager, I want to create a recovery case for an overdue loan so that recovery activity can begin.
- [ ] Case links to a specific loan and borrower
- [ ] Case is created with a default "Open" status

**US-09 — Assign Officer to Case** | Must | Sprint 3
As a Manager, I want to assign a recovery case to a Recovery Officer so that the case gets worked.
- [ ] Manager can select from a list of active officers
- [ ] Officer sees the case in their assigned list immediately after assignment

**US-10 — View AI Risk Score** | Should | Sprint 4
As a Manager, I want to view the AI-generated risk score for a borrower so that I can prioritize high-risk cases.
- [ ] Risk score is displayed on the borrower/case detail view
- [ ] Score updates when relevant borrower data changes

**US-11 — Manager Dashboard** | Must | Sprint 4
As a Manager, I want a dashboard summarizing recovery progress so that I can track performance at a glance.
- [ ] Shows total cases, resolved cases, and high-risk borrower count
- [ ] Data reflects real-time system state

**US-12 — Officer Performance Report** | Should | Sprint 5
As a Manager, I want to view officer performance reports so that I can evaluate team productivity.
- [ ] Report shows cases handled, resolved, and average resolution time per officer

**US-13 — Search & Filter Cases** | Should | Sprint 4
As a Manager, I want to search and filter borrowers/cases by status, risk, or officer so that I can quickly find relevant records.
- [ ] Filters can be combined (e.g., status + risk level)
- [ ] Results update without a full page reload

---

### Recovery Officer

**US-14 — View Assigned Cases** | Must | Sprint 3
As a Recovery Officer, I want to view a list of cases assigned to me so that I know my daily workload.
- [ ] List shows borrower name, loan reference, and case status
- [ ] Only cases assigned to the logged-in officer are shown

**US-15 — Update Case Status** | Must | Sprint 3
As a Recovery Officer, I want to update the status of a case so that progress is tracked.
- [ ] Status options include Open, In Progress, Resolved
- [ ] Status change is timestamped

**US-16 — Log Visit Details** | Must | Sprint 3
As a Recovery Officer, I want to log visit details for a borrower so that field activity is documented.
- [ ] Entry captures date, location notes, and outcome
- [ ] Visit history is viewable chronologically on the case

**US-17 — Upload Remarks** | Should | Sprint 3
As a Recovery Officer, I want to add remarks/comments on a case so that the manager has visibility into the situation.
- [ ] Remarks are timestamped and attributed to the officer
- [ ] Manager can view remarks on the case detail screen

**US-18 — View Borrower & Loan Details** | Must | Sprint 3
As a Recovery Officer, I want to view borrower and loan details for my assigned cases so that I have full context before a visit.
- [ ] Officer can see contact info, loan amount, and due date from the case view

**US-19 — Risk-Prioritized Case List** | Should | Sprint 4
As a Recovery Officer, I want my assigned cases sorted by risk score so that I focus on the most urgent cases first.
- [ ] Case list is sortable by risk score, descending by default

---

### Borrower

**US-20 — View Loan Details** | Must | Sprint 3
As a Borrower, I want to log in and view my loan details so that I know my outstanding balance and due date.
- [ ] Borrower login restricted to their own data only

**US-21 — View Recovery Case Status** | Should | Sprint 4
As a Borrower, I want to view the status of my recovery case so that I understand where things currently stand.
- [ ] Status is read-only from the borrower's view

**US-22 — View Repayment History** | Could | Sprint 5
As a Borrower, I want to view my payment/recovery history so that I can track my repayment progress.
- [ ] History displayed in chronological order

---

### Cross-Cutting / Technical

**US-23 — AI Risk Scoring Pipeline** | Should | Sprint 4
As a system, borrower data should feed into the AI risk model so that a risk score is automatically generated for each active loan.
- [ ] Risk score is generated on case creation and on data update
- [ ] Model output is stored and retrievable via the API

**US-24 — Containerize the Application** | Must | Sprint 6
As a developer, I want the system containerized with Docker so that it can be deployed consistently across environments.
- [ ] Dockerfiles exist for frontend and backend
- [ ] `docker-compose up` runs the full stack locally

**US-25 — Deploy via CI/CD to AWS EC2** | Must | Sprint 6
As a Product Owner, I want the system deployed on AWS EC2 via a CI/CD pipeline so that new releases go live reliably.
- [ ] GitHub Actions (or equivalent) builds and pushes containers on merge to main
- [ ] Deployment to EC2 is triggered automatically or via a single manual step
