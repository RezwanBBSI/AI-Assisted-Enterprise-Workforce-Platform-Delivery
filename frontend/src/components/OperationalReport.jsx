import { useEffect, useState } from "react";

const API = "/api/v1";

function MetricRow({ label, value, unit }) {
  return (
    <tr>
      <td style={{ padding: "10px 16px", borderBottom: "1px solid #eee", color: "#555", fontWeight: 500 }}>
        {label}
      </td>
      <td style={{ padding: "10px 16px", borderBottom: "1px solid #eee", fontWeight: 700, fontSize: 20 }}>
        {value}
        {unit && <span style={{ fontSize: 13, fontWeight: 400, marginLeft: 4, color: "#666" }}>{unit}</span>}
      </td>
    </tr>
  );
}

export default function OperationalReport({ companyId, payPeriodStart, payPeriodEnd, token }) {
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!companyId || !payPeriodStart || !payPeriodEnd) return;
    setLoading(true);
    setError(null);
    const params = new URLSearchParams({
      company_id: companyId,
      pay_period_start: payPeriodStart,
      pay_period_end: payPeriodEnd,
    });
    fetch(`${API}/reports/operational?${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setReport)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [companyId, payPeriodStart, payPeriodEnd, token]);

  if (loading) return <p>Loading operational report…</p>;
  if (error) return <p style={{ color: "red" }}>Error: {error}</p>;
  if (!report) return <p>Enter company and pay period above.</p>;

  return (
    <div style={{ fontFamily: "sans-serif", padding: "1.5rem" }}>
      <h2 style={{ marginBottom: "0.25rem" }}>Operational Report</h2>
      <p style={{ color: "#666", marginTop: 0 }}>
        {report.pay_period_start} → {report.pay_period_end}
      </p>

      <table style={{ borderCollapse: "collapse", minWidth: 360, background: "#fff", borderRadius: 8, overflow: "hidden", boxShadow: "0 1px 4px rgba(0,0,0,0.08)" }}>
        <thead>
          <tr style={{ background: "#1565c0" }}>
            <th style={{ padding: "12px 16px", color: "#fff", textAlign: "left" }}>Metric</th>
            <th style={{ padding: "12px 16px", color: "#fff", textAlign: "left" }}>Value</th>
          </tr>
        </thead>
        <tbody>
          <MetricRow label="Active Employees" value={report.total_employees} />
          <MetricRow label="Regular Hours" value={report.total_regular_hrs.toFixed(1)} unit="hrs" />
          <MetricRow label="Overtime Hours" value={report.total_ot_hrs.toFixed(1)} unit="hrs" />
          <MetricRow label="Total Hours" value={(report.total_regular_hrs + report.total_ot_hrs).toFixed(1)} unit="hrs" />
          <MetricRow label="Absences" value={report.total_absences} />
          <MetricRow label="Late Arrivals" value={report.total_late_arrivals} />
        </tbody>
      </table>

      {/* OT percentage bar */}
      {report.total_regular_hrs + report.total_ot_hrs > 0 && (
        <div style={{ marginTop: "1.5rem", maxWidth: 400 }}>
          <div style={{ fontSize: 13, color: "#555", marginBottom: 4 }}>
            OT as % of total hours
          </div>
          <div style={{ background: "#e0e0e0", borderRadius: 4, height: 16, overflow: "hidden" }}>
            <div
              style={{
                background: "#f57c00",
                height: "100%",
                width: `${Math.min(100, (report.total_ot_hrs / (report.total_regular_hrs + report.total_ot_hrs)) * 100).toFixed(1)}%`,
                transition: "width 0.3s",
              }}
            />
          </div>
          <div style={{ fontSize: 12, color: "#777", marginTop: 4 }}>
            {((report.total_ot_hrs / (report.total_regular_hrs + report.total_ot_hrs)) * 100).toFixed(1)}%
          </div>
        </div>
      )}
    </div>
  );
}
