import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { Layout } from '@/components/layout';
import { ProtectedRoute } from '@/components/common/ProtectedRoute';
import { useAuth } from '@/context/AuthContext';
import { LandingPage, LoginPage, RegisterPage, ForgotPasswordPage, EmailVerificationPage, MFAPage, ResetPasswordPage, DashboardPage, SearchPage, AIChatPage, DocumentsPage, DocumentViewerPage, HistoryPage, AnalyticsPage, SettingsPage, NotificationsPage, ProfilePage, OfflineLibraryPage, SavedSearchesPage } from '@/pages';
import AdminDashboard from '@/pages/AdminDashboard';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Public Route Component (redirects to dashboard if already authenticated)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return <>{children}</>;
};

export const AppRoutes: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
          <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
          <Route path="/forgot-password" element={<PublicRoute><ForgotPasswordPage /></PublicRoute>} />
          <Route path="/verify-email" element={<EmailVerificationPage />} />
          <Route path="/mfa" element={<MFAPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />

          {/* Protected routes */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Layout>
                <DashboardPage />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/search" element={
            <ProtectedRoute>
              <Layout>
                <SearchPage />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/ai-chat" element={
            <ProtectedRoute>
              <Layout>
                <AIChatPage />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/documents" element={
            <ProtectedRoute>
              <Layout>
                <DocumentsPage />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/documents/:id" element={
            <ProtectedRoute>
              <Layout>
                <DocumentViewerPage />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/history" element={
            <ProtectedRoute>
              <Layout>
                <HistoryPage />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/analytics" element={
            <ProtectedRoute>
              <Layout>
                <AnalyticsPage />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/settings" element={
            <ProtectedRoute>
              <Layout>
                <SettingsPage />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/notifications" element={
            <ProtectedRoute>
              <Layout>
                <NotificationsPage />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/profile" element={
            <ProtectedRoute>
              <Layout>
                <ProfilePage />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/saved-searches" element={
            <ProtectedRoute>
              <Layout>
                <SavedSearchesPage />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/offline-library" element={
            <ProtectedRoute>
              <Layout>
                <OfflineLibraryPage />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/admin" element={
            <ProtectedRoute>
              <Layout>
                <AdminDashboard />
              </Layout>
            </ProtectedRoute>
          } />

          {/* Catch all - redirect to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        
        {/* Toast notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: 'var(--color-surface-dark-secondary, #1F2937)',
              color: 'var(--color-text-dark-primary, #F3F4F6)',
            },
            success: {
              iconTheme: {
                primary: 'var(--color-success, #10B981)',
                secondary: 'var(--color-text-dark-primary, #F3F4F6)',
              },
            },
            error: {
              iconTheme: {
                primary: 'var(--color-error, #EF4444)',
                secondary: 'var(--color-text-dark-primary, #F3F4F6)',
              },
            },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  );
};