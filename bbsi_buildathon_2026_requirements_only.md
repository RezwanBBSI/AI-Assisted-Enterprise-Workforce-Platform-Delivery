# BBSI BuildAThon 2026
# Workforce Platform Requirements Document

---

# 1. Purpose

This document defines the core functional and technical requirements for the BBSI BuildAThon 2026.

The objective is to provide participating teams with a clear understanding of the required business capabilities, technical expectations, approved tooling, and delivery scope for the BuildAThon.

The BuildAThon focuses on demonstrating AI-assisted enterprise software delivery using modern Agentic Development Environments (ADEs).

---

# 2. BuildAThon Objective

Teams will design and build a modern Workforce Time Tracking & Payroll Integration Platform.

The application should demonstrate:

- Functional workforce management workflows
- AI-assisted software development
- API-first engineering
- Automated testing
- Security validation
- Operational support readiness
- Platform engineering practices
- Human-in-the-loop governance

The focus of the BuildAThon is practical enterprise application delivery using ADE workflows.

---

# 3. Approved Tooling

## Required ADE Tools

Teams must use the following approved tools:

| Tool | Purpose |
|---|---|
| Claude | Requirements analysis, documentation, code generation, testing support |
| Codex | Code generation, debugging, refactoring, API generation |
| Manus.ai | Multi-step workflow orchestration and automation |

## Required Development Environment

All teams must use:

### GitHub Codespaces

GitHub Codespaces will serve as the standard cloud development environment.

---

# 4. Core Functional Requirements

## 4.1 Workforce Time Management

The application should support:

- Employee clock-in workflows
- Employee clock-out workflows
- Web-based punch management
- Mobile-friendly punch workflows
- Punch validation
- Missing punch detection
- Attendance tracking
- Employee time correction workflows
- Audit logging

---

## 4.2 Scheduling & Leave Management

The application should support:

- Leave request workflows
- Leave approval workflows
- Leave balance tracking
- Shift scheduling
- Break enforcement
- Core-hour validation
- Attendance exception handling

---

## 4.3 Payroll & Compensation

The application should support:

- Online timesheet processing
- Overtime calculations
- Holiday calculations
- Night-shift differential calculations
- PTO management
- Comp-time management
- Payroll export processing
- Payroll integration readiness

---

## 4.4 Compliance & Reporting

The application should support:

- Tax and labor-rule validations
- Compliance reporting
- Attendance exception reporting
- Audit trails
- Operational reporting
- CrossCheck reporting

---

## 4.5 Mobile Workforce Support

The application should support:

- Mobile-friendly workflows
- Mobile punch support
- Responsive UI behavior
- Device accessibility support

---

## 4.6 Enterprise Readiness

The application should support:

- Multi-company workflows
- Multi-location workflows
- Policy configurability
- Role-based access control
- Enterprise scalability considerations

---

# 5. Technical Requirements

## 5.1 API-First Design

Applications should expose APIs suitable for:

- Web applications
- Mobile applications
- Enterprise integrations
- Future extensibility

---

## 5.2 Cloud-Native Alignment

Applications should conceptually align with modern cloud-native practices.

Recommended principles:

- Stateless services
- API-based communication
- Container-ready architecture
- Secure secret management
- Observability support
- Logging and monitoring support

---

## 5.3 Future Integration Readiness

Teams are NOT required to implement:

- CIAM integration
- Event-driven integration
- Enterprise domain integration

However, applications should be designed in a way that future integration is possible.

Applications should conceptually support:

- Future CIAM integration
- Future enterprise domain integrations
- Future event-driven integration patterns
- Future cloud-native extensibility

Teams may document future integration approaches but are NOT required to demonstrate them during the BuildAThon.

---

# 6. Agentic Development Requirements

Teams are expected to demonstrate collaboration between AI-assisted agents and human team members.

---

## 6.1 Product Owner / BA Agent

Purpose:
Transform business features into development-ready requirements.

Expected responsibilities:

- Create user stories
- Create acceptance criteria
- Define workflows
- Define validations
- Produce development-ready requirements
- Produce QA-ready requirements

---

## 6.2 Developer / Platform Engineering Agent

Purpose:
Build and deploy the application.

Expected responsibilities:

- Frontend development
- Backend API development
- Database schema creation
- Integration-ready service development
- CI/CD workflow support
- Platform workflow support

Recommended technologies:

- React or similar frontend framework
- Python/FastAPI or similar backend framework
- Azure SQL or equivalent relational database

---

## 6.3 QA / STE Agent

Purpose:
Validate functionality and quality.

Expected responsibilities:

- UI automation testing
- API automation testing
- Regression testing
- Acceptance criteria validation
- Code coverage analysis
- Test evidence generation

Recommended tooling:

- Playwright
- API automation frameworks

---

## 6.4 Security / Verifier Agent

Purpose:
Validate security posture and secure coding practices.

Expected responsibilities:

- Pull request security review
- Dependency vulnerability scanning
- Secret detection
- Authentication validation
- Authorization validation
- API security verification
- Secure coding validation

---

## 6.5 Customer Support / Triage Agent

Purpose:
Assist with operational diagnostics and incident analysis.

Expected responsibilities:

- Incident analysis
- Log correlation
- Root-cause analysis
- Operational diagnostics
- Intelligent issue classification
- Remediation recommendations

---

## 6.6 BugBot Agent

Purpose:
Assist with defect recreation and remediation.

Expected responsibilities:

- Recreate defects
- Analyze failures
- Identify probable root causes
- Suggest fixes
- Generate remediation workflows

---

# 7. Human-in-the-Loop Governance

AI-assisted workflows must still include human review and governance.

Expected human responsibilities include:

| Role | Responsibility |
|---|---|
| Product Owner | Business prioritization |
| Business Analyst | Requirement validation |
| Solution Architect | Architecture guidance |
| Engineering Lead | Technical oversight |
| QA Lead | Quality approval |
| Security Engineer | Risk review |
| Platform Engineer | Environment governance |
| Support Team | Operational review |

---

# 8. Expected Deliverables

Teams should provide:

## Functional Deliverables

- Working application
- Frontend UI
- Backend APIs
- Database schema
- Integration examples

## Architecture Deliverables

- Solution architecture diagram
- API documentation
- Optional future integration documentation

## Quality Deliverables

- Automated test suite
- Test evidence
- Coverage summary

## Security Deliverables

- Security validation summary
- Vulnerability findings
- Secure coding verification

## Operational Deliverables

- Incident triage example
- Root-cause workflow example
- Logging and observability example

---

# 9. Evaluation Criteria

Teams will be evaluated based on:

| Area | Evaluation Focus |
|---|---|
| Functional Delivery | Workforce workflows and usability |
| API Design | API quality and extensibility |
| AI Usage | Effective ADE tool utilization |
| QA Automation | Automated testing maturity |
| Security | Security validation quality |
| Operational Support | Incident analysis and diagnostics |
| Platform Engineering | GitHub Codespaces workflow maturity |
| Documentation | Requirements and architecture clarity |
| Scalability | Enterprise readiness |

---

# 10. High-Level BuildAThon Workflow

```text
Business Features
        │
        ▼
PO / BA Agent
        │
        ▼
Developer / Platform Engineering Agent
        │
        ▼
QA / STE Verification Agent
        │
        ▼
Security / Verifier Agent
        │
        ▼
GitHub Codespaces + ADE Toolchain
        │
        ▼
Workforce Time Tracking Platform
        │
 ┌──────┴──────┐
 ▼             ▼
Support Agent  BugBot Agent
```

---

# 11. Final Guidance

The BuildAThon is intended to demonstrate practical enterprise software delivery using AI-assisted workflows.

The primary focus areas are:

- Functional delivery
- AI-assisted SDLC workflows
- QA automation
- Security validation
- Platform engineering
- Operational support readiness
- Human-in-the-loop governance

Teams should prioritize clarity, functionality, automation, maintainability, and enterprise readiness.

