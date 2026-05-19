import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getTimeEntries, getLeaveRequests, getTimesheets, getMissingPunches } from '../api';

function StatCard({ label, value, color, to }) {
  const card = (
    <div style={{
      background: '#fff',
      borderRadius: 10,
      padding: '1.25rem 1.5rem',
      boxShadow: '0 2px 8px rgba(0,0,0,0.07)',
      borderLeft: `4px solid ${color}`,
      minWidth: 160,
      flex: 1,
    }}>
      <div style={{ fontSize: 28, fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: 13, color: '#666', marginTop: 4 }}>{label}</div>
    </div>
  );
  return to ? <Link to={to} style={{ textDecoration: 'none' }}>{card}</Link> : card;
}

export default function DashboardPage() {
  const { token, user, companyId, isManager } = useAuth();
  const [stats, setStats] = useState({ openEntry: null, pendingLeave: 0, timesheets: 0, missingPunches: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    const load = async () => {
      try {
        const [entries, leave, sheets] = await Promise.all([
          getTimeEntries(token, 1, 5),
          getLeaveRequests(token, 1, 50),
          getTimesheets(token, 1, 50),
        ]);

        const openEntry = entries.items?.find(e => e.status === 'open') || null;
        const pendingLeave = leave.items?.filter(l => l.status === 'pending').length || 0;
        const timesheets = sheets.total || 0;

        let missingPunches = 0;
        if (isManager && companyId) {
          try {
            const mp = await getMissingPunches(token, companyId);
            missingPunches = mp.length || 0;
          } catch (_) {}
        }

        setStats({ openEntry, pendingLeave, timesheets, missingPunches });
      } catch (_) {}
      setLoading(false);
    };
    load();
  }, [token, companyId, isManager]);

  if (loading) return <p>Loading dashboard…</p>;

  const now = new Date();
  const greeting = now.getHours() < 12 ? 'Good morning' : now.getHours() < 18 ? 'Good afternoon' : 'Good evening';

  return (
    <div>
      <h1 style={{ margin: '0 0 0.25rem', fontSize: 26, color: '#1a1a2e' }}>
        {greeting}, {user?.full_name?.split(' ')[0] || 'there'} 👋
      </h1>
      <p style={{ margin: '0 0 2rem', color: '#666' }}>
        {now.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
      </p>

      {/* Quick stats */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: '2rem' }}>
        <StatCard
          label={stats.openEntry ? '⏱ Currently Clocked In' : '⚪ Not Clocked In'}
          value={stats.openEntry ? 'Active' : '—'}
          color={stats.openEntry ? '#4caf50' : '#9e9e9e'}
          to="/clock"
        />
        <StatCard
          label="Pending Leave Requests"
          value={stats.pendingLeave}
          color="#ff9800"
          to="/leave"
        />
        <StatCard
          label="Total Timesheets"
          value={stats.timesheets}
          color="#1565c0"
          to="/timesheets"
        />
        {isManager && (
          <StatCard
            label="Missing Punches"
            value={stats.missingPunches}
            color={stats.missingPunches > 0 ? '#f44336' : '#4caf50'}
            to="/time-entries"
          />
        )}
      </div>

      {/* Quick Actions */}
      <div style={{ background: '#fff', borderRadius: 10, padding: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.07)', marginBottom: '1.5rem' }}>
        <h2 style={{ margin: '0 0 1rem', fontSize: 17, color: '#333' }}>Quick Actions</h2>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <QuickBtn to="/clock" label="Clock In / Out" color="#1565c0" />
          <QuickBtn to="/leave" label="Request Leave" color="#7b1fa2" />
          <QuickBtn to="/timesheets" label="View Timesheets" color="#00838f" />
          {isManager && <QuickBtn to="/compliance" label="Run Compliance Check" color="#e64a19" />}
        </div>
      </div>

      {/* Role info */}
      <div style={{ background: '#e3f2fd', borderRadius: 10, padding: '1rem 1.5rem' }}>
        <p style={{ margin: 0, fontSize: 13, color: '#1565c0' }}>
          Logged in as <strong>{user?.email}</strong> · Company ID: <code style={{ background: '#fff', padding: '1px 4px', borderRadius: 3 }}>{companyId || 'N/A'}</code>
        </p>
      </div>
    </div>
  );
}

function QuickBtn({ to, label, color }) {
  return (
    <Link
      to={to}
      style={{
        display: 'inline-block',
        padding: '0.6rem 1.2rem',
        background: color,
        color: '#fff',
        borderRadius: 6,
        textDecoration: 'none',
        fontSize: 14,
        fontWeight: 600,
      }}
    >
      {label}
    </Link>
  );
}
