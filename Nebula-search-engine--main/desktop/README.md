# Nebula Search — Desktop App

Electron-based desktop application for Nebula Search, wrapping the existing React frontend into a native Windows, macOS, and Linux app.

## Prerequisites

- Node.js 18+
- npm
- The frontend must be built (`../frontend/dist/`) for production mode

## Setup

```bash
cd desktop
npm install
```

## Development Mode

Runs Electron against the Vite dev server (requires the frontend dev server running on `http://localhost:5173`):

```bash
# Terminal 1 — start the frontend dev server
cd ../frontend
npm run dev

# Terminal 2 — start the desktop app in dev mode
cd ../desktop
npm run dev
```

## Production Build

Builds the frontend, then packages the desktop app:

```bash
cd desktop
npm run build
```

## Platform-Specific Builds

```bash
# Windows (.exe installer)
npm run dist:win

# macOS (.dmg)
npm run dist:mac

# Linux (.AppImage + .deb)
npm run dist:linux
```

Output is written to `desktop/release/`.

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `NEBULA_API_URL` | `http://localhost:8000` | Backend API base URL |
| `NEBULA_DEV_URL` | `http://localhost:5173` | Frontend dev server URL (dev mode only) |

## Security

- `contextIsolation: true` — renderer runs in isolated context
- `nodeIntegration: false` — no Node.js access in renderer
- `sandbox: true` — Chromium sandbox enabled
- External links open in the system browser, not inside the app
- A secure preload bridge (`preload.js`) exposes only the minimal API needed

## Features

- Native window (1280×800, resizable)
- Loads the built frontend from `../frontend/dist/`
- Dev mode with hot-reload against Vite
- External link handling (opens in system browser)
- Cross-platform packaging (Windows NSIS, macOS DMG, Linux AppImage/deb)