import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import ComplianceDashboard from '../components/ComplianceDashboard';
import ViolationsTable from '../components/ViolationsTable';
import { runCompliance } from '../api';

function todayMinus(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

export default function CompliancePage() {
  const { token, companyId } = useAuth();
  const [start, setStart] = useState(todayMinus(14));
  const [end, setEnd] = useState(todayMinus(1));
  const [runResult, setRunResult] = useState(null);
  const [running, setRunning] = useState(false);
  const [runMsg, setRunMsg] = useState(null);
  const [activeTab, setActiveTab] = useState('violations');

  const handleRun = async () => {
    setRunning(true);
    setRunMsg(null);
    try {
      const result = await runCompliance(token, companyId, start, end);
      setRunResult(result);
      setRunMsg(`✅ Found ${result.new_violations} new violation(s)`);
    } catch (err) {
      setRunMsg(`Error: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div>
      <h1 style={{ margin: '0 0 1.5rem', fontSize: 24, color: '#1a1a2e' }}>Compliance</h1>

      {/* Run validation controls */}
      <div style={{ background: '#fff', borderRadius: 10, padding: '1.25rem', marginBottom: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.07)' }}>
        <h3 style={{ margin: '0 0 0.75rem', fontSize: 15 }}>Run Compliance Validation</h3>
        <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div>
            <label style={lbl}>Pay Period Start</label>
            <input type="date" value={start} onChange={e => setStart(e.target.value)} style={inp} />
          </div>
          <div>
            <label style={lbl}>Pay Period End</label>
            <input type="date" value={end} onChange={e => setEnd(e.target.value)} style={inp} />
          </div>
          <button onClick={handleRun} disabled={running || !companyId} style={actionBtn}>
            {running ? 'Running…' : '▶ Run Validation'}
          </button>
        </div>
        {runMsg && (
          <div style={{ marginTop: '0.75rem', color: runMsg.startsWith('Error') ? '#c62828' : '#2e7d32', fontWeight: 600 }}>
            {runMsg}
          </div>
        )}
        {runResult && (
          <div style={{ marginTop: '0.5rem', fontSize: 13, color: '#555' }}>
            Checked: {runResult.entries_checked} entries · {runResult.shifts_checked} shifts ·{' '}
            {runResult.timesheets_checked} timesheets
          </div>
        )}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '2px solid #e0e0e0', marginBottom: '1.5rem', gap: 4 }}>
        {['violations', 'dashboard'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '0.6rem 1.2rem',
              background: activeTab === tab ? '#1565c0' : 'transparent',
              color: activeTab === tab ? '#fff' : '#555',
              border: 'none',
              borderRadius: '6px 6px 0 0',
              cursor: 'pointer',
              fontWeight: activeTab === tab ? 700 : 400,
              fontSize: 14,
            }}
          >
            {tab === 'violations' ? '⚠️ Violations' : '📊 Dashboard'}
          </button>
        ))}
      </div>

      {activeTab === 'violations' && <ViolationsTable companyId={companyId} token={token} />}
      {activeTab === 'dashboard' && (
        <ComplianceDashboard
          companyId={companyId}
          payPeriodStart={start}
          payPeriodEnd={end}
          token={token}
        />
      )}
    </div>
  );
}

const lbl = { display: 'block', fontSize: 12, fontWeight: 600, color: '#555', marginBottom: 3 };
const inp = { padding: '0.45rem 0.6rem', border: '1px solid #ddd', borderRadius: 5, fontSize: 13 };
const actionBtn = { padding: '0.55rem 1.1rem', background: '#e64a19', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14, fontWeight: 600 };
