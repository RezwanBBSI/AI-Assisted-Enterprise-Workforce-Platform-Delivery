import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import OperationalReport from '../components/OperationalReport';
import AuditTrailViewer from '../components/AuditTrailViewer';
import { getAttendanceExceptions, getCrosscheck, getEmployees } from '../api';

function todayMinus(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

export default function ReportsPage() {
  const { token, companyId, isAdmin } = useAuth();
  const [start, setStart] = useState(todayMinus(14));
  const [end, setEnd] = useState(todayMinus(1));
  const [activeTab, setActiveTab] = useState('operational');
  const [employeeMap, setEmployeeMap] = useState({});

  useEffect(() => {
    if (!token || !companyId) return;
    getEmployees(token, companyId, 1, 100)
      .then(d => {
        const map = {};
        (d.items || []).forEach(e => { map[e.id] = e.full_name || e.email; });
        setEmployeeMap(map);
      })
      .catch(() => {});
  }, [token, companyId]);

  const empName = (id) => employeeMap[id] || id?.slice(0, 8) + '…';

  // Attendance exceptions state
  const [exceptions, setExceptions] = useState([]);
  const [exceptLoading, setExceptLoading] = useState(false);
  const [exceptMsg, setExceptMsg] = useState(null);

  // Crosscheck state
  const [crosscheck, setCrosscheck] = useState([]);
  const [crossLoading, setCrossLoading] = useState(false);
  const [crossMsg, setCrossMsg] = useState(null);

  const loadExceptions = async () => {
    setExceptLoading(true);
    setExceptMsg(null);
    try {
      const data = await getAttendanceExceptions(token, companyId, start, end);
      setExceptions(data.items || []);
      setExceptMsg(`${data.total || 0} exception(s) found`);
    } catch (err) {
      setExceptMsg(`Error: ${err.message}`);
    } finally {
      setExceptLoading(false);
    }
  };

  const loadCrosscheck = async () => {
    setCrossLoading(true);
    setCrossMsg(null);
    try {
      const data = await getCrosscheck(token, companyId, start, end);
      setCrosscheck(data.discrepancies || []);
      setCrossMsg(`${data.discrepancies?.length || 0} discrepancy(ies) found`);
    } catch (err) {
      setCrossMsg(`Error: ${err.message}`);
    } finally {
      setCrossLoading(false);
    }
  };

  const TABS = [
    { key: 'operational', label: '📊 Operational' },
    { key: 'exceptions', label: '🚨 Attendance Exceptions' },
    { key: 'crosscheck', label: '🔀 Crosscheck' },
    ...(isAdmin ? [{ key: 'audit', label: '🔍 Audit Trail' }] : []),
  ];

  return (
    <div>
      <h1 style={{ margin: '0 0 1.5rem', fontSize: 24, color: '#1a1a2e' }}>Reports</h1>

      {/* Period selector */}
      <div style={{ background: '#fff', borderRadius: 10, padding: '1rem 1.25rem', marginBottom: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.07)', display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
        <div>
          <label style={lbl}>Report Period Start</label>
          <input type="date" value={start} onChange={e => setStart(e.target.value)} style={inp} />
        </div>
        <div>
          <label style={lbl}>Report Period End</label>
          <input type="date" value={end} onChange={e => setEnd(e.target.value)} style={inp} />
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '2px solid #e0e0e0', marginBottom: '1.5rem', gap: 4, flexWrap: 'wrap' }}>
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            style={{
              padding: '0.6rem 1.1rem',
              background: activeTab === t.key ? '#1565c0' : 'transparent',
              color: activeTab === t.key ? '#fff' : '#555',
              border: 'none',
              borderRadius: '6px 6px 0 0',
              cursor: 'pointer',
              fontWeight: activeTab === t.key ? 700 : 400,
              fontSize: 13,
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Operational */}
      {activeTab === 'operational' && (
        <OperationalReport companyId={companyId} payPeriodStart={start} payPeriodEnd={end} token={token} />
      )}

      {/* Attendance exceptions */}
      {activeTab === 'exceptions' && (
        <div>
          <button onClick={loadExceptions} disabled={exceptLoading || !companyId} style={runBtn}>
            {exceptLoading ? 'Loading…' : '▶ Load Exceptions'}
          </button>
          {exceptMsg && <div style={{ margin: '0.75rem 0', fontSize: 14, color: '#555' }}>{exceptMsg}</div>}
          {exceptions.length > 0 && (
            <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 2px 8px rgba(0,0,0,0.07)', overflow: 'hidden', marginTop: '0.5rem' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                <thead>
                  <tr style={{ background: '#1565c0', color: '#fff' }}>
                    <th style={th}>Employee</th>
                    <th style={th}>Date</th>
                    <th style={th}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {exceptions.map((ex, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #f0f0f0' }}>
                      <td style={td}>{empName(ex.employee_id)}</td>
                      <td style={td}>{ex.date}</td>
                      <td style={td}><span style={{ fontWeight: 600, color: '#e65100' }}>{ex.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Crosscheck */}
      {activeTab === 'crosscheck' && (
        <div>
          <button onClick={loadCrosscheck} disabled={crossLoading || !companyId} style={runBtn}>
            {crossLoading ? 'Loading…' : '▶ Run Crosscheck'}
          </button>
          {crossMsg && <div style={{ margin: '0.75rem 0', fontSize: 14, color: '#555' }}>{crossMsg}</div>}
          {crosscheck.length > 0 && (
            <div style={{ background: '#fff', borderRadius: 10, boxShadow: '0 2px 8px rgba(0,0,0,0.07)', overflow: 'hidden', marginTop: '0.5rem' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                <thead>
                  <tr style={{ background: '#1565c0', color: '#fff' }}>
                    <th style={th}>Employee</th>
                    <th style={th}>Issue</th>
                    <th style={th}>Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {crosscheck.map((d, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #f0f0f0' }}>
                      <td style={td}>{empName(d.employee_id)}</td>
                      <td style={td}><span style={{ color: '#e65100', fontWeight: 600 }}>{d.issue}</span></td>
                      <td style={td}>{d.detail || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Audit trail (admin only) */}
      {activeTab === 'audit' && isAdmin && (
        <AuditTrailViewer token={token} />
      )}
    </div>
  );
}

const lbl = { display: 'block', fontSize: 12, fontWeight: 600, color: '#555', marginBottom: 3 };
const inp = { padding: '0.45rem 0.6rem', border: '1px solid #ddd', borderRadius: 5, fontSize: 13 };
const runBtn = { padding: '0.55rem 1.1rem', background: '#1565c0', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14, fontWeight: 600 };
const th = { padding: '0.75rem 1rem', textAlign: 'left', fontWeight: 600 };
const td = { padding: '0.65rem 1rem', color: '#333' };
