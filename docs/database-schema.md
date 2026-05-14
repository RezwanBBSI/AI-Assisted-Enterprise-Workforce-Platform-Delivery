# Database Schema Reference
# BBSI BuildAThon 2026 — Workforce Platform

> **Auto-generated from:** `backend/app/models/`
> **Last Updated:** Sprint 2 (2026-05-15)
> **Current migration head:** `alembic/versions/08cbdf02a2cd_sprint_2_time_management_tables.py`
> **Apply:** `cd backend && alembic upgrade head`

---

## Overview

```
companies
    └── locations          (company_id FK)
    └── user_roles         (company_id FK)
    └── time_entries       (company_id FK)
    └── attendance_records (company_id FK)

users
    └── user_roles         (user_id FK)
    └── time_entries       (employee_id FK)
    └── time_corrections   (requested_by / approved_by FK)
    └── attendance_records (employee_id FK)
    └── audit_logs         (performed_by FK)

roles
    └── user_roles         (role_id FK)

time_entries
    └── time_corrections   (time_entry_id FK)
    └── attendance_records (time_entry_id FK)
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

---

## Table: `time_entries`

**Model:** `app/models/time_entry.py` → `TimeEntry`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PK | `uuid4()` |
| `employee_id` | `VARCHAR(36)` | FK → `users.id` CASCADE, INDEX | — |
| `company_id` | `VARCHAR(36)` | FK → `companies.id` CASCADE, INDEX | — |
| `location_id` | `VARCHAR(36)` | FK → `locations.id` SET NULL, nullable | — |
| `clock_in` | `DATETIME` | NOT NULL | — |
| `clock_out` | `DATETIME` | nullable | — |
| `status` | `VARCHAR(16)` | NOT NULL | `"open"` |
| `break_minutes` | `INTEGER` | nullable | — |
| `created_at` | `DATETIME` | NOT NULL | `utcnow()` |

**Status values:** `open`, `closed`, `corrected`

**Relationships:**
- `employee` → many-to-one → `User`
- `company` → many-to-one → `Company`
- `location` → many-to-one → `Location` (nullable)
- `corrections` → one-to-many → `TimeCorrection` (cascade all-delete-orphan)

---

## Table: `time_corrections`

**Model:** `app/models/time_correction.py` → `TimeCorrection`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PK | `uuid4()` |
| `time_entry_id` | `VARCHAR(36)` | FK → `time_entries.id` CASCADE, INDEX | — |
| `requested_by` | `VARCHAR(36)` | FK → `users.id` CASCADE | — |
| `approved_by` | `VARCHAR(36)` | FK → `users.id` SET NULL, nullable | — |
| `reason` | `TEXT` | NOT NULL | — |
| `original_clock_in` | `DATETIME` | NOT NULL | — |
| `new_clock_in` | `DATETIME` | NOT NULL | — |
| `original_clock_out` | `DATETIME` | nullable | — |
| `new_clock_out` | `DATETIME` | nullable | — |
| `status` | `VARCHAR(16)` | NOT NULL | `"pending"` |
| `created_at` | `DATETIME` | NOT NULL | `utcnow()` |
| `reviewed_at` | `DATETIME` | nullable | — |

**Status values:** `pending`, `approved`, `denied`

---

## Table: `attendance_records`

**Model:** `app/models/attendance_record.py` → `AttendanceRecord`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PK | `uuid4()` |
| `employee_id` | `VARCHAR(36)` | FK → `users.id` CASCADE, INDEX | — |
| `company_id` | `VARCHAR(36)` | FK → `companies.id` CASCADE | — |
| `date` | `DATE` | NOT NULL | — |
| `status` | `VARCHAR(16)` | NOT NULL | — |
| `time_entry_id` | `VARCHAR(36)` | FK → `time_entries.id` SET NULL, nullable | — |

**Status values:** `present`, `absent`, `late`, `missing_punch`

**Unique constraint:** `uq_attendance_emp_company_date` on `(employee_id, company_id, date)`

---

## Table: `audit_logs`

**Model:** `app/models/audit_log.py` → `AuditLog`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PK | `uuid4()` |
| `entity_type` | `VARCHAR(64)` | INDEX | — |
| `entity_id` | `VARCHAR(36)` | INDEX | — |
| `action` | `VARCHAR(64)` | NOT NULL | — |
| `performed_by` | `VARCHAR(36)` | FK → `users.id` SET NULL, nullable | — |
| `performed_at` | `DATETIME` | NOT NULL | — |
| `details` | `TEXT` | nullable | JSON string |

**Action values (time domain):** `clock_in`, `clock_out`, `correction_submitted`, `correction_approved`, `correction_denied`

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
| Sprint 2 | `time_entries`, `time_corrections`, `attendance_records`, `audit_logs` — time management and punching |
| Sprint 3 | _(planned)_ `shifts`, `schedules`, `leave_requests`, `leave_balances` |
| Sprint 4 | _(planned)_ `pay_periods`, `payroll_records`, `overtime_rules` |
