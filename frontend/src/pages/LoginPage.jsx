import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (role) => {
    const accounts = {
      admin:    { email: 'admin@bbsi.demo',    password: 'Admin1234!' },
      manager:  { email: 'manager@bbsi.demo',  password: 'Manager1234!' },
      employee: { email: 'employee@bbsi.demo', password: 'Employee1234!' },
    };
    setEmail(accounts[role].email);
    setPassword(accounts[role].password);
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #1565c0 0%, #0d47a1 100%)',
      fontFamily: 'system-ui, sans-serif',
    }}>
      <div style={{
        background: '#fff',
        borderRadius: 12,
        padding: '2.5rem',
        width: 380,
        boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
      }}>
        <h1 style={{ margin: '0 0 0.25rem', fontSize: 24, color: '#0d47a1' }}>BBSI Workforce</h1>
        <p style={{ margin: '0 0 1.5rem', color: '#666', fontSize: 14 }}>Sign in to your account</p>

        {error && (
          <div style={{
            background: '#fdecea',
            border: '1px solid #f44336',
            borderRadius: 6,
            padding: '0.6rem 0.9rem',
            marginBottom: '1rem',
            color: '#c62828',
            fontSize: 14,
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <label style={labelStyle}>Email</label>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            style={inputStyle}
            placeholder="you@bbsi.demo"
          />

          <label style={labelStyle}>Password</label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            style={inputStyle}
            placeholder="••••••••"
          />

          <button type="submit" disabled={loading} style={btnStyle}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        {/* Demo quick-fill */}
        <div style={{ marginTop: '1.5rem', borderTop: '1px solid #eee', paddingTop: '1rem' }}>
          <p style={{ fontSize: 12, color: '#666', marginBottom: 8 }}>Demo accounts (click to fill):</p>
          <div style={{ display: 'flex', gap: 6 }}>
            {['admin', 'manager', 'employee'].map(r => (
              <button key={r} onClick={() => fillDemo(r)} style={demoBtn}>
                {r.charAt(0).toUpperCase() + r.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

const labelStyle = {
  display: 'block',
  fontSize: 13,
  fontWeight: 600,
  color: '#444',
  marginBottom: 4,
  marginTop: 12,
};

const inputStyle = {
  width: '100%',
  padding: '0.6rem 0.75rem',
  border: '1px solid #ddd',
  borderRadius: 6,
  fontSize: 14,
  boxSizing: 'border-box',
  outline: 'none',
};

const btnStyle = {
  width: '100%',
  marginTop: '1.25rem',
  padding: '0.75rem',
  background: '#1565c0',
  color: '#fff',
  border: 'none',
  borderRadius: 6,
  fontSize: 15,
  fontWeight: 600,
  cursor: 'pointer',
};

const demoBtn = {
  flex: 1,
  padding: '0.35rem',
  background: '#e3f2fd',
  border: '1px solid #90caf9',
  borderRadius: 4,
  fontSize: 12,
  cursor: 'pointer',
  color: '#1565c0',
  fontWeight: 600,
};
