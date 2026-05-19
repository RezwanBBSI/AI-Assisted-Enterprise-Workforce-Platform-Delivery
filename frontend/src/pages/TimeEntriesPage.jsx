import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { getTimeEntries, submitCorrection } from '../api';

function fmt(dt) {
  if (!dt) return '—';
  return new Date(dt + 'Z').toLocaleString();
}

const STATUS_COLORS = {
  open: { bg: '#e8f5e9', color: '#2e7d32' },
  closed: { bg: '#e3f2fd', color: '#1565c0' },
  corrected: { bg: '#fff3e0', color: '#e65100' },
};

export default function TimeEntriesPage() {
  const { token } = useAuth();
  const [entries, setEntries] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [correcting, setCorrecting] = useState(null); // entry id
  const [corrForm, setCorrForm] = useState({ new_clock_in: '', new_clock_out: '', reason: '' });
  const [corrMsg, setCorrMsg] = useState(null);

  const size = 20;

  const load = async () => {
    setLoading(true);
    try {
      const data = await getTimeEntries(token, page, size);
      setEntries(data.items || []);
      setTotal(data.total || 0);
    } catch (_) {}
    setLoading(false);
  };

  useEffect(() => { load(); }, [token, page]);

  const handleCorrection = async (entryId) => {
    try {
      await submitCorrection(token, entryId, {
        new_clock_in: corrForm.new_clock_in || undefined,
        new_clock_out: corrForm.new_clock_out || undefined,
        reason: corrForm.reason,
      });
      setCorrMsg('✅ Correction submitted for review');
      setCorrecting(null);
      load();
    } catch (err) {
      setCorrMsg(`Error: ${err.message}`);
    }
  };

  const pages = Math.ceil(total / size);

  return (
    <div>
      <h1 style={{ margin: '0 0 1.5rem', fontSize: 24, color: '#1a1a2e' }}>Time Entries</h1>

      {corrMsg && (
        <div style={{ marginBottom: '1rem', padding: '0.6rem 1rem', background: '#e8f5e9', borderRadius: 6, color: '#2e7d32', fontWeight: 600 }}>
          {corrMsg}
        </div>
      )}

      <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 2px 8px rgba(0,0,0,0.07)', overflow: 'hidden' }}>
        {loading ? (
          <p style={{ padding: '1rem', color: '#999' }}>Loading…</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr style={{ background: '#1565c0', color: '#fff' }}>
                <th style={th}>Clock In</th>
                <th style={th}>Clock Out</th>
                <th style={th}>Break (min)</th>
                <th style={th}>Status</th>
                <th style={th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {entries.length === 0 && (
                <tr><td colSpan={5} style={{ padding: '1rem', textAlign: 'center', color: '#999' }}>No entries</td></tr>
              )}
              {entries.map(e => (
                <>
                  <tr key={e.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <td style={td}>{fmt(e.clock_in)}</td>
                    <td style={td}>{fmt(e.clock_out)}</td>
                    <td style={td}>{e.break_minutes ?? 0}</td>
                    <td style={td}>
                      <span style={{ padding: '2px 8px', borderRadius: 10, fontSize: 12, fontWeight: 600, ...(STATUS_COLORS[e.status] || {}) }}>
                        {e.status}
                      </span>
                    </td>
                    <td style={td}>
                      {e.status === 'closed' && (
                        <button
                          onClick={() => { setCorrecting(e.id); setCorrMsg(null); }}
                          style={smallBtn}
                        >
                          Request Correction
                        </button>
                      )}
                    </td>
                  </tr>
                  {correcting === e.id && (
                    <tr key={`corr-${e.id}`} style={{ background: '#fffde7' }}>
                      <td colSpan={5} style={{ padding: '1rem' }}>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'flex-end' }}>
                          <div>
                            <label style={corrLabel}>New Clock In</label>
                            <input type="datetime-local" value={corrForm.new_clock_in}
                              onChange={e => setCorrForm(f => ({ ...f, new_clock_in: e.target.value }))}
                              style={corrInput} />
                          </div>
                          <div>
                            <label style={corrLabel}>New Clock Out</label>
                            <input type="datetime-local" value={corrForm.new_clock_out}
                              onChange={e => setCorrForm(f => ({ ...f, new_clock_out: e.target.value }))}
                              style={corrInput} />
                          </div>
                          <div style={{ flex: 1 }}>
                            <label style={corrLabel}>Reason</label>
                            <input type="text" value={corrForm.reason}
                              onChange={e => setCorrForm(f => ({ ...f, reason: e.target.value }))}
                              placeholder="Explain the correction…"
                              style={{ ...corrInput, width: '100%' }} />
                          </div>
                          <button onClick={() => handleCorrection(e.id)} style={{ ...smallBtn, background: '#1565c0', color: '#fff', padding: '0.4rem 0.8rem' }}>
                            Submit
                          </button>
                          <button onClick={() => setCorrecting(null)} style={{ ...smallBtn, marginLeft: 4 }}>
                            Cancel
                          </button>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {pages > 1 && (
        <div style={{ display: 'flex', gap: 8, marginTop: '1rem', justifyContent: 'flex-end' }}>
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} style={pageBtn}>‹ Prev</button>
          <span style={{ lineHeight: '2rem', fontSize: 13, color: '#555' }}>Page {page} of {pages}</span>
          <button onClick={() => setPage(p => Math.min(pages, p + 1))} disabled={page === pages} style={pageBtn}>Next ›</button>
        </div>
      )}
    </div>
  );
}

const th = { padding: '0.75rem 1rem', textAlign: 'left', fontWeight: 600 };
const td = { padding: '0.65rem 1rem', color: '#333' };
const smallBtn = { padding: '0.3rem 0.7rem', background: '#f0f0f0', border: '1px solid #ddd', borderRadius: 4, cursor: 'pointer', fontSize: 12 };
const pageBtn = { padding: '0.4rem 0.8rem', background: '#fff', border: '1px solid #ddd', borderRadius: 4, cursor: 'pointer', fontSize: 13 };
const corrLabel = { display: 'block', fontSize: 11, fontWeight: 600, color: '#666', marginBottom: 2 };
const corrInput = { padding: '0.4rem', border: '1px solid #ddd', borderRadius: 4, fontSize: 13 };
