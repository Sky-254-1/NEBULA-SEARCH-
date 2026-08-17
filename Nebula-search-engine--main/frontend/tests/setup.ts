import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(() => null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  key: vi.fn(() => null),
  length: 0,
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

// Mock crypto.randomUUID
Object.defineProperty(crypto, 'randomUUID', {
  value: vi.fn(() => 'test-uuid-' + Math.random()),
});

// Mock navigator.onLine
Object.defineProperty(navigator, 'onLine', {
  value: true,
});

// Block all network access during testing
const isDevelopment = () => process.env.NODE_ENV === 'development';

if (isDevelopment()) {
  // Mock fetch to reject all network requests
  global.fetch = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === 'string' ? input : input.url || 'unknown';
    const error = new Error(`Security: All network requests are blocked during tests. Attempted: ${url}`);
    error.name = 'SecurityError';
    throw error;
  });

  // Mock XMLHttpRequest to reject all requests
  global.XMLHttpRequest = vi.fn(() => {
    const mockXHR = {
      open: vi.fn(),
      send: vi.fn(),
      setRequestHeader: vi.fn(),
      abort: vi.fn(),
      getResponseHeader: vi.fn(),
      responseText: '',
      status: 0,
      readyState: 0,
      onload: null,
      onerror: null,
      onreadystatechange: null,
    };

    // Override open to block requests
    mockXHR.open = vi.fn((method: string, url: string, async?: boolean) => {
      const error = new Error(`Security: XMLHttpRequest blocked: ${url}`);
      error.name = 'SecurityError';
      throw error;
    });

    return mockXHR;
  });

  // Mock WebSocket to block connections
  global.WebSocket = vi.fn(() => {
    const mockWS = {
      send: vi.fn(),
      close: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      onerror: vi.fn(),
      onmessage: vi.fn(),
      onopen: vi.fn(),
      onclose: vi.fn(),
      readyState: 3, // CLOSED
    };

    mockWS.close = vi.fn(() => {});
    return mockWS;
  });

  // Block File System API
  Object.defineProperty(window, 'showOpenFilePicker', {
    value: vi.fn(() => Promise.reject(new Error('Security: File picker access blocked in test environment'))),
  });

  // Block clipboard API
  Object.defineProperty(navigator, 'clipboard', {
    value: {
      read: vi.fn(() => Promise.reject(new Error('Security: Clipboard access blocked in test environment'))),
      write: vi.fn(() => Promise.reject(new Error('Security: Clipboard access blocked in test environment'))),
    },
  });

  // Block screen capture API
  Object.defineProperty(window, 'getScreenDetails', {
    value: vi.fn(() => Promise.reject(new Error('Security: Screen capture API blocked in test environment'))),
  });

  // Block media capture
  Object.defineProperty(window.HTMLCanvasElement.prototype, 'toBlob', {
    value: vi.fn(() => Promise.reject(new Error('Security: Canvas operations blocked in test environment'))),
  });

  // Block File API
  global.File = vi.fn(() => {
    throw new Error('Security: File operations blocked in test environment');
  });

  // Block FileReader API
  global.FileReader = vi.fn(() => {
    const mockReader = {
      readAsText: vi.fn(),
      readAsArrayBuffer: vi.fn(),
      readAsDataURL: vi.fn(),
      error: null,
      onload: null,
      onloadend: null,
      onloadstart: null,
      onprogress: null,
      onerror: null,
    };

    mockReader.onload = vi.fn();
    return mockReader;
  });

  // Block FormData operations
  global.FormData = vi.fn(() => {
    return {
      append: vi.fn(),
      delete: vi.fn(),
      get: vi.fn(),
      getAll: vi.fn(),
      has: vi.fn(),
      set: vi.fn(),
      entries: vi.fn(() => []),
      forEach: vi.fn(),
    };
  });

  // Block ServiceWorker API
  Object.defineProperty(navigator, 'serviceWorker', {
    value: {
      register: vi.fn(() => Promise.reject(new Error('Security: Service Worker registration blocked in test environment'))),
      controller: null,
      ready: Promise.reject(new Error('Security: Service Worker API blocked')),
      getRegistrations: vi.fn(() => Promise.resolve([])),
    },
  });

  // Block Notification API
  if ('Notification' in window) {
    Object.defineProperty(window, 'Notification', {
      value: {
        requestPermission: vi.fn(() => Promise.resolve('denied')),
        permission: 'denied',
        Notification: vi.fn(() => {
          return {
            title: '',
            body: '',
            onclick: null,
            onerror: null,
          };
        }),
      },
    });
  }

  // Block Navigator connections
  Object.defineProperty(navigator, 'connection', {
    value: {
      effectiveType: 'unknown',
      type: 'unknown',
      downlink: 0,
      rtt: 0,
    },
  });

  // Block Proximity API
  Object.defineProperty(navigator, 'hapticFeedback', {
    value: vi.fn(() => {
      throw new Error('Security: Haptic feedback API blocked in test environment');
    }),
  });

  // Block URI handler
  Object.defineProperty(window, 'onmessage', {
    set: vi.fn(),
  });

  // Block postMessage restrictions
  window.postMessage = vi.fn((message, targetOrigin) => {
    if (targetOrigin && targetOrigin !== window.location.origin) {
      throw new Error(`Security: Cross-origin postMessage blocked: ${targetOrigin}`);
    }
    return;
  });
}

// Mock sensitive environment variables
Object.defineProperty(window, 'process', {
  value: {
    ...process,
    env: new Proxy(process.env, {
      get: (target, prop) => {
        if (prop.match(/^(API_KEY|SECRET|PASSWORD|TOKEN|KEY|PRIVATE|AUTH|JWT|CREDENTIAL|TOKEN)/i)) {
          return undefined;
        }
        return target[prop];
      },
      has: (target, prop) => {
        if (prop.match(/^(API_KEY|SECRET|PASSWORD|TOKEN|KEY|PRIVATE|AUTH|JWT|CREDENTIAL|TOKEN)/i)) {
          return false;
        }
        return prop in target;
      },
    }),
  },
});

// Block dynamic imports
const originalImport = global.import;
if (originalImport) {
  global.import = async (module: string) => {
    throw new Error(`Security: Dynamic import blocked: ${module}`);
  };
}

// Add security event listener for error tracking
window.addEventListener('error', (event) => {
  if (event.error && event.error.message.includes('Security:')) {
    console.error('[SECURITY]', event.error.message);
    event.preventDefault();
  }
});

window.addEventListener('unhandledrejection', (event) => {
  if (event.reason && event.reason.message && event.reason.message.includes('Security:')) {
    console.error('[SECURITY]', event.reason.message);
    event.preventDefault();
  }
});