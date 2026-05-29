import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { getCompanies, getLocations, getPolicies } from '../api';

const TABS = ['Companies', 'Locations', 'Policies'];

export default function AdminSettingsPage() {
  const { token, companyId, isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState('Companies');

  return (
    <div>
      <h1 style={{ margin: '0 0 0.5rem', fontSize: 24, color: '#1a1a2e' }}>Admin Settings</h1>
      <p style={{ margin: '0 0 1.5rem', color: '#666', fontSize: 14 }}>
        Manage companies, locations, and company policies.
      </p>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: '1.5rem', borderBottom: '2px solid #e0e0e0' }}>
        {TABS.filter(t => t !== 'Companies' || isAdmin).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '0.5rem 1.25rem',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontSize: 14,
              fontWeight: activeTab === tab ? 700 : 400,
              color: activeTab === tab ? '#1565c0' : '#666',
              borderBottom: activeTab === tab ? '2px solid #1565c0' : '2px solid transparent',
              marginBottom: -2,
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'Companies' && <CompaniesTab token={token} />}
      {activeTab === 'Locations' && <LocationsTab token={token} companyId={companyId} />}
      {activeTab === 'Policies' && <PoliciesTab token={token} companyId={companyId} />}
    </div>
  );
}

function CompaniesTab({ token }) {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!token) return;
    getCompanies(token)
      .then(data => setCompanies(data.items || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return <p>Loading companies…</p>;

  return (
    <div>
      {error && <ErrorBox msg={error} />}
      <Table
        headers={['Name', 'ID', 'Status', 'Created']}
        rows={companies.map(c => [
          <strong>{c.name}</strong>,
          <code style={{ fontSize: 11, background: '#f5f5f5', padding: '2px 5px', borderRadius: 3 }}>{c.id}</code>,
          <ActiveBadge active={c.is_active} />,
          c.created_at?.slice(0, 10),
        ])}
        empty="No companies found."
      />
    </div>
  );
}

function LocationsTab({ token, companyId }) {
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!token || !companyId) return;
    getLocations(token, companyId)
      .then(data => setLocations(data.items || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [token, companyId]);

  if (loading) return <p>Loading locations…</p>;

  return (
    <div>
      {error && <ErrorBox msg={error} />}
      <Table
        headers={['Name', 'Timezone', 'Status', 'Created']}
        rows={locations.map(l => [
          <strong>{l.name}</strong>,
          l.timezone || '—',
          <ActiveBadge active={l.is_active} />,
          l.created_at?.slice(0, 10),
        ])}
        empty="No locations found."
      />
    </div>
  );
}

function PoliciesTab({ token, companyId }) {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!token || !companyId) return;
    getPolicies(token, companyId)
      .then(data => setPolicies(Array.isArray(data) ? data : []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [token, companyId]);

  if (loading) return <p>Loading policies…</p>;

  return (
    <div>
      {error && <ErrorBox msg={error} />}
      <Table
        headers={['Policy Key', 'Value', 'Updated By', 'Updated']}
        rows={policies.map(p => [
          <code style={{ fontSize: 12, background: '#f5f5f5', padding: '2px 6px', borderRadius: 3 }}>{p.policy_key}</code>,
          p.policy_value,
          p.updated_by || '—',
          p.updated_at?.slice(0, 10) || '—',
        ])}
        empty="No policies configured."
      />
    </div>
  );
}

/* ── Shared helpers ── */

function Table({ headers, rows, empty }) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14, background: '#fff', borderRadius: 8, overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.07)' }}>
        <thead style={{ background: '#f5f5f5' }}>
          <tr>
            {headers.map(h => (
              <th key={h} style={{ padding: '0.75rem 1rem', textAlign: 'left', fontWeight: 600, color: '#444', fontSize: 12, textTransform: 'uppercase' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr><td colSpan={headers.length} style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>{empty}</td></tr>
          ) : (
            rows.map((row, i) => (
              <tr key={i} style={{ borderTop: '1px solid #f0f0f0' }}>
                {row.map((cell, j) => (
                  <td key={j} style={{ padding: '0.75rem 1rem', color: '#444' }}>{cell}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function ActiveBadge({ active }) {
  return (
    <span style={{
      background: active ? '#e8f5e9' : '#fafafa',
      color: active ? '#2e7d32' : '#595959',
      padding: '2px 10px',
      borderRadius: 12,
      fontSize: 12,
      fontWeight: 600,
    }}>
      {active ? 'Active' : 'Inactive'}
    </span>
  );
}

function ErrorBox({ msg }) {
  return (
    <div style={{ background: '#ffebee', color: '#c62828', padding: '0.75rem 1rem', borderRadius: 6, marginBottom: '1rem', fontSize: 14 }}>
      {msg}
    </div>
  );
}
