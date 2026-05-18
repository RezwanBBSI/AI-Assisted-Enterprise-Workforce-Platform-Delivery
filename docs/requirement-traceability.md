# Requirement Traceability Matrix
# BBSI BuildAThon 2026 — Workforce Time Tracking & Payroll Integration Platform

> **Source:** `bbsi_buildathon_2026_requirements_only.md` + `docs/planning-framework.md`
> **Last Updated:** 2026-05-18

Status values: `Not Started` | `In Progress` | `Complete` | `Deferred`
Priority values: `P1 - Critical` | `P2 - High` | `P3 - Medium` | `P4 - Low`

---

## Section 4.1 — Workforce Time Management

| REQ-ID | Requirement | Feature / Component | Sprint | Story ID | Priority | Status |
|---|---|---|---|---|---|---|
| REQ-101 | Employee clock-in workflows | Time Entry API + Clock-In UI | Sprint 2 | US-101 | P1 | Complete |
| REQ-102 | Employee clock-out workflows | Time Entry API + Clock-Out UI | Sprint 2 | US-102 | P1 | Complete |
| REQ-103 | Web-based punch management | Punch Management UI + API | Sprint 2 | US-103 | P1 | Complete |
| REQ-104 | Mobile-friendly punch workflows | Responsive Punch UI | Sprint 2 | US-104 | P2 | Complete |
| REQ-105 | Punch validation | Punch Validation Service | Sprint 2 | US-105 | P1 | Complete |
| REQ-106 | Missing punch detection | Punch Audit Service | Sprint 2 | US-106 | P2 | Complete |
| REQ-107 | Attendance tracking | Attendance Record API | Sprint 2 | US-107 | P1 | Complete |
| REQ-108 | Employee time correction workflows | Time Correction API + UI | Sprint 2 | US-108 | P2 | Complete |
| REQ-109 | Audit logging | Audit Log Service + DB Table | Sprint 2 | US-109 | P1 | Complete |

---

## Section 4.2 — Scheduling & Leave Management

| REQ-ID | Requirement | Feature / Component | Sprint | Story ID | Priority | Status |
|---|---|---|---|---|---|---|
| REQ-201 | Leave request workflows | Leave Request API + UI | Sprint 3 | US-201 | P1 | Complete |
| REQ-202 | Leave approval workflows | Leave Approval API + UI | Sprint 3 | US-202 | P1 | Complete |
| REQ-203 | Leave balance tracking | Leave Balance Service | Sprint 3 | US-203 | P2 | Complete |
| REQ-204 | Shift scheduling | Shift Schedule API + UI | Sprint 3 | US-204 | P2 | Complete |
| REQ-205 | Break enforcement | Break Rules Service | Sprint 3 | US-205 | P2 | Complete |
| REQ-206 | Core-hour validation | Core Hours Validation Service | Sprint 3 | US-206 | P2 | Complete |
| REQ-207 | Attendance exception handling | Exception Handling API | Sprint 3 | US-207 | P2 | Complete |

---

## Section 4.3 — Payroll & Compensation

| REQ-ID | Requirement | Feature / Component | Sprint | Story ID | Priority | Status |
|---|---|---|---|---|---|---|
| REQ-301 | Online timesheet processing | Timesheet API + UI | Sprint 4 | US-301 | P1 | Complete |
| REQ-302 | Overtime calculations | Payroll Calculation Service | Sprint 4 | US-302 | P1 | Complete |
| REQ-303 | Holiday calculations | Holiday Rules Service | Sprint 4 | US-303 | P2 | Complete |
| REQ-304 | Night-shift differential calculations | Shift Differential Service | Sprint 4 | US-304 | P2 | Complete |
| REQ-305 | PTO management | PTO Balance API + UI | Sprint 4 | US-305 | P2 | Complete |
| REQ-306 | Comp-time management | Comp-Time Service | Sprint 4 | US-306 | P3 | Complete |
| REQ-307 | Payroll export processing | Payroll Export API | Sprint 4 | US-307 | P1 | Complete |
| REQ-308 | Payroll integration readiness | Integration-Ready Export Format | Sprint 4 | US-308 | P2 | Complete |

---

## Section 4.4 — Compliance & Reporting

| REQ-ID | Requirement | Feature / Component | Sprint | Story ID | Priority | Status |
|---|---|---|---|---|---|---|
| REQ-401 | Tax and labor-rule validations | Compliance Validation Service | Sprint 5 | US-401 | P1 | Not Started |
| REQ-402 | Compliance reporting | Compliance Report API + UI | Sprint 5 | US-402 | P1 | Not Started |
| REQ-403 | Attendance exception reporting | Exception Report API | Sprint 5 | US-403 | P2 | Not Started |
| REQ-404 | Audit trails | Audit Trail API + UI | Sprint 5 | US-404 | P1 | Not Started |
| REQ-405 | Operational reporting | Operational Dashboard API | Sprint 5 | US-405 | P2 | Not Started |
| REQ-406 | CrossCheck reporting | CrossCheck Report API | Sprint 5 | US-406 | P2 | Not Started |

---

## Section 4.5 — Mobile Workforce Support

| REQ-ID | Requirement | Feature / Component | Sprint | Story ID | Priority | Status |
|---|---|---|---|---|---|---|
| REQ-501 | Mobile-friendly workflows | Responsive Layout (Tailwind/CSS) | Sprint 2–5 | US-501 | P2 | Not Started |
| REQ-502 | Mobile punch support | Mobile Punch UI | Sprint 2 | US-502 | P2 | Not Started |
| REQ-503 | Responsive UI behavior | Responsive Component Library | Sprint 2–5 | US-503 | P2 | Not Started |
| REQ-504 | Device accessibility support | ARIA Labels, Keyboard Nav | Sprint 6 | US-504 | P3 | Not Started |

---

## Section 4.6 — Enterprise Readiness

| REQ-ID | Requirement | Feature / Component | Sprint | Story ID | Priority | Status |
|---|---|---|---|---|---|---|
| REQ-601 | Multi-company workflows | Company Entity + Scoping | Sprint 1 | US-601 | P1 | Complete |
| REQ-602 | Multi-location workflows | Location Entity + Scoping | Sprint 1 | US-602 | P1 | Complete |
| REQ-603 | Policy configurability | Policy Configuration API | Sprint 3 | US-603 | P2 | Complete |
| REQ-604 | Role-based access control | RBAC Middleware + Role Model | Sprint 1 | US-604 | P1 | Complete |
| REQ-605 | Enterprise scalability considerations | Stateless API Design, DB Indexing | Sprint 1 | US-605 | P2 | Complete |

---

## Section 5 — Technical Requirements

| REQ-ID | Requirement | Feature / Component | Sprint | Story ID | Priority | Status |
|---|---|---|---|---|---|---|
| REQ-701 | API-first design | OpenAPI / Swagger at `/docs` | Sprint 1 | US-701 | P1 | Complete |
| REQ-702 | Stateless services | Stateless FastAPI design | Sprint 1 | US-702 | P1 | Complete |
| REQ-703 | Container-ready architecture | Dockerfile (backend + frontend) | Sprint 7 | US-703 | P3 | Not Started |
| REQ-704 | Secure secret management | `.env` + Pydantic Settings | Sprint 1 | US-704 | P1 | Complete |
| REQ-705 | Observability / logging support | Structured Logging (stdlib/loguru) | Sprint 7 | US-705 | P2 | Not Started |

---

## Summary

| Section | Total Requirements | Not Started | In Progress | Complete | Deferred |
|---|---|---|---|---|---|
| 4.1 Time Management | 9 | 0 | 0 | 9 | 0 |
| 4.2 Scheduling & Leave | 7 | 0 | 0 | 7 | 0 |
| 4.3 Payroll & Compensation | 8 | 0 | 0 | 8 | 0 |
| 4.4 Compliance & Reporting | 6 | 6 | 0 | 0 | 0 |
| 4.5 Mobile Support | 4 | 4 | 0 | 0 | 0 |
| 4.6 Enterprise Readiness | 5 | 0 | 0 | 5 | 0 |
| 5. Technical | 5 | 2 | 0 | 3 | 0 |
| **Total** | **44** | **12** | **0** | **32** | **0** |
