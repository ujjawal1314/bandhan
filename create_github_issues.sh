#!/usr/bin/env bash
# Bulk-creates the 25 Bandhan user stories as GitHub Issues (and, optionally,
# adds them to a GitHub Projects v2 board).
#
# PREREQUISITES:
#   1. Install GitHub CLI:  https://cli.github.com
#   2. Authenticate once:   gh auth login
#   3. Edit the CONFIG block below, then run:   bash create_github_issues.sh
#
set -euo pipefail

# ---------------------- CONFIG (edit these) ----------------------
REPO="your-username/bandhan"     # <-- your repo, e.g. "sumedha123/bandhan"
PROJECT_NUMBER=""                # <-- optional: your Project number (e.g. "1"). Leave blank to skip.
PROJECT_OWNER=""                 # <-- optional: org/user that owns the Project (e.g. "sumedha123"). Leave blank to skip.
# -------------------------------------------------------------------

echo "Creating labels (safe to ignore 'already exists' errors)..."
for label in "user-story" "must-have" "should-have" "could-have" \
             "sprint-2" "sprint-3" "sprint-4" "sprint-5" "sprint-6"; do
  gh label create "$label" --repo "$REPO" --color "ededed" 2>/dev/null || true
done

create_issue () {
  local title="$1"
  local labels="$2"
  local body="$3"

  echo "Creating: $title"
  local url
  url=$(gh issue create --repo "$REPO" --title "$title" --label "$labels" --body "$body")
  echo "  -> $url"

  if [[ -n "$PROJECT_NUMBER" && -n "$PROJECT_OWNER" ]]; then
    gh project item-add "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --url "$url"
  fi
}

# ---------------------- ADMIN ----------------------

create_issue "US-01 — Secure Admin Login" "user-story,must-have,sprint-2" \
$'As an Admin, I want to log in securely so that I can access the system with appropriate permissions.\n\n**Acceptance Criteria**\n- [ ] Login form validates credentials against the backend\n- [ ] JWT issued on successful login\n- [ ] Invalid credentials show a clear error message'

create_issue "US-02 — Manage User Accounts" "user-story,must-have,sprint-2" \
$'As an Admin, I want to create and manage user accounts for Managers and Officers so that I can control who has system access.\n\n**Acceptance Criteria**\n- [ ] Admin can create a new user with name, email, and role\n- [ ] Admin can edit or remove an existing user\n- [ ] New users receive the correct role on creation'

create_issue "US-03 — Assign Roles (RBAC)" "user-story,must-have,sprint-2" \
$'As an Admin, I want to assign roles to users so that access is limited to their responsibilities.\n\n**Acceptance Criteria**\n- [ ] Roles available: Admin, Manager, Recovery Officer, Borrower\n- [ ] Role changes take effect immediately\n- [ ] Unauthorized role/endpoint access returns a 403'

create_issue "US-04 — View System Logs" "user-story,should-have,sprint-5" \
$'As an Admin, I want to view system logs so that I can audit user actions.\n\n**Acceptance Criteria**\n- [ ] Logs capture login attempts and key data changes\n- [ ] Logs are filterable by user and date'

create_issue "US-05 — Deactivate/Reactivate Accounts" "user-story,should-have,sprint-2" \
$'As an Admin, I want to deactivate or reactivate a user account so that former staff immediately lose access.\n\n**Acceptance Criteria**\n- [ ] Deactivated users cannot log in\n- [ ] Deactivation is reversible by an Admin'

# ---------------------- MANAGER ----------------------

create_issue "US-06 — Create Borrower Profile" "user-story,must-have,sprint-3" \
$'As a Manager, I want to create a new borrower profile so that borrower details are recorded in the system.\n\n**Acceptance Criteria**\n- [ ] Form captures contact, address, employment, and documents\n- [ ] Borrower appears in the Borrowers List after creation'

create_issue "US-07 — Create Loan Record" "user-story,must-have,sprint-3" \
$'As a Manager, I want to create a loan record linked to a borrower so that loan details are tracked.\n\n**Acceptance Criteria**\n- [ ] Loan captures amount, due date, interest, and status\n- [ ] Loan is linked to an existing borrower'

create_issue "US-08 — Create Recovery Case" "user-story,must-have,sprint-3" \
$'As a Manager, I want to create a recovery case for an overdue loan so that recovery activity can begin.\n\n**Acceptance Criteria**\n- [ ] Case links to a specific loan and borrower\n- [ ] Case is created with a default "Open" status'

create_issue "US-09 — Assign Officer to Case" "user-story,must-have,sprint-3" \
$'As a Manager, I want to assign a recovery case to a Recovery Officer so that the case gets worked.\n\n**Acceptance Criteria**\n- [ ] Manager can select from a list of active officers\n- [ ] Officer sees the case in their assigned list immediately after assignment'

create_issue "US-10 — View AI Risk Score" "user-story,should-have,sprint-4" \
$'As a Manager, I want to view the AI-generated risk score for a borrower so that I can prioritize high-risk cases.\n\n**Acceptance Criteria**\n- [ ] Risk score is displayed on the borrower/case detail view\n- [ ] Score updates when relevant borrower data changes'

create_issue "US-11 — Manager Dashboard" "user-story,must-have,sprint-4" \
$'As a Manager, I want a dashboard summarizing recovery progress so that I can track performance at a glance.\n\n**Acceptance Criteria**\n- [ ] Shows total cases, resolved cases, and high-risk borrower count\n- [ ] Data reflects real-time system state'

create_issue "US-12 — Officer Performance Report" "user-story,should-have,sprint-5" \
$'As a Manager, I want to view officer performance reports so that I can evaluate team productivity.\n\n**Acceptance Criteria**\n- [ ] Report shows cases handled, resolved, and average resolution time per officer'

create_issue "US-13 — Search & Filter Cases" "user-story,should-have,sprint-4" \
$'As a Manager, I want to search and filter borrowers/cases by status, risk, or officer so that I can quickly find relevant records.\n\n**Acceptance Criteria**\n- [ ] Filters can be combined (e.g., status + risk level)\n- [ ] Results update without a full page reload'

# ---------------------- RECOVERY OFFICER ----------------------

create_issue "US-14 — View Assigned Cases" "user-story,must-have,sprint-3" \
$'As a Recovery Officer, I want to view a list of cases assigned to me so that I know my daily workload.\n\n**Acceptance Criteria**\n- [ ] List shows borrower name, loan reference, and case status\n- [ ] Only cases assigned to the logged-in officer are shown'

create_issue "US-15 — Update Case Status" "user-story,must-have,sprint-3" \
$'As a Recovery Officer, I want to update the status of a case so that progress is tracked.\n\n**Acceptance Criteria**\n- [ ] Status options include Open, In Progress, Resolved\n- [ ] Status change is timestamped'

create_issue "US-16 — Log Visit Details" "user-story,must-have,sprint-3" \
$'As a Recovery Officer, I want to log visit details for a borrower so that field activity is documented.\n\n**Acceptance Criteria**\n- [ ] Entry captures date, location notes, and outcome\n- [ ] Visit history is viewable chronologically on the case'

create_issue "US-17 — Upload Remarks" "user-story,should-have,sprint-3" \
$'As a Recovery Officer, I want to add remarks/comments on a case so that the manager has visibility into the situation.\n\n**Acceptance Criteria**\n- [ ] Remarks are timestamped and attributed to the officer\n- [ ] Manager can view remarks on the case detail screen'

create_issue "US-18 — View Borrower & Loan Details" "user-story,must-have,sprint-3" \
$'As a Recovery Officer, I want to view borrower and loan details for my assigned cases so that I have full context before a visit.\n\n**Acceptance Criteria**\n- [ ] Officer can see contact info, loan amount, and due date from the case view'

create_issue "US-19 — Risk-Prioritized Case List" "user-story,should-have,sprint-4" \
$'As a Recovery Officer, I want my assigned cases sorted by risk score so that I focus on the most urgent cases first.\n\n**Acceptance Criteria**\n- [ ] Case list is sortable by risk score, descending by default'

# ---------------------- BORROWER ----------------------

create_issue "US-20 — View Loan Details" "user-story,must-have,sprint-3" \
$'As a Borrower, I want to log in and view my loan details so that I know my outstanding balance and due date.\n\n**Acceptance Criteria**\n- [ ] Borrower login restricted to their own data only'

create_issue "US-21 — View Recovery Case Status" "user-story,should-have,sprint-4" \
$'As a Borrower, I want to view the status of my recovery case so that I understand where things currently stand.\n\n**Acceptance Criteria**\n- [ ] Status is read-only from the borrower'"'"'s view'

create_issue "US-22 — View Repayment History" "user-story,could-have,sprint-5" \
$'As a Borrower, I want to view my payment/recovery history so that I can track my repayment progress.\n\n**Acceptance Criteria**\n- [ ] History displayed in chronological order'

# ---------------------- CROSS-CUTTING / TECHNICAL ----------------------

create_issue "US-23 — AI Risk Scoring Pipeline" "user-story,should-have,sprint-4" \
$'As a system, borrower data should feed into the AI risk model so that a risk score is automatically generated for each active loan.\n\n**Acceptance Criteria**\n- [ ] Risk score is generated on case creation and on data update\n- [ ] Model output is stored and retrievable via the API'

create_issue "US-24 — Containerize the Application" "user-story,must-have,sprint-6" \
$'As a developer, I want the system containerized with Docker so that it can be deployed consistently across environments.\n\n**Acceptance Criteria**\n- [ ] Dockerfiles exist for frontend and backend\n- [ ] `docker-compose up` runs the full stack locally'

create_issue "US-25 — Deploy via CI/CD to AWS EC2" "user-story,must-have,sprint-6" \
$'As a Product Owner, I want the system deployed on AWS EC2 via a CI/CD pipeline so that new releases go live reliably.\n\n**Acceptance Criteria**\n- [ ] GitHub Actions (or equivalent) builds and pushes containers on merge to main\n- [ ] Deployment to EC2 is triggered automatically or via a single manual step'

echo "Done. Created 25 issues in $REPO."
