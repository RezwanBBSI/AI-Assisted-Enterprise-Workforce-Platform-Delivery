# Incident Triage Example
# BBSI Workforce Platform

> **Scenario:** Employee double clock-in — duplicate punch rejected, traced end-to-end through structured logs.

---

## 1. How the Incident Was Triggered

**Script:** `backend/scripts/simulate_incident.py`

```bash
cd backend
source venv/bin/activate
python scripts/simulate_incident.py
```

The script:
1. Logs in as `employee@bbsi.demo`
2. Issues a valid `POST /api/v1/time-entries/clock-in` → **201 Created**
3. Immediately issues a second `POST /api/v1/time-entries/clock-in` → **409 Conflict**

---

## 2. Observed Log Output

Every request produces a single structured JSON line on the backend's stdout:

**Request 1 — Successful clock-in (201):**
```json
{"timestamp": "2026-05-19T18:42:11Z", "level": "INFO", "request_id": "a3f7c291-1b2e-4d5a-9f0e-cc8821abcd12", "user_id": null, "method": "POST", "path": "/api/v1/time-entries/clock-in", "status": 201, "duration_ms": 34.2}
```

**Request 2 — Duplicate clock-in (409 Conflict):**
```json
{"timestamp": "2026-05-19T18:42:12Z", "level": "WARNING", "request_id": "b9d14e73-3c4a-4f8b-a2d1-ff9934bcde56", "user_id": null, "method": "POST", "path": "/api/v1/time-entries/clock-in", "status": 409, "duration_ms": 18.7}
```

The `X-Request-ID` response header carries the same UUID as `"request_id"` in the log, enabling cross-referencing between client-side error reports and server-side logs.

---

## 3. Log Fields Reference

| Field | Type | Description |
|---|---|---|
| `timestamp` | ISO 8601 UTC | When the request completed |
| `level` | `INFO` / `WARNING` / `ERROR` | `INFO` for 2xx, `WARNING` for 4xx, `ERROR` for 5xx |
| `request_id` | UUID v4 | Unique per request; returned as `X-Request-ID` header |
| `user_id` | UUID or `null` | Populated when JWT decoded on the route |
| `method` | string | HTTP method |
| `path` | string | Request path |
| `status` | int | HTTP status code |
| `duration_ms` | float | Total request processing time in milliseconds |
| `error` | string | Present only on 5xx responses; contains detail or stack trace |

---

## 4. Root-Cause Analysis

| Step | Finding |
|---|---|
| **What happened?** | Employee submitted a clock-in while already clocked in |
| **Where did it fail?** | `PunchValidationService.validate_clock_in()` → raises `PunchError(409, "Already clocked in")` |
| **Log evidence** | `"status": 409` on second request; `"request_id"` matches `X-Request-ID` header |
| **Data integrity** | No duplicate `TimeEntry` was created; the first open entry remains untouched |
| **AuditLog** | No audit record written for rejected requests (only successful actions are audited) |

**Code path:**
```
POST /api/v1/time-entries/clock-in
  → TimeEntryService.clock_in()
    → PunchValidationService.validate_clock_in(db, employee_id, clock_in_time)
      → SELECT time_entries WHERE employee_id=? AND status='open'
      → Found existing open entry → raise PunchError(status_code=409, message="Already clocked in")
  → FastAPI exception handler returns {"detail": "Already clocked in"} with HTTP 409
  → RequestIDLoggingMiddleware logs WARNING line with request_id
```

---

## 5. Remediation Steps

1. **Immediate:** No action required — the system correctly rejected the duplicate and no bad data was created.
2. **Employee UX:** The frontend `ClockInOutPage` already reflects the open-entry state and hides the **Clock In** button when already clocked in. This prevents the user from triggering a 409 in normal usage.
3. **Monitoring:** Alert on `"status": 409` + `"path"` containing `/clock-in` if volume exceeds threshold (suggests API misuse or a client-side bug not checking state before sending requests).
4. **Audit trail:** Managers can verify no ghost entries were created by checking `GET /api/v1/attendance?company_id=<id>` or running `GET /api/v1/reports/crosscheck`.

---

## 6. BugBot Walkthrough

> *This section shows how an AI-assisted debugging workflow would approach this incident.*

**Step 1 — Identify the request_id from the client error:**
The frontend captures `X-Request-ID: b9d14e73-3c4a-4f8b-a2d1-ff9934bcde56` from the response headers and displays it in the error toast.

**Step 2 — Search logs by request_id:**
```bash
grep "b9d14e73" backend.log
# → {"timestamp": "2026-05-19T18:42:12Z", "level": "WARNING", ..., "status": 409, ...}
```

**Step 3 — Confirm no data corruption:**
```bash
# Check for duplicate open entries for the employee
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "http://localhost:8000/api/v1/time-entries?page=1&size=5"
# → Only one open entry for the employee
```

**Step 4 — Root cause confirmed:** `PunchValidationService` correctly guards against duplicates. Incident closed — no remediation needed.

---

## 7. Simulating a 5XX Error

To produce an `ERROR` level log with stack trace enrichment, you can temporarily introduce a fault. The middleware will capture the traceback and emit:

```json
{
  "timestamp": "2026-05-19T18:55:00Z",
  "level": "ERROR",
  "request_id": "f2a09c11-...",
  "user_id": null,
  "method": "POST",
  "path": "/api/v1/time-entries/clock-in",
  "status": 500,
  "duration_ms": 5.1,
  "error": "Traceback (most recent call last):\n  ..."
}
```

The `request_id` in this log line matches the `X-Request-ID` header returned to the client, enabling precise cross-referencing.
