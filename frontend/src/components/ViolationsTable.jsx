import { useEffect, useState } from "react";

const API = "/api/v1";

export default function ViolationsTable({ companyId, token }) {
  const [violations, setViolations] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filterType, setFilterType] = useState("");
  const [filterResolved, setFilterResolved] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [resolveNotes, setResolveNotes] = useState({});

  const size = 20;

  const load = () => {
    if (!companyId) return;
    setLoading(true);
    const params = new URLSearchParams({ company_id: companyId, page, size });
    if (filterType) params.set("violation_type", filterType);
    if (filterResolved !== "") params.set("resolved", filterResolved);
    fetch(`${API}/compliance/violations?${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => {
        setViolations(data.items);
        setTotal(data.total);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, [companyId, page, filterType, filterResolved, token]);

  const resolveViolation = async (id) => {
    const notes = resolveNotes[id] || "Resolved via dashboard";
    const r = await fetch(`${API}/compliance/violations/${id}`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ resolution_notes: notes }),
    });
    if (r.ok) {
      load();
    } else {
      const data = await r.json();
      alert(data.detail || "Failed to resolve violation");
    }
  };

  const totalPages = Math.ceil(total / size);

  return (
    <div style={{ fontFamily: "sans-serif", padding: "1.5rem" }}>
      <h2>Compliance Violations</h2>

      {/* Filters */}
      <div style={{ display: "flex", gap: 12, marginBottom: "1rem", flexWrap: "wrap" }}>
        <select
          value={filterType}
          onChange={(e) => { setFilterType(e.target.value); setPage(1); }}
          style={selectStyle}
        >
          <option value="">All Types</option>
          <option value="missing_punch">Missing Punch</option>
          <option value="max_hours">Max Hours</option>
          <option value="mandatory_break">Mandatory Break</option>
          <option value="ot_threshold">OT Threshold</option>
          <option value="min_wage">Min Wage</option>
        </select>
        <select
          value={filterResolved}
          onChange={(e) => { setFilterResolved(e.target.value); setPage(1); }}
          style={selectStyle}
        >
          <option value="">All Statuses</option>
          <option value="false">Unresolved</option>
          <option value="true">Resolved</option>
        </select>
      </div>

      {loading && <p>Loading…</p>}
      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      {!loading && violations.length === 0 && <p>No violations found.</p>}

      {violations.length > 0 && (
        <table style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr style={{ background: "#f5f5f5" }}>
              <th style={th}>Type</th>
              <th style={th}>Description</th>
              <th style={th}>Occurred At</th>
              <th style={th}>Status</th>
              <th style={th}>Action</th>
            </tr>
          </thead>
          <tbody>
            {violations.map((v) => (
              <tr key={v.id} style={{ opacity: v.resolved ? 0.6 : 1 }}>
                <td style={td}>
                  <span style={{
                    background: typeColor(v.violation_type),
                    color: "#fff",
                    borderRadius: 4,
                    padding: "2px 8px",
                    fontSize: 12,
                  }}>
                    {v.violation_type.replace(/_/g, " ")}
                  </span>
                </td>
                <td style={td}>{v.description}</td>
                <td style={td}>{new Date(v.occurred_at).toLocaleString()}</td>
                <td style={td}>{v.resolved ? "✅ Resolved" : "⚠️ Open"}</td>
                <td style={td}>
                  {!v.resolved && (
                    <div style={{ display: "flex", gap: 6 }}>
                      <input
                        placeholder="Notes…"
                        value={resolveNotes[v.id] || ""}
                        onChange={(e) =>
                          setResolveNotes((prev) => ({ ...prev, [v.id]: e.target.value }))
                        }
                        style={{ padding: "4px 8px", fontSize: 13, flexGrow: 1 }}
                      />
                      <button
                        onClick={() => resolveViolation(v.id)}
                        style={btnStyle}
                      >
                        Resolve
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ marginTop: 16, display: "flex", gap: 8, alignItems: "center" }}>
          <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} style={btnStyle}>
            ‹ Prev
          </button>
          <span>Page {page} of {totalPages}</span>
          <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} style={btnStyle}>
            Next ›
          </button>
        </div>
      )}
    </div>
  );
}

function typeColor(type) {
  const map = {
    missing_punch: "#e53935",
    max_hours: "#8e24aa",
    mandatory_break: "#f57c00",
    ot_threshold: "#1565c0",
    min_wage: "#2e7d32",
  };
  return map[type] || "#555";
}

const th = { padding: "8px 12px", textAlign: "left", borderBottom: "2px solid #ddd" };
const td = { padding: "8px 12px", borderBottom: "1px solid #eee", verticalAlign: "middle" };
const selectStyle = { padding: "6px 10px", borderRadius: 4, border: "1px solid #ccc" };
const btnStyle = {
  padding: "5px 12px",
  borderRadius: 4,
  border: "none",
  background: "#1565c0",
  color: "#fff",
  cursor: "pointer",
};
