import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout } from './components/Layout';
import { HomePage } from './pages/HomePage';
import { LoginPage } from './pages/LoginPage';
import { PrescriptionsListPage } from './pages/PrescriptionsListPage';
import { UploadPrescriptionPage } from './pages/UploadPrescriptionPage';
import { AnalysisDetailPage } from './pages/AnalysisDetailPage';
import { ReviewQueuePage } from './pages/ReviewQueuePage';
import { SystemHealthPage } from './pages/SystemHealthPage';
import { PatientSearchPage } from './pages/PatientSearchPage';
import { PatientTimelinePage } from './pages/PatientTimelinePage';
import { PatientPortalPage } from './pages/PatientPortalPage';
import { Role } from './types/api';
import { ShieldAlert, RefreshCw } from 'lucide-react';

const ProtectedRoute: React.FC<{
  children: React.ReactNode;
  allowedRoles?: Role[];
  disallowPatient?: boolean;
  patientsOnly?: boolean;
}> = ({ children, allowedRoles, disallowPatient, patientsOnly }) => {
  const { session, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-teal-600 animate-spin mx-auto mb-3" />
          <div className="text-xs font-semibold text-slate-600">Verifying Clinical Session...</div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !session) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Privacy Protection: Patients cannot access clinical doctor searches or internal tools
  if (disallowPatient && session.is_patient) {
    return <Navigate to="/patient-portal" replace />;
  }

  // Redirect staff to clinical workspace if they attempt to view patient-only portal
  if (patientsOnly && !session.is_patient) {
    return <Navigate to="/prescriptions" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(session.role)) {
    return (
      <div className="max-w-md mx-auto my-16 bg-white border border-rose-200 rounded-2xl p-8 text-center shadow-sm space-y-4">
        <ShieldAlert className="w-12 h-12 text-rose-500 mx-auto" />
        <h3 className="text-base font-bold text-slate-900">Restricted Clinical Section</h3>
        <p className="text-xs text-slate-600 leading-relaxed">
          This section requires <span className="font-semibold text-teal-700">{allowedRoles.join(' or ')}</span> authorization.
          Your current session is logged in as <span className="font-semibold text-rose-600">{session.role}</span>.
        </p>
      </div>
    );
  }

  return <>{children}</>;
};

import { LanguageProvider } from './context/LanguageContext';
import { ErrorBoundary } from './components/ErrorBoundary';

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <LanguageProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
          {/* Public Modern 3D Dynamic Landing Page */}
          <Route path="/" element={<HomePage />} />

          {/* Unified Login (Patient OTP + Doctor Credential) */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected Clinical Workflows */}
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            {/* Dedicated Patient Portal Dashboard */}
            <Route
              path="patient-portal"
              element={
                <ProtectedRoute patientsOnly>
                  <PatientPortalPage />
                </ProtectedRoute>
              }
            />

            {/* Doctor & Clinical Staff Prescriptions Ledger */}
            <Route
              path="prescriptions"
              element={
                <ProtectedRoute disallowPatient>
                  <PrescriptionsListPage />
                </ProtectedRoute>
              }
            />

            {/* Prescriptions Upload Intake */}
            <Route path="upload" element={<UploadPrescriptionPage />} />

            {/* Doctor-Wide Patient Search & Lookup */}
            <Route
              path="patients"
              element={
                <ProtectedRoute disallowPatient allowedRoles={['DOCTOR', 'REVIEWER', 'ADMIN']}>
                  <PatientSearchPage />
                </ProtectedRoute>
              }
            />

            {/* Patient Medical Timeline Dossier */}
            <Route path="patients/:id" element={<PatientTimelinePage />} />

            {/* Analysis & In-Line Prescription Correction */}
            <Route path="analyses/:id" element={<AnalysisDetailPage />} />

            {/* Clinical Reviewer Sign-Off Queue */}
            <Route
              path="review-queue"
              element={
                <ProtectedRoute disallowPatient allowedRoles={['REVIEWER', 'ADMIN']}>
                  <ReviewQueuePage />
                </ProtectedRoute>
              }
            />

            {/* Diagnostics & Architecture Probes (Admin Only) */}
            <Route
              path="health"
              element={
                <ProtectedRoute disallowPatient allowedRoles={['ADMIN']}>
                  <SystemHealthPage />
                </ProtectedRoute>
              }
            />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
    </LanguageProvider>
    </ErrorBoundary>
  );
};

export default App;
