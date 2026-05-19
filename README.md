# BBSI Workforce Platform
### AI-Assisted Enterprise Workforce Platform Delivery — BBSI BuildAThon 2026

> **Full-stack workforce time-tracking and payroll integration platform** built with FastAPI + React.  
> 7 sprints · 292+ tests · 93% backend coverage · Docker-ready

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2 (async), Alembic, Pydantic v2 |
| Auth | JWT (HS256), bcrypt, RBAC (Admin / Manager / Employee) |
| Frontend | React 19, Vite 8, React Router v7 |
| Database | SQLite (dev) / PostgreSQL 16 (production / Docker) |
| Container | Docker multi-stage builds, nginx, Docker Compose |
| Testing | pytest-asyncio, 292 tests, Playwright E2E |
| Security | slowapi rate limiting, bandit 0 HIGH, pip-audit 0 CVEs |

---

## Quick Start — Local Development

### Prerequisites
- Python 3.12+
- Node.js 22+

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head              # create all tables
python scripts/seed.py            # seed demo data + default users
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

---

## Quick Start — Docker Compose

```bash
# 1. Clone and enter the repo
git clone https://github.com/RezwanBBSI/AI-Assisted-Enterprise-Workforce-Platform-Delivery.git
cd AI-Assisted-Enterprise-Workforce-Platform-Delivery

# 2. Copy and configure environment
cp backend/.env.example backend/.env
# Edit backend/.env if you want to change the secret key or DB credentials

# 3. Start all services
docker-compose up --build

# 4. Verify backend health
curl http://localhost:8000/health
# → {"status": "ok", "service": "Workforce Platform API"}
```

- **Frontend** → http://localhost:80
- **Backend API** → http://localhost:8000
- **Swagger docs** → http://localhost:8000/docs

---

## Demo Accounts

| Role | Email | Password |
|---|---|---|
| Admin | `admin@bbsi.demo` | `Admin1234!` |
| Manager | `manager@bbsi.demo` | `Manager1234!` |
| Employee | `employee@bbsi.demo` | `Employee1234!` |

> Seed these with: `python scripts/seed.py` (local) or they are auto-seeded on first boot in Docker.

---

## Project Structure

```
/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # Route handlers (14 modules)
│   │   ├── core/               # Config, security, deps, logging
│   │   ├── models/             # SQLAlchemy ORM models (17 tables)
│   │   ├── schemas/            # Pydantic request/response models
│   │   └── services/           # Business logic layer
│   ├── alembic/versions/       # DB migrations (6 migration files)
│   ├── scripts/                # seed.py, simulate_incident.py
│   ├── tests/                  # 292 tests, 93% coverage
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api.js              # Centralized API client
│   │   ├── context/            # AuthContext
│   │   ├── components/         # Shared UI components
│   │   └── pages/              # Route-level page components
│   ├── nginx.conf              # Production nginx config
│   └── Dockerfile
├── docs/                       # Planning, schema, API reference, roadmap
├── docker-compose.yml
└── README.md
```

---

## Running Tests

```bash
cd backend
source venv/bin/activate
pytest --tb=short -q                          # all 292 tests
pytest --cov=app --cov-report=term-missing    # with coverage report
```

### Static Analysis

```bash
bandit -r app -ll                             # 0 HIGH findings
pip-audit -r requirements.txt                 # 0 CVEs
```

### E2E Tests (Playwright)

```bash
cd frontend
npx playwright install chromium
npm run test:e2e
```

---

## Incident Simulation

```bash
cd backend
source venv/bin/activate
python scripts/simulate_incident.py
```

Triggers a duplicate clock-in to produce a structured error log. See [docs/incident-triage-example.md](docs/incident-triage-example.md) for the full root-cause walkthrough.

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env`:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./workforce.db` | SQLAlchemy DB URL |
| `SECRET_KEY` | `change-me-in-production` | JWT signing secret |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT lifetime |
| `ALLOWED_ORIGINS` | `["http://localhost:5173"]` | CORS origins |
| `POSTGRES_USER` | `workforce` | Docker PostgreSQL user |
| `POSTGRES_PASSWORD` | `workforce_secret` | Docker PostgreSQL password |
| `POSTGRES_DB` | `workforce` | Docker PostgreSQL database name |

---

## Documentation

| Doc | Description |
|---|---|
| [docs/roadmap.md](docs/roadmap.md) | Sprint plan and completion status |
| [docs/api-reference.md](docs/api-reference.md) | All endpoints with request/response schemas |
| [docs/database-schema.md](docs/database-schema.md) | All 17 tables with columns and FK relationships |
| [docs/requirement-traceability.md](docs/requirement-traceability.md) | REQ-ID → sprint → test coverage mapping |
| [docs/incident-triage-example.md](docs/incident-triage-example.md) | Structured log + root-cause walkthrough |
| [docs/planning-framework.md](docs/planning-framework.md) | Methodology, agent roles, DoD |
