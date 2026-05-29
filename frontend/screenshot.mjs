/**
 * Screenshot script — captures every page of the BBSI Workforce Platform.
 * Usage: node screenshot.mjs
 * Output: ../walkthrough/screenshots/
 */
import { chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT_DIR = path.join(__dirname, '..', 'walkthrough', 'screenshots');
fs.mkdirSync(OUT_DIR, { recursive: true });

const BASE = 'http://localhost:5173';
const ADMIN    = { email: 'admin@bbsi.demo',    password: 'Admin1234!' };
const MANAGER  = { email: 'manager@bbsi.demo',  password: 'Manager1234!' };
const EMPLOYEE = { email: 'employee@bbsi.demo', password: 'Employee1234!' };

async function login(page, creds) {
  await page.goto(`${BASE}/login`);
  await page.waitForSelector('input[type="email"]');
  await page.fill('input[type="email"]', creds.email);
  await page.fill('input[type="password"]', creds.password);
  await page.click('button[type="submit"]');
  await page.waitForURL(url => !url.toString().includes('/login'), { timeout: 8000 });
  await page.waitForTimeout(600);
}

async function shot(page, name, description) {
  await page.waitForTimeout(500); // let data load
  const file = path.join(OUT_DIR, `${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  console.log(`  ✓ ${name}.png  — ${description}`);
  return { name, description, file: `screenshots/${name}.png` };
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const shots = [];

  // ── 1. Login page ────────────────────────────────────────────────────────
  console.log('\n📸 Login page');
  await page.goto(`${BASE}/login`);
  await page.waitForSelector('input[type="email"]');
  shots.push(await shot(page, '01-login', 'Login page — credential form with demo quick-fill buttons'));

  // ── Sign in as Employee ───────────────────────────────────────────────────
  console.log('\n📸 Employee views');
  await login(page, EMPLOYEE);

  await page.goto(`${BASE}/`);
  await page.waitForTimeout(1000);
  shots.push(await shot(page, '02-dashboard-employee', 'Dashboard — leave balance cards, quick stats (Employee view)'));

  await page.goto(`${BASE}/clock`);
  await page.waitForTimeout(800);
  shots.push(await shot(page, '03-clock-in-out', 'Clock In / Out — punch form and recent time entries'));

  await page.goto(`${BASE}/time-entries`);
  await page.waitForTimeout(800);
  shots.push(await shot(page, '04-time-entries', 'Time Entries — list with correction request capability'));

  await page.goto(`${BASE}/timesheets`);
  await page.waitForTimeout(800);
  shots.push(await shot(page, '05-timesheets-employee', 'Timesheets — pay periods, hours summary, submit/approve lifecycle'));

  await page.goto(`${BASE}/leave`);
  await page.waitForTimeout(800);
  shots.push(await shot(page, '06-leave-requests-employee', 'Leave Requests — submit requests, view status badges'));

  await page.goto(`${BASE}/schedules`);
  await page.waitForTimeout(800);
  shots.push(await shot(page, '07-schedules-employee', 'Schedules — upcoming shifts with employee names'));

  // ── Sign in as Manager ────────────────────────────────────────────────────
  console.log('\n📸 Manager views');
  await login(page, MANAGER);

  await page.goto(`${BASE}/`);
  await page.waitForTimeout(1000);
  shots.push(await shot(page, '08-dashboard-manager', 'Dashboard — Manager view with team overview'));

  await page.goto(`${BASE}/schedules`);
  await page.waitForTimeout(800);
  shots.push(await shot(page, '09-schedules-manager', 'Schedules — Manager can create and manage team shifts'));

  await page.goto(`${BASE}/employees`);
  await page.waitForTimeout(800);
  shots.push(await shot(page, '10-employees', 'Employees — directory with roles and active status'));

  await page.goto(`${BASE}/compliance`);
  await page.waitForTimeout(800);
  shots.push(await shot(page, '11-compliance', 'Compliance — violation tracking dashboard'));

  await page.goto(`${BASE}/reports`);
  await page.waitForTimeout(1000);
  shots.push(await shot(page, '12-reports-operational', 'Reports — Operational report tab'));

  // Click Attendance Exceptions tab
  await page.click('button:has-text("Attendance")').catch(() => {});
  await page.waitForTimeout(400);
  shots.push(await shot(page, '13-reports-exceptions', 'Reports — Attendance Exceptions tab'));

  // Click Crosscheck tab
  await page.click('button:has-text("Crosscheck")').catch(() => {});
  await page.waitForTimeout(400);
  shots.push(await shot(page, '14-reports-crosscheck', 'Reports — Crosscheck tab'));

  // ── Sign in as Admin ──────────────────────────────────────────────────────
  console.log('\n📸 Admin views');
  await login(page, ADMIN);

  await page.goto(`${BASE}/payroll`);
  await page.waitForTimeout(800);
  shots.push(await shot(page, '15-payroll', 'Payroll Export — approve timesheets and export to CSV/JSON'));

  await page.goto(`${BASE}/admin`);
  await page.waitForTimeout(800);
  shots.push(await shot(page, '16-admin-settings', 'Admin Settings — companies, locations, policies tabs'));

  // Click Locations tab
  await page.click('button:has-text("Locations")').catch(() => {});
  await page.waitForTimeout(400);
  shots.push(await shot(page, '17-admin-locations', 'Admin Settings — Locations tab'));

  // Click Policies tab
  await page.click('button:has-text("Policies")').catch(() => {});
  await page.waitForTimeout(400);
  shots.push(await shot(page, '18-admin-policies', 'Admin Settings — Policies tab'));

  // Audit trail in Reports
  await page.goto(`${BASE}/reports`);
  await page.waitForTimeout(600);
  await page.click('button:has-text("Audit")').catch(() => {});
  await page.waitForTimeout(800);
  shots.push(await shot(page, '19-audit-trail', 'Reports — Audit Trail (Admin only) with filters and pagination'));

  await browser.close();

  // ── Write captions index ─────────────────────────────────────────────────
  const indexPath = path.join(OUT_DIR, '..', 'screenshots-index.md');
  const rows = shots.map(s =>
    `| ![${s.description}](${s.file}) | **${s.name.replace(/^\d+-/, '').replace(/-/g, ' ')}** — ${s.description} |`
  ).join('\n');

  fs.writeFileSync(indexPath, `# BBSI Workforce Platform — Screenshot Index\n\n` +
    `| Screenshot | Caption |\n|---|---|\n${rows}\n`);

  console.log(`\n✅ ${shots.length} screenshots saved to walkthrough/screenshots/`);
  console.log(`📄 Index written to walkthrough/screenshots-index.md`);
})();
