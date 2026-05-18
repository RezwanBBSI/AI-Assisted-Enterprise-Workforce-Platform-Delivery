import { useState } from "react";

const API_BASE = "http://localhost:8000/api/v1";

/**
 * PayrollExportPage — lets a Manager/Admin pick a pay period and format,
 * then export a timesheet as CSV or JSON.
 *
 * Props:
 *   timesheetId  (string)  — UUID of the approved timesheet to export
 *   token        (string)  — Bearer token for a Manager or Admin
 */
export default function PayrollExportPage({ timesheetId, token }) {
  const [format, setFormat] = useState("csv");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleExport() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const resp = await fetch(`${API_BASE}/timesheets/${timesheetId}/export`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ export_format: format }),
      });
      if (!resp.ok) {
        const body = await resp.json();
        throw new Error(body.detail || resp.statusText);
      }
      setResult(await resp.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleDownload() {
    if (!result) return;
    const blob = new Blob([result.content], {
      type: format === "csv" ? "text/csv" : "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = result.export.file_name;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="payroll-export-page">
      <h2>Payroll Export</h2>

      <div>
        <label htmlFor="format-select">Export Format: </label>
        <select
          id="format-select"
          value={format}
          onChange={(e) => setFormat(e.target.value)}
        >
          <option value="csv">CSV</option>
          <option value="json">JSON</option>
        </select>
      </div>

      <button onClick={handleExport} disabled={loading}>
        {loading ? "Generating…" : "Generate Export"}
      </button>

      {error && <p className="error">{error}</p>}

      {result && (
        <div className="export-result">
          <p>
            Export ready — <strong>{result.export.record_count}</strong> line items
            ({result.export.export_format.toUpperCase()})
          </p>
          <p>
            Period: {result.export.pay_period_start} → {result.export.pay_period_end}
          </p>
          <button onClick={handleDownload}>
            Download {result.export.file_name}
          </button>
        </div>
      )}
    </div>
  );
}
