# Product Roadmap
# BBSI BuildAThon 2026 — Workforce Time Tracking & Payroll Integration Platform

> **Source:** `docs/planning-framework.md` + `docs/requirement-traceability.md`
> **Last Updated:** 2026-05-14
> **Current Sprint:** Sprint 1 — Foundation 🔄

---

## Overview

The platform is delivered across **7 sprints**, each building on the previous. Foundation work (auth, DB, RBAC) is done first so all subsequent feature sprints have a stable base. QA and security validation run alongside development and are formally finalized in Sprint 6.

```
Sprint 1 ──▶ Sprint 2 ──▶ Sprint 3 ──▶ Sprint 4 ──▶ Sprint 5 ──▶ Sprint 6 ──▶ Sprint 7
Foundation   Time Mgmt   Scheduling   Payroll      Compliance    QA &         Ops
🔄 CURRENT   & Punching  & Leave      & Comp        & Reporting   Security     Readiness
```

---

## Current Status — 2026-05-14

| Item | Status |
|---|---|
| Repo scaffolded (backend + frontend) | ✅ Done |
| Python venv created & activated | ✅ Done |
| FastAPI + dependencies installed | ✅ Done |
| React (Vite) frontend scaffolded | ✅ Done |
| `.gitignore` for both folders | ✅ Done |
| Planning docs created (`docs/`) | ✅ Done |
| Database setup (SQLAlchemy + Alembic) | ⬜ Not Started |
| Core DB models (User, Company, Location, Role) | ⬜ Not Started |
| Auth endpoints (register / login / JWT) | ⬜ Not Started |
| RBAC middleware | ⬜ Not Started |

---

## Sprint 1 — Foundation 🔄 CURRENT

**Goal:** Establish the technical backbone. Nothing user-visible ships yet, but every subsequent sprint depends on this.

### DB Models

| Model | Key Fields |
|---|---|
| `Company` | id (UUID PK), name, is_active, created_at |
| `Location` | id, company_id (FK→Company), name, timezone, is_active |
| `Role` | id, name (`Admin` / `Manager` / `Employee`) |
| `User` | id (UUID PK), email (unique, indexed), hashed_password, full_name, is_active, created_at |
| `UserRole` | user_id (FK→User), company_id (FK→Company), role_id (FK→Role) |

### API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | None | Create user account |
| POST | `/api/v1/auth/login` | None | Return JWT access token |
| POST | `/api/v1/auth/refresh` | JWT | Issue refreshed token |
| GET | `/api/v1/auth/me` | JWT | Return current user |
| GET | `/api/v1/companies` | Admin | Paginated company list |
| POST | `/api/v1/companies` | Admin | Create company |
| GET | `/api/v1/locations` | Admin/Manager | Paginated locations scoped to company |
| POST | `/api/v1/locations` | Admin/Manager | Create location |

### Infrastructure Tasks
- SQLAlchemy async session factory wired to FastAPI lifespan
- Alembic configured; `alembic upgrade head` creates all tables
- JWT utility: `create_access_token()`, `decode_token()` with expiry enforcement
- `get_current_user` dependency (raises 401 on invalid/expired token)
- `require_role(*roles)` dependency (raises 403 on insufficient role)
- Global pagination dependency (`?page=1&size=20`) applied to all list endpoints
- Passwords hashed with `passlib[bcrypt]`; plaintext never stored or logged

### Phase Completion Criteria — Sprint 1 is DONE when:
- [ ] `alembic upgrade head` runs without error and all 5 tables exist in the DB
- [ ] `POST /auth/register` → `POST /auth/login` → `GET /auth/me` flow works end-to-end
- [ ] Expired JWT returns `401 Unauthorized` (verified by pytest)
- [ ] Employee role requesting an Admin-only route returns `403 Forbidden` (verified by pytest)
- [ ] Swagger UI at `/docs` shows all 8 endpoints with correct request/response schemas
- [ ] Pagination working: `?page=2&size=5` returns correct slice with `total` in response
- [ ] **100% branch coverage** on `AuthService` and RBAC dependency
- [ ] Overall backend line coverage ≥ 90%
- [ ] `pip-audit` reports 0 known vulnerabilities

---

## Sprint 2 — Workforce Time Management

**Goal:** Core employee punch workflows — the primary feature of the platform.

### DB Models

| Model | Key Fields |
|---|---|
| `TimeEntry` | id (UUID), employee_id (FK→User), company_id, location_id, clock_in (UTC), clock_out (UTC, nullable), status (`open`/`closed`/`corrected`), created_at |
| `TimeCorrection` | id, time_entry_id (FK→TimeEntry), requested_by, approved_by (nullable), reason, original_clock_in, new_clock_in, original_clock_out, new_clock_out, status (`pending`/`approved`/`denied`) |
| `AttendanceRecord` | id, employee_id, company_id, date, status (`present`/`absent`/`late`/`missing_punch`) |
| `AuditLog` | id, entity_type, entity_id (UUID), action, performed_by (FK→User), performed_at, details (JSON) |

### API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/time-entries/clock-in` | Employee | Create open entry; 409 if already open |
| POST | `/api/v1/time-entries/clock-out` | Employee | Close open entry; 404 if none open |
| GET | `/api/v1/time-entries` | Employee/Manager | Paginated; filter by employee_id, date range, status |
| GET | `/api/v1/time-entries/{id}` | Employee/Manager | Single entry |
| POST | `/api/v1/time-entries/{id}/correction` | Employee | Submit correction request |
| PUT | `/api/v1/time-entries/{id}/correction/{cid}` | Manager | Approve or deny correction |
| GET | `/api/v1/attendance` | Manager | Daily records per employee; filter by date range |
| GET | `/api/v1/attendance/missing-punches` | Manager | Open entries older than 24 hours |

### Punch Validation Rules (`PunchValidationService`)
- Clock-in rejected if employee already has an `open` entry → `409`
- Clock-in rejected if timestamp is in the future → `422`
- Clock-out rejected if `clock_out ≤ clock_in` → `422`
- Clock-out rejected if no open entry exists for employee → `404`
- Every punch event (in, out, correction) writes one `AuditLog` record

### Frontend Components

| Component | Description |
|---|---|
| `DashboardPage` | Today's punch status, Clock In/Out button, last 7-day summary |
| `PunchWidget` | Large touch-friendly button; shows `Clocked In since HH:MM` or `Clocked Out` |
| `TimeEntriesTable` | Manager view; paginated; sortable by date/employee; links to correction |
| `CorrectionModal` | Employee submits reason + proposed times; manager approves/denies inline |

### Phase Completion Criteria — Sprint 2 is DONE when:
- [ ] Full clock-in → clock-out → view flow works end-to-end (Playwright test passes)
- [ ] Duplicate clock-in returns `409`; future timestamp returns `422` — both covered by pytest
- [ ] Every clock event produces exactly one `AuditLog` record (verified by pytest asserting DB row)
- [ ] Manager views time entries filtered by `?employee_id=X&from=Y&to=Z` correctly
- [ ] Approved time correction updates the `TimeEntry` and logs the change in `AuditLog`
- [ ] `GET /attendance/missing-punches` correctly returns entries open > 24 hrs (seeded test data)
- [ ] **100% branch coverage** on `PunchValidationService`
- [ ] Playwright tests passing: clock-in, clock-out, duplicate error, correction approval
- [ ] Clock In/Out button functional and visible on 375px mobile viewport

---

## Sprint 3 — Scheduling & Leave Management

**Goal:** Enable managers to schedule shifts and employees to request and track leave.

### DB Models

| Model | Key Fields |
|---|---|
| `LeaveRequest` | id, employee_id, company_id, leave_type (`pto`/`sick`/`comp`/`unpaid`), start_date, end_date, days_requested, reason, status (`pending`/`approved`/`denied`/`cancelled`), reviewed_by, reviewed_at, review_comment |
| `LeaveBalance` | id, employee_id, company_id, year, pto_total, pto_used, sick_total, sick_used, comp_earned, comp_used |
| `ShiftSchedule` | id, employee_id, company_id, location_id, shift_date, shift_start (time), shift_end (time), break_minutes, created_by |
| `CompanyPolicy` | id, company_id, policy_key (indexed), policy_value (JSON), updated_by, updated_at |

### API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/leave-requests` | Employee | Submit leave request |
| GET | `/api/v1/leave-requests` | Employee/Manager | List; filter by employee/status/date range |
| PUT | `/api/v1/leave-requests/{id}/review` | Manager | Approve or deny with comment |
| PUT | `/api/v1/leave-requests/{id}/cancel` | Employee | Cancel pending request |
| GET | `/api/v1/leave-balances/{employee_id}` | Employee/Manager | Current year balance |
| POST | `/api/v1/schedules` | Manager | Create shift |
| GET | `/api/v1/schedules` | Employee/Manager | List; filter by employee_id / date range |
| PUT | `/api/v1/schedules/{id}` | Manager | Update shift |
| DELETE | `/api/v1/schedules/{id}` | Manager | Remove shift |
| GET | `/api/v1/policies` | Admin/Manager | List company policies |
| PUT | `/api/v1/policies/{key}` | Admin | Update policy value |

### Business Rules
- **Break enforcement:** shifts ≤ 6 hrs → 0 min required; 6–8 hrs → ≥ 30 min; > 8 hrs → ≥ 60 min; violation raises `422`
- **Leave balance check:** request rejected if `days_requested > available balance` for the leave type → `422`
- **Core-hour validation:** punch outside company-configured window (stored in `CompanyPolicy`) auto-flags `AttendanceRecord.status = late`
- **Attendance exception:** if employee has a scheduled shift but no `TimeEntry` for that date, auto-create `AttendanceRecord.status = absent`

### Frontend Components

| Component | Description |
|---|---|
| `LeaveRequestForm` | Date range picker, leave type dropdown, reason field; balance shown inline |
| `LeaveApprovalInbox` | Manager view; pending requests; Approve/Deny buttons with comment field |
| `LeaveBalanceCard` | Employee view; PTO / Sick / Comp used vs. remaining |
| `WeeklyScheduleCalendar` | Manager view; weekly grid per employee; click to add/edit shift |

### Phase Completion Criteria — Sprint 3 is DONE when:
- [ ] Employee submits leave request → manager approves → employee balance decremented (Playwright E2E passes)
- [ ] Over-balance leave request returns `422` (pytest)
- [ ] Shift created by manager appears on employee's weekly calendar view
- [ ] Break enforcement: shift > 6 hrs with `break_minutes = 0` returns `422` (pytest)
- [ ] Core-hour punch outside configured window creates `AttendanceRecord` with `status = late` (pytest)
- [ ] No-punch on scheduled shift day creates `AttendanceRecord` with `status = absent` (pytest)
- [ ] **100% branch coverage** on `LeaveValidationService` and `BreakEnforcementService`
- [ ] Playwright tests passing: leave submission, approval, balance display, shift creation

---

## Sprint 4 — Payroll & Compensation

**Goal:** Process timesheets and calculate all compensation components accurately.

### DB Models

| Model | Key Fields |
|---|---|
| `Timesheet` | id, employee_id, company_id, pay_period_start, pay_period_end, status (`draft`/`submitted`/`approved`/`exported`), total_regular_hrs, total_ot_hrs, total_holiday_hrs, total_differential_hrs, submitted_at, approved_by, approved_at |
| `PayrollLineItem` | id, timesheet_id (FK→Timesheet), date, hours_worked, rate_type (`regular`/`overtime`/`holiday`/`night_differential`/`pto`/`comp`), rate_multiplier, notes |
| `PayrollExport` | id, company_id, pay_period_start, pay_period_end, exported_at, exported_by, format (`csv`/`json`), record_count, file_path |

### API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/timesheets/generate` | Manager | Auto-generate from time entries for a pay period |
| GET | `/api/v1/timesheets` | Employee/Manager | List; filter by employee/pay period/status |
| GET | `/api/v1/timesheets/{id}` | Employee/Manager | Full timesheet with all line items |
| PUT | `/api/v1/timesheets/{id}/submit` | Employee | Submit for approval |
| PUT | `/api/v1/timesheets/{id}/approve` | Manager | Approve timesheet |
| POST | `/api/v1/timesheets/{id}/export` | Manager | Generate CSV or JSON export |
| GET | `/api/v1/payroll/exports/{id}/download` | Manager | Download export file |

### Calculation Rules (`PayrollCalculationService`)

| Rule | Logic |
|---|---|
| Regular | First 8 hrs/day AND first 40 hrs/week → 1.0× |
| Daily OT | Hours 8–12 in a day → 1.5× (threshold configurable via `CompanyPolicy`) |
| Daily double time | Hours > 12 in a day → 2.0× (configurable) |
| Weekly OT | Hours 40–60 in a week → 1.5× |
| Holiday pay | Entry on a date in `CompanyPolicy.holiday_dates` → 2.0× |
| Night differential | Hours within overnight window (default 22:00–06:00, configurable) → 1.25× |
| PTO | Approved PTO leave day → 8 hrs at 1.0× (regular) on timesheet |
| Comp-time earned | OT hours optionally banked as comp balance (per `CompanyPolicy`) |
| Comp-time used | Approved comp leave deducted from `LeaveBalance.comp_earned` |

### Frontend Components

| Component | Description |
|---|---|
| `TimesheetPage` | Line items table: date, hours, rate type, multiplier; submit button |
| `PayPeriodSummaryCard` | Total regular / OT / holiday / differential hours at a glance |
| `PayrollExportPage` | Pay period selector, format selector (CSV/JSON), generate + download button |

### Phase Completion Criteria — Sprint 4 is DONE when:
- [ ] Timesheet generated from Sprint 2 time entries correctly categorises all rate types
- [ ] Daily OT (> 8 hrs): dedicated pytest confirms 1.5× applied to correct hours only
- [ ] Weekly OT (> 40 hrs): dedicated pytest with multi-day entries confirms correct split
- [ ] Double time (> 12 hrs/day): dedicated pytest confirms 2.0× on hours beyond threshold
- [ ] Holiday multiplier applied only on dates listed in `CompanyPolicy.holiday_dates` (pytest)
- [ ] Night differential applied only within configured overnight window (pytest with boundary values)
- [ ] PTO approved in Sprint 3 appears as `rate_type = pto` line item on timesheet (pytest)
- [ ] CSV export validated against documented schema; JSON export parseable (pytest)
- [ ] Timesheet submit → approve → export flow passes Playwright E2E test
- [ ] **100% branch coverage** on `PayrollCalculationService`

---

## Sprint 5 — Compliance & Reporting

**Goal:** Labor-rule compliance engine, all operational reports, and immutable audit trail viewer.

### DB Models

| Model | Key Fields |
|---|---|
| `ComplianceViolation` | id, employee_id, company_id, violation_type (`missing_punch`/`min_wage`/`max_hours`/`mandatory_break`/`ot_threshold`), description, occurred_at, resolved (bool), resolved_at, resolved_by, resolution_notes |

### API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/compliance/validate` | Manager/Admin | Run compliance check for a pay period |
| GET | `/api/v1/compliance/violations` | Manager/Admin | List; filter by employee/date/type/resolved |
| PUT | `/api/v1/compliance/violations/{id}/resolve` | Manager/Admin | Mark resolved with notes |
| GET | `/api/v1/reports/compliance` | Manager/Admin | Compliance summary per pay period (JSON + CSV) |
| GET | `/api/v1/reports/attendance-exceptions` | Manager/Admin | Exception records with resolution status (JSON + CSV) |
| GET | `/api/v1/reports/audit-trail` | Admin only | Full immutable log; paginated; filter by entity/date |
| GET | `/api/v1/reports/operational` | Manager/Admin | Total hrs, OT hrs, absences, late arrivals per period |
| GET | `/api/v1/reports/crosscheck` | Manager/Admin | Time entries vs. schedules discrepancies |

### Compliance Validation Rules (`ComplianceValidationService`)

| Violation Type | Trigger Condition |
|---|---|
| `missing_punch` | `TimeEntry` with no `clock_out` after pay period end |
| `min_wage` | Calculated hourly rate < `CompanyPolicy.min_wage` |
| `max_hours` | Weekly total > `CompanyPolicy.max_hours_per_week` (default 60) |
| `mandatory_break` | Shift > 6 hrs with `break_minutes = 0` on `ShiftSchedule` |
| `ot_threshold` | OT hours exceed `CompanyPolicy.ot_alert_threshold` for the period |

### Frontend Components

| Component | Description |
|---|---|
| `ReportsDashboard` | Tabbed layout: Compliance / Exceptions / Audit Trail / Operational / CrossCheck |
| `ComplianceViolationsList` | Filterable table; Resolve button opens notes modal |
| `AuditTrailViewer` | Admin only; read-only immutable log; filter by entity type and date |
| `OperationalDashboard` | Summary cards (total hrs, OT hrs, absences) + drill-down data table |

### Phase Completion Criteria — Sprint 5 is DONE when:
- [ ] `POST /compliance/validate` returns all 5 violation types when seeded test data contains each condition (pytest per violation type)
- [ ] Resolve workflow: `PUT /compliance/violations/{id}/resolve` sets `resolved = true` and records `resolution_notes`
- [ ] All 8 report endpoints return correct JSON and a downloadable CSV file (pytest + Playwright download test)
- [ ] Audit trail is read-only: no POST/PUT/DELETE on audit entries; Admin-only access enforced (pytest)
- [ ] CrossCheck report correctly flags entries with no schedule and schedules with no entry (seeded data, pytest)
- [ ] **100% branch coverage** on `ComplianceValidationService`
- [ ] Playwright tests: run compliance check, resolve violation, download compliance CSV, view audit trail

---

## Sprint 6 — QA & Security Hardening

**Goal:** Full automated test suite, security validation, accessibility sign-off, and coverage gates.

### Testing Tasks

| Task | Tool | Target |
|---|---|---|
| API unit + integration tests | pytest + httpx | Every endpoint; happy path + all error cases |
| Backend line coverage | pytest-cov | ≥ 90% overall |
| Backend branch coverage | pytest-cov | **100%** on all service classes |
| All 44 REQ-IDs covered | pytest | At least one test per requirement |
| E2E UI tests | Playwright (headless) | Clock-in/out, leave flow, timesheet submit, report download |
| Dependency CVE scan | pip-audit | 0 vulnerabilities |
| Static analysis | bandit | 0 high-severity findings |
| Secret scan | gitleaks / grep | 0 secrets in codebase |
| ARIA labels | manual + axe | All interactive elements labelled |
| Keyboard navigation | manual | All forms navigable without mouse |

### Security Hardening Tasks

| Task | Implementation |
|---|---|
| Rate limiting on login | `slowapi`: max 5 attempts per 5 min per IP → `429` |
| Content-Type validation | Reject non-`application/json` POST/PUT requests |
| Payload size limits | `max_length` on all Pydantic string fields; reject oversized bodies |
| CORS enforcement | Non-whitelisted origins return `403` |
| JWT expiry test | Manually expired token returns `401` |
| RBAC matrix test | Each role tested against each restricted endpoint |

### Phase Completion Criteria — Sprint 6 is DONE when:
- [ ] `pytest --cov=app --cov-branch` shows ≥ **90% line coverage** and **100% branch coverage** on all `services/` classes
- [ ] All 44 REQ-IDs have at least one passing pytest (verified by test naming convention `test_req_XXX_*`)
- [ ] All Playwright E2E tests pass in headless mode (`npx playwright test`)
- [ ] `pip-audit` reports **0 vulnerabilities**
- [ ] `bandit -r backend/app -ll` reports **0 high-severity** findings
- [ ] Secret scan reports **0 findings**
- [ ] 6th login attempt within 5 min returns `429 Too Many Requests` (pytest)
- [ ] Request from non-whitelisted origin rejected by CORS (pytest)
- [ ] Expired JWT returns `401` (pytest)
- [ ] Security validation summary document written and reviewed by Security Engineer

---

## Sprint 7 — Operational Readiness

**Goal:** Containerisation, structured logging, and incident triage demonstration.

### Tasks

| Task | Detail |
|---|---|
| `backend/Dockerfile` | Multi-stage build; non-root user; `HEALTHCHECK curl /health`; minimal final image |
| `frontend/Dockerfile` | Build stage (Node 22); serve stage (nginx); static assets only in final image |
| `docker-compose.yml` | Services: `backend`, `frontend`, `db` (PostgreSQL); env vars via `.env`; health checks |
| Request ID middleware | UUID generated per request; added to all log lines and `X-Request-ID` response header |
| Structured log format | JSON: `timestamp`, `level`, `request_id`, `user_id`, `method`, `path`, `status`, `duration_ms` |
| Error log enrichment | Stack trace, `request_id`, `user_id` on every 5XX response |
| Simulated incident | Script triggers duplicate clock-in; full log trace produced end-to-end |
| Root-cause workflow | Documented in `docs/incident-triage-example.md` with log excerpts and BugBot walkthrough |
| README update | Full local setup + Docker Compose setup + env var reference |

### Phase Completion Criteria — Sprint 7 is DONE when:
- [ ] `docker-compose up` starts all three services without error
- [ ] `GET /health` returns `200` from inside the running backend container (`docker exec` or curl)
- [ ] Every API request log line contains all 8 required fields (verified by parsing log output in pytest)
- [ ] Simulated incident: error log produced, `request_id` traceable across request lifecycle
- [ ] `docs/incident-triage-example.md` contains log excerpts, root-cause statement, and remediation steps
- [ ] `README.md` updated: fresh clone → `docker-compose up` → working app in < 5 commands
- [ ] All environment variables present in `.env.example`

---

## Feature Priority Summary

| Priority | Count | Description |
|---|---|---|
| P1 - Critical | 20 | Must ship for a functional, secure platform |
| P2 - High | 18 | Core enterprise features; expected for BuildAThon scoring |
| P3 - Medium | 4 | Polish and operational completeness |
| P4 - Low | 0 | — |

---

## Future Integration Roadmap (Post-BuildAThon)

These are **not in scope** for the BuildAThon but the architecture is designed to support them:

| Integration | Approach |
|---|---|
| CIAM (e.g., Azure AD B2C) | Replace local JWT auth with OIDC token validation |
| Event-driven integration | Publish punch/payroll events to Azure Service Bus or Kafka |
| ERP / HRIS integration | Expose payroll export as a webhook-triggered feed |
| Cloud-native deployment | AKS / Azure Container Apps with managed identity |
