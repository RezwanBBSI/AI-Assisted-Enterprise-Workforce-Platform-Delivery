# Database Schema Reference
# BBSI BuildAThon 2026 — Workforce Platform

> **Auto-generated from:** `backend/app/models/`
> **Last Updated:** Sprint 5 (2026-06-15)
> **Current migration head:** `alembic/versions/b7e3f9a2c851_sprint_5_compliance.py`
> **Apply:** `cd backend && alembic upgrade head`

---

## Overview

```
companies
    └── locations          (company_id FK)
    └── user_roles         (company_id FK)
    └── time_entries       (company_id FK)
    └── attendance_records (company_id FK)
    └── leave_requests     (company_id FK)
    └── leave_balances     (company_id FK)
    └── shift_schedules    (company_id FK)
    └── company_policies   (company_id FK)
    └── timesheets         (company_id FK)
    └── payroll_exports    (company_id FK)

users
    └── user_roles         (user_id FK)
    └── time_entries       (employee_id FK)
    └── time_corrections   (requested_by / approved_by FK)
    └── attendance_records (employee_id FK)
    └── audit_logs         (performed_by FK)
    └── leave_requests     (employee_id / reviewed_by FK)
    └── leave_balances     (employee_id FK)
    └── shift_schedules    (employee_id / created_by FK)
    └── company_policies   (updated_by FK)
    └── timesheets         (employee_id / approved_by FK)
    └── payroll_exports    (exported_by FK)
    └── compliance_violations (employee_id / resolved_by FK)

roles
    └── user_roles         (role_id FK)

time_entries
    └── time_corrections   (time_entry_id FK)
    └── attendance_records (time_entry_id FK)

timesheets
    └── payroll_line_items (timesheet_id FK)
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

**Action values (leave domain):** `leave_submitted`, `leave_approved`, `leave_denied`, `leave_cancelled`

**Action values (schedule domain):** `shift_created`, `shift_updated`, `shift_deleted`

---

## Table: `leave_requests`

**Model:** `app/models/leave_request.py` → `LeaveRequest`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PK | `uuid4()` |
| `employee_id` | `VARCHAR(36)` | FK → `users.id` CASCADE, INDEX | — |
| `company_id` | `VARCHAR(36)` | FK → `companies.id` CASCADE, INDEX | — |
| `leave_type` | `VARCHAR(16)` | NOT NULL | — |
| `start_date` | `DATE` | NOT NULL | — |
| `end_date` | `DATE` | NOT NULL | — |
| `days_requested` | `FLOAT` | NOT NULL | — |
| `reason` | `TEXT` | nullable | — |
| `status` | `VARCHAR(16)` | NOT NULL | `"pending"` |
| `reviewed_by` | `VARCHAR(36)` | FK → `users.id` SET NULL, nullable | — |
| `reviewed_at` | `DATETIME` | nullable | — |
| `review_comment` | `TEXT` | nullable | — |
| `created_at` | `DATETIME` | NOT NULL | `utcnow()` |

**Leave type values:** `pto`, `sick`, `comp`, `unpaid`

**Status values:** `pending`, `approved`, `denied`, `cancelled`

**Relationships:**
- `employee` → many-to-one → `User` (via `employee_id`)
- `reviewer` → many-to-one → `User` (via `reviewed_by`; nullable)
- `company` → many-to-one → `Company`

---

## Table: `leave_balances`

**Model:** `app/models/leave_balance.py` → `LeaveBalance`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PK | `uuid4()` |
| `employee_id` | `VARCHAR(36)` | FK → `users.id` CASCADE, INDEX | — |
| `company_id` | `VARCHAR(36)` | FK → `companies.id` CASCADE, INDEX | — |
| `year` | `INTEGER` | NOT NULL | — |
| `pto_total` | `FLOAT` | NOT NULL | `0.0` |
| `pto_used` | `FLOAT` | NOT NULL | `0.0` |
| `sick_total` | `FLOAT` | NOT NULL | `0.0` |
| `sick_used` | `FLOAT` | NOT NULL | `0.0` |
| `comp_earned` | `FLOAT` | NOT NULL | `0.0` |
| `comp_used` | `FLOAT` | NOT NULL | `0.0` |
| `updated_at` | `DATETIME` | NOT NULL | `utcnow()` |

**Unique constraint:** `uq_leave_balance_employee_company_year` on `(employee_id, company_id, year)`

> If no row exists for the requested `(employee_id, company_id, year)`, the API auto-creates a zeroed row.

---

## Table: `shift_schedules`

**Model:** `app/models/shift_schedule.py` → `ShiftSchedule`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PK | `uuid4()` |
| `employee_id` | `VARCHAR(36)` | FK → `users.id` CASCADE, INDEX | — |
| `company_id` | `VARCHAR(36)` | FK → `companies.id` CASCADE, INDEX | — |
| `location_id` | `VARCHAR(36)` | FK → `locations.id` SET NULL, nullable | — |
| `shift_date` | `DATE` | NOT NULL, INDEX | — |
| `shift_start` | `TIME` | NOT NULL | — |
| `shift_end` | `TIME` | NOT NULL | — |
| `break_minutes` | `INTEGER` | NOT NULL | `0` |
| `created_by` | `VARCHAR(36)` | FK → `users.id` SET NULL, nullable | — |
| `created_at` | `DATETIME` | NOT NULL | `utcnow()` |

**Break enforcement rules:**
- Shift duration ≤ 6 hrs → 0 min required
- Shift duration > 6 hrs and ≤ 8 hrs → minimum 30 min break
- Shift duration > 8 hrs → minimum 60 min break

**Relationships:**
- `employee` → many-to-one → `User` (via `employee_id`)
- `creator` → many-to-one → `User` (via `created_by`; nullable)
- `location` → many-to-one → `Location` (nullable)
- `company` → many-to-one → `Company`

---

## Table: `company_policies`

**Model:** `app/models/company_policy.py` → `CompanyPolicy`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PK | `uuid4()` |
| `company_id` | `VARCHAR(36)` | FK → `companies.id` CASCADE, INDEX | — |
| `policy_key` | `VARCHAR(64)` | NOT NULL, INDEX | — |
| `policy_value` | `TEXT` | NOT NULL | — |
| `updated_by` | `VARCHAR(36)` | FK → `users.id` SET NULL, nullable | — |
| `updated_at` | `DATETIME` | NOT NULL | `utcnow()` |

**Unique constraint:** `uq_company_policy_key` on `(company_id, policy_key)`

> `policy_value` stores JSON-serialized values (numbers, strings, arrays, objects) as text.

**Example keys:** `core_hours_start`, `core_hours_end`, `overtime_threshold`, `min_wage`, `max_hours_per_week`, `holiday_dates`

---

## Table: `timesheets`

**Model:** `app/models/timesheet.py` → `Timesheet`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PK | `uuid4()` |
| `employee_id` | `VARCHAR(36)` | FK → `users.id` CASCADE, INDEX | — |
| `company_id` | `VARCHAR(36)` | FK → `companies.id` CASCADE, INDEX | — |
| `pay_period_start` | `DATE` | NOT NULL | — |
| `pay_period_end` | `DATE` | NOT NULL | — |
| `status` | `VARCHAR(16)` | NOT NULL | `"draft"` |
| `total_regular_hrs` | `FLOAT` | NOT NULL | `0.0` |
| `total_ot_hrs` | `FLOAT` | NOT NULL | `0.0` |
| `total_holiday_hrs` | `FLOAT` | NOT NULL | `0.0` |
| `total_differential_hrs` | `FLOAT` | NOT NULL | `0.0` |
| `submitted_at` | `DATETIME` | nullable | — |
| `approved_by` | `VARCHAR(36)` | FK → `users.id` SET NULL, nullable | — |
| `approved_at` | `DATETIME` | nullable | — |
| `created_at` | `DATETIME` | NOT NULL | `utcnow()` |

**Status values:** `draft` → `submitted` → `approved` → `exported`

**Relationships:**
- `employee` → many-to-one → `User`
- `approver` → many-to-one → `User` (nullable)
- `company` → many-to-one → `Company`
- `line_items` → one-to-many → `PayrollLineItem` (cascade delete-orphan)

---

## Table: `payroll_line_items`

**Model:** `app/models/payroll_line_item.py` → `PayrollLineItem`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PK | `uuid4()` |
| `timesheet_id` | `VARCHAR(36)` | FK → `timesheets.id` CASCADE, INDEX | — |
| `entry_date` | `DATE` | NOT NULL | — |
| `hours_worked` | `FLOAT` | NOT NULL | — |
| `rate_type` | `VARCHAR(32)` | NOT NULL | — |
| `rate_multiplier` | `FLOAT` | NOT NULL | `1.0` |
| `notes` | `TEXT` | nullable | — |
| `created_at` | `DATETIME` | NOT NULL | `utcnow()` |

**Rate type values:** `regular`, `overtime`, `double_time`, `holiday`, `night_differential`, `pto`, `sick`, `comp`

**Relationships:**
- `timesheet` → many-to-one → `Timesheet`

---

## Table: `payroll_exports`

**Model:** `app/models/payroll_export.py` → `PayrollExport`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PK | `uuid4()` |
| `company_id` | `VARCHAR(36)` | FK → `companies.id` CASCADE, INDEX | — |
| `pay_period_start` | `DATE` | NOT NULL | — |
| `pay_period_end` | `DATE` | NOT NULL | — |
| `exported_at` | `DATETIME` | NOT NULL | `utcnow()` |
| `exported_by` | `VARCHAR(36)` | FK → `users.id` SET NULL, nullable | — |
| `export_format` | `VARCHAR(8)` | NOT NULL | `"csv"` |
| `record_count` | `INTEGER` | NOT NULL | `0` |
| `file_name` | `VARCHAR(255)` | NOT NULL | — |

**Export format values:** `csv`, `json`

**Relationships:**
- `company` → many-to-one → `Company`
- `exporter` → many-to-one → `User` (nullable)

---

## Table: `compliance_violations`

**Model:** `app/models/compliance_violation.py` → `ComplianceViolation`
**Migration:** `alembic/versions/b7e3f9a2c851_sprint_5_compliance.py`

| Column | Type | Constraints | Default |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PK | `uuid4()` |
| `employee_id` | `VARCHAR(36)` | FK → `users.id` CASCADE, INDEX | — |
| `company_id` | `VARCHAR(36)` | FK → `companies.id` CASCADE, INDEX | — |
| `violation_type` | `VARCHAR(32)` | NOT NULL, INDEX | — |
| `description` | `TEXT` | NOT NULL | — |
| `occurred_at` | `DATETIME` | NOT NULL | — |
| `resolved` | `BOOLEAN` | NOT NULL | `False` |
| `resolved_at` | `DATETIME` | nullable | — |
| `resolved_by` | `VARCHAR(36)` | FK → `users.id` SET NULL, nullable | — |
| `resolution_notes` | `TEXT` | nullable | — |
| `created_at` | `DATETIME` | NOT NULL | `utcnow()` |

**Violation type values:** `missing_punch` · `min_wage` · `max_hours` · `mandatory_break` · `ot_threshold`

**Indexes:** `ix_compliance_violations_employee_id`, `ix_compliance_violations_company_id`, `ix_compliance_violations_violation_type`

**Relationships:**
- `employee` → many-to-one → `User` (foreign_keys: employee_id)
- `resolver` → many-to-one → `User` nullable (foreign_keys: resolved_by)
- `company` → many-to-one → `Company`

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
| Sprint 3 | `leave_requests`, `leave_balances`, `shift_schedules`, `company_policies` — scheduling and leave management |
| Sprint 4 | `timesheets`, `payroll_line_items`, `payroll_exports` — payroll calculation, timesheets, and exports |
| Sprint 5 | `compliance_violations` — labor-rule compliance tracking, violation resolution, and reporting |
