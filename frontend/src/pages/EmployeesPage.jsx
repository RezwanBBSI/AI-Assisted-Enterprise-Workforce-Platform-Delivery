import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { getEmployees } from '../api';

const roleBadge = {
  Admin:    { background: '#fce4ec', color: '#c62828' },
  Manager:  { background: '#e8eaf6', color: '#283593' },
  Employee: { background: '#e8f5e9', color: '#2e7d32' },
};

export default function EmployeesPage() {
  const { token, companyId } = useAuth();
  const [employees, setEmployees] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const size = 20;

  useEffect(() => {
    if (!token || !companyId) return;
    setLoading(true);
    getEmployees(token, companyId, page, size)
      .then(data => {
        setEmployees(data.items || []);
        setTotal(data.total || 0);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [token, companyId, page]);

  const filtered = search.trim()
    ? employees.filter(e =>
        e.full_name?.toLowerCase().includes(search.toLowerCase()) ||
        e.email?.toLowerCase().includes(search.toLowerCase())
      )
    : employees;

  const totalPages = Math.ceil(total / size);

  return (
    <div>
      <h1 style={{ margin: '0 0 0.5rem', fontSize: 24, color: '#1a1a2e' }}>Employees</h1>
      <p style={{ margin: '0 0 1.5rem', color: '#666', fontSize: 14 }}>
        {total} employee{total !== 1 ? 's' : ''} in this company
      </p>

      {error && (
        <div style={{ background: '#ffebee', color: '#c62828', padding: '0.75rem 1rem', borderRadius: 6, marginBottom: '1rem', fontSize: 14 }}>
          {error}
        </div>
      )}

      {/* Search */}
      <div style={{ marginBottom: '1rem' }}>
        <input
          type="text"
          placeholder="Search by name or email…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: 6,
            border: '1px solid #ddd',
            fontSize: 14,
            width: '100%',
            maxWidth: 360,
            boxSizing: 'border-box',
          }}
        />
      </div>

      {loading ? (
        <p>Loading…</p>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14, background: '#fff', borderRadius: 8, overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.07)' }}>
            <thead style={{ background: '#f5f5f5' }}>
              <tr>
                {['Name', 'Email', 'Role', 'Status'].map(h => (
                  <th key={h} style={{ padding: '0.75rem 1rem', textAlign: 'left', fontWeight: 600, color: '#444', fontSize: 12, textTransform: 'uppercase' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={4} style={{ padding: '2rem', textAlign: 'center', color: '#999' }}>
                    {search ? 'No employees match your search.' : 'No employees found.'}
                  </td>
                </tr>
              )}
              {filtered.map(emp => {
                const roleName = emp.roles?.[0]?.role_name || 'Unknown';
                const badge = roleBadge[roleName] || { background: '#f5f5f5', color: '#555' };
                return (
                  <tr key={emp.id} style={{ borderTop: '1px solid #f0f0f0' }}>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 500, color: '#1a1a2e' }}>
                      {emp.full_name}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: '#555' }}>{emp.email}</td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <span style={{ ...badge, padding: '2px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600 }}>
                        {roleName}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }}>
                      <span style={{
                        background: emp.is_active ? '#e8f5e9' : '#fafafa',
                        color: emp.is_active ? '#2e7d32' : '#999',
                        padding: '2px 10px',
                        borderRadius: 12,
                        fontSize: 12,
                        fontWeight: 600,
                      }}>
                        {emp.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', gap: 8, marginTop: '1rem', alignItems: 'center' }}>
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            style={pageBtnStyle(page !== 1)}
          >
            ← Prev
          </button>
          <span style={{ fontSize: 13, color: '#666' }}>Page {page} of {totalPages}</span>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            style={pageBtnStyle(page !== totalPages)}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}

function pageBtnStyle(enabled) {
  return {
    padding: '5px 14px',
    borderRadius: 5,
    border: '1px solid #ddd',
    background: enabled ? '#1565c0' : '#f5f5f5',
    color: enabled ? '#fff' : '#bbb',
    cursor: enabled ? 'pointer' : 'not-allowed',
    fontSize: 13,
  };
}
