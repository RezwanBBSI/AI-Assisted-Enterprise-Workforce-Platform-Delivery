# BBSI Workforce Platform — App Walkthrough

Visual tour of the platform. Start both servers with `./start.sh` from the project root, then open [http://localhost:5173](http://localhost:5173).

**Demo credentials:**

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@bbsi.demo | Admin1234! |
| Manager | manager@bbsi.demo | Manager1234! |
| Employee | employee@bbsi.demo | Employee1234! |

---

## 1. Login

![Login page](screenshots/01-login.png)

**Caption:** The login screen. Use one of the demo credentials above, or click a quick-fill button to auto-populate the form.

---

## 2. Dashboard (Employee)

![Dashboard — Employee](screenshots/02-dashboard-employee.png)

**Caption:** The employee dashboard shows leave balance cards (PTO / Sick / Comp), quick-action buttons, and a summary of recent activity.

---

## 3. Clock In / Out

![Clock In / Out](screenshots/03-clock-in-out.png)

**Caption:** Employees clock in and out here. The form captures location and notes; recent punches appear below.

---

## 4. Time Entries

![Time Entries](screenshots/04-time-entries.png)

**Caption:** A paginated list of all time entries. Employees can submit a correction request for any entry. Managers see the full team.

---

## 5. Timesheets (Employee)

![Timesheets — Employee](screenshots/05-timesheets-employee.png)

**Caption:** Timesheet lifecycle — draft → submitted → approved → exported. Employees submit; managers approve; payroll exports to CSV/JSON.

---

## 6. Leave Requests (Employee)

![Leave Requests — Employee](screenshots/06-leave-requests-employee.png)

**Caption:** Employees submit PTO, sick, or comp leave requests. Status badges show pending / approved / denied / cancelled. Remaining balances appear in the form header.

---

## 7. Schedules (Employee)

![Schedules — Employee](screenshots/07-schedules-employee.png)

**Caption:** The employee's upcoming shifts. Names are resolved — no raw UUIDs shown.

---

## 8. Dashboard (Manager)

![Dashboard — Manager](screenshots/08-dashboard-manager.png)

**Caption:** The manager's dashboard includes team-level stats alongside personal leave balances.

---

## 9. Schedules (Manager)

![Schedules — Manager](screenshots/09-schedules-manager.png)

**Caption:** Managers create and assign shifts. The shift form uses `shift_start` / `shift_end` datetime fields. All team members' shifts appear in the table.

---

## 10. Employees

![Employees](screenshots/10-employees.png)

**Caption:** Employee directory accessible to Managers and Admins. Shows name, email, role badge, and active/inactive status. Supports search filtering.

---

## 11. Compliance

![Compliance](screenshots/11-compliance.png)

**Caption:** Compliance dashboard listing violation records (meal break, overtime, missed punch, etc.) with severity and resolution status.

---

## 12. Reports — Operational

![Reports — Operational](screenshots/12-reports-operational.png)

**Caption:** The operational report summarises hours, overtime, and costs for a pay period. Filterable by date range.

---

## 13. Reports — Attendance Exceptions

![Reports — Attendance Exceptions](screenshots/13-reports-exceptions.png)

**Caption:** Attendance exceptions (late arrivals, no-shows) for the selected date range. Employee names are resolved — no UUIDs.

---

## 14. Reports — Crosscheck

![Reports — Crosscheck](screenshots/14-reports-crosscheck.png)

**Caption:** Crosscheck report flags discrepancies between time entries and scheduled shifts. Employee names resolved in results table.

---

## 15. Payroll Export

![Payroll Export](screenshots/15-payroll.png)

**Caption:** Admin/Manager-only payroll page. Approved timesheets appear in the "Ready to Export" section; one-click CSV or JSON export.

---

## 16. Admin Settings — Companies

![Admin Settings — Companies](screenshots/16-admin-settings.png)

**Caption:** Admin Settings panel — Companies tab. Shows all registered companies with IDs. Tabs: Companies / Locations / Policies.

---

## 17. Admin Settings — Locations

![Admin Settings — Locations](screenshots/17-admin-locations.png)

**Caption:** Locations tab. Lists all work sites with address, city, and state.

---

## 18. Admin Settings — Policies

![Admin Settings — Policies](screenshots/18-admin-policies.png)

**Caption:** Company policies tab. Key-value pairs that control business rules (overtime threshold, max shift hours, break requirements, etc.).

---

## 19. Audit Trail

![Audit Trail](screenshots/19-audit-trail.png)

**Caption:** Admin-only audit trail. Every create/update/delete action is logged with entity type, ID, actor, and timestamp. Filterable by entity type and date range; paginated 20 per page.

---

*Screenshots captured 2026-05-29 against live dev environment.*
