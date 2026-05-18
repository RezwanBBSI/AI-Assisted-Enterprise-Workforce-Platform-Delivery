import { useEffect, useState } from "react";

const API = "/api/v1";

function StatCard({ label, value, accent }) {
  return (
    <div
      style={{
        background: "#fff",
        border: `2px solid ${accent}`,
        borderRadius: 8,
        padding: "1rem 1.5rem",
        minWidth: 160,
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: 32, fontWeight: 700, color: accent }}>{value}</div>
      <div style={{ fontSize: 14, color: "#555", marginTop: 4 }}>{label}</div>
    </div>
  );
}

export default function ComplianceDashboard({ companyId, payPeriodStart, payPeriodEnd, token }) {
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
    fetch(`${API}/reports/compliance?${params}`, {
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

  if (loading) return <p>Loading compliance dashboard…</p>;
  if (error) return <p style={{ color: "red" }}>Error: {error}</p>;
  if (!report) return <p>Enter company and pay period above.</p>;

  return (
    <div style={{ fontFamily: "sans-serif", padding: "1.5rem" }}>
      <h2 style={{ marginBottom: "0.5rem" }}>Compliance Dashboard</h2>
      <p style={{ color: "#666", marginTop: 0 }}>
        {report.pay_period_start} → {report.pay_period_end}
      </p>

      {/* Summary cards */}
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: "2rem" }}>
        <StatCard label="Total Violations" value={report.total_violations} accent="#e53935" />
        <StatCard label="Unresolved" value={report.unresolved} accent="#f57c00" />
        <StatCard
          label="Resolved"
          value={report.total_violations - report.unresolved}
          accent="#43a047"
        />
      </div>

      {/* By-type breakdown */}
      {Object.keys(report.by_type).length > 0 && (
        <div style={{ marginBottom: "2rem" }}>
          <h3>By Type</h3>
          <table style={{ borderCollapse: "collapse", width: "100%", maxWidth: 480 }}>
            <thead>
              <tr style={{ background: "#f5f5f5" }}>
                <th style={th}>Violation Type</th>
                <th style={th}>Count</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(report.by_type).map(([type, count]) => (
                <tr key={type}>
                  <td style={td}>{type.replace(/_/g, " ")}</td>
                  <td style={td}>{count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const th = { padding: "8px 12px", textAlign: "left", borderBottom: "2px solid #ddd" };
const td = { padding: "8px 12px", borderBottom: "1px solid #eee" };
