# User Story Template
# BBSI BuildAThon 2026 — Workforce Time Tracking & Payroll Integration Platform

> **Source:** `docs/planning-framework.md` + `docs/roadmap.md`
> **Last Updated:** 2026-05-14

---

## How to Use This Template

Copy the **Story Template** block below for each new user story. Fill in every field before moving the story to `In Progress`. Stories missing acceptance criteria or a REQ-ID traceability link are **not ready for development**.

---

## Story Template

```markdown
## [US-XXX] Story Title

**REQ-ID(s):** REQ-XXX, REQ-XXX
**Sprint:** Sprint X
**Priority:** P1 / P2 / P3 / P4
**Status:** Not Started / In Progress / Complete
**Agent Owner:** PO/BA Agent
**Developer:** Developer / Platform Engineering Agent

---

### As a...
[role: Employee / Manager / Admin / Payroll Officer / Compliance Officer]

### I want to...
[action: one clear, specific thing the user wants to do]

### So that...
[business value: why this matters to them]

---

### Acceptance Criteria

**Scenario 1: [Happy path title]**
- **Given** [precondition — system state or user context]
- **When** [user action]
- **Then** [expected outcome — specific and testable]

**Scenario 2: [Alternate / edge case title]**
- **Given** [precondition]
- **When** [action]
- **Then** [expected outcome]

**Scenario 3: [Failure / validation case title]**
- **Given** [precondition]
- **When** [invalid or out-of-bounds action]
- **Then** [system should reject / return error / show message]

---

### API Contract (if applicable)

**Endpoint:** `METHOD /api/v1/resource`
**Auth:** Required / Not required
**Request Body:**
```json
{
  "field": "type"
}
```
**Success Response (2XX):**
```json
{
  "field": "value"
}
```
**Error Responses:**
- `400` — Validation error
- `401` — Unauthorized
- `403` — Forbidden (RBAC)
- `404` — Resource not found

---

### UI Notes (if applicable)

- Screen / component: [e.g., Clock-In button on Dashboard]
- Mobile behavior: [describe responsive expectations]
- Validation messages: [list inline error messages]

---

### Definition of Done Checklist

- [ ] Code implemented and peer-reviewed (Engineering Lead)
- [ ] Unit tests written; coverage ≥ 80% on new code
- [ ] Acceptance criteria validated by QA Agent (Playwright / API test)
- [ ] Security Agent PR review — no blocking findings
- [ ] API endpoint documented in OpenAPI / Swagger
- [ ] No hardcoded secrets or credentials
- [ ] Works on desktop and mobile viewport
- [ ] Requirement-traceability.md updated (Status → Complete)

---

### QA Agent Notes

_To be filled in by QA / STE Agent after testing._

- Test file: `tests/...`
- Test result: Pass / Fail
- Coverage: X%
- Evidence: [screenshot / report link]

---

### Security Agent Notes

_To be filled in by Security / Verifier Agent after PR review._

- PR reviewed: Yes / No
- Findings: None / [list findings]
- Blocking: Yes / No
- Sign-off: Approved / Rejected

---

### Notes / Out of Scope

[Any clarifications, known limitations, or items explicitly out of scope for this story.]
```

---

## Completed Story Example

```markdown
## [US-101] Employee Clock-In

**REQ-ID(s):** REQ-101, REQ-109
**Sprint:** Sprint 2
**Priority:** P1
**Status:** Not Started
**Agent Owner:** PO/BA Agent
**Developer:** Developer / Platform Engineering Agent

---

### As a...
Employee

### I want to...
Click a Clock-In button on the web or mobile dashboard

### So that...
My shift start time is recorded accurately and I have an active time entry for the day

---

### Acceptance Criteria

**Scenario 1: Successful clock-in**
- **Given** I am logged in as an Employee with no active time entry today
- **When** I click "Clock In"
- **Then** a new time entry is created with my employee ID, company ID, location ID, and the current UTC timestamp; I see a confirmation message and the button changes to "Clock Out"

**Scenario 2: Already clocked in**
- **Given** I am logged in and already have an open time entry today
- **When** I click "Clock In"
- **Then** the system returns a 409 error and displays "You are already clocked in"

**Scenario 3: Unauthenticated user**
- **Given** I am not logged in
- **When** I attempt to call the clock-in endpoint
- **Then** the system returns a 401 Unauthorized response

---

### API Contract

**Endpoint:** `POST /api/v1/time-entries/clock-in`
**Auth:** Required (Employee role)
**Request Body:** _(none — employee ID sourced from JWT)_
**Success Response (201):**
```json
{
  "id": "uuid",
  "employee_id": "uuid",
  "clock_in": "2026-05-14T09:00:00Z",
  "clock_out": null,
  "status": "open"
}
```
**Error Responses:**
- `401` — Not authenticated
- `409` — Already clocked in

---

### UI Notes

- Screen: Employee Dashboard → Clock-In/Out widget
- Mobile: Full-width button, large touch target (min 48px height)
- Validation message: "You are already clocked in" shown inline below button

---

### Definition of Done Checklist

- [ ] Code implemented and peer-reviewed
- [ ] Unit tests written; coverage ≥ 80%
- [ ] Playwright test: clock-in happy path + already-clocked-in error
- [ ] Security Agent PR review complete
- [ ] Endpoint in Swagger
- [ ] No hardcoded secrets
- [ ] Responsive on mobile
- [ ] requirement-traceability.md REQ-101 → Complete
```

---

## Story ID Convention

| Prefix | Range | Domain |
|---|---|---|
| US-1XX | 101–199 | Time Management |
| US-2XX | 201–299 | Scheduling & Leave |
| US-3XX | 301–399 | Payroll & Compensation |
| US-4XX | 401–499 | Compliance & Reporting |
| US-5XX | 501–599 | Mobile & Accessibility |
| US-6XX | 601–699 | Enterprise Readiness |
| US-7XX | 701–799 | Technical / Platform |

---

## Agent Handoff Flow

```
PO/BA Agent          Developer Agent       QA Agent             Security Agent
    │                     │                    │                     │
    │  Story ready        │                    │                     │
    │─────────────────▶   │                    │                     │
    │                     │  Implementation    │                     │
    │                     │─────────────────▶  │                     │
    │                     │                    │  Tests pass         │
    │                     │                    │─────────────────▶   │
    │                     │                    │                     │  PR approved
    │                     │◀────────────────────────────────────────  │
    │                     │  Merge to develop  │                     │
```
