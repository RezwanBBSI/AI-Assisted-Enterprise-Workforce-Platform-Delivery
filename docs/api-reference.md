# API Reference
# BBSI BuildAThon 2026 — Workforce Platform

> **Base URL (dev):** `http://localhost:8000/api/v1`
> **Swagger UI:** `http://localhost:8000/docs`
> **ReDoc:** `http://localhost:8000/redoc`
> **Last Updated:** Sprint 1 (2026-05-14)

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
  "timezone": "America/Chicago"
}
```

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

## Common Error Responses

| Code | Meaning |
|---|---|
| `401 Unauthorized` | Missing, expired, or invalid JWT |
| `403 Forbidden` | Authenticated but insufficient role |
| `404 Not Found` | Resource does not exist |
| `409 Conflict` | Duplicate resource (e.g., email already taken) |
| `422 Unprocessable Entity` | Request body failed validation |

---

## Upcoming Endpoints (Sprint 2+)

| Sprint | Endpoints |
|---|---|
| Sprint 2 | `POST /time-entries/clock-in`, `POST /time-entries/clock-out`, `GET /time-entries`, correction workflow, attendance |
| Sprint 3 | Shifts, schedules, leave requests, leave balances |
| Sprint 4 | Pay periods, payroll records, overtime calculations |
| Sprint 5 | Compliance reports, audit logs, export |

> This file is updated at the end of each sprint. See `docs/roadmap.md` for full sprint specs.
