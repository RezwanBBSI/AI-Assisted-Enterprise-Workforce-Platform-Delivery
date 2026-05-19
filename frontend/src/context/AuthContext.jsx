import { createContext, useContext, useState, useCallback } from 'react';
import { login as apiLogin, getMe } from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('wf_token') || null);
  const [user, setUser] = useState(() => {
    const u = localStorage.getItem('wf_user');
    return u ? JSON.parse(u) : null;
  });
  const [companyId, setCompanyId] = useState(() => localStorage.getItem('wf_company') || null);

  const login = useCallback(async (email, password) => {
    const data = await apiLogin(email, password);
    const tok = data.access_token;
    localStorage.setItem('wf_token', tok);
    setToken(tok);

    const me = await getMe(tok);
    localStorage.setItem('wf_user', JSON.stringify(me));
    setUser(me);

    // Pick the first company from the user's roles
    const cid = me.roles?.[0]?.company_id || null;
    if (cid) {
      localStorage.setItem('wf_company', cid);
      setCompanyId(cid);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('wf_token');
    localStorage.removeItem('wf_user');
    localStorage.removeItem('wf_company');
    setToken(null);
    setUser(null);
    setCompanyId(null);
  }, []);

  // Derive role from user.roles
  const role = user?.roles?.[0]?.role_name || null;
  const isAdmin = role === 'Admin';
  const isManager = role === 'Manager' || role === 'Admin';

  return (
    <AuthContext.Provider value={{ token, user, companyId, role, isAdmin, isManager, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
