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

**Deliverables:**

| REQ-ID | Feature | Notes |
|---|---|---|
| REQ-601 | Multi-company entity & scoping | Company model, DB table, FK relationships |
| REQ-602 | Multi-location entity & scoping | Location model linked to Company |
| REQ-604 | Role-based access control (RBAC) | Roles: Admin, Manager, Employee; JWT claims |
| REQ-701 | API-first design | OpenAPI / Swagger live at `/docs` |
| REQ-702 | Stateless FastAPI services | Dependency injection, no server-side session |
| REQ-704 | Secure secret management | `.env` / pydantic-settings wired end-to-end |
| REQ-605 | Enterprise scalability baseline | DB indexes, pagination on list endpoints |

**Milestone:** Auth flow (register / login / refresh) working; protected routes enforcing RBAC; Swagger UI accessible.

---

## Sprint 2 — Workforce Time Management

**Goal:** Core employee punch workflows — the primary feature of the platform.

**Deliverables:**

| REQ-ID | Feature | Notes |
|---|---|---|
| REQ-101 | Clock-in API + UI | POST `/api/v1/time-entries/clock-in` |
| REQ-102 | Clock-out API + UI | POST `/api/v1/time-entries/clock-out` |
| REQ-103 | Web punch management UI | Punch list, status indicators |
| REQ-104 | Mobile-friendly punch UI | Responsive layout, touch-optimized |
| REQ-105 | Punch validation service | Overlapping punches, future timestamps |
| REQ-106 | Missing punch detection | Automated flag on incomplete time entries |
| REQ-107 | Attendance tracking | Daily attendance record per employee |
| REQ-108 | Time correction workflow | Manager-initiated correction with reason |
| REQ-109 | Audit logging | Every punch event logged with user + timestamp |
| REQ-502 | Mobile punch support | Same clock-in/out UI responsive on mobile |

**Milestone:** An employee can clock in, clock out, and have their attendance recorded. A manager can view and correct entries. All changes are audit-logged.

---

## Sprint 3 — Scheduling & Leave Management

**Goal:** Enable managers to schedule shifts and employees to request leave.

**Deliverables:**

| REQ-ID | Feature | Notes |
|---|---|---|
| REQ-201 | Leave request workflow | Employee submits leave request |
| REQ-202 | Leave approval workflow | Manager approves / denies with comment |
| REQ-203 | Leave balance tracking | PTO/sick/comp balance per employee |
| REQ-204 | Shift scheduling | Manager creates/assigns shifts |
| REQ-205 | Break enforcement | Minimum break rules per shift |
| REQ-206 | Core-hour validation | Flag punches outside core hours |
| REQ-207 | Attendance exception handling | Auto-flag absences, late arrivals |
| REQ-603 | Policy configurability | Company-level leave & scheduling policies |

**Milestone:** Managers can publish schedules; employees can request and track leave; exceptions surface automatically.

---

## Sprint 4 — Payroll & Compensation

**Goal:** Process timesheets and calculate all compensation components.

**Deliverables:**

| REQ-ID | Feature | Notes |
|---|---|---|
| REQ-301 | Online timesheet processing | Weekly timesheet review + submit flow |
| REQ-302 | Overtime calculations | 40-hr weekly rule; 8-hr daily OT configurable |
| REQ-303 | Holiday calculations | Holiday pay multiplier from policy config |
| REQ-304 | Night-shift differential | Rate multiplier for configured overnight hours |
| REQ-305 | PTO management | PTO accrual, usage, carry-over |
| REQ-306 | Comp-time management | Comp-time earned and used tracking |
| REQ-307 | Payroll export processing | CSV / JSON export endpoint per pay period |
| REQ-308 | Payroll integration readiness | Export schema documented for future ERP hookup |

**Milestone:** A full pay-period timesheet can be processed, all compensation rules applied, and a payroll export file generated.

---

## Sprint 5 — Compliance & Reporting

**Goal:** Audit trails, compliance validation, and all operational reports.

**Deliverables:**

| REQ-ID | Feature | Notes |
|---|---|---|
| REQ-401 | Tax and labor-rule validations | Configurable rule engine; flag violations |
| REQ-402 | Compliance reporting | Report per pay period with violations |
| REQ-403 | Attendance exception reporting | Exception list with resolution status |
| REQ-404 | Audit trails | Full immutable log viewer (admin only) |
| REQ-405 | Operational reporting | Manager dashboard: hours, OT, absences |
| REQ-406 | CrossCheck reporting | Cross-reference time entries vs. schedules |

**Milestone:** Compliance officer can run a full audit trail; manager can generate operational reports; labor-rule violations are surfaced automatically.

---

## Sprint 6 — QA & Security Hardening

**Goal:** Full automated test suite, security validation, and coverage sign-off.

**Deliverables:**

| Area | Deliverable |
|---|---|
| UI Automation | Playwright tests covering all critical user workflows |
| API Automation | Pytest-based API test suite for all endpoints |
| Code Coverage | ≥ 80% backend coverage report |
| Security Review | Full dependency scan (pip-audit), secret detection |
| Auth Validation | JWT expiry, RBAC enforcement, brute-force protection |
| API Security | CORS, rate limiting, input validation checks |
| Accessibility | ARIA labels, keyboard navigation (REQ-504) |

**Milestone:** Test evidence package generated; security validation summary signed off; zero P1 / P2 vulnerabilities.

---

## Sprint 7 — Operational Readiness

**Goal:** Observability, containerization, and incident triage demonstration.

**Deliverables:**

| REQ-ID | Feature | Notes |
|---|---|---|
| REQ-703 | Dockerfile (backend + frontend) | Container-ready builds |
| REQ-705 | Structured logging & observability | Request IDs, error levels, log correlation |
| — | Incident triage example | End-to-end log trace for a simulated incident |
| — | Root-cause workflow example | BugBot Agent walkthrough |
| — | Observability dashboard notes | Future Datadog / Azure Monitor integration points |

**Milestone:** Application runs in Docker; a simulated incident can be triaged from logs; platform is demo-ready.

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
