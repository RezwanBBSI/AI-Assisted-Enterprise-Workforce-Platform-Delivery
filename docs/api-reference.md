# API Reference
# BBSI BuildAThon 2026 — Workforce Platform

> **Base URL (dev):** `http://localhost:8000/api/v1`
> **Swagger UI:** `http://localhost:8000/docs`
> **ReDoc:** `http://localhost:8000/redoc`
> **Last Updated:** Sprint 2 (2026-05-15)

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

## Upcoming Endpoints (Sprint 3+)

| Sprint | Endpoints |
|---|---|
| Sprint 3 | Shifts, schedules, leave requests, leave balances |
| Sprint 4 | Pay periods, payroll records, overtime calculations |
| Sprint 5 | Compliance reports, export |

> This file is updated at the end of each sprint. See `docs/roadmap.md` for full sprint specs.
