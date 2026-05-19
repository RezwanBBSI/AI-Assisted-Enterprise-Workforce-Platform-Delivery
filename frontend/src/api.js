/**
 * Centralized API client.
 * All requests go through /api/v1 (proxied to localhost:8000 by Vite dev server).
 */

const BASE = '/api/v1';

function authHeaders(token) {
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function request(method, path, body, token) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: authHeaders(token),
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const json = await res.json();
      detail = json.detail || detail;
    } catch (_) {}
    throw new Error(detail);
  }

  // 204 No Content
  if (res.status === 204) return null;
  return res.json();
}

// ── Auth ─────────────────────────────────────────────────────────────────────
export const login = (email, password) =>
  request('POST', '/auth/login', { email, password });

export const register = (email, password, fullName) =>
  request('POST', '/auth/register', { email, password, full_name: fullName });

export const getMe = (token) => request('GET', '/auth/me', undefined, token);

// ── Employees ────────────────────────────────────────────────────────────────
export const getEmployees = (token, companyId, page = 1, size = 50) =>
  request('GET', `/employees?company_id=${companyId}&page=${page}&size=${size}`, undefined, token);

// ── Time Entries ─────────────────────────────────────────────────────────────
export const clockIn = (token, companyId, locationId) =>
  request('POST', '/time-entries/clock-in', { company_id: companyId, location_id: locationId }, token);

export const clockOut = (token) =>
  request('POST', '/time-entries/clock-out', {}, token);

export const getTimeEntries = (token, page = 1, size = 20) =>
  request('GET', `/time-entries?page=${page}&size=${size}`, undefined, token);

export const submitCorrection = (token, entryId, payload) =>
  request('POST', `/time-entries/${entryId}/correction`, payload, token);

// ── Attendance ────────────────────────────────────────────────────────────────
export const getAttendance = (token, companyId, page = 1, size = 20) =>
  request('GET', `/attendance?company_id=${companyId}&page=${page}&size=${size}`, undefined, token);

export const getMissingPunches = (token, companyId) =>
  request('GET', `/attendance/missing-punches?company_id=${companyId}`, undefined, token);

// ── Schedules ─────────────────────────────────────────────────────────────────
export const getSchedules = (token, companyId, page = 1, size = 20) =>
  request('GET', `/schedules?company_id=${companyId}&page=${page}&size=${size}`, undefined, token);

export const createSchedule = (token, payload) =>
  request('POST', '/schedules', payload, token);

export const deleteSchedule = (token, id) =>
  request('DELETE', `/schedules/${id}`, undefined, token);

// ── Leave Requests ─────────────────────────────────────────────────────────────
export const getLeaveRequests = (token, page = 1, size = 20) =>
  request('GET', `/leave-requests?page=${page}&size=${size}`, undefined, token);

export const submitLeaveRequest = (token, payload) =>
  request('POST', '/leave-requests', payload, token);

export const reviewLeaveRequest = (token, id, status, comment) =>
  request('PUT', `/leave-requests/${id}/review`, { status, comment }, token);

export const cancelLeaveRequest = (token, id) =>
  request('PUT', `/leave-requests/${id}/cancel`, {}, token);

// ── Leave Balances ─────────────────────────────────────────────────────────────
export const getLeaveBalance = (token, employeeId, companyId) =>
  request('GET', `/leave-balances/${employeeId}?company_id=${companyId}`, undefined, token);

// ── Timesheets ─────────────────────────────────────────────────────────────────
export const getTimesheets = (token, page = 1, size = 20) =>
  request('GET', `/timesheets?page=${page}&size=${size}`, undefined, token);

export const generateTimesheet = (token, companyId, employeeId, start, end) =>
  request('POST', '/timesheets/generate', {
    company_id: companyId,
    employee_id: employeeId,
    pay_period_start: start,
    pay_period_end: end,
  }, token);

export const submitTimesheet = (token, id) =>
  request('PUT', `/timesheets/${id}/submit`, {}, token);

export const approveTimesheet = (token, id) =>
  request('PUT', `/timesheets/${id}/approve`, {}, token);

export const exportTimesheet = (token, id, format = 'csv') =>
  request('POST', `/timesheets/${id}/export`, { format }, token);

// ── Compliance ─────────────────────────────────────────────────────────────────
export const runCompliance = (token, companyId, start, end) =>
  request('POST', '/compliance/validate', {
    company_id: companyId,
    pay_period_start: start,
    pay_period_end: end,
  }, token);

export const getViolations = (token, companyId, page = 1, size = 20) =>
  request('GET', `/compliance/violations?company_id=${companyId}&page=${page}&size=${size}`, undefined, token);

export const resolveViolation = (token, id, notes) =>
  request('PUT', `/compliance/violations/${id}`, { resolution_notes: notes }, token);

// ── Reports ───────────────────────────────────────────────────────────────────
export const getComplianceReport = (token, companyId, start, end) =>
  request('GET', `/reports/compliance?company_id=${companyId}&pay_period_start=${start}&pay_period_end=${end}`, undefined, token);

export const getOperationalReport = (token, companyId, start, end) =>
  request('GET', `/reports/operational?company_id=${companyId}&pay_period_start=${start}&pay_period_end=${end}`, undefined, token);

export const getAuditTrail = (token, page = 1, size = 20) =>
  request('GET', `/reports/audit-trail?page=${page}&size=${size}`, undefined, token);

export const getAttendanceExceptions = (token, companyId, start, end, page = 1, size = 20) =>
  request('GET', `/reports/attendance-exceptions?company_id=${companyId}&pay_period_start=${start}&pay_period_end=${end}&page=${page}&size=${size}`, undefined, token);

export const getCrosscheck = (token, companyId, start, end) =>
  request('GET', `/reports/crosscheck?company_id=${companyId}&pay_period_start=${start}&pay_period_end=${end}`, undefined, token);

// ── Companies / Locations ─────────────────────────────────────────────────────
export const getCompanies = (token, page = 1, size = 50) =>
  request('GET', `/companies?page=${page}&size=${size}`, undefined, token);

export const getLocations = (token, companyId, page = 1, size = 50) =>
  request('GET', `/locations?company_id=${companyId}&page=${page}&size=${size}`, undefined, token);

// ── Policies ──────────────────────────────────────────────────────────────────
export const getPolicies = (token, companyId) =>
  request('GET', `/policies?company_id=${companyId}`, undefined, token);
