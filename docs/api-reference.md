# API Reference
# BBSI BuildAThon 2026 — Workforce Platform

> **Base URL (dev):** `http://localhost:8000/api/v1`
> **Swagger UI:** `http://localhost:8000/docs`
> **ReDoc:** `http://localhost:8000/redoc`
> **Last Updated:** Sprint 3 (2026-05-15)

---

## Authentication

All protected endpoints require a Bearer JWT in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens are issued by `POST /auth/login`. Default expiry: **60 minutes** (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` in `.env`).

| Symbol | Meaning |
|---|---|
| 🔓 | No authentication required |
| 🔒 | Valid JWT required (any active user) |
| 🔒 Admin | JWT + Admin role required |
| 🔒 Admin \| Manager | JWT + Admin or Manager role required |

---

## Health

### `GET /health` 🔓

Returns service liveness status.

**Response `200`:**
```json
{ "status": "ok", "service": "Workforce Platform API" }
```

---

## Auth Endpoints — `/api/v1/auth`

### `POST /auth/register` 🔓

Create a new user account.

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "plaintext_password",
  "full_name": "Jane Smith"
}
```

**Response `201`:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Jane Smith",
  "is_active": true,
  "created_at": "2026-05-14T19:00:00Z"
}
```

**Errors:**
| Code | Reason |
|---|---|
| `409` | Email already registered |
| `422` | Validation error (invalid email, missing field) |

---

### `POST /auth/login` 🔓

Authenticate and receive a JWT access token.

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "plaintext_password"
}
```

**Response `200`:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

**Errors:**
| Code | Reason |
|---|---|
| `401` | Invalid credentials or inactive account |

---

### `POST /auth/refresh` 🔒

Exchange a valid (non-expired) token for a fresh one.

**Request:** No body — token read from `Authorization` header.

**Response `200`:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

**Errors:**
| Code | Reason |
|---|---|
| `401` | Token expired, invalid, or user not found |

---

### `GET /auth/me` 🔒

Return the currently authenticated user's profile.

**Response `200`:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Jane Smith",
  "is_active": true,
  "created_at": "2026-05-14T19:00:00Z"
}
```

**Errors:**
| Code | Reason |
|---|---|
| `401` | Missing, expired, or invalid token |

---

## Companies — `/api/v1/companies`

### `GET /companies` 🔒 Admin

Paginated list of all companies.

**Query parameters:**
| Param | Type | Default | Notes |
|---|---|---|---|
| `page` | integer | `1` | Min: 1 |
| `size` | integer | `20` | Min: 1, Max: 100 |

**Response `200`:**
```json
{
  "total": 42,
  "page": 1,
  "size": 20,
  "items": [
    { "id": "uuid", "name": "BBSI Demo", "is_active": true, "created_at": "..." }
  ]
}
```

**Errors:**
| Code | Reason |
|---|---|
| `401` | Not authenticated |
| `403` | User does not have Admin role |

---

### `POST /companies` 🔒 Admin

Create a new company.

**Request body:**
```json
{ "name": "Acme Corp" }
```

**Response `201`:**
```json
{
  "id": "uuid",
  "name": "Acme Corp",
  "is_active": true,
  "created_at": "2026-05-14T19:00:00Z"
}
```

**Errors:**
| Code | Reason |
|---|---|
| `401` | Not authenticated |
| `403` | User does not have Admin role |

---

## Locations — `/api/v1/locations`

### `GET /locations` 🔒 Admin | Manager

Paginated list of locations, optionally filtered by company.

**Query parameters:**
| Param | Type | Default | Notes |
|---|---|---|---|
| `company_id` | string (UUID) | — | Optional filter |
| `page` | integer | `1` | Min: 1 |
| `size` | integer | `20` | Min: 1, Max: 100 |

**Response `200`:**
```json
{
  "total": 5,
  "page": 1,
  "size": 20,
  "items": [
    { "id": "uuid", "company_id": "uuid", "name": "HQ", "timezone": "America/New_York", "is_active": true }
  ]
}
```

---

### `POST /locations` 🔒 Admin | Manager

Create a new location under a company.

**Request body:**
```json
{
  "company_id": "uuid",
  "name": "Downtown Office",
  "address_line_1": "123 Main St",
  "city": "Chicago",
  "state": "IL",
  "zip_code": "60601",
  "country": "US",
  "timezone": "America/Chicago"
}
```

> All address fields are optional. `country` defaults to `"US"`. `timezone` defaults to `"UTC"`.

**Response `201`:**
```json
{
  "id": "uuid",
  "company_id": "uuid",
  "name": "Downtown Office",
  "timezone": "America/Chicago",
  "is_active": true
}
```

---

## Employees — `/api/v1/employees`

### `GET /employees` 🔒 Admin | Manager

Paginated list of all employees who have at least one company role. Optionally filter by company.

**Query parameters:**
| Param | Type | Default | Description |
|---|---|---|---|
| `company_id` | `string` | — | Filter employees belonging to this company |
| `page` | `integer` | `1` | Page number |
| `size` | `integer` | `20` | Page size (max 100) |

**Response `200`:**
```json
{
  "total": 3,
  "page": 1,
  "size": 20,
  "items": [
    {
      "id": "uuid",
      "email": "employee@bbsi.demo",
      "full_name": "Employee",
      "is_active": true,
      "created_at": "2026-05-14T00:00:00",
      "roles": [
        { "company_id": "uuid", "role_name": "Employee" }
      ]
    }
  ]
}
```

**Errors:**
| Code | Reason |
|---|---|
| `401` | Not authenticated |
| `403` | Authenticated user is not Manager or Admin |

---

### `GET /employees/{employee_id}` 🔒 Admin | Manager

Fetch a single employee by their UUID, including their assigned roles.

**Response `200`:**
```json
{
  "id": "uuid",
  "email": "admin@bbsi.demo",
  "full_name": "Admin",
  "is_active": true,
  "created_at": "2026-05-14T00:00:00",
  "roles": [
    { "company_id": "uuid", "role_name": "Admin" }
  ]
}
```

**Errors:**
| Code | Reason |
|---|---|
| `401` | Not authenticated |
| `403` | Authenticated user is not Manager or Admin |
| `404` | Employee not found |

---

## Time Entries — `/api/v1/time-entries`

### `POST /time-entries/clock-in` 🔒

Record a clock-in for the authenticated employee.

**Request body:**
```json
{
  "company_id": "uuid",
  "location_id": "uuid",
  "timestamp": "2026-05-15T09:00:00Z"
}
```
> `location_id` and `timestamp` are optional. If `timestamp` is omitted, server UTC now is used.

**Response `201`:**
```json
{
  "id": "uuid",
  "employee_id": "uuid",
  "company_id": "uuid",
  "location_id": "uuid",
  "clock_in": "2026-05-15T09:00:00",
  "clock_out": null,
  "status": "open",
  "break_minutes": null,
  "created_at": "2026-05-15T09:00:00"
}
```

**Errors:**
| Code | Reason |
|---|---|
| `401` | Not authenticated |
| `409` | Employee already has an open time entry |
| `422` | Timestamp is in the future |

---

### `POST /time-entries/clock-out` 🔒

Close the current open time entry for the authenticated employee.

**Request body:**
```json
{ "timestamp": "2026-05-15T17:30:00Z" }
```
> `timestamp` is optional; defaults to server UTC now.

**Response `200`:** `TimeEntryResponse` with `status: "closed"`

**Errors:**
| Code | Reason |
|---|---|
| `401` | Not authenticated |
| `404` | No open time entry found |
| `422` | Timestamp in the future, or before clock_in |

---

### `GET /time-entries` 🔒

Paginated list of time entries. Employees see only their own; Managers/Admins see all.

**Query parameters:**
| Param | Type | Notes |
|---|---|---|
| `employee_id` | string | Manager/Admin only filter |
| `company_id` | string | Optional filter |
| `status` | string | `open`, `closed`, or `corrected` |
| `page` | integer | Default `1` |
| `size` | integer | Default `20` |

**Response `200`:** Paginated `TimeEntryResponse` list.

---

### `GET /time-entries/{id}` 🔒

Fetch a single time entry. Employees may only retrieve their own entries.

**Errors:**
| Code | Reason |
|---|---|
| `403` | Employee requesting another user's entry |
| `404` | Entry not found |

---

### `POST /time-entries/{id}/correction` 🔒

Submit a correction request for a time entry (own entries only).

**Request body:**
```json
{
  "reason": "Forgot to clock in when I arrived",
  "new_clock_in": "2026-05-15T08:45:00Z",
  "new_clock_out": "2026-05-15T17:00:00Z"
}
```
> `new_clock_out` is optional.

**Response `201`:** `CorrectionResponse` with `status: "pending"`

**Errors:**
| Code | Reason |
|---|---|
| `403` | Attempting to correct another employee's entry |
| `404` | Entry not found |

---

### `PUT /time-entries/{id}/correction/{cid}` 🔒 Admin | Manager

Approve or deny a pending correction.

**Request body:**
```json
{ "approve": true }
```

**Response `200`:** `CorrectionResponse` with updated `status` and `reviewed_at`.

If approved, the parent `TimeEntry` is updated with the new times and its `status` becomes `"corrected"`.

**Errors:**
| Code | Reason |
|---|---|
| `403` | Employee role cannot review corrections |
| `404` | Correction or entry not found |
| `409` | Correction already reviewed |

---

## Attendance — `/api/v1/attendance`

### `GET /attendance` 🔒 Admin | Manager

Paginated list of daily attendance records.

**Query parameters:**
| Param | Type | Notes |
|---|---|---|
| `company_id` | string | Optional filter |
| `employee_id` | string | Optional filter |
| `page` | integer | Default `1` |
| `size` | integer | Default `20` |

**Response `200`:** Paginated `AttendanceResponse` list.

---

### `GET /attendance/missing-punches` 🔒 Admin | Manager

Return all open time entries with a `clock_in` older than 24 hours (employees who forgot to clock out).

**Query parameters:**
| Param | Type | Notes |
|---|---|---|
| `company_id` | string | Optional filter |

**Response `200`:** `list[TimeEntryResponse]`

---

## Common Error Responses

| Code | Meaning |
|---|---|
| `401 Unauthorized` | Missing, expired, or invalid JWT |
| `403 Forbidden` | Authenticated but insufficient role |
| `404 Not Found` | Resource does not exist |
| `409 Conflict` | Duplicate resource or already-reviewed correction |
| `422 Unprocessable Entity` | Request body failed validation or business rule (future timestamp, etc.) |

---

## Leave Requests — `/api/v1/leave-requests`

### `POST /leave-requests` 🔒

Submit a new leave request for the authenticated employee.

**Request body:**
```json
{
  "employee_id": "uuid",
  "company_id": "uuid",
  "leave_type": "pto",
  "start_date": "2026-06-01",
  "end_date": "2026-06-05",
  "days_requested": 5.0,
  "reason": "Family vacation"
}
```

> `leave_type` values: `pto`, `sick`, `comp`, `unpaid`. `reason` is optional. `unpaid` leave skips balance check.

**Response `201`:** `LeaveRequestResponse`

**Errors:**
| Code | Reason |
|---|---|
| `401` | Not authenticated |
| `422` | `end_date` before `start_date`, or `days_requested` exceeds available balance |

---

### `GET /leave-requests` 🔒

Paginated list of leave requests. Employees see only their own; Managers/Admins see all.

**Query parameters:**
| Param | Type | Notes |
|---|---|---|
| `company_id` | string | Optional filter |
| `status` | string | `pending`, `approved`, `denied`, `cancelled` |
| `employee_id` | string | Manager/Admin only filter |
| `page` | integer | Default `1` |
| `size` | integer | Default `20` |

**Response `200`:** Paginated `LeaveRequestResponse` list.

---

### `PUT /leave-requests/{request_id}/review` 🔒 Admin | Manager

Approve or deny a pending leave request. On approval, balance is decremented.

**Request body:**
```json
{ "approve": true, "comment": "Approved — enjoy the vacation!" }
```

**Response `200`:** `LeaveRequestResponse` with updated `status`, `reviewed_at`, and `review_comment`.

**Errors:**
| Code | Reason |
|---|---|
| `403` | Employee role cannot review |
| `404` | Request not found |
| `409` | Request already reviewed |

---

### `PUT /leave-requests/{request_id}/cancel` 🔒

Cancel a pending leave request. Employees may only cancel their own.

**Response `200`:** `LeaveRequestResponse` with `status: "cancelled"`.

**Errors:**
| Code | Reason |
|---|---|
| `403` | Attempting to cancel another employee's request |
| `409` | Request already reviewed (approved/denied); cannot cancel |

---

## Leave Balances — `/api/v1/leave-balances`

### `GET /leave-balances/{employee_id}` 🔒

Get leave balance for a specific employee. Employees may only retrieve their own; Managers/Admins may retrieve any.

**Query parameters:**
| Param | Type | Notes |
|---|---|---|
| `company_id` | string | **Required** |
| `year` | integer | Optional; defaults to current year |

**Response `200`:**
```json
{
  "id": "uuid",
  "employee_id": "uuid",
  "company_id": "uuid",
  "year": 2026,
  "pto_total": 10.0,
  "pto_used": 0.0,
  "sick_total": 5.0,
  "sick_used": 0.0,
  "comp_earned": 5.0,
  "comp_used": 0.0,
  "updated_at": "2026-05-15T00:00:00"
}
```

> If no balance row exists, a zeroed row is auto-created and returned.

**Errors:**
| Code | Reason |
|---|---|
| `403` | Employee requesting another employee's balance |

---

## Schedules — `/api/v1/schedules`

### `POST /schedules` 🔒 Admin | Manager

Create a shift assignment for an employee.

**Request body:**
```json
{
  "employee_id": "uuid",
  "company_id": "uuid",
  "location_id": "uuid",
  "shift_date": "2026-06-02",
  "shift_start": "09:00:00",
  "shift_end": "17:00:00",
  "break_minutes": 60
}
```

> `location_id` is optional. `shift_start`/`shift_end` are `HH:MM:SS` time strings.

**Response `201`:** `ShiftResponse`

**Break enforcement (422 if violated):**
| Shift Duration | Minimum Break |
|---|---|
| ≤ 6 hours | 0 minutes |
| > 6 hours and ≤ 8 hours | 30 minutes |
| > 8 hours | 60 minutes |

**Errors:**
| Code | Reason |
|---|---|
| `401` | Not authenticated |
| `403` | Employee role cannot create shifts |
| `422` | Break minimum not met |

---

### `GET /schedules` 🔒

Paginated list of shifts. Employees see only their own; Managers/Admins see all.

**Query parameters:**
| Param | Type | Notes |
|---|---|---|
| `company_id` | string | Optional filter |
| `employee_id` | string | Manager/Admin only filter |
| `date_from` | date | Optional lower bound (ISO date) |
| `date_to` | date | Optional upper bound (ISO date) |
| `page` | integer | Default `1` |
| `size` | integer | Default `20` |

**Response `200`:** Paginated `ShiftResponse` list.

---

### `PUT /schedules/{shift_id}` 🔒 Admin | Manager

Update an existing shift.

**Request body (all fields optional):**
```json
{ "shift_start": "08:00:00", "shift_end": "16:00:00", "break_minutes": 30 }
```

> Break enforcement applies to updated values. 422 returned if result violates rules.

**Response `200`:** Updated `ShiftResponse`.

**Errors:**
| Code | Reason |
|---|---|
| `404` | Shift not found |
| `422` | Updated break value below minimum |

---

### `DELETE /schedules/{shift_id}` 🔒 Admin | Manager

Permanently delete a shift.

**Response `204`:** No content.

**Errors:**
| Code | Reason |
|---|---|
| `404` | Shift not found |

---

## Policies — `/api/v1/policies`

### `GET /policies` 🔒 Admin | Manager

List all policies for a company.

**Query parameters:**
| Param | Type | Notes |
|---|---|---|
| `company_id` | string | **Required** |

**Response `200`:** `list[PolicyResponse]`
```json
[
  { "id": "uuid", "company_id": "uuid", "policy_key": "core_hours_start", "policy_value": "09:00", "updated_at": "..." },
  { "id": "uuid", "company_id": "uuid", "policy_key": "overtime_threshold", "policy_value": "40", "updated_at": "..." }
]
```

---

### `PUT /policies/{policy_key}` 🔒 Admin

Create or update a policy value (upsert).

**Query parameters:**
| Param | Type | Notes |
|---|---|---|
| `company_id` | string | **Required** |

**Request body:**
```json
{ "policy_value": "09:00" }
```

**Response `200`:** `PolicyResponse` with the updated or newly created policy.

**Errors:**
| Code | Reason |
|---|---|
| `403` | Manager role cannot write policies; Admin only |

---

## Common Error Responses

| Code | Meaning |
|---|---|
| `401 Unauthorized` | Missing, expired, or invalid JWT |
| `403 Forbidden` | Authenticated but insufficient role |
| `404 Not Found` | Resource does not exist |
| `409 Conflict` | Duplicate resource or already-reviewed request |
| `422 Unprocessable Entity` | Request body failed validation or business rule (break minimum, over-balance, etc.) |

---

## Upcoming Endpoints (Sprint 4+)

| Sprint | Endpoints |
|---|---|
| Sprint 4 | Timesheets, payroll line items, payroll exports, overtime calculations |
| Sprint 5 | Compliance violations, audit trail reports, operational reports |

> This file is updated at the end of each sprint. See `docs/roadmap.md` for full sprint specs.
