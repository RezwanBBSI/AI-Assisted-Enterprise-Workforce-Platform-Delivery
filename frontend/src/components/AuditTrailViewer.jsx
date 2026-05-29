import { useEffect, useState } from "react";

const API = "/api/v1";

export default function AuditTrailViewer({ token }) {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [entityType, setEntityType] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const size = 20;

  useEffect(() => {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams({ page, size });
    if (entityType) params.set("entity_type", entityType);
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    fetch(`${API}/reports/audit-trail?${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => {
        setItems(data.items);
        setTotal(data.total);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [token, page, entityType, startDate, endDate]);

  const totalPages = Math.ceil(total / size);

  return (
    <div style={{ fontFamily: "sans-serif", padding: "1.5rem" }}>
      <h2>Audit Trail</h2>

      {/* Filters */}
      <div style={{ display: "flex", gap: 12, marginBottom: "1rem", flexWrap: "wrap", alignItems: "flex-end" }}>
        <div>
          <label style={labelStyle}>Entity Type</label>
          <input
            placeholder="e.g. time_entry"
            value={entityType}
            onChange={(e) => { setEntityType(e.target.value); setPage(1); }}
            style={inputStyle}
          />
        </div>
        <div>
          <label style={labelStyle}>From</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => { setStartDate(e.target.value); setPage(1); }}
            style={inputStyle}
          />
        </div>
        <div>
          <label style={labelStyle}>To</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => { setEndDate(e.target.value); setPage(1); }}
            style={inputStyle}
          />
        </div>
        <button
          onClick={() => { setEntityType(""); setStartDate(""); setEndDate(""); setPage(1); }}
          style={clearBtnStyle}
        >
          Clear
        </button>
      </div>

      {loading && <p>Loading audit trail…</p>}
      {error && <p style={{ color: "red" }}>Error: {error}</p>}
      {!loading && items.length === 0 && <p>No audit log entries found.</p>}

      {items.length > 0 && (
        <table style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr style={{ background: "#f5f5f5" }}>
              <th style={th}>Performed At</th>
              <th style={th}>Entity Type</th>
              <th style={th}>Entity ID</th>
              <th style={th}>Action</th>
              <th style={th}>Performed By</th>
              <th style={th}>Details</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td style={td}>{new Date(item.performed_at).toLocaleString()}</td>
                <td style={td}>
                  <code style={{ fontSize: 12, background: "#f0f0f0", padding: "2px 6px", borderRadius: 3 }}>
                    {item.entity_type}
                  </code>
                </td>
                <td style={{ ...td, fontSize: 12, color: "#666" }}>{item.entity_id}</td>
                <td style={td}>
                  <span style={{ fontWeight: 600, color: actionColor(item.action) }}>
                    {item.action}
                  </span>
                </td>
                <td style={{ ...td, fontSize: 12, color: "#666" }}>{item.performed_by || "—"}</td>
                <td style={{ ...td, fontSize: 12, color: "#666", maxWidth: 320 }}>
                  {item.details ? (
                    <code style={{ fontSize: 11, wordBreak: "break-all" }}>{item.details}</code>
                  ) : "—"}
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
          <span>Page {page} of {totalPages} ({total} entries)</span>
          <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} style={btnStyle}>
            Next ›
          </button>
        </div>
      )}
    </div>
  );
}

function actionColor(action) {
  const map = { create: "#2e7d32", update: "#1565c0", delete: "#c62828", resolve: "#6a1b9a" };
  return map[action] || "#333";
}

const th = { padding: "8px 12px", textAlign: "left", borderBottom: "2px solid #ddd" };
const td = { padding: "8px 12px", borderBottom: "1px solid #eee" };
const labelStyle = { display: "block", fontSize: 12, color: "#555", marginBottom: 4 };
const inputStyle = { padding: "6px 10px", borderRadius: 4, border: "1px solid #ccc", minWidth: 140 };
const btnStyle = { padding: "5px 12px", borderRadius: 4, border: "none", background: "#1565c0", color: "#fff", cursor: "pointer" };
const clearBtnStyle = { ...btnStyle, background: "#616161" };
