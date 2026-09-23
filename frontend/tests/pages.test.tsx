import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import React from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { QueryClient } from '@tanstack/react-query';

const queryClient = new QueryClient();

const withProviders = (component: React.ReactElement) => render(
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      {component}
    </BrowserRouter>
  </QueryClientProvider>
);

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => React.createElement('div', props, children),
    span: ({ children, ...props }: any) => React.createElement('span', props, children),
  },
  AnimatePresence: ({ children }: any) => React.createElement(React.Fragment, null, children),
}));

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  Search: () => React.createElement('svg', { 'data-testid': 'search-icon' }),
  Bookmark: () => React.createElement('svg', { 'data-testid': 'bookmark-icon' }),
  Trash2: () => React.createElement('svg', { 'data-testid': 'trash-icon' }),
  Play: () => React.createElement('svg', { 'data-testid': 'play-icon' }),
  Plus: () => React.createElement('svg', { 'data-testid': 'plus-icon' }),
  X: () => React.createElement('svg', { 'data-testid': 'x-icon' }),
  Mail: () => React.createElement('svg', { 'data-testid': 'mail-icon' }),
  ArrowLeft: () => React.createElement('svg', { 'data-testid': 'arrow-left-icon' }),
  CheckCircle: () => React.createElement('svg', { 'data-testid': 'check-circle-icon' }),
  XCircle: () => React.createElement('svg', { 'data-testid': 'x-circle-icon' }),
  Loader2: () => React.createElement('svg', { 'data-testid': 'loader-icon' }),
  Lock: () => React.createElement('svg', { 'data-testid': 'lock-icon' }),
  Shield: () => React.createElement('svg', { 'data-testid': 'shield-icon' }),
  KeyRound: () => React.createElement('svg', { 'data-testid': 'key-icon' }),
  FileText: () => React.createElement('svg', { 'data-testid': 'file-text-icon' }),
  Download: () => React.createElement('svg', { 'data-testid': 'download-icon' }),
  Share2: () => React.createElement('svg', { 'data-testid': 'share-icon' }),
  ZoomIn: () => React.createElement('svg', { 'data-testid': 'zoom-in-icon' }),
  ZoomOut: () => React.createElement('svg', { 'data-testid': 'zoom-out-icon' }),
  Maximize: () => React.createElement('svg', { 'data-testid': 'maximize-icon' }),
  Bell: () => React.createElement('svg', { 'data-testid': 'bell-icon' }),
  Check: () => React.createElement('svg', { 'data-testid': 'check-icon' }),
  CheckCheck: () => React.createElement('svg', { 'data-testid': 'check-check-icon' }),
  Upload: () => React.createElement('svg', { 'data-testid': 'upload-icon' }),
  History: () => React.createElement('svg', { 'data-testid': 'history-icon' }),
}));

// Mock saved-searches API
vi.mock('@/api/saved-searches', () => ({
  savedSearchesApi: {
    list: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
  },
}));

// Mock @/state
vi.mock('@/state', () => ({
  useNotificationStore: () => ({
    notifications: [],
    unreadCount: 0,
    isLoading: false,
    fetchNotifications: vi.fn(),
    markAsRead: vi.fn(),
    markAllAsRead: vi.fn(),
  }),
  useDocumentStore: () => ({
    documents: [],
    isLoading: false,
    uploadProgress: 0,
    error: null,
    fetchDocuments: vi.fn(),
    uploadDocument: vi.fn(),
    deleteDocument: vi.fn(),
    clearError: vi.fn(),
  }),
}));

// Mock @/types
vi.mock('@/types', () => ({}));

// ============================================
// ForgotPasswordPage Tests
// ============================================
describe('ForgotPasswordPage', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('renders the forgot password form', async () => {
    const { ForgotPasswordPage } = await import('@/pages/ForgotPasswordPage');
    render(
      <BrowserRouter>
        <ForgotPasswordPage />
      </BrowserRouter>
    );

    expect(screen.getByText('Forgot Password?')).toBeDefined();
    expect(screen.getByPlaceholderText('you@example.com')).toBeDefined();
    expect(screen.getByText('Send Reset Link')).toBeDefined();
  });

  it('shows success state after submitting email', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true });
    
    const { ForgotPasswordPage } = await import('@/pages/ForgotPasswordPage');
    render(
      <BrowserRouter>
        <ForgotPasswordPage />
      </BrowserRouter>
    );

    const input = screen.getByPlaceholderText('you@example.com');
    await userEvent.type(input, 'test@example.com');
    
    const button = screen.getByText('Send Reset Link');
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText('Check Your Email')).toBeDefined();
    });
  });

  it('shows error on failed submission', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));
    
    const { ForgotPasswordPage } = await import('@/pages/ForgotPasswordPage');
    render(
      <BrowserRouter>
        <ForgotPasswordPage />
      </BrowserRouter>
    );

    const input = screen.getByPlaceholderText('you@example.com');
    await userEvent.type(input, 'test@example.com');
    
    const button = screen.getByText('Send Reset Link');
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText('Forgot Password?')).toBeDefined();
    });
  });
});

// ============================================
// EmailVerificationPage Tests
// ============================================
describe('EmailVerificationPage', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('shows error when no token provided', async () => {
    const { EmailVerificationPage } = await import('@/pages/EmailVerificationPage');
    render(
      <BrowserRouter>
        <EmailVerificationPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Verification Failed')).toBeDefined();
    });
  });

  it('shows success when verification succeeds', async () => {
    mockFetch.mockResolvedValueOnce({ ok: true });
    
    const { EmailVerificationPage } = await import('@/pages/EmailVerificationPage');
    render(
      <MemoryRouter initialEntries={['/verify-email?token=valid-token']}>
        <EmailVerificationPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Email Verified!')).toBeDefined();
    });
  });
});

// ============================================
// MFAPage Tests
// ============================================
describe('MFAPage', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('renders the MFA form', async () => {
    const { MFAPage } = await import('@/pages/MFAPage');
    render(
      <BrowserRouter>
        <MFAPage />
      </BrowserRouter>
    );

    expect(screen.getByText('Two-Factor Authentication')).toBeDefined();
    expect(screen.getByPlaceholderText('000000')).toBeDefined();
    expect(screen.getByText('Verify Code')).toBeDefined();
  });

  it('accepts 6-digit code input', async () => {
    const { MFAPage } = await import('@/pages/MFAPage');
    render(
      <BrowserRouter>
        <MFAPage />
      </BrowserRouter>
    );

    const input = screen.getByPlaceholderText('000000') as HTMLInputElement;
    await userEvent.type(input, '123456');
    
    expect(input.value).toBe('123456');
  });

  it('only accepts numeric input', async () => {
    const { MFAPage } = await import('@/pages/MFAPage');
    render(
      <BrowserRouter>
        <MFAPage />
      </BrowserRouter>
    );

    const input = screen.getByPlaceholderText('000000') as HTMLInputElement;
    await userEvent.type(input, 'abc123def');
    
    expect(input.value).toBe('123');
  });
});

// ============================================
// ResetPasswordPage Tests
// ============================================
describe('ResetPasswordPage', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('shows error when no token in URL', async () => {
    const { ResetPasswordPage } = await import('@/pages/ResetPasswordPage');
    withProviders(<ResetPasswordPage />);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /invalid reset link/i })).toBeDefined();
      expect(screen.getByText('Request a new reset link')).toBeDefined();
    });
  });
});

// ============================================
// BottomNav Tests
// ============================================
describe('BottomNav', () => {
  it('renders all navigation items', async () => {
    const { BottomNav } = await import('@/components/layout/BottomNav');
    render(
      <BrowserRouter>
        <BottomNav />
      </BrowserRouter>
    );

    expect(screen.getByText('Search')).toBeDefined();
    expect(screen.getByText('AI Chat')).toBeDefined();
    expect(screen.getByText('Documents')).toBeDefined();
    expect(screen.getByText('History')).toBeDefined();
    expect(screen.getByText('Alerts')).toBeDefined();
  });

  it('has correct aria-labels', async () => {
    const { BottomNav } = await import('@/components/layout/BottomNav');
    render(
      <BrowserRouter>
        <BottomNav />
      </BrowserRouter>
    );

    expect(screen.getByLabelText('Search')).toBeDefined();
    expect(screen.getByLabelText('AI Chat')).toBeDefined();
    expect(screen.getByLabelText('Documents')).toBeDefined();
    expect(screen.getByLabelText('History')).toBeDefined();
    expect(screen.getByLabelText('Alerts')).toBeDefined();
  });
});