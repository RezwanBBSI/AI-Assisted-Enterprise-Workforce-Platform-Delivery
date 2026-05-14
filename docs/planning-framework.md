# Planning Framework
# BBSI BuildAThon 2026 — Workforce Time Tracking & Payroll Integration Platform

> **Source:** Derived from `bbsi_buildathon_2026_requirements_only.md`
> **Last Updated:** 2026-05-14

---

## 1. Methodology

This project follows an **AI-Assisted Agile** delivery model, where human team members retain decision authority while AI agents accelerate every phase of the SDLC.

| Principle | Application |
|---|---|
| Iterative delivery | Short sprints with working software at each milestone |
| API-first | Backend contracts defined before UI implementation |
| Test-driven | Acceptance criteria written before code |
| Shift-left security | Security reviewed at PR stage, not post-delivery |
| Human-in-the-loop | All agent outputs reviewed and approved by a human before merge |

---

## 2. ADE Toolchain

| Tool | Role in This Project |
|---|---|
| **GitHub Copilot (Claude)** | Requirements analysis, documentation, code generation, testing support |
| **Codex** | Code generation, debugging, refactoring, API scaffolding |
| **Manus.ai** | Multi-step workflow orchestration and automation |
| **GitHub Codespaces** | Standard cloud development environment for all team members |

---

## 3. Agent Roles & Responsibilities

### 3.1 Product Owner / BA Agent
- Transforms business features from the requirements doc into development-ready user stories
- Writes acceptance criteria using Given / When / Then format
- Defines validation rules and workflow logic
- Produces QA-ready requirements for each story

### 3.2 Developer / Platform Engineering Agent
- Implements backend APIs using **Python / FastAPI**
- Implements frontend UI using **React (Vite)**
- Creates and manages the **database schema** (SQLite for dev, Azure SQL-compatible for prod)
- Maintains CI/CD pipeline and GitHub Codespaces configuration
- Follows API-first design: OpenAPI spec before implementation

### 3.3 QA / STE Agent
- Writes and executes automated UI tests using **Playwright**
- Writes and executes API automation tests
- Validates each user story against its acceptance criteria
- Generates test evidence (screenshots, reports, coverage summaries)

### 3.4 Security / Verifier Agent
- Reviews every pull request for secure coding violations
- Scans dependencies for known vulnerabilities
- Validates authentication and authorization on all endpoints
- Detects secrets or hardcoded credentials in code
- Produces a security validation summary per sprint

### 3.5 Customer Support / Triage Agent
- Assists with incident analysis using application logs
- Correlates errors across backend and frontend
- Produces root-cause analysis reports
- Classifies issues and recommends remediation steps

### 3.6 BugBot Agent
- Reproduces reported defects from issue descriptions
- Identifies probable root causes
- Suggests targeted fixes
- Generates remediation workflow steps for the Developer Agent

---

## 4. Human-in-the-Loop Governance

AI agents **propose**; humans **approve**.

| Human Role | Responsibility |
|---|---|
| Product Owner | Business prioritization, story acceptance |
| Business Analyst | Requirement validation, story review |
| Solution Architect | Architecture guidance, design decisions |
| Engineering Lead | Technical oversight, PR approval |
| QA Lead | Test plan approval, quality sign-off |
| Security Engineer | Risk review, security finding triage |
| Platform Engineer | Environment governance, CI/CD approval |
| Support Team | Operational review, incident sign-off |

---

## 5. Sprint Structure

### Sprint 1 — Foundation
**Focus:** Database setup, authentication, RBAC, and core API skeleton.

**DB Models to Create:**
- `Company` — id (UUID), name, is_active, created_at
- `Location` — id, company_id (FK→Company), name, timezone, is_active
- `Role` — id, name (`Admin` / `Manager` / `Employee`)
- `User` — id (UUID), email (unique, indexed), hashed_password, full_name, is_active, created_at
- `UserRole` — user_id (FK→User), company_id (FK→Company), role_id (FK→Role) [junction table]

**API Endpoints to Implement:**
- `POST /api/v1/auth/register` — create user; return user object (no password)
- `POST /api/v1/auth/login` — validate credentials; return `access_token` + `token_type`
- `POST /api/v1/auth/refresh` — issue new access token from valid token
- `GET  /api/v1/auth/me` — return current authenticated user (JWT required)
- `GET  /api/v1/companies` — list companies (Admin only, paginated)
- `POST /api/v1/companies` — create company (Admin only)
- `GET  /api/v1/locations` — list locations scoped to company (paginated)
- `POST /api/v1/locations` — create location (Admin / Manager)

**Infrastructure Tasks:**
- Wire SQLAlchemy with async session factory
- Configure Alembic; generate and run first migration
- Implement JWT encode/decode utilities (HS256, configurable expiry)
- Implement `get_current_user` FastAPI dependency
- Implement `require_role(*roles)` RBAC dependency
- Add global pagination dependency (`?page=1&size=20`)
- Confirm Swagger UI live at `http://localhost:8000/docs`

---

### Sprint 2 — Workforce Time Management
**Focus:** Clock-in/out, punch validation, attendance, corrections, audit logging.

**DB Models to Create:**
- `TimeEntry` — id, employee_id (FK→User), company_id (FK→Company), location_id (FK→Location), clock_in (UTC datetime), clock_out (UTC datetime, nullable), status (`open` / `closed` / `corrected`), created_at
- `TimeCorrection` — id, time_entry_id (FK→TimeEntry), requested_by (FK→User), approved_by (FK→User, nullable), reason, original_clock_in, new_clock_in, original_clock_out, new_clock_out, status (`pending` / `approved` / `denied`), created_at
- `AttendanceRecord` — id, employee_id, company_id, date, status (`present` / `absent` / `late` / `missing_punch`), created_at
- `AuditLog` — id, entity_type, entity_id, action, performed_by (FK→User), performed_at, details (JSON)

**API Endpoints to Implement:**
- `POST /api/v1/time-entries/clock-in` — create open time entry; 409 if already open
- `POST /api/v1/time-entries/clock-out` — close open entry; 404 if no open entry
- `GET  /api/v1/time-entries` — paginated list; filter by employee_id, date range, status
- `GET  /api/v1/time-entries/{id}` — single entry
- `POST /api/v1/time-entries/{id}/correction` — employee submits correction request
- `PUT  /api/v1/time-entries/{id}/correction/{correction_id}` — manager approves / denies
- `GET  /api/v1/attendance` — daily records per employee; filter by date range
- `GET  /api/v1/attendance/missing-punches` — list all open entries older than 24 hours

**Punch Validation Rules (PunchValidationService):**
- Reject clock-in if an open entry already exists for that employee today → 409
- Reject clock-in with a future timestamp → 422
- Reject clock-out if clock_out <= clock_in → 422
- Reject time entries that overlap with an existing closed entry → 409

**Frontend Pages / Components:**
- `DashboardPage` — shows today's punch status, Clock In / Clock Out button, last 7-day summary
- `PunchWidget` — large touch-friendly button; shows current status (`Clocked In since HH:MM` / `Clocked Out`)
- `TimeEntriesTable` — manager view; paginated; sortable by date/employee
- `CorrectionModal` — employee submits reason + proposed times; manager approves / denies inline

---

### Sprint 3 — Scheduling & Leave Management
**Focus:** Leave workflows, shift scheduling, break enforcement, policy configuration.

**DB Models to Create:**
- `LeaveRequest` — id, employee_id (FK→User), company_id, leave_type (`pto` / `sick` / `comp` / `unpaid`), start_date, end_date, days_requested, reason, status (`pending` / `approved` / `denied` / `cancelled`), reviewed_by (FK→User, nullable), reviewed_at, review_comment
- `LeaveBalance` — id, employee_id, company_id, year, pto_total, pto_used, sick_total, sick_used, comp_earned, comp_used
- `ShiftSchedule` — id, employee_id (FK→User), company_id, location_id, shift_date, shift_start (time), shift_end (time), break_minutes, created_by (FK→User)
- `CompanyPolicy` — id, company_id, policy_key (indexed), policy_value (JSON), updated_by, updated_at

**API Endpoints to Implement:**
- `POST /api/v1/leave-requests` — employee submits leave request
- `GET  /api/v1/leave-requests` — list; filter by employee/status/date range
- `PUT  /api/v1/leave-requests/{id}/review` — manager approves / denies with comment
- `PUT  /api/v1/leave-requests/{id}/cancel` — employee cancels pending request
- `GET  /api/v1/leave-balances/{employee_id}` — current year balance
- `POST /api/v1/schedules` — manager creates shift
- `GET  /api/v1/schedules` — list; filter by employee_id / date range
- `PUT  /api/v1/schedules/{id}` — update shift
- `DELETE /api/v1/schedules/{id}` — remove shift
- `GET  /api/v1/policies` — list company policies (Admin / Manager)
- `PUT  /api/v1/policies/{key}` — admin updates a policy value

**Business Rules (enforced in services):**
- Break enforcement: shifts ≤ 6 hrs → 0 min break required; 6–8 hrs → ≥ 30 min; > 8 hrs → ≥ 60 min
- Core-hour validation: punches outside company-configured core hours auto-flagged in `AttendanceRecord`
- Leave balance check: reject leave request if requested days > available balance for leave type
- Attendance exception: auto-create exception record when employee has no time entry on a scheduled shift day

**Frontend Pages / Components:**
- `LeaveRequestForm` — date picker, leave type selector, reason field; balance shown inline
- `LeaveApprovalInbox` — manager view; pending requests with approve / deny buttons
- `LeaveBalanceCard` — employee view; PTO / Sick / Comp balances with used/remaining
- `WeeklyScheduleCalendar` — manager view; drag-drop shift assignment per employee

---

### Sprint 4 — Payroll & Compensation
**Focus:** Timesheet generation, all compensation calculations, payroll export.

**DB Models to Create:**
- `Timesheet` — id, employee_id, company_id, pay_period_start, pay_period_end, status (`draft` / `submitted` / `approved` / `exported`), total_regular_hrs, total_ot_hrs, total_holiday_hrs, total_differential_hrs, submitted_at, approved_by, approved_at
- `PayrollLineItem` — id, timesheet_id (FK→Timesheet), date, hours_worked, rate_type (`regular` / `overtime` / `holiday` / `night_differential` / `pto` / `comp`), rate_multiplier, notes
- `PayrollExport` — id, company_id, pay_period_start, pay_period_end, exported_at, exported_by (FK→User), format (`csv` / `json`), record_count, file_path

**API Endpoints to Implement:**
- `POST /api/v1/timesheets/generate` — generate timesheet from time entries for a given pay period
- `GET  /api/v1/timesheets` — list; filter by employee/pay period/status
- `GET  /api/v1/timesheets/{id}` — full timesheet with line items
- `PUT  /api/v1/timesheets/{id}/submit` — employee submits for approval
- `PUT  /api/v1/timesheets/{id}/approve` — manager approves
- `POST /api/v1/timesheets/{id}/export` — generate CSV or JSON export
- `GET  /api/v1/payroll/exports/{id}/download` — download the export file

**Calculation Rules (PayrollCalculationService):**
- Regular hours: first 8 hrs/day and first 40 hrs/week at 1.0x
- Daily overtime: hours > 8/day at 1.5x (configurable via `CompanyPolicy`)
- Weekly overtime: hours > 40/week at 1.5x
- Double time: hours > 12/day at 2.0x (configurable)
- Holiday pay: entries on dates in `CompanyPolicy.holiday_dates` at 2.0x
- Night-shift differential: hours within configurable overnight window (default 22:00–06:00) at 1.25x
- PTO: approved PTO leave days converted to 8 hrs paid regular on timesheet
- Comp-time: OT hours optionally banked as comp balance instead of paid OT (per policy)
- Comp leave: comp hours used deducted from `LeaveBalance.comp_earned`

**Frontend Pages / Components:**
- `TimesheetPage` — line items table with rate type, hours, multiplier; submit button
- `PayrollExportPage` — pay period selector, format selector (CSV/JSON), download button
- `PayPeriodSummaryCard` — total regular / OT / holiday / differential hours at a glance

---

### Sprint 5 — Compliance & Reporting
**Focus:** Labor-rule engine, compliance violations, all operational reports, audit trail viewer.

**DB Models to Create:**
- `ComplianceViolation` — id, employee_id, company_id, violation_type (`missing_punch` / `min_wage` / `max_hours` / `mandatory_break` / `overtime_threshold`), description, occurred_at, resolved (bool), resolved_at, resolved_by, resolution_notes

**API Endpoints to Implement:**
- `POST /api/v1/compliance/validate` — run compliance check for a pay period; return violations list
- `GET  /api/v1/compliance/violations` — list; filter by employee/date/type/resolved
- `PUT  /api/v1/compliance/violations/{id}/resolve` — mark resolved with notes
- `GET  /api/v1/reports/compliance` — compliance summary per pay period (JSON + CSV download)
- `GET  /api/v1/reports/attendance-exceptions` — exception records with resolution status (JSON + CSV)
- `GET  /api/v1/reports/audit-trail` — admin only; full immutable log, paginated, filterable by entity/date
- `GET  /api/v1/reports/operational` — manager dashboard: total hrs, OT hrs, absences, late arrivals per period
- `GET  /api/v1/reports/crosscheck` — cross-reference time entries vs. schedules; flag discrepancies

**Business Rules (ComplianceValidationService):**
- Missing punch: flag any `TimeEntry` with no `clock_out` beyond end of pay period
- Minimum wage: flag if `total_hours * hourly_rate < minimum_wage * total_hours` (rate from `CompanyPolicy`)
- Maximum hours: flag if weekly hours exceed company-configured maximum (default 60 hrs/week)
- Mandatory break: flag if a shift > 6 hrs with `break_minutes` = 0 on `ShiftSchedule`
- Overtime threshold: flag if OT hours exceed company-configured threshold per period

**Frontend Pages / Components:**
- `ReportsDashboard` — tabbed layout: Compliance / Attendance Exceptions / Audit Trail / Operational / CrossCheck
- `ComplianceViolationsList` — filterable table; resolve button with notes modal
- `AuditTrailViewer` — admin only; read-only immutable log with filters
- `OperationalDashboard` — summary cards + data table for manager review

---

### Sprint 6 — QA & Security Hardening
**Focus:** Full automated test suite, security validation, accessibility, coverage gates.

**Testing Tasks:**
- Configure `pytest` with `pytest-cov` and `httpx` (async test client)
- Write API tests for every endpoint (happy path + all defined error cases)
- Configure Playwright; write E2E tests for: clock-in/out flow, leave request/approval, timesheet submit, report CSV download
- Run `pip-audit` and resolve all known vulnerabilities
- Run `bandit -r backend/app` and resolve all high-severity findings
- Run secret scan (`gitleaks` or `grep -r "SECRET\|PASSWORD\|TOKEN"`) against codebase
- Add ARIA labels to all interactive UI elements; verify keyboard navigation on all forms

**Security Hardening Tasks:**
- Add rate limiting to `POST /auth/login` (max 5 attempts per 5 min per IP; use `slowapi`)
- Validate Content-Type header on all POST/PUT routes
- Set `max_length` on all string Pydantic fields to prevent oversized payloads
- Verify CORS only allows whitelisted origins in production config
- Confirm JWT `exp` claim enforced; test with manually expired token

---

### Sprint 7 — Operational Readiness
**Focus:** Containerization, structured logging, incident triage demonstration.

**Tasks:**
- Write `backend/Dockerfile` — multi-stage build; non-root user; `HEALTHCHECK` instruction
- Write `frontend/Dockerfile` — build stage (Node) + serve stage (nginx)
- Write `docker-compose.yml` — services: `backend`, `frontend`, `db` (PostgreSQL for prod simulation)
- Implement request ID middleware: generate UUID per request; include in all log lines and response header `X-Request-ID`
- Structured log format: `{"timestamp": ..., "level": ..., "request_id": ..., "user_id": ..., "method": ..., "path": ..., "status": ..., "duration_ms": ...}`
- Simulate incident: script triggers a failed clock-in (e.g., duplicate punch); log output traced end-to-end
- Document root-cause workflow in `docs/incident-triage-example.md`
- Update `README.md` with full local setup steps + Docker Compose setup

---

## 6. Definition of Done

### Story-Level DoD
A user story is **Done** when ALL of the following are true:

| Gate | Requirement |
|---|---|
| Implementation | Code written, self-reviewed, and PR opened against `develop` |
| Peer review | Engineering Lead has approved the PR |
| Unit tests | New business logic has **100% branch coverage** |
| API tests | Every new endpoint has pytest tests covering happy path + all documented error cases |
| Coverage gate | Overall backend line coverage does not drop below **90%** |
| AC validation | QA Agent has run Playwright / API tests against all Given/When/Then criteria; all pass |
| Security review | Security Agent PR review complete; **0 high or critical findings** unresolved |
| OpenAPI | Every new endpoint documented in Swagger (`/docs`) with correct request/response schemas |
| No secrets | `grep -r "SECRET\|PASSWORD\|TOKEN\|KEY"` finds no hardcoded values in changed files |
| Responsiveness | Feature tested and functional on mobile viewport (375px wide) and desktop (1280px) |
| Traceability | `docs/requirement-traceability.md` updated: REQ-ID status → `Complete` |

---

### Sprint-Level Completion Criteria

#### Sprint 1 — Foundation is Complete When:
- [ ] Alembic migration runs with `alembic upgrade head` and creates all tables without error
- [ ] `POST /auth/register` + `POST /auth/login` return correct responses and JWT is valid
- [ ] Expired JWT returns `401 Unauthorized`
- [ ] `Employee` role cannot access `Admin`-only route; returns `403 Forbidden`
- [ ] Swagger UI (`/docs`) lists all implemented endpoints with correct schemas
- [ ] `GET /api/v1/companies` returns paginated results with `page` and `size` query params working
- [ ] **100% branch coverage** on `auth` service and RBAC dependency
- [ ] Overall backend coverage ≥ 90%
- [ ] `pip-audit` shows 0 known vulnerabilities

#### Sprint 2 — Time Management is Complete When:
- [ ] Employee can clock in → clock out → view their entry in one user flow (E2E Playwright test passes)
- [ ] Duplicate clock-in returns `409`; future timestamp returns `422` — both covered by pytest
- [ ] Every punch event (clock-in, clock-out, correction) creates an `AuditLog` record — verified by test
- [ ] Manager can view all employee time entries filtered by date range
- [ ] Manager can approve a time correction; original entry updated; audit log records the change
- [ ] `GET /attendance/missing-punches` correctly identifies entries open > 24 hrs
- [ ] **100% branch coverage** on `PunchValidationService`
- [ ] Playwright tests: clock-in flow, clock-out flow, duplicate punch error, correction approval
- [ ] Mobile viewport: Clock In/Out button usable on 375px width

#### Sprint 3 — Scheduling & Leave is Complete When:
- [ ] Employee can submit a leave request; manager receives it in approval inbox
- [ ] Manager can approve or deny with a comment; employee sees updated status
- [ ] Leave balance deducted correctly on approval; over-balance request rejected with `422`
- [ ] Shift created by manager appears on employee's weekly calendar view
- [ ] Break enforcement rule correctly rejects a shift > 6 hrs with 0 break minutes
- [ ] Core-hour violation flagged in `AttendanceRecord` when punch is outside configured window
- [ ] **100% branch coverage** on `LeaveValidationService` and `BreakEnforcementService`
- [ ] Playwright tests: leave request → approval flow, shift creation, balance display

#### Sprint 4 — Payroll is Complete When:
- [ ] Timesheet auto-generated from time entries correctly categorises regular, OT, holiday, and differential hours
- [ ] Daily OT (> 8 hrs), weekly OT (> 40 hrs), and double time (> 12 hrs) computed correctly — each case has a dedicated pytest
- [ ] Holiday pay multiplier applied on configured holiday dates
- [ ] Night-shift differential applied only within configured overnight window
- [ ] PTO leave approved in Sprint 3 appears as paid hours on timesheet
- [ ] CSV and JSON exports produced; schema matches documented format
- [ ] **100% branch coverage** on `PayrollCalculationService` (every rate-type branch tested)
- [ ] Playwright test: generate timesheet → submit → approve → download CSV export

#### Sprint 5 — Compliance is Complete When:
- [ ] `POST /compliance/validate` returns correct violations for a pay period containing known issues (seeded test data)
- [ ] All 5 violation types (missing punch, min wage, max hours, mandatory break, OT threshold) have corresponding pytest
- [ ] Audit trail returns immutable records; Admin can filter by entity type and date range
- [ ] CrossCheck report correctly flags employees with time entries but no matching schedule, and vice versa
- [ ] All 8 report endpoints return both JSON and downloadable CSV
- [ ] **100% branch coverage** on `ComplianceValidationService`
- [ ] Playwright tests: run compliance check, view violations, download report, view audit trail (admin)

#### Sprint 6 — QA & Security is Complete When:
- [ ] Backend line coverage ≥ **90%**; branch coverage **100%** on all service classes
- [ ] All 44 REQ-IDs have at least one passing pytest
- [ ] All Playwright E2E tests pass in headless mode
- [ ] `pip-audit` reports **0 vulnerabilities**
- [ ] `bandit` reports **0 high-severity** findings
- [ ] Secret scan reports **0 secrets** in the codebase
- [ ] Rate limiting on `/auth/login` verified: 6th attempt within 5 min returns `429`
- [ ] Expired JWT tested and returns `401`
- [ ] CORS test: request from unlisted origin returns `403`
- [ ] Security validation summary document completed and reviewed

#### Sprint 7 — Operational Readiness is Complete When:
- [ ] `docker-compose up` starts backend + frontend + database with no errors
- [ ] `GET /health` returns `200` inside the running container
- [ ] Every API request log line contains: `timestamp`, `request_id`, `method`, `path`, `status`, `duration_ms`
- [ ] Simulated incident log trace produced end-to-end (error → log → root cause identified)
- [ ] `README.md` contains complete local setup and Docker setup instructions
- [ ] All environment variables documented in `.env.example`

---

## 7. Branching Strategy

```
main          ← stable, deployable
  └── develop ← integration branch
        └── feature/<story-id>-short-description
        └── bugfix/<issue-id>-short-description
        └── hotfix/<issue-id>-short-description
```

- All work branches from `develop`
- PRs require at minimum: 1 human review + Security Agent check
- `develop` merges to `main` at the end of each sprint after QA sign-off

---

## 8. Folder Structure Convention

```
/
├── backend/              # Python / FastAPI
│   ├── app/
│   │   ├── api/v1/       # Route handlers
│   │   ├── core/         # Config, security, dependencies
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   └── services/     # Business logic layer
│   └── tests/
├── frontend/             # React / Vite
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/     # API client layer
│   │   └── store/        # State management
│   └── tests/
├── docs/                 # All planning and architecture docs
└── prompt-history/       # AI prompt log
```

---

## 9. API Design Standards

- All endpoints versioned under `/api/v1/`
- RESTful resource naming (nouns, not verbs)
- JSON request and response bodies
- Standard error response shape: `{ "detail": "...", "code": "..." }`
- Authentication via JWT Bearer token on all protected routes
- OpenAPI docs auto-generated at `/docs`

---

## 10. Security Standards

- Passwords hashed with bcrypt (passlib)
- JWT tokens signed with HS256; expiry enforced
- No secrets in source code — all via `.env` / environment variables
- CORS restricted to known frontend origins
- Role-based access control enforced at the route level
- Dependencies scanned for CVEs before each sprint release
