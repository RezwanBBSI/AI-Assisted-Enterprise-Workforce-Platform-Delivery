import { useState } from "react";

const API_BASE = "http://localhost:8000/api/v1";

/**
 * PayPeriodSummaryCard — shows aggregated hours from a timesheet.
 * Props: timesheet (object from GET /timesheets/{id})
 */
export function PayPeriodSummaryCard({ timesheet }) {
  if (!timesheet) return null;

  const rows = [
    { label: "Regular", hours: timesheet.total_regular_hrs, multiplier: "1.0×" },
    { label: "Overtime / Double-time", hours: timesheet.total_ot_hrs, multiplier: "1.5× / 2.0×" },
    { label: "Holiday", hours: timesheet.total_holiday_hrs, multiplier: "2.0×" },
    { label: "Night Differential", hours: timesheet.total_differential_hrs, multiplier: "1.25×" },
  ];

  const totalHours =
    timesheet.total_regular_hrs +
    timesheet.total_ot_hrs +
    timesheet.total_holiday_hrs +
    timesheet.total_differential_hrs;

  return (
    <div className="summary-card">
      <h3>
        Pay Period: {timesheet.pay_period_start} → {timesheet.pay_period_end}
      </h3>
      <p>
        Status: <strong>{timesheet.status}</strong>
      </p>
      <table>
        <thead>
          <tr>
            <th>Type</th>
            <th>Hours</th>
            <th>Multiplier</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.label}>
              <td>{r.label}</td>
              <td>{r.hours.toFixed(2)}</td>
              <td>{r.multiplier}</td>
            </tr>
          ))}
          <tr>
            <td>
              <strong>Total</strong>
            </td>
            <td>
              <strong>{totalHours.toFixed(2)}</strong>
            </td>
            <td />
          </tr>
        </tbody>
      </table>
    </div>
  );
}
