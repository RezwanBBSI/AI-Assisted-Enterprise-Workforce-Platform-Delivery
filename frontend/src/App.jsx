import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';

import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ClockInOutPage from './pages/ClockInOutPage';
import TimeEntriesPage from './pages/TimeEntriesPage';
import SchedulesPage from './pages/SchedulesPage';
import LeaveRequestsPage from './pages/LeaveRequestsPage';
import TimesheetsPage from './pages/TimesheetsPage';
import PayrollPage from './pages/PayrollPage';
import CompliancePage from './pages/CompliancePage';
import ReportsPage from './pages/ReportsPage';
import EmployeesPage from './pages/EmployeesPage';
import AdminSettingsPage from './pages/AdminSettingsPage';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected — all roles */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout><DashboardPage /></Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/clock"
            element={
              <ProtectedRoute>
                <Layout><ClockInOutPage /></Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/time-entries"
            element={
              <ProtectedRoute>
                <Layout><TimeEntriesPage /></Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/schedules"
            element={
              <ProtectedRoute>
                <Layout><SchedulesPage /></Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/leave"
            element={
              <ProtectedRoute>
                <Layout><LeaveRequestsPage /></Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/timesheets"
            element={
              <ProtectedRoute>
                <Layout><TimesheetsPage /></Layout>
              </ProtectedRoute>
            }
          />

          {/* Protected — Manager / Admin */}
          <Route
            path="/payroll"
            element={
              <ProtectedRoute requireManager>
                <Layout><PayrollPage /></Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/employees"
            element={
              <ProtectedRoute requireManager>
                <Layout><EmployeesPage /></Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/compliance"
            element={
              <ProtectedRoute requireManager>
                <Layout><CompliancePage /></Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/reports"
            element={
              <ProtectedRoute requireManager>
                <Layout><ReportsPage /></Layout>
              </ProtectedRoute>
            }
          />

          {/* Protected — Admin only */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute requireAdmin>
                <Layout><AdminSettingsPage /></Layout>
              </ProtectedRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
