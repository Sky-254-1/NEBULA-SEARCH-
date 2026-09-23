# Nebula Search Engine — Layout Templates

## Purpose

Defines the core layout templates used across all screens. Every screen specification references one of these templates.

---

## Template 1: Centered Card (Authentication)

### Wireframe
```
┌─────────────────────────────────────────────┐
│                                             │
│               ┌─────────────────┐            │
│               │                 │            │
│               │    [Logo]       │            │
│               │                 │            │
│               │    Title        │            │
│               │    Subtitle     │            │
│               │                 │            │
│               │    [Form]       │            │
│               │                 │            │
│               │    [Button]     │            │
│               │                 │            │
│               │    Link         │            │
│               │                 │            │
│               └─────────────────┘            │
│                                             │
│              Footer (minimal)               │
└─────────────────────────────────────────────┘
```

### Specifications
- **Card width:** 400px (desktop), 360px (tablet), full-width with 24px margins (mobile)
- **Card padding:** 32px (desktop), 24px (mobile)
- **Card background:** `--color-bg-primary`
- **Card shadow:** `--shadow-xl`
- **Card radius:** `--radius-xl` (16px)
- **Page background:** `--color-bg-secondary`
- **Max content width:** 400px
- **Vertical centering:** flexbox, min-height 100vh
- **Footer:** 48px height, fixed or static

### Breakpoints
| Property | Desktop (≥1024px) | Tablet (768-1023px) | Mobile (<768px) |
|----------|-------------------|---------------------|-----------------|
| Card width | 400px | 360px | calc(100% - 48px) |
| Card padding | 32px | 32px | 24px |
| Vertical margin | auto | auto | 48px top |

### Accessibility
- `role="main"` on card container
- `aria-labelledby` on title
- Focus first input on load
- Skip link to card content

### Used By
- Login, Signup, Forgot Password, Email Verification, MFA

---

## Template 2: Sidebar + Content (Main App)

### Wireframe
```
┌─────────────┬──────────────────────────────────────┐
│             │                                      │
│  Sidebar    │  Top Bar (64px)                      │
│  (240px)    │  [Logo] [Search Bar] [Actions] [User]│
│             ├──────────────────────────────────────┤
│  Nav Icon   │                                      │
│  Nav Icon   │  Content Area                        │
│  Nav Icon   │  (Padding: 24px)                     │
│  Nav Icon   │                                      │
│  Nav Icon   │                                      │
│             │                                      │
│  User Info  │                                      │
└─────────────┴──────────────────────────────────────┘
```

### Specifications
- **Sidebar width:** 240px collapsed, 280px expanded
- **Sidebar bg:** `--color-bg-secondary` (light), `--color-bg-secondary` (dark)
- **Sidebar border-right:** 1px solid `--color-border`
- **Top bar height:** 64px
- **Top bar bg:** `--color-bg-primary`
- **Top bar border-bottom:** 1px solid `--color-border`
- **Content padding:** 24px
- **Content max-width:** 1440px (centered when wider)
- **Min content width:** 0 (flex-shrink: 1)

### Sidebar Items
- Each nav item: 48px height
- Icon: 24×24px, margin-right: 12px
- Label: `--text-sm`, `--font-medium`
- Active indicator: 3px left border, primary-500
- Item padding: 0 16px
- Item hover: `--color-bg-tertiary`
- Item gap: 4px

### Breakpoints
| Element | Desktop | Tablet | Mobile |
|---------|---------|--------|--------|
| Sidebar | 240px (persistent) | 0 (collapsible overlay) | Hidden (bottom nav) |
| Top bar | 64px | 56px | 56px |
| Content padding | 24px | 20px | 16px |

### Accessibility
- `role="navigation"` on sidebar
- `aria-expanded` on collapse toggle
- Skip link: "Skip to main content"
- Sidebar items have `aria-current="page"`

### Used By
- Dashboard, Search Results, Documents, Analytics, Settings, History, Profile

---

## Template 3: Full-Width Minimal (Landing/Search)

### Wireframe
```
┌─────────────────────────────────────────────┐
│  Top Bar (minimal)                          │
│  [Logo]                    [Login] [Signup] │
├─────────────────────────────────────────────┤
│                                             │
│                                             │
│           ┌─────────────────┐               │
│           │                 │               │
│           │   Hero Text     │               │
│           │                 │               │
│           │   [Search Bar]  │               │
│           │                 │               │
│           │   Quick Links   │               │
│           └─────────────────┘               │
│                                             │
│                                             │
│  Features Section                           │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐          │
│  │Card │ │Card │ │Card │ │Card │           │
│  └─────┘ └─────┘ └─────┘ └─────┘          │
│                                             │
│  Footer                                     │
└─────────────────────────────────────────────┘
```

### Specifications
- **Full viewport height:** min-height 100vh
- **Top bar:** 64px, transparent bg (adds bg-color on scroll)
- **Hero area:** 60vh minimum, centered content
- **Search bar width:** 640px (desktop), 100% - 48px (mobile)
- **Max content width:** 1200px (feature sections)
- **Footer:** 80px height
- **Background:** subtle gradient or solid

### Breakpoints
| Element | Desktop | Tablet | Mobile |
|---------|---------|--------|--------|
| Top bar | 64px | 56px | 56px |
| Search bar | 640px | 480px | calc(100% - 32px) |
| Hero min-height | 60vh | 50vh | 40vh |

### Used By
- Landing Page, Error Pages

---

## Template 4: Split Panel (AI Chat)

### Wireframe
```
┌─────────────┬──────────────────────────────────────┬──────────────┐
│             │                                      │              │
│  Sidebar    │  AI Chat Workspace                   │  Right Panel │
│  (240px)    │                                      │  (360px)     │
│             │  ┌─────────────────────────────────┐  │              │
│  Nav        │  │ ← New Chat   [Model] [⋮]      │  │  Sources     │
│             │  ├─────────────────────────────────┤  │  Citations   │
│  Nav        │  │                                 │  │              │
│             │  │  Messages (scrollable)          │  │  Related     │
│  Nav        │  │                                 │  │              │
│             │  │  • User message                 │  │  Document    │
│  Nav        │  │  • AI streaming response        │  │  Metadata    │
│             │  │                                 │  │              │
│  Nav        │  │                                 │  │              │
│             │  ├─────────────────────────────────┤  │              │
│  User Info  │  │ [Input]                 [Send]  │  │              │
│             │  │ [Attach] [Mic]                  │  │              │
└─────────────┴──────────────────────────────────────┴──────────────┘
```

### Specifications
- **Chat header:** 56px, border-bottom
- **Messages area:** flex-1, overflow-y auto, padding 16px
- **Input area:** 80px (includes padding), border-top
- **Input height:** 48px, expandable to 120px max
- **Right panel:** 360px width, border-left, scrollable
- **Message bubble max width:** 75% of container
- **Avatar size:** 32×32px (AI), 32×32px (User)

### Breakpoints
| Element | Desktop | Tablet | Mobile |
|---------|---------|--------|--------|
| Right panel | 360px | Collapsed (toggle) | Full-screen overlay |
| Sidebar | 240px | Collapsed | Bottom nav |
| Chat width | flex-1 | flex-1 | 100% |

### Used By
- AI Chat Workspace, AI Search

---

## Template 5: Data Dashboard (Analytics/Admin)

### Wireframe
```
┌─────────────┬──────────────────────────────────────────┐
│             │  Top Bar                                 │
│  Sidebar    │  [Breadcrumbs]         [Date Range] [Export]│
│  (240px)    ├──────────────────────────────────────────┤
│             │                                          │
│  Nav        │  Stats Row                               │
│  Nav        │  ┌──────┐┌──────┐┌──────┐┌──────┐      │
│  Nav        │  │Stat 1││Stat 2││Stat 3││Stat 4│      │
│  Nav        │  └──────┘└──────┘└──────┘└──────┘      │
│  Nav        │                                          │
│             │  Chart Area                              │
│  Nav        │  ┌────────────────────────────────────┐  │
│             │  │                                    │  │
│  User Info  │  │        Line/Bar Chart              │  │
│             │  │                                    │  │
│             │  └────────────────────────────────────┘  │
│             │                                          │
│             │  Data Table                              │
│             │  ┌────────────────────────────────────┐  │
│             │  │ Header │ Header │ Header │ Actions│  │
│             │  ├────────────────────────────────────┤  │
│             │  │ Row    │ Row    │ Row    │ [⋮]    │  │
│             │  │ Row    │ Row    │ Row    │ [⋮]    │  │
│             │  └────────────────────────────────────┘  │
│             │                                          │
└─────────────┴──────────────────────────────────────────┘
```

### Specifications
- **Content padding:** 24px
- **Stats cards:** 280px min-width, flex grid
- **Chart area:** 400px min-height
- **Data table:** full-width, 56px row height
- **Date range picker:** dropdown button, 40px height
- **Export button:** ghost variant
- **Card gap:** 16px

### Used By
- Analytics Dashboard, AI Analytics, Admin Dashboard, Monitoring

---

## Template 6: Detail/Preview (Document Viewer)

### Wireframe
```
┌─────────────┬──────────────────────────────────────┐
│             │  Top Bar                             │
│  Sidebar    │  ← Back to Library  [Download] [Share]│
│  (240px)    ├──────────────────────────────────────┤
│             │                                      │
│  Nav        │  Split Preview                       │
│             │  ┌─────────────────┬──────────────┐  │
│  Nav        │  │                 │  Metadata    │  │
│             │  │  Document       │  ──────────  │  │
│  Nav        │  │  Viewer         │  Title       │  │
│             │  │  (PDF/Image)    │  Author      │  │
│  Nav        │  │                 │  Date        │  │
│             │  │                 │  Size        │  │
│  Nav        │  │                 │  Tags        │  │
│             │  │                 │              │  │
│  User Info  │  │                 │  [Edit Tags] │  │
│             │  │                 │              │  │
│             │  └─────────────────┴──────────────┘  │
│             │                                      │
└─────────────┴──────────────────────────────────────┘
```

### Specifications
- **Document viewer:** flex-1, min-height 500px
- **Metadata panel:** 320px width, border-left
- **Toolbar height:** 48px
- **Zoom controls:** bottom-right floating, 40px buttons
- **Page navigation:** bottom-center

### Used By
- Document Viewer

---

**Last Updated:** 2026-07-17