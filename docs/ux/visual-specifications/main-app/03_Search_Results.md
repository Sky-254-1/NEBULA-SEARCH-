# Nebula Search Engine — Search Results Screen Visual Specification

## 1. Screen Overview

### Purpose
Display search results with AI summary, hybrid results (keyword + semantic), and filtering capabilities.

### Primary Actions
1. View search results
2. Interact with AI summary (if enabled)
3. Filter and refine results
4. Execute new or refined search

### Secondary Actions
- Save search
- Share results
- View source citations
- Access follow-up questions

---

## 2. Layout

### Desktop (≥1024px)
```
┌─────────────┬──────────────────────────────────────────────────┬──────────────┐
│             │  Top Bar                                         │              │
│  Sidebar    │  [←] [🔍 Search query...]          [🔔] [👤]    │  Right Panel │
│  (240px)    ├──────────────────────────────────────────────────┤  (360px)     │
│             │                                                  │  (optional)  │
│  🔍 Search  │  Filters Bar                                     │              │
│  💬 AI      │  [All] [Documents] [Web] [Images] [Videos]      │  AI Context  │
│  📁 Docs    │  [Date ▼] [Type ▼] [Sort ▼]                     │  or          │
│  📊 Analytics│──────────────────────────────────────────────────│  Document    │
│  🕐 History │                                                  │  Preview     │
│  🔔 Notifs  │  Results Summary: "12 results (0.3s)"           │              │
│             │                                                  │              │
│  ⚙️ Settings│  ┌─ AI Summary ──────────────────────────────┐  │              │
│  👤 Profile │  │ 🤖 AI Summary                    [👍][👎] │  │              │
│             │  │ Nebula uses hybrid search combining...  │  │              │
│             │  │ [1] [2] [3]                             │  │              │
│  User Info  │  │ 💡 [What is hybrid?] [How does it work?]│  │              │
│             │  └──────────────────────────────────────────┘  │              │
│             │                                                  │              │
│             │  ┌─ Result 1 ────────────────────────────────┐  │              │
│             │  │ [Icon] Document Title                     │  │              │
│             │  │ https://example.com/doc                   │  │              │
│             │  │ Excerpt with <mark>highlight</mark>...   │  │              │
│             │  │ PDF · 2.4 MB · Modified 2d ago           │  │              │
│             │  │ [Save] [Share] [Preview]                  │  │              │
│             │  └──────────────────────────────────────────┘  │              │
│             │                                                  │              │
│             │  ┌─ Result 2 ────────────────────────────────┐  │              │
│             │  │ ...                                        │  │              │
│             │  └──────────────────────────────────────────┘  │              │
│             │                                                  │              │
│             │  [Load More] / Page 1 of 5                      │              │
│             │                                                  │              │
└─────────────┴──────────────────────────────────────────────────┴──────────────┘
```

### Layout Template
- **Template:** Template 2 (Sidebar + Content) with optional right panel
- **Content padding:** 24px
- **Right panel:** 360px (AI context, document preview, or sources)

---

## 3. Component Placement

### Filters Bar
```
Height: 48px
Padding: 0
Display: flex, align center, gap 8px
Border-bottom: 1px solid --color-border
Margin-bottom: 16px

Filter chips (left):
  [All] — primary chip (active), rest are default chips
  [Documents] [Web] [Images] [Videos]
  Chip height: 32px, radius: 16px (pill), padding: 0 16px

Filter dropdowns (right):
  [Date: Any time ▼] — 32px height, text-sm
  [Type: Any ▼] — 32px height
  [Sort: Relevance ▼] — 32px height
```

### Results Summary
```
"About 12 results (0.3 seconds)" — text-sm, text-tertiary
Margin-bottom: 16px
```

### AI Summary Card
```
Background: primary-50 (light), primary-900 (dark)
Border: 1px solid primary-200
Border-radius: 12px
Padding: 20px
Margin-bottom: 20px

Content:
  Header row:
    🤖 "AI Summary" badge — text-xs, bg primary-500, white text, radius 4px
    [👍 Thumbs up] [👎 Thumbs down] — 32×32px icon buttons, right-aligned
  
  AI Response text:
    Font: text-sm (14px), line-height 1.6
    Color: text-secondary
  
  Citations:
    [1] [2] [3] — inline links, primary-600, font-medium
    On click: scroll to source or show tooltip
  
  Follow-up suggestions:
    Chips: [What is hybrid search?] [How does it work?] [Tell me more]
    Margin-top: 12px
    Chip height: 28px, bg white, border gray-200, radius 14px
    
  Actions:
    [Copy] [Save] [Share] — icon buttons, 32×32px
```

### Result Cards
```
Each result:
  Padding: 16px
  Border-radius: 8px
  Background: transparent
  Border: 1px solid transparent
  Margin-bottom: 8px
  
  Hover: bg gray-50, border gray-200
  
  Content layout (flex, gap 12px):
    Left: File type icon / Favicon (24×24px)
    Center (flex 1):
      Title: text-base, font-semibold, text-primary, link color primary-600 hover
        — line-clamp: 1
      URL: text-sm, text-tertiary, truncate
        — margin-top: 2px
      Snippet: text-sm, text-secondary, line-clamp: 2
        — margin-top: 4px
        — <mark>highlight</mark> bg: yellow-200 (#fef08a)
      Metadata: text-xs, text-tertiary, margin-top: 8px
        — "Type: PDF · Size: 2.4 MB · Modified: 2d ago"
    Right (actions):
      [⋮] 44×44px icon button (menu: Save, Share, Preview, Open)
```

### Pagination / Load More
```
Option A (Desktop): Page numbers
  Center-aligned
  [← Prev] [1] [2] [3] [...] [5] [Next →]
  Page buttons: 36×36px, current page primary-500 bg
  
Option B (Mobile): Infinite scroll
  "Load more results" button at bottom
  Or auto-load on scroll to 80%
```

### Empty State
```
Centered, padding 80px 24px:
  Icon: 🔍 64×64px, text-tertiary
  "No results found for" + query
  "Try adjusting your search or filters"
  [Clear filters] [Search suggestions] buttons
```

---

## 4. Typography

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Result title | 16px | 600 | primary-600 |
| URL | 14px | 400 | text-tertiary |
| Snippet | 14px | 400 | text-secondary |
| Metadata | 12px | 400 | text-tertiary |
| AI summary text | 14px | 400 | text-secondary |
| Results count | 14px | 400 | text-tertiary |
| Filter chip text | 13px | 500 | text-secondary |
| Active filter chip | 13px | 500 | primary-600 |
| Section label | 12px | 600 | text-tertiary |

---

## 5. Color Usage

### Light Mode
- **Page bg:** #f9fafb
- **Result hover:** #f9fafb bg, #e5e7eb border
- **AI summary bg:** #eff6ff (primary-50)
- **AI summary border:** #bfdbfe (primary-200)
- **Highlight:** #fef08a (yellow-200)
- **Active filter:** #3b82f6 text, #dbeafe bg
- **Skeleton loader:** #e5e7eb

### Dark Mode
- **Page bg:** #0f172a
- **Result hover:** #1e293b bg, #334155 border
- **AI summary bg:** #1e3a8a (primary-900)
- **AI summary border:** #1e40af (primary-800)
- **Highlight:** #854d0e (yellow-700)
- **Active filter:** #60a5fa text, #1e3a8a bg
- **Skeleton loader:** #334155

---

## 6. Interaction States

### Result Cards
| State | Background | Border | Shadow |
|-------|-----------|--------|--------|
| Default | transparent | transparent | none |
| Hover | gray-50 | gray-200 | none |
| Focus | gray-50 | primary-500 | focus ring |
| Selected | primary-50 | primary-200 | none |
| Loading | skeleton shimmer | transparent | none |

### Filter Chips
| State | Background | Text Color | Border |
|-------|-----------|-----------|--------|
| Default | transparent | text-secondary | gray-200 |
| Hover | gray-100 | text-primary | gray-300 |
| Active | primary-50 | primary-600 | primary-200 |
| Focus | same as state | same | primary-500 ring |

---

## 7. Animations

- **Results appear:** Stagger fade-in-up 300ms, 50ms delay each
- **AI summary:** Streaming text appears 30ms per character
- **Filter change:** Results fade out 150ms, new results fade in 200ms
- **Result hover:** Background transition 150ms
- **Pagination:** Content cross-fade 200ms
- **Empty state:** Fade in 300ms

---

## 8. Responsive Layout

### Desktop (≥1024px)
- Full 3-column layout (sidebar + results + right panel)
- 10 results per page
- Pagination buttons

### Laptop (1024-1279px)
- No right panel (toggle to open)
- 8 results per page

### Tablet (768-1023px)
- Collapsed sidebar
- No right panel
- Filters: horizontal scrollable row
- 6 results per page
- Infinite scroll

### Phone (<768px)
- Bottom navigation
- Filters: horizontal scroll below top bar
- AI summary: collapsible card
- Results: full-width cards
- 5 results per page
- Infinite scroll
- Actions: swipe left to reveal

---

## 9. Accessibility

### Keyboard
```
Tab: Through results list
↑↓: Navigate results (when focused in list)
Enter: Open result
S: Save result (when focused)
A: Toggle AI summary
F: Focus filters
1-9: Jump to result number
Escape: Clear search / close panel
```

### ARIA
```html
<section role="search" aria-label="Search results">
  <div role="status" aria-live="polite">12 results found</div>
  <div role="region" aria-label="AI generated summary">
  <ul aria-label="Search results">
    <li role="article">
      <a href="/doc/123" aria-label="Document Title - PDF, 2.4 MB">
```

### Focus
- Focus first result after search
- Focus AI summary toggle after AI loads
- Return focus to search bar on new search

---

## 10. Developer Notes

### Component Hierarchy
```
SearchResultsPage
├── AppShell (sidebar + top bar)
├── FiltersBar
│   ├── TypeChips (All, Documents, Web, etc.)
│   └── FilterDropdowns (Date, Type, Sort)
├── ResultsContent
│   ├── ResultsSummary
│   ├── AISummaryCard (conditional)
│   │   ├── Badge + Feedback
│   │   ├── ResponseText (streaming)
│   │   ├── Citations
│   │   └── FollowUpChips
│   ├── ResultsList
│   │   ├── ResultCard × N
│   │   │   ├── Icon + Title + URL
│   │   │   ├── Snippet + Highlights
│   │   │   ├── Metadata
│   │   │   └── ActionsMenu
│   │   └── EmptyState
│   └── Pagination
└── RightPanel (optional)
    ├── AIContextPanel
    └── DocumentPreviewPanel
```

### State
```
query: string
results: SearchResult[]
totalResults: number
searchTime: number
aiSummary: { text, citations, confidence }
isLoading: boolean
isStreaming: boolean
activeFilters: { type, date, sort }
page: number
selectedResult: string | null
```

### API
```
GET /api/v1/search?q={query}&type={type}&page={page}&sort={sort}
Response: {
  results: [{ id, title, url, snippet, type, size, date }],
  total: 12,
  time: 0.3,
  ai_summary: { text, citations, confidence }
}
```

---

**Last Updated:** 2026-07-17