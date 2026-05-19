import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { getSchedules, createSchedule, deleteSchedule, getLocations, getEmployees } from '../api';

function fmt(dt) { return dt ? new Date(dt).toLocaleString() : '—'; }
function fmtDate(d) { return d ? new Date(d).toLocaleDateString() : '—'; }

export default function SchedulesPage() {
  const { token, companyId, isManager } = useAuth();
  const [shifts, setShifts] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [locations, setLocations] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    employee_id: '', location_id: '', shift_date: '',
    start_time: '09:00', end_time: '17:00', break_minutes: 30,
  });
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState(null);

  const size = 20;

  const load = async () => {
    setLoading(true);
    try {
      const data = await getSchedules(token, companyId, page, size);
      setShifts(data.items || []);
      setTotal(data.total || 0);
    } catch (_) {}
    setLoading(false);
  };

  useEffect(() => {
    load();
    if (companyId) {
      getLocations(token, companyId).then(d => setLocations(d.items || [])).catch(() => {});
      if (isManager) {
        getEmployees(token, companyId).then(d => setEmployees(d.items || [])).catch(() => {});
      }
    }
  }, [token, companyId, page]);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await createSchedule(token, { ...form, company_id: companyId, break_minutes: Number(form.break_minutes) });
      setMsg('✅ Shift created');
      setShowForm(false);
      load();
    } catch (err) {
      setMsg(`Error: ${err.message}`);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this shift?')) return;
    try {
      await deleteSchedule(token, id);
      setMsg('✅ Shift deleted');
      load();
    } catch (err) {
      setMsg(`Error: ${err.message}`);
    }
  };

  const pages = Math.ceil(total / size);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <h1 style={{ margin: 0, fontSize: 24, color: '#1a1a2e' }}>Schedules</h1>
        {isManager && (
          <button onClick={() => setShowForm(!showForm)} style={actionBtn}>
            {showForm ? 'Cancel' : '+ New Shift'}
          </button>
        )}
      </div>

      {msg && <div style={{ marginBottom: '1rem', padding: '0.6rem 1rem', background: '#e8f5e9', borderRadius: 6, color: '#2e7d32' }}>{msg}</div>}

      {showForm && isManager && (
        <form onSubmit={handleCreate} style={{ background: '#fff', borderRadius: 10, padding: '1.25rem', marginBottom: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.07)' }}>
          <h3 style={{ margin: '0 0 1rem', fontSize: 15 }}>New Shift</h3>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <div>
              <label style={lbl}>Employee</label>
              <select required value={form.employee_id} onChange={e => setForm(f => ({ ...f, employee_id: e.target.value }))} style={inp}>
                <option value="">Select…</option>
                {employees.map(emp => <option key={emp.id} value={emp.id}>{emp.full_name || emp.email}</option>)}
              </select>
            </div>
            <div>
              <label style={lbl}>Location</label>
              <select value={form.location_id} onChange={e => setForm(f => ({ ...f, location_id: e.target.value }))} style={inp}>
                <option value="">None</option>
                {locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
            </div>
            <div>
              <label style={lbl}>Date</label>
              <input type="date" required value={form.shift_date} onChange={e => setForm(f => ({ ...f, shift_date: e.target.value }))} style={inp} />
            </div>
            <div>
              <label style={lbl}>Start Time</label>
              <input type="time" required value={form.start_time} onChange={e => setForm(f => ({ ...f, start_time: e.target.value }))} style={inp} />
            </div>
            <div>
              <label style={lbl}>End Time</label>
              <input type="time" required value={form.end_time} onChange={e => setForm(f => ({ ...f, end_time: e.target.value }))} style={inp} />
            </div>
            <div>
              <label style={lbl}>Break (min)</label>
              <input type="number" min="0" step="15" value={form.break_minutes} onChange={e => setForm(f => ({ ...f, break_minutes: e.target.value }))} style={{ ...inp, width: 70 }} />
            </div>
          </div>
          <button type="submit" style={{ ...actionBtn, marginTop: '0.75rem' }}>Create Shift</button>
        </form>
      )}

      <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 2px 8px rgba(0,0,0,0.07)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ background: '#1565c0', color: '#fff' }}>
              <th style={th}>Date</th>
              <th style={th}>Start</th>
              <th style={th}>End</th>
              <th style={th}>Break</th>
              <th style={th}>Employee ID</th>
              {isManager && <th style={th}>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={6} style={{ padding: '1rem', textAlign: 'center' }}>Loading…</td></tr>}
            {!loading && shifts.length === 0 && <tr><td colSpan={6} style={{ padding: '1rem', textAlign: 'center', color: '#999' }}>No shifts scheduled</td></tr>}
            {shifts.map(s => (
              <tr key={s.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                <td style={td}>{fmtDate(s.shift_date)}</td>
                <td style={td}>{s.start_time}</td>
                <td style={td}>{s.end_time}</td>
                <td style={td}>{s.break_minutes} min</td>
                <td style={td}><code style={{ fontSize: 11, color: '#666' }}>{s.employee_id?.slice(0, 8)}…</code></td>
                {isManager && (
                  <td style={td}>
                    <button onClick={() => handleDelete(s.id)} style={{ ...smallBtn, color: '#c62828', borderColor: '#ffcdd2' }}>Delete</button>
                  </td>
                )}
              </tr>
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
const smallBtn = { padding: '0.3rem 0.7rem', background: '#fff', border: '1px solid #ddd', borderRadius: 4, cursor: 'pointer', fontSize: 12 };
const pageBtn = { padding: '0.4rem 0.8rem', background: '#fff', border: '1px solid #ddd', borderRadius: 4, cursor: 'pointer', fontSize: 13 };
const actionBtn = { padding: '0.55rem 1.1rem', background: '#1565c0', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14, fontWeight: 600 };
