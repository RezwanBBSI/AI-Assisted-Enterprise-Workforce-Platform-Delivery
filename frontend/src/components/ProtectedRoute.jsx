import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children, requireAdmin = false, requireManager = false }) {
  const { token, isAdmin, isManager } = useAuth();

  if (!token) return <Navigate to="/login" replace />;
  if (requireAdmin && !isAdmin) return <Navigate to="/" replace />;
  if (requireManager && !isManager) return <Navigate to="/" replace />;

  return children;
}
