import React, { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import { LoadingSpinner } from './components/common/LoadingSpinner';

// Layout
import { PatientLayout } from './components/layout/PatientLayout';
import { DoctorLayout } from './components/layout/DoctorLayout';
import { AdminLayout } from './components/layout/AdminLayout';

// Public Pages
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';

// Patient Pages
import { PatientDashboard } from './pages/PatientDashboard';
import { HealthCheckinPage } from './pages/HealthCheckinPage';
import { ScreeningResultPage } from './pages/ScreeningResultPage';
import { HealthMemoryPage } from './pages/HealthMemoryPage';
import { CareRoutePage } from './pages/CareRoutePage';
import { EmergencyPage } from './pages/EmergencyPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { MedicationsPage } from './pages/MedicationsPage';
import { AppointmentsPage } from './pages/AppointmentsPage';
import { PrescriptionsPage } from './pages/PrescriptionsPage';
import { PatientProfilePage } from './pages/PatientProfilePage';

// Doctor Pages
import { DoctorDashboard } from './pages/DoctorDashboard';
import { DoctorPatientView } from './pages/DoctorPatientView';
import { DoctorAppointmentsPage } from './pages/DoctorAppointmentsPage';

// Community Pages (lazy: pulls in Leaflet map tiles + Recharts)
const CommunityDashboard = lazy(() => import('./pages/CommunityDashboard').then(m => ({ default: m.CommunityDashboard })));
const CommunityMapPage = lazy(() => import('./pages/CommunityMapPage').then(m => ({ default: m.CommunityMapPage })));

// Admin Pages
import { AdminDashboard } from './pages/AdminDashboard';

function ProtectedRoute({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex items-center justify-center min-h-screen"><LoadingSpinner /></div>;
  if (!user) return <Navigate to="/login" />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" />;
  return <>{children}</>;
}

function App() {
  return (
    <Router>
      <Routes>
        {/* Public */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Patient Routes */}
        <Route path="/patient" element={<ProtectedRoute roles={['patient']}><PatientLayout /></ProtectedRoute>}>
          <Route index element={<PatientDashboard />} />
          <Route path="checkin" element={<HealthCheckinPage />} />
          <Route path="screening/:id" element={<ScreeningResultPage />} />
          <Route path="health-memory" element={<HealthMemoryPage />} />
          <Route path="care-route" element={<CareRoutePage />} />
          <Route path="emergency" element={<EmergencyPage />} />
          <Route path="documents" element={<DocumentsPage />} />
          <Route path="medications" element={<MedicationsPage />} />
          <Route path="prescriptions" element={<PrescriptionsPage />} />
          <Route path="appointments" element={<AppointmentsPage />} />
          <Route path="profile" element={<PatientProfilePage />} />
        </Route>

        {/* Doctor Routes */}
        <Route path="/doctor" element={<ProtectedRoute roles={['doctor']}><DoctorLayout /></ProtectedRoute>}>
          <Route index element={<DoctorDashboard />} />
          <Route path="appointments" element={<DoctorAppointmentsPage />} />
          <Route path="patients/:id" element={<DoctorPatientView />} />
        </Route>

        {/* Community Routes */}
        <Route path="/community" element={<ProtectedRoute roles={['admin', 'community_authority']}><AdminLayout /></ProtectedRoute>}>
          <Route index element={<Suspense fallback={<LoadingSpinner />}><CommunityDashboard /></Suspense>} />
          <Route path="map" element={<Suspense fallback={<LoadingSpinner />}><CommunityMapPage /></Suspense>} />
        </Route>

        {/* Admin Routes */}
        <Route path="/admin" element={<ProtectedRoute roles={['admin']}><AdminLayout /></ProtectedRoute>}>
          <Route index element={<AdminDashboard />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;
