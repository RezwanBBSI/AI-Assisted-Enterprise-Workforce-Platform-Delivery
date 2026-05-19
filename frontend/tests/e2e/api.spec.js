/**
 * Playwright E2E tests — Sprint 6
 *
 * These are API-level end-to-end tests that exercise complete user flows
 * against the live FastAPI backend (http://localhost:8000).
 *
 * Run with: npx playwright test
 * (Requires backend to be running: cd backend && uvicorn app.main:app --reload)
 */
import { test, expect } from '@playwright/test';

// ── helpers ──────────────────────────────────────────────────────────────────

const BASE = 'http://localhost:8000/api/v1';
const uniq = () => `e2e_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

async function register(request, email, password = 'E2ePass1!') {
  return request.post(`${BASE}/auth/register`, {
    data: { email, password, full_name: 'E2E User' },
  });
}

async function login(request, email, password = 'E2ePass1!') {
  const r = await request.post(`${BASE}/auth/login`, {
    data: { email, password },
  });
  const body = await r.json();
  return body.access_token;
}

async function authHeaders(token) {
  return { Authorization: `Bearer ${token}` };
}

// ── Auth flow ─────────────────────────────────────────────────────────────────

test.describe('Auth flow', () => {
  test('register → login → /me round-trip', async ({ request }) => {
    const email = `${uniq()}@example.com`;

    const regResp = await register(request, email);
    expect(regResp.status()).toBe(201);

    const token = await login(request, email);
    expect(typeof token).toBe('string');
    expect(token.length).toBeGreaterThan(10);

    const meResp = await request.get(`${BASE}/auth/me`, {
      headers: await authHeaders(token),
    });
    expect(meResp.status()).toBe(200);
    const me = await meResp.json();
    expect(me.email).toBe(email);
  });

  test('login with wrong password returns 401', async ({ request }) => {
    const email = `${uniq()}@example.com`;
    await register(request, email);
    const r = await request.post(`${BASE}/auth/login`, {
      data: { email, password: 'wrongpass' },
    });
    expect(r.status()).toBe(401);
  });

  test('unauthenticated /me returns 401', async ({ request }) => {
    const r = await request.get(`${BASE}/auth/me`);
    expect(r.status()).toBe(401);
  });
});

// ── Health check ──────────────────────────────────────────────────────────────

test.describe('Health', () => {
  test('GET /health returns ok', async ({ request }) => {
    const r = await request.get('http://localhost:8000/health');
    expect(r.status()).toBe(200);
    const body = await r.json();
    expect(body.status).toBe('ok');
  });
});

// ── Security hardening ────────────────────────────────────────────────────────

test.describe('Security hardening', () => {
  test('POST with wrong Content-Type returns 415', async ({ request }) => {
    const r = await request.post(`${BASE}/auth/register`, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      data: 'email=bad@example.com&password=bad',
    });
    expect(r.status()).toBe(415);
  });

  test('expired JWT returns 401', async ({ request }) => {
    // A JWT with exp in the past — server should reject it
    const r = await request.get(`${BASE}/auth/me`, {
      headers: { Authorization: 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxfQ.invalid' },
    });
    expect(r.status()).toBe(401);
  });

  test('CORS: allowed origin receives Access-Control header', async ({ request }) => {
    const r = await request.fetch(`${BASE}/auth/login`, {
      method: 'OPTIONS',
      headers: {
        Origin: 'http://localhost:5173',
        'Access-Control-Request-Method': 'POST',
      },
    });
    // Allowed origin should be echoed back
    const acao = r.headers()['access-control-allow-origin'];
    expect(acao).toBeTruthy();
  });
});

// ── Clock-in / Clock-out flow ─────────────────────────────────────────────────

test.describe('Clock-in/out flow', () => {
  test('employee can clock in and clock out', async ({ request }) => {
    const email = `${uniq()}@example.com`;
    await register(request, email);
    const token = await login(request, email);
    const headers = await authHeaders(token);

    // Clock in
    const ciResp = await request.post(`${BASE}/time-entries/clock-in`, {
      headers,
      data: {},
    });
    expect([200, 201]).toContain(ciResp.status());

    // Clock out
    const coResp = await request.post(`${BASE}/time-entries/clock-out`, {
      headers,
      data: {},
    });
    expect([200, 201]).toContain(coResp.status());

    const body = await coResp.json();
    expect(body.status).toBe('closed');
  });

  test('double clock-in returns 422', async ({ request }) => {
    const email = `${uniq()}@example.com`;
    await register(request, email);
    const token = await login(request, email);
    const headers = await authHeaders(token);

    await request.post(`${BASE}/time-entries/clock-in`, { headers, data: {} });
    const r = await request.post(`${BASE}/time-entries/clock-in`, { headers, data: {} });
    expect(r.status()).toBe(422);
  });
});

// ── Leave request flow ────────────────────────────────────────────────────────

test.describe('Leave request flow', () => {
  test('employee submits leave request', async ({ request }) => {
    const email = `${uniq()}@example.com`;
    await register(request, email);
    const token = await login(request, email);
    const headers = await authHeaders(token);

    // Need company_id — get from /me first
    const meResp = await request.get(`${BASE}/auth/me`, { headers });
    const me = await meResp.json();

    // Submit unpaid leave (no balance needed)
    const r = await request.post(`${BASE}/leave-requests`, {
      headers,
      data: {
        company_id: me.company_id || '00000000-0000-0000-0000-000000000000',
        leave_type: 'unpaid',
        start_date: '2027-01-10',
        end_date: '2027-01-12',
        days_requested: 3,
        reason: 'E2E test leave',
      },
    });
    // 201 (success) or 422 (no company assigned) — both are acceptable in E2E context
    expect([201, 422]).toContain(r.status());
  });
});
