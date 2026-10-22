# Nebula Search Engine — Mobile Screen Specifications

## Overview

All mobile screens follow mobile-first responsive patterns defined in the UX documentation. This document covers the specific mobile adaptations for every screen.

---

## Common Mobile Patterns

### Bottom Navigation
```
┌──────────────────────────────────────────────┐
│                                              │
│              Content Area                    │
│                                              │
├──────────────────────────────────────────────┤
│  🔍    💬    📁    📊    👤                  │
│ Search  AI   Docs  Analytics Profile         │
│ ───── (active indicator)                     │
└──────────────────────────────────────────────┘
```
- **Height:** 56px + safe-area-bottom
- **5 tabs max**
- **Active:** 3px top border primary-500
- **Hide on scroll down, show on scroll up**

### Top Bar (Mobile)
```
Height: 56px
Padding: 0 12px
Left: [≡ Hamburger] (44×44px)
Center: [Nebula Logo] (28px height)
Right: [🔔] (44×44px) + [👤] (36×36px)
```

### Touch Gestures
- **Swipe left:** Delete/archive item
- **Swipe right:** Favorite/save item
- **Pull down:** Refresh content
- **Swipe from left edge:** Open sidebar
- **Tap top:** Scroll to top

---

## 1. Mobile Landing Page

```
┌──────────────────────────────────────────────┐
│  [≡] [Nebula]          [🌙] [👤]           │
├──────────────────────────────────────────────┤
│                                              │
│                                              │
│         Search the universe                  │
│         of knowledge.                        │
│                                              │
│    ┌──────────────────────────────────┐     │
│    │ 🔍 What would you like to know? │     │
│    └──────────────────────────────────┘     │
│       [🎤]                                  │
│                                              │
│    🔒 Private. No tracking.                 │
│                                              │
│  ┌──────┐ ┌──────┐                         │
│  │ Card │ │ Card │                         │
│  └──────┘ └──────┘                         │
│  ┌──────┐ ┌──────┐                         │
│  │ Card │ │ Card │                         │
│  └──────┘ └──────┘                         │
│                                              │
│  Footer (compact)                           │
└──────────────────────────────────────────────┘
```

### Adaptations
- **Hero text:** 32px (2rem), 800 weight
- **Subheadline:** hidden on small screens
- **Search bar:** full-width (100% - 32px), 56px height
- **Feature cards:** 2-column grid
- **Top bar actions:** Reduced to essential

---

## 2. Mobile Search Results

```
┌──────────────────────────────────────────────┐
│  [←] [🔍 search query...]              [🔔]│
├──────────────────────────────────────────────┤
│  [All] [Docs] [Web] [Images] → (scroll)    │
│                                              │
│  ┌─ AI Summary ───────────────────────┐    │
│  │ 🤖 AI answer... [Expand ▼]        │    │
│  └────────────────────────────────────┘    │
│                                              │
│  ┌─ Result 1 ─────────────────────────┐    │
│  │ Title                               │    │
│  │ snippet with highlight...           │    │
│  │ PDF · 2.4MB                        │    │
│  └────────────────────────────────────┘    │
│                                              │
│  [Load More]                                │
└──────────────────────────────────────────────┘
```

### Adaptations
- **Filters:** Horizontal scrollable chip row
- **AI Summary:** Collapsible (expandable)
- **Results:** Full-width cards, compact
- **Actions:** Swipe left to reveal (Save, Share)
- **Pagination:** "Load More" button (infinite scroll)

---

## 3. Mobile AI Chat

```
┌──────────────────────────────────────────────┐
│  [←] AI Assistant              [⋮] [Clear]│
├──────────────────────────────────────────────┤
│                                              │
│  💬 What is hybrid search?                  │
│  ┌────────────────────────────────┐        │
│  │ Hybrid search combines...     │        │
│  │ [1][2]                        │        │
│  │ [Tell me more] [How...]      │        │
│  └────────────────────────────────┘        │
│                                              │
├──────────────────────────────────────────────┤
│  [📎] [Type a message...]      [🎤] [▶]   │
└──────────────────────────────────────────────┘
```

### Adaptations
- **Full-screen chat** (no sidebar)
- **Input:** Fixed bottom, keyboard-aware
- **Messages:** 90% max width
- **Right panel:** Full-screen overlay (toggle)
- **Header:** Compact, back button + title

---

## 4. Mobile Documents

```
┌──────────────────────────────────────────────┐
│  [≡] Documents                    [+ Upload]│
├──────────────────────────────────────────────┤
│  🔍 Search documents...                     │
│                                              │
│  ┌──────────────────────────────────────┐   │
│  │ 📄 report.pdf         2.4MB  2d ago  │   │
│  └──────────────────────────────────────┘   │
│  ┌──────────────────────────────────────┐   │
│  │ 📄 notes.md           0.8MB  5d ago  │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  [Load More]                                │
└──────────────────────────────────────────────┘
```

### Adaptations
- **List view** (not grid) for mobile
- **FAB** for quick upload (56×56px, bottom-right)
- **Swipe:** Left to delete, right to favorite
- **Search:** Inline at top

---

## 5. Mobile Dashboard

```
┌──────────────────────────────────────────────┐
│  [≡] Nebula                       [🔔] [👤]│
├──────────────────────────────────────────────┤
│  Good morning, Alex!                        │
│                                              │
│  ┌─ Recent Searches ────────────────────┐   │
│  │ 🕐 AI architecture          2h ago   │   │
│  │ 🕐 Document search          5h ago   │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  Stats                                       │
│  12 searches today   8 saved               │
│  2.4GB of 10GB used                         │
│                                              │
│  [Upload] [New Chat] [Saved] [Reports]      │
└──────────────────────────────────────────────┘
```

### Adaptations
- **Stats:** Compact 2×2 grid or horizontal scroll
- **Recent items:** List view, 3-4 items
- **Quick actions:** Horizontal scrollable row of 4 buttons
- **No sidebar** (bottom nav instead)

---

## 6. Mobile Settings

```
┌──────────────────────────────────────────────┐
│  [←] Settings                                │
├──────────────────────────────────────────────┤
│  [General] [Privacy] [AI] → (tabs, scroll)  │
│                                              │
│  General                                     │
│  ┌──────────────────────────────────────┐   │
│  │ Theme                                │   │
│  │ [Light] [Dark] [System]             │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  Language   [English ▼]                    │
│  Timezone   [(UTC+0) UTC ▼]                │
│  Results/page  [20 ▼]                      │
│                                              │
│  [Save Changes]                             │
└──────────────────────────────────────────────┘
```

### Adaptations
- **Tabs:** Horizontal scrollable at top
- **No sidebar** — sections stack vertically
- **Full-width controls**
- **Save button:** Sticky bottom or inline

---

## 7. Mobile Auth (Login/Signup)

```
┌──────────────────────────────────────────────┐
│                                              │
│         [Nebula Logo]                       │
│                                              │
│         Welcome back                        │
│         Sign in to your account             │
│                                              │
│    ┌──────────────────────────────────┐     │
│    │ Email                           │     │
│    └──────────────────────────────────┘     │
│                                              │
│    ┌──────────────────────────────────┐     │
│    │ Password                  [👁]  │     │
│    └──────────────────────────────────┘     │
│                                              │
│    □ Remember me    Forgot password?        │
│                                              │
│    [Sign In]                                │
│                                              │
│    ─── or continue with ───                 │
│    [G] [GitHub] [M]                        │
│                                              │
│    Don't have an account? Create one        │
│                                              │
└──────────────────────────────────────────────┘
```

### Adaptations
- **Card:** Full-width with 24px margins
- **Card padding:** 24px
- **Top margin:** 32px (not centered vertically)
- **Inputs:** 48px height (larger touch targets)
- **Social buttons:** Full-width or 3-col

---

## 8. Mobile Error States

```
┌──────────────────────────────────────────────┐
│  [Nebula Logo]                               │
│                                              │
│                                              │
│            [Icon] 80×80px                   │
│                                              │
│            404                               │
│                                              │
│         Page Not Found                      │
│                                              │
│    The page you're looking for               │
│    doesn't exist or has been moved.          │
│                                              │
│    [Search Nebula]                          │
│    [Go Home]                                │
│                                              │
└──────────────────────────────────────────────┘
```

### Adaptations
- **Icon:** 80×80px (vs 120px desktop)
- **Error code:** 36px (vs 48px desktop)
- **Full-width buttons** (stacked vertically)

---

## Mobile Performance Targets

- **FCP:** < 1.5s (3G network)
- **TTI:** < 3s
- **Bundle size:** < 150KB
- **Images:** < 100KB each
- **Touch targets:** ≥ 44×44px

---

## Device Testing Checklist

- [ ] iPhone SE (320px)
- [ ] iPhone 12/13/14 (390px)
- [ ] iPhone 14 Pro Max (430px)
- [ ] Samsung Galaxy S21 (360px)
- [ ] Google Pixel 7 (412px)
- [ ] Galaxy Z Fold (folded: 600px)

---

**Last Updated:** 2026-07-17