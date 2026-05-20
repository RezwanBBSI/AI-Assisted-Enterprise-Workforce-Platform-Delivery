import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { getTimesheets, exportTimesheet } from '../api';

const statusBadge = {
  draft:     { bg: '#e0e0e0', color: '#555' },
  submitted: { bg: '#fff3e0', color: '#e65100' },
  approved:  { bg: '#e8f5e9', color: '#2e7d32' },
  exported:  { bg: '#e3f2fd', color: '#1565c0' },
};

export default function PayrollPage() {
  const { token } = useAuth();
  const [timesheets, setTimesheets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(null);
  const [results, setResults] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    getTimesheets(token, 1, 100)
      .then(data => setTimesheets(data.items || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [token]);

  async function handleExport(id, format) {
    setExporting(id + format);
    setError(null);
    try {
      const data = await exportTimesheet(token, id, format);
      const content = data.content || JSON.stringify(data, null, 2);
      const blob = new Blob([content], {
        type: format === 'csv' ? 'text/csv' : 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `timesheet-${id}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
      setResults(prev => ({ ...prev, [id]: `Exported as ${format.toUpperCase()}` }));
    } catch (e) {
      setError(e.message);
    } finally {
      setExporting(null);
    }
  }

  if (loading) return <p>Loading timesheets…</p>;

  const exportable = timesheets.filter(t => t.status === 'approved' || t.status === 'exported');
  const other = timesheets.filter(t => t.status !== 'approved' && t.status !== 'exported');

  return (
    <div>
      <h1 style={{ margin: '0 0 0.5rem', fontSize: 24, color: '#1a1a2e' }}>Payroll Export</h1>
      <p style={{ margin: '0 0 1.5rem', color: '#666', fontSize: 14 }}>
        Export approved timesheets to CSV or JSON for payroll processing.
      </p>

      {error && (
        <div style={{ background: '#ffebee', color: '#c62828', padding: '0.75rem 1rem', borderRadius: 6, marginBottom: '1rem', fontSize: 14 }}>
          {error}
        </div>
      )}

      {exportable.length === 0 && (
        <div style={{ background: '#fff3e0', color: '#e65100', padding: '1rem', borderRadius: 8, marginBottom: '1.5rem', fontSize: 14 }}>
          No approved timesheets available for export yet.
        </div>
      )}

      {exportable.length > 0 && (
        <section style={{ marginBottom: '2rem' }}>
          <h2 style={{ fontSize: 16, color: '#333', marginBottom: '0.75rem' }}>Ready to Export</h2>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14, background: '#fff', borderRadius: 8, overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.07)' }}>
              <thead style={{ background: '#f5f5f5' }}>
                <tr>
                  {['Employee', 'Pay Period', 'Reg Hrs', 'OT Hrs', 'Status', 'Export'].map(h => (
                    <th key={h} style={{ padding: '0.75rem 1rem', textAlign: 'left', fontWeight: 600, color: '#444', fontSize: 12, textTransform: 'uppercase' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {exportable.map(t => {
                  const badge = statusBadge[t.status] || statusBadge.draft;
                  return (
                    <tr key={t.id} style={{ borderTop: '1px solid #f0f0f0' }}>
                      <td style={{ padding: '0.75rem 1rem', color: '#333' }}>{t.employee_id?.slice(0, 8)}…</td>
                      <td style={{ padding: '0.75rem 1rem', color: '#555' }}>
                        {t.pay_period_start?.slice(0, 10)} → {t.pay_period_end?.slice(0, 10)}
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>{(t.total_regular_hrs || 0).toFixed(1)}</td>
                      <td style={{ padding: '0.75rem 1rem' }}>{(t.total_ot_hrs || 0).toFixed(1)}</td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <span style={{ ...badge, padding: '2px 8px', borderRadius: 12, fontSize: 12, fontWeight: 600 }}>
                          {t.status}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        {results[t.id] ? (
                          <span style={{ color: '#2e7d32', fontSize: 13 }}>✓ {results[t.id]}</span>
                        ) : (
                          <div style={{ display: 'flex', gap: 8 }}>
                            <button
                              onClick={() => handleExport(t.id, 'csv')}
                              disabled={!!exporting}
                              style={btnStyle('#1565c0')}
                            >
                              {exporting === t.id + 'csv' ? '…' : 'CSV'}
                            </button>
                            <button
                              onClick={() => handleExport(t.id, 'json')}
                              disabled={!!exporting}
                              style={btnStyle('#00838f')}
                            >
                              {exporting === t.id + 'json' ? '…' : 'JSON'}
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {other.length > 0 && (
        <section>
          <h2 style={{ fontSize: 16, color: '#333', marginBottom: '0.75rem' }}>Other Timesheets</h2>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14, background: '#fff', borderRadius: 8, overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.07)' }}>
              <thead style={{ background: '#f5f5f5' }}>
                <tr>
                  {['Employee', 'Pay Period', 'Reg Hrs', 'Status'].map(h => (
                    <th key={h} style={{ padding: '0.75rem 1rem', textAlign: 'left', fontWeight: 600, color: '#444', fontSize: 12, textTransform: 'uppercase' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {other.map(t => {
                  const badge = statusBadge[t.status] || statusBadge.draft;
                  return (
                    <tr key={t.id} style={{ borderTop: '1px solid #f0f0f0' }}>
                      <td style={{ padding: '0.75rem 1rem', color: '#333' }}>{t.employee_id?.slice(0, 8)}…</td>
                      <td style={{ padding: '0.75rem 1rem', color: '#555' }}>
                        {t.pay_period_start?.slice(0, 10)} → {t.pay_period_end?.slice(0, 10)}
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>{(t.total_regular_hrs || 0).toFixed(1)}</td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <span style={{ ...badge, padding: '2px 8px', borderRadius: 12, fontSize: 12, fontWeight: 600 }}>
                          {t.status}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}

function btnStyle(color) {
  return {
    background: color,
    color: '#fff',
    border: 'none',
    padding: '4px 12px',
    borderRadius: 4,
    cursor: 'pointer',
    fontSize: 12,
    fontWeight: 600,
  };
}
