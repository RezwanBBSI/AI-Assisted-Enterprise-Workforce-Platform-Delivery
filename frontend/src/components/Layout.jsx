import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NAV_LINKS = [
  { to: '/',               label: '🏠 Dashboard',     roles: ['Admin', 'Manager', 'Employee'] },
  { to: '/clock',          label: '⏱ Clock In/Out',   roles: ['Admin', 'Manager', 'Employee'] },
  { to: '/time-entries',   label: '📋 Time Entries',   roles: ['Admin', 'Manager', 'Employee'] },
  { to: '/schedules',      label: '📅 Schedules',      roles: ['Admin', 'Manager', 'Employee'] },
  { to: '/leave',          label: '🌴 Leave',          roles: ['Admin', 'Manager', 'Employee'] },
  { to: '/timesheets',     label: '💰 Timesheets',     roles: ['Admin', 'Manager', 'Employee'] },
  { to: '/compliance',     label: '⚠️ Compliance',     roles: ['Admin', 'Manager'] },
  { to: '/reports',        label: '📊 Reports',        roles: ['Admin', 'Manager'] },
];

const sidebarStyle = {
  width: 220,
  minHeight: '100vh',
  background: '#1565c0',
  color: '#fff',
  display: 'flex',
  flexDirection: 'column',
  padding: '1.5rem 0',
  flexShrink: 0,
};

const logoStyle = {
  padding: '0 1.25rem 1.5rem',
  borderBottom: '1px solid rgba(255,255,255,0.15)',
  marginBottom: '0.75rem',
};

const linkStyle = {
  display: 'block',
  padding: '0.6rem 1.25rem',
  color: 'rgba(255,255,255,0.8)',
  textDecoration: 'none',
  fontSize: 14,
  borderRadius: 6,
  margin: '2px 0.5rem',
  transition: 'background 0.15s',
};

const activeLinkStyle = {
  ...linkStyle,
  background: 'rgba(255,255,255,0.2)',
  color: '#fff',
  fontWeight: 600,
};

export default function Layout({ children }) {
  const { user, role, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const visibleLinks = NAV_LINKS.filter(l => !role || l.roles.includes(role));

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: 'system-ui, sans-serif' }}>
      {/* Sidebar */}
      <nav style={sidebarStyle}>
        <div style={logoStyle}>
          <div style={{ fontWeight: 700, fontSize: 16 }}>BBSI Workforce</div>
          <div style={{ fontSize: 12, opacity: 0.7, marginTop: 2 }}>{role || '—'}</div>
        </div>

        {visibleLinks.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => (isActive ? activeLinkStyle : linkStyle)}
          >
            {label}
          </NavLink>
        ))}

        <div style={{ marginTop: 'auto', padding: '1rem 1.25rem', borderTop: '1px solid rgba(255,255,255,0.15)' }}>
          <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 4 }}>{user?.email}</div>
          <button
            onClick={handleLogout}
            style={{
              background: 'rgba(255,255,255,0.15)',
              border: 'none',
              color: '#fff',
              padding: '0.4rem 0.8rem',
              borderRadius: 4,
              cursor: 'pointer',
              fontSize: 13,
              width: '100%',
            }}
          >
            Sign Out
          </button>
        </div>
      </nav>

      {/* Main content */}
      <main style={{ flex: 1, padding: '2rem', background: '#f5f6fa', overflowY: 'auto' }}>
        {children}
      </main>
    </div>
  );
}
