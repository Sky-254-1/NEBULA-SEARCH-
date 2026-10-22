import { lazy, Suspense } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import { SearchProvider } from './state/SearchContext';
import { HomePage } from './pages/HomePage';
import './styles/app.css';

const HistoryPage = lazy(() =>
  import('./pages/HistoryPage').then((m) => ({ default: m.HistoryPage }))
);

function PageLoader() {
  return (
    <div className="page-loading" aria-busy="true">
      <div className="skeleton-card" style={{ width: 240, margin: '4rem auto' }} />
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <SearchProvider>
          <BrowserRouter>
            <Suspense fallback={<PageLoader />}>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/history" element={<HistoryPage />} />
                <Route path="/legacy" element={<LegacyRedirect />} />
              </Routes>
            </Suspense>
          </BrowserRouter>
        </SearchProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

function LegacyRedirect() {
  window.location.href = '/legacy/index.html';
  return null;
}
