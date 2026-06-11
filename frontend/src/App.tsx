import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';

// Auth pages
import LoginPage    from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ConfirmPage        from './pages/ConfirmPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage  from './pages/ResetPasswordPage';

// Portal pages
import AdminDashboard   from './pages/admin/AdminDashboard';
import DoctorDashboard  from './pages/doctor/DoctorDashboard';
import PatientDashboard from './pages/patient/PatientDashboard';

// Shared
import LoadingSpinner from './components/shared/LoadingSpinner';

function ProtectedRoute({
  children,
  allowedRoles,
}: {
  children: JSX.Element;
  allowedRoles: string[];
}) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingSpinner fullscreen />;
  if (!user)   return <Navigate to="/login" replace />;
  if (!allowedRoles.some((r) => user.groups.includes(r as never)))
    return <Navigate to="/unauthorized" replace />;
  return children;
}

function RoleRouter() {
  const { user, loading } = useAuth();
  if (loading) return <LoadingSpinner fullscreen />;
  if (!user)   return <Navigate to="/login" replace />;
  if (user.groups.includes('Admins'))   return <Navigate to="/admin"   replace />;
  if (user.groups.includes('Doctors'))  return <Navigate to="/doctor"  replace />;
  if (user.groups.includes('Patients')) return <Navigate to="/patient" replace />;
  return <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login"    element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/confirm"         element={<ConfirmPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password"  element={<ResetPasswordPage />} />
      <Route path="/"         element={<RoleRouter />} />

      {/* Admin portal */}
      <Route
        path="/admin/*"
        element={
          <ProtectedRoute allowedRoles={['Admins']}>
            <AdminDashboard />
          </ProtectedRoute>
        }
      />

      {/* Doctor portal */}
      <Route
        path="/doctor/*"
        element={
          <ProtectedRoute allowedRoles={['Doctors']}>
            <DoctorDashboard />
          </ProtectedRoute>
        }
      />

      {/* Patient portal */}
      <Route
        path="/patient/*"
        element={
          <ProtectedRoute allowedRoles={['Patients']}>
            <PatientDashboard />
          </ProtectedRoute>
        }
      />

      {/* Fallbacks */}
      <Route path="/unauthorized" element={
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-800">Access Denied</h1>
            <p className="text-gray-500 mt-2">You don't have permission to view this page.</p>
          </div>
        </div>
      } />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
