# Nebula Search Frontend

Production-ready React frontend for the Nebula Search Engine.

## Features

- **Modern UI/UX**: Built with React 19, TypeScript, and TailwindCSS
- **Authentication**: JWT-based auth with auto-refresh
- **Search**: Web search, hybrid search, and semantic search
- **AI Chat**: Streaming AI responses with markdown rendering
- **Document Management**: Upload, view, and manage documents
- **Analytics**: Comprehensive usage and performance metrics
- **Offline Support**: IndexedDB caching and background sync
- **PWA**: Installable with offline capabilities
- **Dark Mode**: Full dark/light theme support
- **Responsive**: Mobile-first design

## Tech Stack

- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **React Router** - Routing
- **TanStack Query** - Data fetching and caching
- **Zustand** - State management
- **Axios** - HTTP client
- **Framer Motion** - Animations
- **Lucide React** - Icons
- **React Markdown** - Markdown rendering
- **Recharts** - Charts and analytics
- **IndexedDB (idb)** - Offline storage
- **PWA** - Progressive Web App

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API service layer
│   │   ├── client.ts     # Axios client with interceptors
│   │   ├── auth.ts       # Authentication API
│   │   ├── search.ts     # Search API
│   │   ├── ai.ts         # AI chat API
│   │   ├── storage.ts    # Document storage API
│   │   ├── vector.ts     # Vector search API
│   │   ├── analytics.ts  # Analytics API
│   │   └── features.ts   # Features API (bookmarks, collections, etc.)
│   ├── assets/           # Images, fonts, etc.
│   ├── auth/             # Authentication components
│   ├── components/       # Reusable components
│   │   ├── common/       # Common UI components
│   │   ├── layout/       # Layout components
│   │   ├── search/       # Search components
│   │   ├── ai/           # AI chat components
│   │   ├── upload/       # Upload components
│   │   ├── analytics/    # Analytics components
│   │   ├── settings/     # Settings components
│   │   └── dashboard/    # Dashboard components
│   ├── hooks/            # Custom React hooks
│   ├── pages/            # Page components
│   │   ├── LandingPage.tsx
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── SearchPage.tsx
│   │   ├── AIChatPage.tsx
│   │   ├── DocumentsPage.tsx
│   │   ├── HistoryPage.tsx
│   │   ├── AnalyticsPage.tsx
│   │   ├── SettingsPage.tsx
│   │   └── NotificationsPage.tsx
│   ├── routes/           # Route configuration
│   ├── services/         # Business logic services
│   ├── state/            # Zustand stores
│   │   ├── useAuthStore.ts
│   │   ├── useSearchStore.ts
│   │   ├── useAIChatStore.ts
│   │   ├── useDocumentStore.ts
│   │   ├── useAnalyticsStore.ts
│   │   ├── useSettingsStore.ts
│   │   ├── useOfflineStore.ts
│   │   └── useNotificationStore.ts
│   ├── styles/           # Global styles
│   ├── types/            # TypeScript type definitions
│   ├── utils/            # Utility functions
│   └── workers/          # Service workers
├── public/               # Static assets
├── package.json
├── vite.config.ts
├── tsconfig.json
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend server running on http://localhost:8000

### Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` if your backend is running on a different URL.

3. Start the development server:
```bash
npm run dev
```

The app will be available at http://localhost:5173

### Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000/api/v1` |
| `VITE_APP_NAME` | Application name | `Nebula Search` |
| `VITE_APP_VERSION` | Application version | `1.0.0` |

## Features in Detail

### Authentication
- Email/password login and registration
- JWT token management with auto-refresh
- Secure token storage in localStorage
- Protected routes

### Search
- Web search with multiple backends (Wikipedia, Brave, SerpAPI)
- Hybrid search combining keyword and semantic search
- Search history
- Result filtering and pagination

### AI Chat
- Streaming AI responses
- Markdown rendering with syntax highlighting
- Chat history persistence
- Copy to clipboard

### Document Management
- Drag-and-drop upload
- Progress tracking
- Document library with search
- Delete and re-index operations

### Analytics
- Usage statistics
- Search analytics
- Performance metrics
- Interactive charts

### Offline Support
- IndexedDB for local storage
- Search result caching
- Upload queue for offline actions
- Background sync when back online

### PWA Features
- Install prompt
- Offline banner
- Service worker caching
- App-like experience

## API Integration

The frontend integrates with the following backend endpoints:

- **Auth**: `/api/v1/auth/*`
- **Search**: `/api/v1/search/*`
- **AI**: `/api/v1/ai/*`
- **Storage**: `/api/v1/storage/*`
- **Vector**: `/api/v1/vector/*`
- **Analytics**: `/api/v1/analytics/*`
- **Features**: `/api/v1/*` (saved searches, collections, bookmarks, notifications)

## State Management

Zustand stores manage global state:

- **useAuthStore**: User authentication state
- **useSearchStore**: Search queries and results
- **useAIChatStore**: AI chat messages and streaming
- **useDocumentStore**: Document library and uploads
- **useAnalyticsStore**: Analytics data
- **useSettingsStore**: User preferences
- **useOfflineStore**: Offline queue and status
- **useNotificationStore**: Notifications

## Security

- JWT token-based authentication
- Automatic token refresh
- XSS prevention through React's built-in escaping
- CSRF protection
- Secure HTTP-only cookies (optional)
- Input validation and sanitization

## Performance

- Code splitting and lazy loading
- React Query for intelligent caching
- Debounced search inputs
- Virtualized lists for large datasets
- Image optimization
- Bundle optimization with manual chunks

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Follow the existing code style
2. Use TypeScript for all new code
3. Write tests for new features
4. Update documentation as needed

## License

Proprietary - All rights reserved