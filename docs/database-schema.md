# Database Schema Reference
# BBSI BuildAThon 2026 — Workforce Platform

> **Auto-generated from:** `backend/app/models/`
> **Last Updated:** Sprint 1 (2026-05-14)
> **Migration file:** `alembic/versions/72c2b223f8ae_initial_schema.py`
> **Apply:** `cd backend && alembic upgrade head`

---

## Overview

```
companies
    └── locations       (company_id FK)
    └── user_roles      (company_id FK)

users
    └── user_roles      (user_id FK)

roles
    └── user_roles      (role_id FK)
```

---

## Table: `companies`

**Model:** `app/models/company.py` → `Company`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PK | `uuid4()` |
| `name` | `VARCHAR(255)` | NOT NULL | — |
| `is_active` | `BOOLEAN` | NOT NULL | `True` |
| `created_at` | `DATETIME` (tz-aware) | NOT NULL | `utcnow()` |

**Relationships:**
- `locations` → one-to-many → `Location.company_id`
- `user_roles` → one-to-many → `UserRole.company_id`

---

## Table: `locations`

**Model:** `app/models/location.py` → `Location`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PK | `uuid4()` |
| `company_id` | `VARCHAR(36)` | FK → `companies.id` ON DELETE CASCADE, INDEX | — |
| `name` | `VARCHAR(255)` | NOT NULL | — |
| `address_line_1` | `VARCHAR(255)` | nullable | — |
| `city` | `VARCHAR(100)` | nullable | — |
| `state` | `VARCHAR(2)` | nullable | 2-letter US state code, e.g. `WA` |
| `zip_code` | `VARCHAR(10)` | nullable | — |
| `country` | `VARCHAR(2)` | NOT NULL | `"US"` |
| `timezone` | `VARCHAR(64)` | NOT NULL | `"UTC"` |
| `is_active` | `BOOLEAN` | NOT NULL | `True` |

**Relationships:**
- `company` → many-to-one → `Company`

---

## Table: `roles`

**Model:** `app/models/role.py` → `Role`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PK | `uuid4()` |
| `name` | `VARCHAR(50)` | UNIQUE, NOT NULL | — |

**Seeded values:** `Admin`, `Manager`, `Employee`

**Enum helper:** `app/models/role.py::RoleName` (use for safe string references)

**Relationships:**
- `user_roles` → one-to-many → `UserRole.role_id`

---

## Table: `users`

**Model:** `app/models/user.py` → `User`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PK | `uuid4()` |
| `email` | `VARCHAR(255)` | UNIQUE, INDEX, NOT NULL | — |
| `hashed_password` | `VARCHAR(255)` | NOT NULL | bcrypt hash |
| `full_name` | `VARCHAR(255)` | NOT NULL | — |
| `is_active` | `BOOLEAN` | NOT NULL | `True` |
| `created_at` | `DATETIME` (tz-aware) | NOT NULL | `utcnow()` |

> ⚠️ `hashed_password` is never returned in any API response. Plaintext passwords are never stored or logged.

**Relationships:**
- `user_roles` → one-to-many → `UserRole.user_id`

---

## Table: `user_roles`

**Model:** `app/models/user_role.py` → `UserRole`

| Column | Type | Constraints |
|---|---|---|
| `user_id` | `VARCHAR(36)` | PK, FK → `users.id` ON DELETE CASCADE |
| `company_id` | `VARCHAR(36)` | PK, FK → `companies.id` ON DELETE CASCADE |
| `role_id` | `VARCHAR(36)` | PK, FK → `roles.id` ON DELETE CASCADE |

**Unique constraint:** `uq_user_company_role` on `(user_id, company_id, role_id)`

> A user may hold different roles in different companies (e.g., Admin at Company A, Employee at Company B).

**Relationships:**
- `user` → many-to-one → `User`
- `company` → many-to-one → `Company`
- `role` → many-to-one → `Role`

---

## System Tables

| Table | Purpose |
|---|---|
| `alembic_version` | Tracks applied migration revisions. Do not modify manually. |

---

## Migration Guide

```bash
# Apply all pending migrations
cd backend && alembic upgrade head

# Generate a new migration after changing models
alembic revision --autogenerate -m "description of change"

# Roll back one migration
alembic downgrade -1

# Show current revision
alembic current
```

> **SQLite note:** All migrations use `render_as_batch=True` to support column alterations on SQLite (which doesn't support ALTER COLUMN natively).

---

## Seeding

```bash
cd backend
source venv/bin/activate

# Seed roles + default company:
python scripts/seed.py

# Seed and assign Admin role to a user:
python scripts/seed.py --email you@example.com --role Admin

# Reset DB and re-seed (DEV ONLY):
python scripts/seed.py --reset --email you@example.com
```

---

## Sprint Changelog

| Sprint | Changes |
|---|---|
| Sprint 1 | Initial schema: `companies`, `locations`, `roles`, `users`, `user_roles` |
| Sprint 1 (patch) | Added address fields to `locations`: `address_line_1`, `city`, `state`, `zip_code`, `country` |
| Sprint 2 | _(planned)_ `time_entries`, `time_corrections`, `attendance_records`, `audit_logs` |
| Sprint 3 | _(planned)_ `shifts`, `schedules`, `leave_requests`, `leave_balances` |
| Sprint 4 | _(planned)_ `pay_periods`, `payroll_records`, `overtime_rules` |
