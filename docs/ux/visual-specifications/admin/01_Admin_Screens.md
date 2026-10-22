# Nebula Search Engine — Administration Screens Visual Specification

## Overview

Six admin screens for system management. Admin screens use Template 5 (Data Dashboard) or Template 2 (Sidebar + Content). All require admin role.

---

## 1. Administration Dashboard

### Purpose
High-level system overview for administrators.

### Layout
```
┌─────────────┬──────────────────────────────────────────────────┐
│  Admin      │  Admin Dashboard         [Last 24h ▼] [Refresh]  │
│  Sidebar    ├──────────────────────────────────────────────────┤
│  (240px)    │  Stats Row (6 cards)                            │
│             │  ┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐┌──────┐│
│  📊 Dashboard│  │Users ││Search││AI    ││Docs  ││Errors││Uptime││
│  👥 Users   │  │1,234 ││12.8K ││4.5K  ││3,421 ││23    ││99.97%││
│  🤖 Models  │  └──────┘└──────┘└──────┘└──────┘└──────┘└──────┘│
│  🔍 Indexes │                                                  │
│  📈 Monitor │  System Health                                   │
│  📋 Logs    │  ┌──────────────────────────────────────────┐   │
│             │  │ CPU: ████████░░ 68%   Memory: ██████░░ 55%│   │
│  ⚙️ Settings│  │ Disk: ██░░░░░░░░ 22%  API:  ██████████ 98%│   │
│             │  └──────────────────────────────────────────┘   │
│             │                                                  │
│  Admin User │  Recent Activity                                 │
│             │  ┌──────────────────────────────────────────┐   │
│             │  │ [12:34] User "john" registered           │   │
│             │  │ [12:30] Admin "alex" updated settings    │   │
│             │  └──────────────────────────────────────────┘   │
└─────────────┴──────────────────────────────────────────────────┘
```

### Components
- **6 stat cards** in a row (desktop), 3×2 (tablet), 2×3 (mobile)
- **System health** bars with colored indicators
- **Activity feed** — last 10 actions, timestamped
- **Quick actions:** [Refresh] [View Logs] [Run Report]

---

## 2. User Management

### Purpose
Manage user accounts, roles, and permissions.

### Layout
```
┌─────────────┬──────────────────────────────────────────────────┐
│  Admin      │  User Management                                 │
│  Sidebar    │  [🔍 Search users...]  [Filter ▼] [Invite User] │
│             ├──────────────────────────────────────────────────┤
│             │  ┌────┬──────────┬────────┬────────┬────────┐   │
│             │  │ ☐  │ Name    │ Email  │ Role   │ Status │   │
│             │  ├────┼──────────┼────────┼────────┼────────┤   │
│             │  │ ☐  │ John D  │ j@e.co │ User   │ Active │   │
│             │  │ ☐  │ Jane S  │ j@s.co │ Admin  │ Active │   │
│             │  └────┴──────────┴────────┴────────┴────────┘   │
│             │                                                  │
│             │  [Bulk Actions ▼]        Page 1 of 25          │
└─────────────┴──────────────────────────────────────────────────┘
```

### Components
- **Data table** with selection, sorting, filtering
- **Search** with debounce
- **User role badges:** Admin (purple), User (blue), Viewer (gray)
- **Status indicators:** Active (green), Inactive (gray), Suspended (red)
- **Bulk actions:** Delete, Suspend, Change Role, Export
- **Invite modal:** Email input + role selector + optional message
- **Row actions:** [Edit] [Suspend] [Delete] [Reset Password]

### User Detail Modal
```
┌──────────────────────────────────────────────┐
│  Edit User                          [×]     │
├──────────────────────────────────────────────┤
│  Name: [John Doe]                           │
│  Email: [john@example.com]                  │
│  Role: [User ▼]                             │
│  Status: [Active ▼]                         │
│  MFA: [Enabled]                             │
│  Created: Jan 15, 2026                      │
│  Last Login: 2 hours ago                    │
│  Storage Used: 1.2 GB of 10 GB              │
│                                              │
│  [Save Changes] [Cancel] [Delete User]     │
└──────────────────────────────────────────────┘
```

### User Table Specifications
| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Header | 13px | 600 | text-secondary |
| Name | 14px | 500 | text-primary |
| Email | 14px | 400 | text-tertiary |
| Role badge | 12px | 500 | white |
| Status dot | 8px | — | success-500 |
| Row height | 56px | — | — |

---

## 3. AI Model Manager

### Purpose
Configure and monitor AI models available to users.

### Layout
```
┌─────────────┬──────────────────────────────────────────────────┐
│  Admin      │  AI Model Manager               [Add Model ▼]  │
│  Sidebar    ├──────────────────────────────────────────────────┤
│             │  ┌──────────────────────────────────────────┐   │
│             │  │ GPT-4        ● Online   1,234 req today  │   │
│             │  │ Provider: OpenAI  │  Cost: $0.03/1K      │   │
│             │  │ [Configure] [Disable] [Test]             │   │
│             │  ├──────────────────────────────────────────┤   │
│             │  │ Claude 3     ● Online   567 req today    │   │
│             │  │ Provider: Anthropic │ Cost: $0.02/1K     │   │
│             │  │ [Configure] [Disable] [Test]             │   │
│             │  ├──────────────────────────────────────────┤   │
│             │  │ Local Model  ○ Offline  0 req today      │   │
│             │  │ Provider: Local    │  Cost: $0           │   │
│             │  │ [Configure] [Enable] [Test]              │   │
│             │  └──────────────────────────────────────────┘   │
│             │                                                  │
└─────────────┴──────────────────────────────────────────────────┘
```

### Model Card Specifications
- **Padding:** 24px
- **Border:** 1px solid --color-border
- **Border-radius:** 12px
- **Margin-bottom:** 12px
- **Status dot:** 10px, green (online) / gray (offline) / red (error)
- **Usage bar:** 6px height, gradient fill

### Model Config Modal
- API Key input (masked)
- Rate limit: max requests per minute
- Temperature range: min/max
- Token limit: max tokens per response
- Cost per 1K tokens: input
- Enabled for roles: checkbox list

---

## 4. Search Index Manager

### Purpose
Monitor and manage search indexes, trigger reindexing, and view index health.

### Layout
```
┌─────────────┬──────────────────────────────────────────────────┐
│  Admin      │  Search Index Manager        [Rebuild Index]    │
│  Sidebar    ├──────────────────────────────────────────────────┤
│             │  ┌────────────┬────────┬────────┬────────────┐  │
│             │  │ Index      │ Docs   │ Size   │ Last Updated│  │
│             │  ├────────────┼────────┼────────┼────────────┤  │
│             │  │ Main       │ 3,421  │ 2.4GB  │ 5m ago     │  │
│             │  │ Vector     │ 12,847 │ 1.8GB  │ 5m ago     │  │
│             │  │ Knowledge  │ 847    │ 120MB  │ 1h ago     │  │
│             │  └────────────┴────────┴────────┴────────────┘  │
│             │                                                  │
│             │  Index Health                                     │
│             │  Main: ✅ Healthy (99.7% hit rate)              │
│             │  Vector: ⚠️ Degraded (85% recall)               │
│             │  Knowledge: ✅ Healthy (100% uptime)            │
└─────────────┴──────────────────────────────────────────────────┘
```

### Actions per Index
- [Rebuild] — Full reindex (with confirmation, shows ETA)
- [Optimize] — Optimize index structure
- [Clear] — Clear and rebuild from scratch
- [Download] — Download index snapshot

### Rebuild Progress
```
Rebuilding "Main" index...
  Documents processed: 2,847 / 3,421 (83%)
  Estimated time remaining: 2 minutes
  Status: Processing embeddings...

[Cancel] [Pause]
```

---

## 5. Monitoring Dashboard

### Purpose
Real-time system monitoring with metrics, alerts, and health status.

### Layout
```
┌─────────────┬──────────────────────────────────────────────────┐
│  Admin      │  Monitoring Dashboard    [Auto-refresh: 30s ▼]  │
│  Sidebar    ├──────────────────────────────────────────────────┤
│             │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│             │  │ CPU      │ │ Memory   │ │ Disk     │        │
│             │  │ 68%      │ │ 55%      │ │ 22%      │        │
│             │  │ ┌─── gauge│ │ ┌───gauge│ │ ┌───gauge│        │
│             │  └──────────┘ └──────────┘ └──────────┘        │
│             │                                                  │
│             │  Service Status                                  │
│             │  ✅ API Server      ● Operational  12ms latency │
│             │  ✅ Database        ● Operational  8ms          │
│             │  ✅ Redis Cache     ● Operational  2ms          │
│             │  ⚠️ Vector DB       ⚠️ Degraded    150ms        │
│             │  ✅ AI Service      ● Operational  1.2s         │
│             │                                                  │
│             │  Recent Alerts                                   │
│             │  ⚠️ [15:23] Vector DB latency > 100ms           │
│             │  ✅ [14:00] Database connection restored         │
└─────────────┴──────────────────────────────────────────────────┘
```

### Components
- **Gauges:** Circular progress (0-100%), colored by threshold
- **Service list:** Status icon + name + description + latency
- **Alerts feed:** Timestamped, color-coded by severity
- **Auto-refresh toggle:** Dropdown: 10s / 30s / 60s / Off

### Threshold Colors
| Range | Color |
|-------|-------|
| 0-50% | success-500 |
| 51-80% | warning-500 |
| 81-100% | error-500 |

---

## 6. Logs Viewer

### Purpose
View and search system logs with filtering and export.

### Layout
```
┌─────────────┬──────────────────────────────────────────────────┐
│  Admin      │  Logs Viewer                                     │
│  Sidebar    │  [🔍 Search logs...]  [Level ▼] [Service ▼]     │
│             │  [Export] [Clear]                                │
│             ├──────────────────────────────────────────────────┤
│             │  ┌────────────────────────────────────────────┐  │
│             │  │ [INFO]  [12:34] User login successful     │  │
│             │  │ [ERROR] [12:30] Database timeout exceeded │  │
│             │  │ [WARN]  [12:28] High memory usage (82%)  │  │
│             │  │ [INFO]  [12:25] Search index rebuilt     │  │
│             │  └────────────────────────────────────────────┘  │
│             │                                                  │
│             │  Auto-refresh: On  ▲ Page 1 of 124 ▼           │
└─────────────┴──────────────────────────────────────────────────┘
```

### Log Entry Specifications
- **Padding:** 8px 16px
- **Font:** --font-mono (JetBrains Mono), 13px
- **Level badge:** 4px left border (color-coded)
- **Row hover:** gray-50 bg
- **Row height:** 36px (compact)

### Log Level Colors
| Level | Border | Text Color |
|-------|--------|------------|
| DEBUG | gray-400 | gray-500 |
| INFO | primary-500 | text-primary |
| WARN | warning-500 | warning-700 |
| ERROR | error-500 | error-700 |
| FATAL | error-700 | error-700 bold |

### Filters
- **Level:** Multi-select checkboxes (DEBUG, INFO, WARN, ERROR, FATAL)
- **Service:** Dropdown (API, Database, Cache, AI, Vector)
- **Date range:** From/To date pickers
- **Search:** Full-text search across log messages

### Auto-refresh
- Toggle: On/Off
- Interval: 5 seconds
- New logs appear at top with highlight animation

---

## Admin-Specific Responsive

- **Desktop:** Full layouts as described
- **Tablet:** Charts/gauges stack vertically, tables horizontal scroll
- **Mobile:** Single column, critical metrics only, hide detailed tables

---

## Admin Accessibility

- All data tables use proper `<th scope>`, `<caption>`
- Charts have alt text fallbacks
- Log viewer uses `aria-live="polite"` for auto-refresh
- Color-coded statuses include text labels (not just color)

---

## Admin Security

- All admin routes require admin role
- Session timeout: 30 minutes of inactivity
- Audit logging for all admin actions
- Bulk actions require confirmation dialog
- Export limits: max 10,000 rows per export

---

**Last Updated:** 2026-07-17