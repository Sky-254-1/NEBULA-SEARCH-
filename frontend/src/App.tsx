import React, { useEffect } from 'react';
import { AppRoutes } from '@/routes';
import { AuthProvider } from '@/context/AuthContext';
import ErrorBoundary from '@/components/ErrorBoundary';
import { setupGlobalErrorHandlers } from '@/utils/errorHandling';

function App() {
  // Initialize global error handlers
  useEffect(() => {
    setupGlobalErrorHandlers();
  }, []);

  // Global keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Cmd/Ctrl+K or / to focus search
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector<HTMLInputElement>(
          'input[type="text"], input[type="search"], input[placeholder*="Search"], input[placeholder*="search"]'
        );
        if (searchInput) {
          searchInput.focus();
          searchInput.select();
        }
      }
      // Escape to close modals or blur active element
      if (e.key === 'Escape') {
        const active = document.activeElement as HTMLElement;
        if (active && active.tagName === 'INPUT') {
          active.blur();
        }
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
