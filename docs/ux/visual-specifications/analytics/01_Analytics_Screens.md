# Nebula Search Engine — Analytics Screens Visual Specification

## Overview

Two analytics dashboards: Search Analytics (usage metrics) and AI Analytics (AI-specific metrics). Both follow the Template 5 (Data Dashboard) layout pattern.

---

## 1. Search Analytics

### Purpose
Track search usage, popular queries, user behavior, and performance metrics.

### Desktop Layout
```
┌─────────────┬──────────────────────────────────────────────────┐
│  Sidebar    │  Top Bar                                         │
│  (240px)    │  Search Analytics          [Last 30 days ▼] [Export]│
│             ├──────────────────────────────────────────────────┤
│  🔍 Search  │  Stats Row                                      │
│  💬 AI      │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │
│  📁 Docs    │  │ 12,847 │ │ 3,421  │ │ 2.4s   │ │ 87%    │  │
│  📊 Analytics│  │Queries │ │Users   │ │Avg Time│ │CTR     │  │
│  🕐 History │  └────────┘ └────────┘ └────────┘ └────────┘  │
│  🔔 Notifs  │                                                  │
│             │  Chart: Queries Over Time                        │
│  ⚙️ Settings│  ┌──────────────────────────────────────────┐   │
│  👤 Profile │  │  ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁  (line chart)         │   │
│             │  └──────────────────────────────────────────┘   │
│  User Info  │                                                  │
│             │  Table: Top Searches                             │
│             │  ┌──────────┬────────┬───────┬────────┐        │
│             │  │ Query    │ Count  │ CTR   │ Trend  │        │
│             │  ├──────────┼────────┼───────┼────────┤        │
│             │  │ nebula   │ 2,847  │ 91%   │ ↑ 23%  │        │
│             │  │ AI search│ 1,923  │ 88%   │ ↑ 15%  │        │
│             │  └──────────┴────────┴───────┴────────┘        │
│             │                                                  │
└─────────────┴──────────────────────────────────────────────────┘
```

### Components

**Stats Cards (4):**
- Queries: "12,847" (total), "↗ 23% vs last period"
- Users: "3,421" (unique), "↗ 12% vs last period"
- Avg Time: "2.4s" (search time), "✓ 15% faster"
- CTR: "87%" (click-through), "↗ 5% vs last period"

**Chart (Queries Over Time):**
- Type: Line chart with area fill
- Height: 280px
- X-axis: Date (7-day intervals)
- Y-axis: Count
- Gradient fill: primary-500 with 0.2 opacity
- Line color: primary-500
- Grid lines: gray-100 (light), gray-800 (dark)
- Tooltip: On hover, shows exact value + date

**Data Table (Top Searches):**
- Sortable columns
- Pagination: 10 per page
- Row hover: gray-50
- Trend indicator: ↑ green, ↓ red, → gray
- Search within table

### Date Range Picker
- Position: Top right
- Presets: [Today] [7 days] [30 days] [90 days] [Custom]
- Custom: Date range picker with calendar

---

## 2. AI Analytics

### Purpose
Monitor AI assistant usage, model performance, response quality, and user satisfaction.

### Key Metrics
- **AI Queries:** "4,521" total, "↗ 34% vs last period"
- **Avg Response Time:** "1.8s" (P95: 3.2s)
- **Satisfaction:** "4.2/5.0" based on 892 ratings
- **Model Usage:** GPT-4: 62%, Claude: 28%, Local: 10%

### Charts
- **Model Distribution:** Donut chart (3 segments)
  - GPT-4: 62% (blue)
  - Claude: 28% (green)
  - Local: 10% (purple)
- **Response Time Trend:** Line chart (P50, P95, P99)
- **Satisfaction Trend:** Bar chart (daily average)

### Top Questions Table
```
┌──────────────────────────┬────────┬────────┬──────────┐
│ Question                 │ Count  │ Avg    │ Avg      │
│                         │        │ Rating │ Time     │
├──────────────────────────┼────────┼────────┼──────────┤
│ What is hybrid search?  │ 847   │ 4.5    │ 1.2s    │
│ How does AI work?       │ 623   │ 4.2    │ 1.8s    │
└──────────────────────────┴────────┴────────┴──────────┘
```

### Token Usage
- Total tokens consumed: 2.4M
- Input tokens: 1.1M
- Output tokens: 1.3M
- Estimated cost: $12.47

---

## Typography

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Stat value | 30px | 700 | text-primary |
| Stat label | 14px | 400 | text-tertiary |
| Chart title | 16px | 600 | text-primary |
| Table header | 13px | 600 | text-secondary |
| Table cell | 14px | 400 | text-primary |
| Trend up | 13px | 500 | success-600 |
| Trend down | 13px | 500 | error-600 |

---

## Colors

Standard light/dark tokens. Additional chart colors:
- **Chart line:** #3b82f6 (primary-500)
- **Chart area fill:** rgba(59,130,246,0.15)
- **Grid lines:** #e5e7eb (light), #334155 (dark)
- **Satisfaction:** #22c55e (good), #f59e0b (avg), #ef4444 (poor)
- **GPT-4 segment:** #3b82f6
- **Claude segment:** #22c55e
- **Local segment:** #8b5cf6

---

## Animations

- **Stats cards:** Count-up animation (1s duration)
- **Charts:** Draw animation (1.5s duration)
- **Table rows:** Stagger fade-in (50ms delay)
- **Date change:** Cross-fade charts (300ms)

---

## Responsive

- **Desktop:** Full layout, 4 stat cards, full charts
- **Tablet:** 2×2 stat cards, charts stacked
- **Mobile:** 2×2 stat cards (smaller), charts single column, table horizontal scroll

---

## Accessibility

### Charts ARIA
```html
<figure aria-label="Queries over time chart">
  <img src="chart-fallback.png" alt="Line chart showing 12,847 queries over 30 days, peaking on day 15" />
  <figcaption>Search queries from June 1 to June 30, 2026</figcaption>
</figure>
```

### Data Table ARIA
```html
<table role="table" aria-label="Top search queries">
  <caption>Top 10 search queries by count</caption>
  <thead>
    <tr><th scope="col">Query</th><th scope="col">Count</th></tr>
  </thead>
</table>
```

---

## Developer Notes

### API
```
GET /api/v1/analytics/search?period=30d
Response: { total_queries, unique_users, avg_time, ctr, chart_data, top_queries }

GET /api/v1/analytics/ai?period=30d
Response: { total_queries, avg_response, satisfaction, model_usage, token_usage }
```

### Chart Library
Use lightweight charting library (e.g., Chart.js, Recharts) with:
- Responsive containers
- Dark mode support
- Accessible fallbacks
- Performance for 30-90 day ranges

---

**Last Updated:** 2026-07-17