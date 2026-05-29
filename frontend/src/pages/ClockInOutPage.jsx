import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { clockIn, clockOut, getTimeEntries, getLocations } from '../api';

function fmt(dt) {
  if (!dt) return '—';
  return new Date(dt + 'Z').toLocaleString();
}

function duration(start, end) {
  if (!start) return '—';
  const s = new Date(start + 'Z');
  const e = end ? new Date(end + 'Z') : new Date();
  const mins = Math.round((e - s) / 60000);
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return `${h}h ${m}m`;
}

export default function ClockInOutPage() {
  const { token, companyId } = useAuth();
  const [entries, setEntries] = useState([]);
  const [openEntry, setOpenEntry] = useState(null);
  const [locations, setLocations] = useState([]);
  const [locationId, setLocationId] = useState('');
  const [loading, setLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState(null);
  const [error, setError] = useState(null);

  const loadEntries = async () => {
    try {
      const data = await getTimeEntries(token, 1, 10);
      const items = data.items || [];
      setEntries(items);
      setOpenEntry(items.find(e => e.status === 'open') || null);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    if (!token) return;
    loadEntries();
    if (companyId) {
      getLocations(token, companyId).then(d => {
        const locs = d.items || [];
        setLocations(locs);
        if (locs.length > 0) setLocationId(locs[0].id);
      }).catch(() => {});
    }
  }, [token, companyId]);

  const handleClockIn = async () => {
    setLoading(true);
    setActionMsg(null);
    setError(null);
    try {
      await clockIn(token, companyId, locationId || undefined);
      setActionMsg('✅ Clocked in successfully!');
      await loadEntries();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClockOut = async () => {
    setLoading(true);
    setActionMsg(null);
    setError(null);
    try {
      await clockOut(token);
      setActionMsg('✅ Clocked out successfully!');
      await loadEntries();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 style={{ margin: '0 0 1.5rem', fontSize: 24, color: '#1a1a2e' }}>Clock In / Out</h1>

      {/* Status card */}
      <div style={{
        background: openEntry ? '#e8f5e9' : '#fff',
        border: `2px solid ${openEntry ? '#4caf50' : '#e0e0e0'}`,
        borderRadius: 12,
        padding: '1.5rem',
        marginBottom: '1.5rem',
        maxWidth: 480,
      }}>
        <div style={{ fontSize: 16, fontWeight: 700, color: openEntry ? '#2e7d32' : '#555', marginBottom: 8 }}>
          {openEntry ? '⏱ Currently Clocked In' : '⚪ Not Clocked In'}
        </div>
        {openEntry && (
          <div style={{ fontSize: 14, color: '#555' }}>
            <div>Since: {fmt(openEntry.clock_in)}</div>
            <div>Duration: {duration(openEntry.clock_in, null)}</div>
            {openEntry.location_id && <div>Location ID: {openEntry.location_id}</div>}
          </div>
        )}
      </div>

      {/* Location selector */}
      {!openEntry && locations.length > 0 && (
        <div style={{ marginBottom: '1rem', maxWidth: 480 }}>
          <label style={{ fontSize: 13, fontWeight: 600, color: '#444', display: 'block', marginBottom: 4 }}>
            Location
          </label>
          <select
            value={locationId}
            onChange={e => setLocationId(e.target.value)}
            style={{ width: '100%', padding: '0.5rem', borderRadius: 6, border: '1px solid #ddd', fontSize: 14 }}
          >
            {locations.map(l => (
              <option key={l.id} value={l.id}>{l.name}</option>
            ))}
          </select>
        </div>
      )}

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: 12, marginBottom: '1.5rem' }}>
        {!openEntry && (
          <button onClick={handleClockIn} disabled={loading} style={{ ...actionBtn, background: '#1565c0' }}>
            {loading ? '…' : '🟢 Clock In'}
          </button>
        )}
        {openEntry && (
          <button onClick={handleClockOut} disabled={loading} style={{ ...actionBtn, background: '#c62828' }}>
            {loading ? '…' : '🔴 Clock Out'}
          </button>
        )}
      </div>

      {actionMsg && <div style={{ color: '#2e7d32', marginBottom: '1rem', fontWeight: 600 }}>{actionMsg}</div>}
      {error && <div style={{ color: '#c62828', marginBottom: '1rem' }}>Error: {error}</div>}

      {/* Recent entries */}
      <h2 style={{ fontSize: 17, margin: '0 0 0.75rem', color: '#333' }}>Recent Entries</h2>
      <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 2px 8px rgba(0,0,0,0.07)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ background: '#1565c0', color: '#fff' }}>
              <th style={th}>Clock In</th>
              <th style={th}>Clock Out</th>
              <th style={th}>Duration</th>
              <th style={th}>Status</th>
            </tr>
          </thead>
          <tbody>
            {entries.length === 0 && (
              <tr><td colSpan={4} style={{ padding: '1rem', textAlign: 'center', color: '#666' }}>No entries yet</td></tr>
            )}
            {entries.map(e => (
              <tr key={e.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                <td style={td}>{fmt(e.clock_in)}</td>
                <td style={td}>{fmt(e.clock_out)}</td>
                <td style={td}>{duration(e.clock_in, e.clock_out)}</td>
                <td style={td}>
                  <span style={{
                    padding: '2px 8px',
                    borderRadius: 10,
                    fontSize: 12,
                    background: e.status === 'open' ? '#e8f5e9' : '#e3f2fd',
                    color: e.status === 'open' ? '#2e7d32' : '#1565c0',
                    fontWeight: 600,
                  }}>
                    {e.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const actionBtn = {
  padding: '0.7rem 1.5rem',
  color: '#fff',
  border: 'none',
  borderRadius: 6,
  fontSize: 15,
  fontWeight: 700,
  cursor: 'pointer',
};

const th = { padding: '0.75rem 1rem', textAlign: 'left', fontWeight: 600 };
const td = { padding: '0.65rem 1rem', color: '#333' };
