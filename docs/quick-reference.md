# Quick Reference
# BBSI BuildAThon 2026 — Workforce Time Tracking & Payroll Integration Platform

> **Last Updated:** 2026-07-01

---

## Build Sequence — What to Build Next

> Work through these in order. Each step unblocks the next.

| # | Step | Sprint | Status |
|---|---|---|---|
| 1 | SQLAlchemy base + Alembic setup | Sprint 1 | ✅ Done |
| 2 | Core models: `User`, `Company`, `Location`, `Role` | Sprint 1 | ✅ Done |
| 3 | First Alembic migration | Sprint 1 | ✅ Done |
| 4 | Auth endpoints: register / login / JWT | Sprint 1 | ✅ Done |
| 5 | RBAC middleware + protect routes | Sprint 1 | ✅ Done |
| 6 | `TimeEntry` + `AuditLog` models + migration | Sprint 2 | ✅ Done |
| 7 | Clock-in / clock-out API + punch validation | Sprint 2 | ✅ Done |
| 8 | Attendance tracking + missing punch detection | Sprint 2 | ✅ Done |
| 9 | Time correction workflow | Sprint 2 | ✅ Done |
| 10 | Frontend: Dashboard + clock-in/out widget | Sprint 2 | ✅ Done |
| 11 | Leave & shift models + migration | Sprint 3 | ✅ Done |
| 12 | Leave request/approval API + balance tracking | Sprint 3 | ✅ Done |
| 13 | Shift scheduling API + break/core-hour rules | Sprint 3 | ✅ Done |
| 14 | Policy configuration API | Sprint 3 | ✅ Done |
| 15 | Frontend: Leave management + schedule views | Sprint 3 | ✅ Done |
| 16 | Timesheet + PayrollExport models + migration | Sprint 4 | ✅ Done |
| 17 | Payroll calculation service (OT, holiday, differential) | Sprint 4 | ✅ Done |
| 18 | PTO/comp-time management + payroll export endpoint | Sprint 4 | ✅ Done |
| 19 | Frontend: Timesheet review + submit UI | Sprint 4 | ✅ Done |
| 20 | Compliance validation service (labor-rule engine) | Sprint 5 | ✅ Done |
| 21 | Report generation endpoints + audit trail viewer | Sprint 5 | ✅ Done |
| 22 | Frontend: Reports dashboard | Sprint 5 | ✅ Done |
| 23 | pytest API test suite (292 tests, 93% coverage) | Sprint 6 | ✅ Done |
| 24 | Playwright E2E test suite | Sprint 6 | ✅ Done |
| 25 | Security review (pip-audit, bandit, rate limit, CORS) | Sprint 6 | ✅ Done |
| 26 | Dockerfiles (backend + frontend) | Sprint 7 | ⬜ Next |
| 27 | Structured logging + incident triage demo | Sprint 7 | ⬜ |

---

## Start the Project

### Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
# API → http://localhost:8000
# Swagger UI → http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm run dev
# UI → http://localhost:5173
```

### QA & Security (Sprint 6)
```bash
# Run full test suite with coverage
cd backend && source venv/bin/activate
pytest --cov=app --cov-report=term-missing

# Static security analysis
bandit -r app -ll

# CVE scan
pip-audit -r requirements.txt --skip-editable

# Playwright E2E tests (requires backend running on :8000)
cd frontend
npm run test:e2e
```

---

## Key URLs (Local Dev)

| URL | Purpose |
|---|---|
| `http://localhost:8000/docs` | Interactive API docs (Swagger UI) |
| `http://localhost:8000/redoc` | API docs (ReDoc) |
| `http://localhost:8000/health` | Backend health check |
| `http://localhost:5173` | React frontend |

---

## Project Structure

```
/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app + CORS + router registration
│   │   ├── core/config.py    # Settings from .env (pydantic-settings)
│   │   ├── api/v1/           # All route handlers
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   └── services/         # Business logic
│   ├── venv/                 # Python virtual environment
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Page-level components
│   │   ├── services/         # API client (axios / fetch)
│   │   └── store/            # State management
│   └── package.json
├── docs/
│   ├── planning-framework.md       # Methodology, agent roles, sprint structure
│   ├── requirement-traceability.md # REQ-ID → feature → story mapping
│   ├── roadmap.md                  # Sprint-by-sprint delivery plan
│   ├── user-story-template.md      # Story format + completed example
│   └── quick-reference.md          # This file
└── prompt-history/
    └── prompt_history_001.md       # AI prompt log
```

---

## Agent Roles at a Glance

| Agent | Primary Tool | Responsibility |
|---|---|---|
| PO / BA Agent | Claude (GitHub Copilot) | User stories, acceptance criteria, requirement analysis |
| Developer Agent | Codex / GitHub Copilot | Backend API, frontend UI, DB schema, CI/CD |
| QA Agent | Playwright + pytest | UI automation, API tests, coverage, test evidence |
| Security Agent | pip-audit, custom review | PR security review, CVE scan, secret detection, auth validation |
| Support / Triage Agent | Claude | Log correlation, root-cause analysis, incident classification |
| BugBot Agent | Claude | Defect reproduction, root-cause, fix suggestions |

---

## Sprint Roadmap Summary

| Sprint | Focus | Key Milestone |
|---|---|---|
| 1 | Foundation | Auth, RBAC, DB schema, OpenAPI |
| 2 | Time Management | Clock-in/out, punch management, audit log |
| 3 | Scheduling & Leave | Leave workflows, shift scheduling |
| 4 | Payroll & Compensation | Timesheets, OT, payroll export |
| 5 | Compliance & Reporting | Audit trails, compliance reports |
| 6 | QA & Security | Full test suite, security sign-off |
| 7 | Operational Readiness | Docker, logging, incident triage demo |

---

## Requirement Coverage

| Domain | Requirements | REQ-ID Range |
|---|---|---|
| Time Management | 9 | REQ-101 – REQ-109 |
| Scheduling & Leave | 7 | REQ-201 – REQ-207 |
| Payroll & Compensation | 8 | REQ-301 – REQ-308 |
| Compliance & Reporting | 6 | REQ-401 – REQ-406 |
| Mobile Support | 4 | REQ-501 – REQ-504 |
| Enterprise Readiness | 5 | REQ-601 – REQ-605 |
| Technical | 5 | REQ-701 – REQ-705 |
| **Total** | **44** | |

Full traceability → `docs/requirement-traceability.md`

---

## API Conventions

- Base path: `/api/v1/`
- Auth: `Authorization: Bearer <JWT>` on all protected routes
- Error shape: `{ "detail": "message", "code": "ERROR_CODE" }`
- Pagination: `?page=1&size=20` on all list endpoints
- Timestamps: ISO 8601 UTC (`2026-05-14T09:00:00Z`)

---

## Environment Variables

Copy `backend/.env.example` → `backend/.env` and fill in:

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./workforce.db` |
| `SECRET_KEY` | JWT signing secret — **change in prod** | `change-me-in-production` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token TTL | `60` |
| `ALLOWED_ORIGINS` | CORS whitelist | `["http://localhost:3000","http://localhost:5173"]` |

---

## Common Commands

```bash
# Install / update backend deps
cd backend && source venv/bin/activate && pip install -r requirements.txt

# Freeze backend deps after adding a new package
pip freeze > requirements.txt

# Install frontend deps
cd frontend && npm install

# Run backend tests
cd backend && source venv/bin/activate && pytest --cov=app tests/

# Run frontend tests
cd frontend && npm test

# Run Playwright tests
cd frontend && npx playwright test
```

---

## Branching Cheat Sheet

```bash
# Start a new feature
git checkout develop
git pull
git checkout -b feature/US-101-employee-clock-in

# Open a PR to develop when done
# PR requires: Engineering Lead review + Security Agent check
```

---

## Key Docs

| Document | Purpose |
|---|---|
| [Planning Framework](planning-framework.md) | Methodology, agent roles, DoD, standards |
| [Requirement Traceability](requirement-traceability.md) | All 44 requirements tracked with status |
| [Roadmap](roadmap.md) | Sprint plan with deliverables |
| [User Story Template](user-story-template.md) | Story format, example, agent handoff flow |
| [Requirements Source](../bbsi_buildathon_2026_requirements_only.md) | Original BuildAThon requirements |
| [Prompt History](../prompt-history/prompt_history_001.md) | AI prompt log |
