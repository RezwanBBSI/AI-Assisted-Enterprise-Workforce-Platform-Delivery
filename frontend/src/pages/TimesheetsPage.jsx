import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  getTimesheets, generateTimesheet, submitTimesheet,
  approveTimesheet, exportTimesheet, getEmployees,
} from '../api';

const RATE_LABELS = {
  regular: 'Regular', overtime: 'Overtime', double_time: 'Double-time',
  holiday: 'Holiday', night_differential: 'Night Diff.', pto: 'PTO', sick: 'Sick', comp: 'Comp',
};

const STATUS_COLORS = {
  draft:     { bg: '#f5f5f5', color: '#555' },
  submitted: { bg: '#fff3e0', color: '#e65100' },
  approved:  { bg: '#e8f5e9', color: '#2e7d32' },
  exported:  { bg: '#e3f2fd', color: '#1565c0' },
};

function fmt(d) { return d ? new Date(d).toLocaleDateString() : '—'; }

export default function TimesheetsPage() {
  const { token, companyId, user, isManager } = useAuth();
  const [timesheets, setTimesheets] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [expanded, setExpanded] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [genForm, setGenForm] = useState({ employee_id: '', start: '', end: '' });
  const [showGen, setShowGen] = useState(false);
  const [msg, setMsg] = useState(null);
  const [loading, setLoading] = useState(false);

  const size = 20;

  const load = async () => {
    setLoading(true);
    try {
      const data = await getTimesheets(token, page, size);
      setTimesheets(data.items || []);
      setTotal(data.total || 0);
    } catch (_) {}
    setLoading(false);
  };

  useEffect(() => {
    load();
    if (isManager && companyId) {
      getEmployees(token, companyId).then(d => setEmployees(d.items || [])).catch(() => {});
    }
  }, [token, page]);

  const handleGenerate = async (e) => {
    e.preventDefault();
    try {
      await generateTimesheet(token, companyId, genForm.employee_id, genForm.start, genForm.end);
      setMsg('✅ Timesheet generated');
      setShowGen(false);
      load();
    } catch (err) {
      setMsg(`Error: ${err.message}`);
    }
  };

  const handleSubmit = async (id) => {
    try {
      await submitTimesheet(token, id);
      setMsg('✅ Timesheet submitted');
      load();
    } catch (err) {
      setMsg(`Error: ${err.message}`);
    }
  };

  const handleApprove = async (id) => {
    try {
      await approveTimesheet(token, id);
      setMsg('✅ Timesheet approved');
      load();
    } catch (err) {
      setMsg(`Error: ${err.message}`);
    }
  };

  const handleExport = async (id, format) => {
    try {
      const data = await exportTimesheet(token, id, format);
      const blob = new Blob([data.content], { type: format === 'csv' ? 'text/csv' : 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = data.file_name || `timesheet.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setMsg(`Export error: ${err.message}`);
    }
  };

  const pages = Math.ceil(total / size);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <h1 style={{ margin: 0, fontSize: 24, color: '#1a1a2e' }}>Timesheets</h1>
        {isManager && (
          <button onClick={() => setShowGen(!showGen)} style={actionBtn}>
            {showGen ? 'Cancel' : '+ Generate Timesheet'}
          </button>
        )}
      </div>

      {msg && <div style={{ marginBottom: '1rem', padding: '0.6rem 1rem', background: '#e8f5e9', borderRadius: 6, color: '#2e7d32' }}>{msg}</div>}

      {showGen && isManager && (
        <form onSubmit={handleGenerate} style={{ background: '#fff', borderRadius: 10, padding: '1.25rem', marginBottom: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.07)' }}>
          <h3 style={{ margin: '0 0 1rem', fontSize: 15 }}>Generate Timesheet</h3>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <div>
              <label style={lbl}>Employee</label>
              <select required value={genForm.employee_id} onChange={e => setGenForm(f => ({ ...f, employee_id: e.target.value }))} style={inp}>
                <option value="">Select…</option>
                {employees.map(emp => <option key={emp.id} value={emp.id}>{emp.full_name || emp.email}</option>)}
              </select>
            </div>
            <div>
              <label style={lbl}>Period Start</label>
              <input type="date" required value={genForm.start} onChange={e => setGenForm(f => ({ ...f, start: e.target.value }))} style={inp} />
            </div>
            <div>
              <label style={lbl}>Period End</label>
              <input type="date" required value={genForm.end} onChange={e => setGenForm(f => ({ ...f, end: e.target.value }))} style={inp} />
            </div>
          </div>
          <button type="submit" style={{ ...actionBtn, marginTop: '0.75rem' }}>Generate</button>
        </form>
      )}

      <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 2px 8px rgba(0,0,0,0.07)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ background: '#1565c0', color: '#fff' }}>
              <th style={th}>Period</th>
              <th style={th}>Regular</th>
              <th style={th}>OT</th>
              <th style={th}>Status</th>
              <th style={th}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={5} style={{ padding: '1rem', textAlign: 'center' }}>Loading…</td></tr>}
            {!loading && timesheets.length === 0 && <tr><td colSpan={5} style={{ padding: '1rem', textAlign: 'center', color: '#999' }}>No timesheets yet</td></tr>}
            {timesheets.map(ts => (
              <>
                <tr
                  key={ts.id}
                  style={{ borderBottom: '1px solid #f0f0f0', cursor: 'pointer', background: expanded === ts.id ? '#f5f9ff' : '#fff' }}
                  onClick={() => setExpanded(expanded === ts.id ? null : ts.id)}
                >
                  <td style={td}>{fmt(ts.pay_period_start)} – {fmt(ts.pay_period_end)}</td>
                  <td style={td}>{ts.regular_hours?.toFixed(2)} h</td>
                  <td style={td}>{ts.overtime_hours?.toFixed(2)} h</td>
                  <td style={td}>
                    <span style={{ padding: '2px 8px', borderRadius: 10, fontSize: 12, fontWeight: 600, ...(STATUS_COLORS[ts.status] || {}) }}>
                      {ts.status}
                    </span>
                  </td>
                  <td style={td} onClick={e => e.stopPropagation()}>
                    {ts.status === 'draft' && (
                      <button onClick={() => handleSubmit(ts.id)} style={smallBtn}>Submit</button>
                    )}
                    {ts.status === 'submitted' && isManager && (
                      <button onClick={() => handleApprove(ts.id)} style={{ ...smallBtn, background: '#e8f5e9', color: '#2e7d32', borderColor: '#a5d6a7' }}>Approve</button>
                    )}
                    {ts.status === 'approved' && isManager && (
                      <>
                        <button onClick={() => handleExport(ts.id, 'csv')} style={smallBtn}>CSV</button>
                        <button onClick={() => handleExport(ts.id, 'json')} style={{ ...smallBtn, marginLeft: 4 }}>JSON</button>
                      </>
                    )}
                  </td>
                </tr>
                {expanded === ts.id && ts.line_items?.length > 0 && (
                  <tr key={`li-${ts.id}`}>
                    <td colSpan={5} style={{ padding: '0 1rem 1rem' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, marginTop: 4 }}>
                        <thead>
                          <tr style={{ background: '#f5f5f5' }}>
                            <th style={{ ...th, fontSize: 12 }}>Type</th>
                            <th style={{ ...th, fontSize: 12 }}>Hours</th>
                            <th style={{ ...th, fontSize: 12 }}>Multiplier</th>
                          </tr>
                        </thead>
                        <tbody>
                          {ts.line_items.map(li => (
                            <tr key={li.id} style={{ borderBottom: '1px solid #f5f5f5' }}>
                              <td style={td}>{RATE_LABELS[li.rate_type] || li.rate_type}</td>
                              <td style={td}>{li.hours.toFixed(2)} h</td>
                              <td style={td}>×{li.rate_multiplier}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>

      {pages > 1 && (
        <div style={{ display: 'flex', gap: 8, marginTop: '1rem', justifyContent: 'flex-end' }}>
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} style={pageBtn}>‹ Prev</button>
          <span style={{ lineHeight: '2rem', fontSize: 13 }}>Page {page} of {pages}</span>
          <button onClick={() => setPage(p => Math.min(pages, p + 1))} disabled={page === pages} style={pageBtn}>Next ›</button>
        </div>
      )}
    </div>
  );
}

const th = { padding: '0.75rem 1rem', textAlign: 'left', fontWeight: 600 };
const td = { padding: '0.65rem 1rem', color: '#333' };
const lbl = { display: 'block', fontSize: 12, fontWeight: 600, color: '#555', marginBottom: 3, marginTop: 8 };
const inp = { padding: '0.45rem 0.6rem', border: '1px solid #ddd', borderRadius: 5, fontSize: 13 };
const smallBtn = { padding: '0.3rem 0.7rem', background: '#f0f0f0', border: '1px solid #ddd', borderRadius: 4, cursor: 'pointer', fontSize: 12, marginRight: 2 };
const pageBtn = { padding: '0.4rem 0.8rem', background: '#fff', border: '1px solid #ddd', borderRadius: 4, cursor: 'pointer', fontSize: 13 };
const actionBtn = { padding: '0.55rem 1.1rem', background: '#1565c0', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14, fontWeight: 600 };
