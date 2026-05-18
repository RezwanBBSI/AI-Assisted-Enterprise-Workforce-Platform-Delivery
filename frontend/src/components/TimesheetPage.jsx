import { useState } from "react";
import { PayPeriodSummaryCard } from "./PayPeriodSummaryCard";

const API_BASE = "http://localhost:8000/api/v1";

const RATE_TYPE_LABELS = {
  regular: "Regular",
  overtime: "Overtime",
  double_time: "Double-time",
  holiday: "Holiday",
  night_differential: "Night Diff.",
  pto: "PTO",
  sick: "Sick",
  comp: "Comp",
};

/**
 * TimesheetPage — displays line items for a timesheet and allows the employee
 * to submit it for approval.
 *
 * Props:
 *   timesheetId  (string)  — UUID of the timesheet to display
 *   token        (string)  — Bearer token for the current user
 *   isEmployee   (boolean) — show the Submit button only for employees
 */
export default function TimesheetPage({ timesheetId, token, isEmployee }) {
  const [timesheet, setTimesheet] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [submitStatus, setSubmitStatus] = useState(null);

  async function fetchTimesheet() {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${API_BASE}/timesheets/${timesheetId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
      setTimesheet(await resp.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit() {
    setSubmitStatus(null);
    try {
      const resp = await fetch(`${API_BASE}/timesheets/${timesheetId}/submit`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) {
        const body = await resp.json();
        throw new Error(body.detail || resp.statusText);
      }
      const updated = await resp.json();
      setTimesheet(updated);
      setSubmitStatus("Timesheet submitted for approval.");
    } catch (err) {
      setSubmitStatus(`Error: ${err.message}`);
    }
  }

  return (
    <div className="timesheet-page">
      <h2>Timesheet</h2>

      {!timesheet && (
        <button onClick={fetchTimesheet} disabled={loading}>
          {loading ? "Loading…" : "Load Timesheet"}
        </button>
      )}

      {error && <p className="error">{error}</p>}

      {timesheet && (
        <>
          <PayPeriodSummaryCard timesheet={timesheet} />

          <h4>Line Items</h4>
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Hours</th>
                <th>Multiplier</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {timesheet.line_items.map((item) => (
                <tr key={item.id}>
                  <td>{item.entry_date}</td>
                  <td>{RATE_TYPE_LABELS[item.rate_type] ?? item.rate_type}</td>
                  <td>{item.hours_worked.toFixed(2)}</td>
                  <td>{item.rate_multiplier}×</td>
                  <td>{item.notes ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {isEmployee && timesheet.status === "draft" && (
            <button onClick={handleSubmit}>Submit for Approval</button>
          )}
          {submitStatus && <p>{submitStatus}</p>}
        </>
      )}
    </div>
  );
}
