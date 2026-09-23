# Nebula Search Engine — Remaining Main Application Screens

## Contents
1. Document Library
2. Document Viewer
3. Search History
4. Saved Searches
5. AI Search
6. Notifications

---

## 1. Document Library

### Purpose
Browse, search, organize, and manage uploaded documents.

### Desktop Layout (Template 2)
```
┌─────────────┬──────────────────────────────────────────────────┐
│  Sidebar    │  Top Bar                                         │
│  (240px)    │  Documents                    [+ Upload] [≡]    │
│             ├──────────────────────────────────────────────────┤
│  🔍 Search  │  Folder Nav    │  Document Grid                  │
│  💬 AI      │  ──────────    │  ┌────────┐┌────────┐┌────────┐│
│  📁 Docs    │  📁 All        │  │ 📄     ││ 📄     ││ 📄     ││
│  📊 Analytics│  📁 Recent     │  │report  ││notes   ││data.csv││
│  🕐 History │  📁 Shared     │  │PDF 2MB ││MD 0.8MB││CSV 1MB ││
│  🔔 Notifs  │  📁 Favorites  │  └────────┘└────────┘└────────┘│
│             │                │  ┌────────┐┌────────┐          │
│  ⚙️ Settings│  Tags          │  │ 📄     ││ 📄     │          │
│  👤 Profile │  #important    │  │slides  ││image   │          │
│             │  #work         │  │PPTX 5MB││PNG 3MB │          │
│             │                │  └────────┘└────────┘          │
│  User Info  │                │  [Showing 1-8 of 47] [1 2 3 ►]│
└─────────────┴──────────────────────────────────────────────────┘
```

### Components
- **Folder sidebar:** 200px, collapsible on tablet
- **Document grid:** Responsive (4-col desktop, 3-col tablet, 2-col mobile)
- **Search bar:** Inline at top of grid
- **Sort dropdown:** Name, Date, Size, Type
- **View toggle:** Grid / List view icons

### Document Card (Grid View)
```
Width: calc(25% - 12px)
Height: 180px
Padding: 16px
Border: 1px solid --color-border
Radius: 12px
Hover: shadow-md, translateY(-2px)

Content:
  File type icon: 40×40px (PDF blue, DOCX blue, MD orange, etc.)
  File name: text-sm, font-semibold, truncate
  File size: text-xs, text-tertiary
  Date: text-xs, text-tertiary
  Tags: small chips
  Checkbox: top-right corner (for multi-select)
  Context menu: [⋮] bottom-right
```

### Document List View
```
Header: Name | Type | Size | Date | Actions
Row height: 48px
Each row: icon + name + type badge + size + date + [⋮]
Hover: bg gray-50
Sort: Click header to sort
```

### Empty State
```
Icon: 📁 80×80px
"No documents yet"
"Upload your first document to get started."
[Upload Document] button
```

### Keyboard
```
Ctrl+U: Upload
N: New folder (modal)
R: Rename selected
D: Delete selected (confirmation)
Space: Toggle selection
```

---

## 2. Document Viewer

### Purpose
Preview and interact with uploaded documents (PDF, images, text).

### Desktop Layout (Template 6)
```
┌─────────────┬──────────────────────────────────────────────────┐
│  Sidebar    │  Top Bar                                         │
│  (240px)    │  ← Back to Library  [Download] [Share] [⋮]     │
│             ├──────────────────────────────────────────────────┤
│  🔍 Search  │  ┌──────────────────────┬──────────────────┐    │
│  💬 AI      │  │                      │  Metadata        │    │
│  📁 Docs    │  │  Document Viewer     │  ──────────     │    │
│  📊 Analytics│  │                      │  Name: report   │    │
│  🕐 History │  │  [PDF/Image Content]  │  Type: PDF      │    │
│  🔔 Notifs  │  │                      │  Size: 2.4 MB   │    │
│             │  │                      │  Pages: 12      │    │
│  ⚙️ Settings│  │                      │  Created: Jan 15│    │
│  👤 Profile │  │                      │  Tags: #work    │    │
│             │  │                      │                 │    │
│  User Info  │  │                      │  [Edit Tags]    │    │
│             │  │                      │                 │    │
│             │  └──────────────────────┴──────────────────┘    │
│             │                                                  │
│             │  Toolbar: [−] [100% ▼] [+] [Fit] [⬅ ➡]        │
└─────────────┴──────────────────────────────────────────────────┘
```

### Components
- **Document viewer:** flex-1, min-height 500px, white bg (like paper)
- **Metadata panel:** 320px, border-left, scrollable
- **Toolbar:** 48px, sticky top within viewer
  - Zoom controls: [-], dropdown [100%], [+], [Fit to width]
  - Page nav: [⬅ Prev] [Page 3 of 12] [Next ➡]
  - Fullscreen toggle
- **Text selection:** Selectable text for searchable PDFs
- **Loading state:** Skeleton with page outline

### Zoom Levels
25%, 50%, 75%, 100%, 125%, 150%, 200%, Fit to Width, Fit to Page

### Page Navigation
- Arrow keys: Previous/Next page
- Scroll: Continuous scroll mode
- Thumbnails sidebar (toggle): Small page previews

### Accessibility
```html
<article role="document" aria-label="Document: report.pdf">
  <div role="toolbar" aria-label="Document controls">
  <div role="status" aria-live="polite">Page 3 of 12</div>
</article>
```

---

## 3. Search History

### Purpose
View and manage past search queries.

### Desktop Layout
```
┌─────────────┬──────────────────────────────────────────────────┐
│  Sidebar    │  Top Bar                                         │
│             ├──────────────────────────────────────────────────┤
│             │  Search History                    [Clear All]   │
│             │  [🔍 Search history...]  [Filter ▼]             │
│             │                                                  │
│             │  Today                                           │
│             │  ┌──────────────────────────────────────────┐   │
│             │  │ 🕐 AI-powered search architecture 2h ago│   │
│             │  │ 🔖 📤 [⋮]                              │   │
│             │  └──────────────────────────────────────────┘   │
│             │  ┌──────────────────────────────────────────┐   │
│             │  │ 🕐 Document management best practices   │   │
│             │  │   5h ago  🔖 [⋮]                       │   │
│             │  └──────────────────────────────────────────┘   │
│             │                                                  │
│             │  Yesterday                                      │
│             │  ┌──────────────────────────────────────────┐   │
│             │  │ 🕐 Nebula API documentation  yesterday  │   │
│             │  └──────────────────────────────────────────┘   │
│             │                                                  │
│             │  [Load More]   Showing 8 of 234 items          │
└─────────────┴──────────────────────────────────────────────────┘
```

### Components
- **Grouped by date:** Today, Yesterday, This Week, Earlier
- **Search within history:** Inline search input
- **Filter:** All, With AI Summary, Saved, Documents only
- **Item actions:** [🔖 Save search] [📤 Share] [⋮ Delete]
- **Bulk select:** Checkbox per item + select all
- **Clear all:** Button with confirmation dialog

### Item Specifications
- **Height:** 64px
- **Padding:** 12px 16px
- **Border-radius:** 8px
- **Hover:** bg gray-50
- **Query text:** text-base, font-medium
- **Timestamp:** text-sm, text-tertiary
- **Actions:** Hidden until hover/focus

### Empty State
"No search history yet. Start searching to see your history here."

---

## 4. Saved Searches

### Purpose
View, manage, and re-run saved searches.

### Desktop Layout
```
┌─────────────┬──────────────────────────────────────────────────┐
│  Sidebar    │  Saved Searches                [+ New Saved]    │
│             ├──────────────────────────────────────────────────┤
│             │  [🔍 Filter saved searches...]                  │
│             │                                                  │
│             │  ┌──────────────────────────────────────────┐   │
│             │  │ 🔖 AI Search Architecture               │   │
│             │  │ "AI-powered search" · 3d ago · 12 results│   │
│             │  │ [Run] [Edit] [Share] [Delete]           │   │
│             │  ├──────────────────────────────────────────┤   │
│             │  │ 🔖 Hybrid Search Techniques             │   │
│             │  │ "hybrid search BM25" · 1w ago · 8 results│   │
│             │  │ [Run] [Edit] [Share] [Delete]           │   │
│             │  └──────────────────────────────────────────┘   │
│             │                                                  │
│             │  [Load More]   8 saved searches                │
└─────────────┴──────────────────────────────────────────────────┘
```

### Components
- **Cards** with search name, query snippet, date, result count
- **Actions:** Run (re-execute), Edit (rename/change query), Share, Delete
- **Create new:** Modal with name + query fields
- **Empty state:** "No saved searches yet. Save a search from the results page."

---

## 5. AI Search

### Purpose
AI-powered search with natural language queries and summarized results.

### Desktop Layout
```
┌─────────────┬──────────────────────────────────────────────────┐
│  Sidebar    │  Top Bar                                         │
│             ├──────────────────────────────────────────────────┤
│             │  ┌──────────────────────────────────────────┐   │
│             │  │ 🤖 Ask Nebula AI anything...     [🎤] ▶ │   │
│             │  └──────────────────────────────────────────┘   │
│             │                                                  │
│             │  ┌─ AI Response ────────────────────────────┐   │
│             │  │ 🤖 AI                                    │   │
│             │  │                                          │   │
│             │  │ Based on your documents, hybrid search   │   │
│             │  │ combines...                              │   │
│             │  │                                          │   │
│             │  │ Sources: [1] [2] [3]                    │   │
│             │  │                                          │   │
│             │  │ [Copy] [Save] [Share] [👍] [👎]        │   │
│             │  └──────────────────────────────────────────┘   │
│             │                                                  │
│             │  💡 Follow-up:                                   │
│             │  [Tell me more] [How is this different?]        │
│             │                                                  │
│             │  Related Results                                 │
│             │  ┌─ Result 1 ──────────────────────────────┐   │
│             │  │ ...                                     │   │
│             │  └─────────────────────────────────────────┘   │
└─────────────┴──────────────────────────────────────────────────┘
```

### Components
- **AI input:** Large textarea with submit, similar to chat input
- **AI response card:** Same as AI Chat Workspace
- **Follow-up suggestions:** Chips below response
- **Related results:** Compact search results below AI content
- **Sources panel:** Right panel (360px) with citations

### Difference from AI Chat
- More search-focused (AI summary + search results)
- Less conversational, more Q&A
- Results appear below AI answer

---

## 6. Notifications

### Purpose
View and manage system notifications, alerts, and updates.

### Desktop Layout
```
┌─────────────┬──────────────────────────────────────────────────┐
│  Sidebar    │  Notifications               [Mark all read]    │
│             ├──────────────────────────────────────────────────┤
│             │  [All] [Unread] [Alerts] [Updates]              │
│             │                                                  │
│             │  Today                                           │
│             │  ┌──────────────────────────────────────────┐   │
│             │  │ 🔔 New document indexed: report.pdf     │   │
│             │  │ 2m ago                              [○] │   │
│             │  ├──────────────────────────────────────────┤   │
│             │  │ ⚠️ Search index optimized successfully  │   │
│             │  │ 1h ago                              [●] │   │
│             │  └──────────────────────────────────────────┘   │
│             │                                                  │
│             │  Yesterday                                      │
│             │  ┌──────────────────────────────────────────┐   │
│             │  │ 🤖 Weekly AI summary available           │   │
│             │  │ yesterday                            [●] │   │
│             │  └──────────────────────────────────────────┘   │
└─────────────┴──────────────────────────────────────────────────┘
```

### Components
- **Tabs:** All, Unread, Alerts, Updates
- **Grouped by date:** Today, Yesterday, This Week, Earlier
- **Item height:** 56px
- **Read indicator:** ○ (unread blue dot), ● (read gray)
- **Item types:**
  - 🔔 Info (blue)
  - ⚠️ Alert (yellow)
  - ✅ Success (green)
  - ❌ Error (red)
  - 🤖 AI Update (purple)

### Notification Item
```
Flex row:
  Icon: 20×20px, colored by type
  Text: "New document indexed: report.pdf" — text-sm, font-medium
  Time: "2m ago" — text-xs, text-tertiary
  Read dot: 8px circle, blue if unread
  Actions: [⋮] dismiss, view details
```

### Empty State
"All caught up! No new notifications."

---

## Design References

All these screens use:
- **Layout:** Template 2 (Sidebar + Content)
- **Components:** Cards, List Items, Buttons, Dropdowns
- **Navigation:** Sidebar, Top Bar
- **Animations:** Page Load, List Hover, Card Hover

---

**Last Updated:** 2026-07-17