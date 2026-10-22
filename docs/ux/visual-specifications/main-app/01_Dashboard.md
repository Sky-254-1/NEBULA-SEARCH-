# Nebula Search Engine — Dashboard Visual Specification

## 1. Screen Overview

### Purpose
Provide authenticated users with a personalized home screen showing recent activity, quick actions, and key metrics.

### Primary Actions
1. Execute a search (global search bar in top bar)
2. View recent searches and documents
3. Navigate to key sections (AI, Documents, Analytics)

### Secondary Actions
- View saved searches
- Check notifications
- Access quick actions (upload, new chat)
- View storage usage

---

## 2. Layout

### Desktop (≥1024px)
```
┌─────────────┬──────────────────────────────────────────────────┐
│             │  Top Bar (64px)                                  │
│  Sidebar    │  [☰] [Nebula] [🔍 Search... Ctrl+K]  [🔔] [👤]│
│  (240px)    ├──────────────────────────────────────────────────┤
│             │                                                  │
│  🔍 Search  │  Welcome back, Alex!                    [Date]  │
│  💬 AI      │                                                  │
│  📁 Docs    │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  📊 Analytics│  │ Recent   │ │ Saved    │ │ Storage  │        │
│  🕐 History │  │ Searches │ │ Searches │ │ Used     │        │
│  🔔 Notifs  │  │ 12 today  │ │ 8 saved  │ │ 2.4/10GB │        │
│             │  └──────────┘ └──────────┘ └──────────┘        │
│  ⚙️ Settings│                                                  │
│  👤 Profile │  Recent Searches                    [View all →]│
│             │  ┌────────────────────────────────────────────┐  │
│  User Info  │  │ 🕐 AI-powered search architecture — 2h ago │  │
│             │  │ 🕐 Document management best practices — 5h │  │
│             │  │ 🕐 Nebula API documentation — yesterday    │  │
│             │  └────────────────────────────────────────────┘  │
│             │                                                  │
│             │  Recent Documents                   [View all →]│
│             │  ┌────────┐ ┌────────┐ ┌────────┐              │
│             │  │ Doc 1  │ │ Doc 2  │ │ Doc 3  │              │
│             │  │ PDF    │ │ DOCX   │ │ MD     │              │
│             │  │ 2.4MB  │ │ 1.1MB  │ │ 0.8MB  │              │
│             │  └────────┘ └────────┘ └────────┘              │
│             │                                                  │
│             │  Quick Actions                                   │
│             │  [📤 Upload] [💬 New Chat] [📋 Saved] [📊 Report]│
│             │                                                  │
└─────────────┴──────────────────────────────────────────────────┘
```

### Layout Template
- **Template:** Template 2 (Sidebar + Content)
- **Content padding:** 24px
- **Max content width:** 1200px

---

## 3. Component Placement

### Top Bar
```
Left: [☰ Hamburger] (44×44px) + [Nebula Logo] (32px height)
Center: Search bar (flex-1, max 480px, 44px height)
Right: [🔔 Notifications] (44×44px) + [👤 Avatar] (40×40px)
```

### Welcome Section
```
Row layout (flex, space-between, align center):
  Left:
    "Welcome back, Alex!" — text-2xl (24px), semibold, text-primary
    "Here's what's happening with your searches." — text-sm, text-tertiary
  Right:
    Date display — text-sm, text-tertiary
    [Today] [This Week] [This Month] quick filter chips
Margin-bottom: 24px
```

### Stats Cards Row
```
3 cards in a row, gap 16px, equal width:

Card 1: Recent Searches
  Icon: 🔍 32×32px, primary-100 bg, primary-500 icon
  Value: "12" — text-3xl (30px), bold, text-primary
  Label: "searches today" — text-sm, text-tertiary
  Trend: "↑ 23% from yesterday" — text-xs, success-600

Card 2: Saved Searches
  Icon: 🔖 32×32px, secondary-100 bg, secondary-500 icon
  Value: "8" — text-3xl, bold, text-primary
  Label: "saved searches" — text-sm, text-tertiary
  Trend: "2 new this week" — text-xs, primary-600

Card 3: Storage Used
  Icon: 💾 32×32px, warning-100 bg, warning-500 icon
  Value: "2.4" — text-3xl, bold, text-primary
  Label: "GB of 10 GB used" — text-sm, text-tertiary
  Progress bar: 24% fill, 6px height, radius 3px

Card specs:
  Padding: 20px
  Background: --color-bg-primary
  Border: 1px solid --color-border
  Border-radius: 12px
  Shadow: shadow-sm
  Hover: shadow-md, translateY(-2px), 250ms
```

### Recent Searches Section
```
Section header:
  "Recent Searches" — text-lg (18px), semibold, text-primary
  "View all →" link — text-sm, primary-500
  Margin-bottom: 12px

List items (3 shown):
  Each item:
    Height: 56px
    Padding: 0 16px
    Border-radius: 8px
    Display: flex, align center, gap 12px
    Hover: bg gray-50
    
    Icon: 🕐 20×20px, text-tertiary
    Query: "AI-powered search architecture" — text-base, text-primary, flex 1
    Time: "2h ago" — text-sm, text-tertiary
    Actions: [⋮] 44×44px icon button
```

### Recent Documents Section
```
Section header:
  "Recent Documents" — text-lg, semibold
  "View all →" link
  Margin-bottom: 12px

Document cards (3 shown, horizontal scroll on mobile):
  Card width: 200px
  Card height: 160px
  Padding: 16px
  Background: --color-bg-primary
  Border: 1px solid --color-border
  Border-radius: 12px
  
  Content:
    File type icon: 40×40px (PDF, DOCX, MD icons)
    File name: text-sm, semibold, truncate
    File size: text-xs, text-tertiary
    Date: text-xs, text-tertiary
    Actions: [⋮] menu
```

### Quick Actions Row
```
4 action buttons, gap 12px:
  [📤 Upload Document] — secondary button with icon
  [💬 New AI Chat] — secondary button with icon
  [📋 Saved Searches] — ghost button with icon
  [📊 View Analytics] — ghost button with icon

Button height: 40px
Padding: 0 16px
```

---

## 4. Typography

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Welcome heading | 24px | 600 | text-primary |
| Welcome subtitle | 14px | 400 | text-tertiary |
| Stat value | 30px | 700 | text-primary |
| Stat label | 14px | 400 | text-tertiary |
| Stat trend | 12px | 500 | success-600 |
| Section title | 18px | 600 | text-primary |
| Search query | 16px | 400 | text-primary |
| Search time | 14px | 400 | text-tertiary |
| Doc file name | 14px | 600 | text-primary |
| Doc metadata | 12px | 400 | text-tertiary |
| Quick action text | 14px | 500 | text-secondary |

---

## 5. Color Usage

### Light Mode
- **Page bg:** #f9fafb
- **Sidebar:** #ffffff
- **Cards:** #ffffff
- **Stat card 1 bg:** #eff6ff (primary-50)
- **Stat card 2 bg:** #f0fdf4 (secondary-50)
- **Stat card 3 bg:** #fffbeb (warning-50)
- **List hover:** #f9fafb
- **Border:** #e5e7eb

### Dark Mode
- **Page bg:** #0f172a
- **Sidebar:** #1e293b
- **Cards:** #1e293b
- **Stat card 1 bg:** #1e3a8a (primary-900)
- **Stat card 2 bg:** #14532d (secondary-900)
- **Stat card 3 bg:** #78350f (warning-900)
- **List hover:** #1e293b
- **Border:** #334155

---

## 6. Interaction States

### Stat Cards
| State | Transform | Shadow |
|-------|-----------|--------|
| Default | scale(1) | shadow-sm |
| Hover | translateY(-2px) | shadow-md |
| Focus | translateY(-2px) | focus ring |

### Search List Items
| State | Background |
|-------|------------|
| Default | transparent |
| Hover | gray-50 |
| Focus | primary-50 + ring |

### Quick Action Buttons
Standard button states (see design system reference)

---

## 7. Animations

- **Page load:** Content fades in 300ms, stats stagger 100ms each
- **Stat cards:** Hover lift 200ms
- **List items:** Hover bg transition 150ms
- **Document cards:** Hover lift + shadow 250ms
- **Quick actions:** Standard button press 150ms

---

## 8. Responsive Layout

### Desktop (≥1024px)
- Full layout with sidebar
- 3 stat cards in a row
- 3 document cards visible

### Laptop (1024-1279px)
- Same as desktop
- Slightly smaller stat cards

### Tablet (768-1023px)
- Sidebar collapsed (hamburger)
- 2 stat cards per row (3rd wraps)
- 2 document cards visible
- Content padding: 20px

### Phone (<768px)
- Bottom navigation (no sidebar)
- Stats: 1 card per row (stacked)
- Recent searches: 2 items shown
- Documents: horizontal scroll
- Content padding: 16px
- Quick actions: scrollable row

### Ultra-wide (≥1920px)
- Content max-width: 1440px
- 4 stat cards (add "AI Queries")
- 4+ document cards

---

## 9. Accessibility

### Keyboard Navigation
```
Tab order:
  1. Skip to main content
  2. Sidebar toggle
  3. Logo (home)
  4. Search bar
  5. Notifications
  6. User avatar
  7. Stat cards (3)
  8. Recent searches list
  9. View all links
  10. Document cards
  11. Quick action buttons

Shortcuts:
  Ctrl+K: Focus search
  Ctrl+1-6: Navigate sections
  S: Focus search list
  D: Focus documents
```

### ARIA
```html
<main role="main" aria-label="Dashboard">
  <section aria-label="Statistics">
    <article aria-label="Recent searches: 12 today">
  <section aria-label="Recent searches">
    <ul>
      <li role="listitem">
  <section aria-label="Recent documents">
```

### Focus Management
- Auto-focus search bar on page load (optional, configurable)
- Tab moves through sections in logical order
- Skip link to main content

---

## 10. Developer Notes

### Component Hierarchy
```
DashboardPage
├── AppShell
│   ├── Sidebar (Template 2)
│   ├── TopBar
│   │   ├── HamburgerToggle
│   │   ├── Logo
│   │   ├── SearchBar (header variant)
│   │   ├── NotificationBell
│   │   └── UserAvatar
│   └── Content
│       ├── WelcomeSection
│       │   ├── Greeting
│       │   └── DateFilter
│       ├── StatsRow
│       │   ├── StatCard × 3
│       │   │   ├── Icon
│       │   │   ├── Value
│       │   │   ├── Label
│       │   │   └── Trend
│       ├── RecentSearches
│       │   ├── SectionHeader
│       │   └── SearchList
│       │       └── SearchItem × 3
│       ├── RecentDocuments
│       │   ├── SectionHeader
│       │   └── DocumentGrid
│       │       └── DocCard × 3
│       └── QuickActions
│           └── ActionButton × 4
```

### API Endpoints
```
GET /api/v1/dashboard/stats
Response: { searches_today, saved_searches, storage_used, storage_total }

GET /api/v1/dashboard/recent-searches?limit=3
Response: [{ id, query, timestamp }]

GET /api/v1/dashboard/recent-documents?limit=3
Response: [{ id, name, type, size, updated_at }]
```

### State Management
```
stats: { searchesToday, savedSearches, storageUsed, storageTotal }
recentSearches: SearchItem[]
recentDocuments: Document[]
isLoading: boolean
error: string | null
```

### Empty States
```
No recent searches:
  "No searches yet. Start searching to see your history here."
  [Start Searching] CTA button

No documents:
  "No documents uploaded yet."
  [Upload Document] CTA button
```

---

**Design System References:**
- Layout Template: Template 2 (Sidebar + Content)
- Components: Stat Cards, List Items, Document Cards, Buttons
- Navigation: Sidebar, Top Bar
- Animations: Page Load, Card Hover

**Last Updated:** 2026-07-17