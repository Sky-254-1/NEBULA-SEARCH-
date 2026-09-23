# Nebula Search Engine — Error Pages Visual Specification

## Overview

All error pages follow a consistent pattern: centered layout with illustration, error code, message, and action buttons. They use Template 3 (Full-Width Minimal).

---

## Common Layout (All Error Pages)

```
┌──────────────────────────────────────────────────────────┐
│  Top Bar (minimal)                                       │
│  [Nebula Logo]                    [Dark/Light] [Login]   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│                                                          │
│                                                          │
│                    [Illustration]                        │
│                    120×120px                             │
│                                                          │
│                    Error Code                            │
│                    text-5xl (48px), bold                  │
│                                                          │
│                    Error Title                           │
│                    text-2xl (24px), semibold              │
│                                                          │
│                    Error Description                     │
│                    text-base, text-tertiary, max-w 400px  │
│                                                          │
│                    [Primary Action] [Secondary Action]    │
│                                                          │
│                                                          │
│                                                          │
│              Footer: Privacy | Terms | Docs              │
└──────────────────────────────────────────────────────────┘
```

### Specifications
- **Page bg:** --color-bg-secondary
- **Content:** Centered flex column, min-height 60vh
- **Illustration:** 120×120px, centered
- **Error code:** 48px, 800 weight, text-primary
- **Title:** 24px, 600 weight, text-primary
- **Description:** 16px, 400 weight, text-tertiary, max-width 400px
- **Actions:** Row of 1-2 buttons, gap 12px, centered
- **Top bar:** 64px, minimal (logo + theme toggle + login)
- **Footer:** 64px, minimal links

---

## 1. 400 Bad Request

```
Code: 400
Title: "Bad Request"
Description: "The request could not be processed. Please check your input and try again."
Icon: ⚠️ (warning triangle)
Primary Action: [Go Home]
Secondary Action: [Contact Support]
```

---

## 2. 401 Unauthorized

```
Code: 401
Title: "Unauthorized"
Description: "You need to sign in to access this page. Please log in and try again."
Icon: 🔒 (lock)
Primary Action: [Sign In]
Secondary Action: [Go Home]
```

---

## 3. 403 Forbidden

```
Code: 403
Title: "Access Denied"
Description: "You don't have permission to access this resource. Contact your administrator if you believe this is a mistake."
Icon: 🚫 (prohibited)
Primary Action: [Go Home]
Secondary Action: [Request Access]
```

---

## 4. 404 Not Found

```
Code: 404
Title: "Page Not Found"
Description: "The page you're looking for doesn't exist or has been moved. Try searching for what you need."
Icon: 🔍 (search with question mark)
Primary Action: [Search Nebula]
Secondary Action: [Go Home]
```

---

## 5. 429 Rate Limited

```
Code: 429
Title: "Too Many Requests"
Description: "You've made too many requests. Please wait before trying again."
Icon: ⏱️ (timer)
Primary Action: [Try Again] (disabled with countdown)
Secondary Action: [Go Home]
Extra: "Retry in 45s" countdown timer
```

---

## 6. 500 Server Error

```
Code: 500
Title: "Something Went Wrong"
Description: "An unexpected error occurred. Our team has been notified. Please try again in a few minutes."
Icon: 🔧 (wrench/tools)
Primary Action: [Try Again]
Secondary Action: [Contact Support]
Extra: Error reference ID (text-xs, text-tertiary): "Ref: ERR-7A3F-2026"
```

---

## 7. Maintenance Mode

```
Code: 🔧
Title: "Under Maintenance"
Description: "Nebula is currently undergoing scheduled maintenance. We'll be back shortly."
Icon: 🛠️ (construction)
Primary Action: [Refresh]
Secondary Action: [Check Status]
Extra: "Estimated completion: 30 minutes" — text-sm, text-tertiary
Progress bar: indeterminate, 6px height
```

---

## 8. Offline Mode

```
Code: 📡
Title: "You're Offline"
Description: "You've lost connection to the internet. Some features may be unavailable."
Icon: 📡 (satellite with X)
Primary Action: [Retry Connection]
Secondary Action: [Browse Offline Content]
Extra: "Showing cached results from your last session" — text-sm, text-tertiary
```

---

## Color Variations

| Page | Icon Color | Primary Button |
|------|-----------|----------------|
| 400 | warning-500 | primary-600 |
| 401 | primary-500 | primary-600 |
| 403 | error-500 | primary-600 |
| 404 | text-tertiary | primary-600 |
| 429 | warning-500 | gray-400 (disabled) |
| 500 | error-500 | primary-600 |
| Maintenance | primary-500 | primary-600 |
| Offline | text-tertiary | primary-600 |

---

## Animations

- **Page load:** Fade in 300ms
- **Illustration:** Subtle float animation (translateY 0→-4px→0, 3s loop)
- **Countdown (429):** Smooth number update each second
- **Retry button:** Pulse animation when available

---

## Responsive

- **Desktop:** Full layout as described
- **Tablet:** Same, slightly smaller text
- **Mobile:** Compact, illustration 80×80px, error code 36px

---

## Accessibility

### Keyboard
```
Tab: Primary action → Secondary action → Footer links
Enter: Activate button
```

### ARIA
```html
<main role="main" aria-labelledby="error-title">
  <h1 id="error-title" class="sr-only">404 Page Not Found</h1>
  <div role="alert" aria-live="assertive">
    <p>Error 404: The page you're looking for doesn't exist.</p>
  </div>
</main>
```

---

## Developer Notes

### Component
```typescript
interface ErrorPageProps {
  code: string | number;
  title: string;
  description: string;
  icon: string;
  primaryAction: { label: string; onClick: () => void };
  secondaryAction?: { label: string; onClick: () => void };
  extra?: { label: string; value: string };
}
```

### Status Codes
```typescript
const ERROR_PAGES = {
  400: { title: "Bad Request", icon: "⚠️", ... },
  401: { title: "Unauthorized", icon: "🔒", ... },
  403: { title: "Forbidden", icon: "🚫", ... },
  404: { title: "Not Found", icon: "🔍", ... },
  429: { title: "Rate Limited", icon: "⏱️", ... },
  500: { title: "Server Error", icon: "🔧", ... },
  maintenance: { title: "Maintenance", icon: "🛠️", ... },
  offline: { title: "Offline", icon: "📡", ... },
};
```

---

**Last Updated:** 2026-07-17