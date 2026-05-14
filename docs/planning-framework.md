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

| Phase | Sprint(s) | Focus |
|---|---|---|
| Foundation | Sprint 1 | Repo setup, DB schema, auth, core API skeleton |
| Time Management | Sprint 2 | Clock-in/out, punch management, audit logging |
| Scheduling & Leave | Sprint 3 | Leave workflows, shift scheduling, break enforcement |
| Payroll & Compensation | Sprint 4 | Timesheets, overtime, holiday, PTO, payroll export |
| Compliance & Reporting | Sprint 5 | Audit trails, compliance reports, CrossCheck reporting |
| QA & Security | Sprint 6 | Full test suite, security validation, performance review |
| Operational Readiness | Sprint 7 | Incident triage example, observability, final polish |

---

## 6. Definition of Done

A user story is **Done** when:

- [ ] Code is written and peer-reviewed (Engineering Lead approval)
- [ ] Unit tests pass with ≥ 80% coverage on new code
- [ ] Acceptance criteria validated by QA Agent (Playwright / API tests)
- [ ] Security Agent has reviewed the PR and found no blocking issues
- [ ] API endpoint is documented in OpenAPI / Swagger
- [ ] No hardcoded secrets or credentials
- [ ] Feature works on both desktop and mobile viewport

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
