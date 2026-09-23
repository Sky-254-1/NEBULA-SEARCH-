# Nebula Search Engine — Global Search Screen Visual Specification

## 1. Screen Overview

### Purpose
The command center for all search activities. Provides instant search suggestions, recent searches, and quick access to commands.

### Primary Actions
1. Type a search query
2. View and select from suggestions
3. Execute search (Enter)

### Secondary Actions
- Use voice search
- Access search history via dropdown
- Use command palette (Ctrl+K)
- Filter search type (web, documents, images)

---

## 2. Layout

The Global Search is an overlay/modal that appears on Ctrl+K or clicking the search bar in the top navigation.

### Command Palette / Search Overlay
```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│                        ┌────────────────────────┐            │
│                        │ 🔍 Search anything...  │            │
│                        │                        │            │
│                        │ Recent Searches        │            │
│                        │  🕐 AI architecture    │  [×]       │
│                        │  🕐 Document search    │  [×]       │
│                        │                        │            │
│                        │ Suggestions            │            │
│                        │  → nebula search       │            │
│                        │  → nebula pricing      │            │
│                        │                        │            │
│                        │ Commands               │            │
│                        │  > Upload document     │            │
│                        │  > Toggle dark mode    │            │
│                        │                        │            │
│                        │ [Press ↑↓ Enter Esc]   │            │
│                        └────────────────────────┘            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Layout Template
- **Template:** Custom full-screen overlay
- **Overlay backdrop:** rgba(0,0,0,0.3) with blur(4px)
- **Dialog width:** 640px (desktop), 90vw (mobile)
- **Dialog max-height:** 60vh
- **Dialog position:** top: 15vh, centered horizontally
- **Dialog bg:** --color-bg-primary
- **Dialog radius:** --radius-xl (16px)
- **Dialog shadow:** --shadow-2xl

---

## 3. Component Placement

### Search Input (Command Palette Header)
```
Height: 64px
Padding: 0 20px
Border-bottom: 1px solid --color-border
Display: flex, align center, gap 12px

Left: Search icon (24×24px, text-tertiary)
Center: Input (flex: 1, height: 100%, font-size: 18px, no border/outline)
Right: 
  - Voice search button (44×44px)
  - Search type indicator chip ("All" dropdown)
  - Escape hint: "ESC" badge (text-xs, bg gray-100, text-tertiary, radius 4px, padding 2px 6px)

Placeholder: "Search documents, web, AI..."
```

### Results Sections (below input)
```
Sections stacked vertically with labels:

Recent Searches (if available):
  Section label: "Recent Searches" — text-xs, uppercase, tracking-wide, text-tertiary, padding 8px 20px
  Items: 3-5 items
  Each item: height 44px, padding 0 20px, flex, gap 12px
    Icon: 🕐 16×16px, text-tertiary
    Text: query text, text-sm, flex 1
    Remove: [×] 32×32px icon button (hidden until hover/focus)

Suggestions (always visible when typing):
  Section label: "Suggestions" — text-xs, uppercase, text-tertiary, padding 8px 20px
  Items: 5-8 items, same format as above
  Right arrow icon: → 16×16px, text-tertiary

Commands (when typing ">"):
  Section label: "Commands" — text-xs, uppercase, text-tertiary
  Items: command items with ">" prefix
  
  Available commands:
    > upload — Upload document
    > new chat — Start new AI chat
    > toggle theme — Switch dark/light
    > goto [page] — Navigate
    > export — Export data
```

### Footer
```
Height: 40px
Padding: 0 20px
Border-top: 1px solid --color-border
Display: flex, align center, gap 16px
Text: "↑↓ Navigate · Enter Select · Esc Close" — text-xs, text-tertiary
```

---

## 4. Typography

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Input text | 18px | 400 | text-primary |
| Placeholder | 18px | 400 | text-disabled |
| Section labels | 12px | 600 | text-tertiary |
| Suggestion text | 14px | 400 | text-primary |
| Recent query text | 14px | 500 | text-primary |
| Command text | 14px | 500 | text-primary |
| Footer text | 12px | 400 | text-tertiary |

---

## 5. Colors

### Light Mode
- **Overlay bg:** rgba(0,0,0,0.3)
- **Dialog bg:** #ffffff
- **Border:** #e5e7eb
- **Selected item:** #eff6ff (primary-50)
- **Hover item:** #f9fafb
- **Section label:** #6b7280
- **Remove button:** #9ca3af (hover: #ef4444)

### Dark Mode
- **Overlay bg:** rgba(0,0,0,0.5)
- **Dialog bg:** #1e293b
- **Border:** #334155
- **Selected item:** #1e3a8a (primary-900)
- **Hover item:** #0f172a
- **Section label:** #9ca3af
- **Remove button:** #6b7280 (hover: #f87171)

---

## 6. Interaction States

### Items
| State | Background | Text |
|-------|-----------|------|
| Default | transparent | text-primary |
| Hover | gray-50 | text-primary |
| Selected (keyboard) | primary-50 | primary-600 |
| Active | gray-100 | text-primary |

### Keyboard Navigation
- ↑↓: Navigate between items (cross-section)
- Enter: Select item / Execute search
- Tab: Move between sections
- Escape: Close overlay
- Delete: Remove recent search item
- >: Switch to command mode

---

## 7. Animations

- **Open:** Fade in backdrop 150ms + scale(0.95→1) dialog 200ms
- **Close:** Fade out 150ms
- **Item selection:** Background transition 100ms
- **Section transitions:** Smooth scroll
- **Mode switch (search→command):** Icon swap 150ms

---

## 8. Responsive

- **Desktop:** 640px dialog width
- **Tablet:** 540px dialog width
- **Mobile:** 90vw width, full-width below 480px
- **Mobile position:** top: 10vh
- **Touch behavior:** Same but with larger touch targets

---

## 9. Accessibility

### Keyboard
```
Ctrl+K: Open
Escape: Close
↑↓: Navigate items
Enter: Execute/Select
Delete: Remove recent
```

### ARIA
```html
<div role="dialog" aria-modal="true" aria-label="Search or type command">
  <input role="combobox" aria-expanded="true" aria-autocomplete="list"
    aria-controls="search-suggestions" />
  <ul id="search-suggestions" role="listbox">
    <li role="option" aria-selected="true">
```

### Focus Management
- Auto-focus input on open
- Trap focus within dialog
- Return focus to trigger element on close

---

## 10. Developer Notes

### Component States
```
query: string
isOpen: boolean
mode: 'search' | 'command'
suggestions: Suggestion[]
recentSearches: RecentSearch[]
selectedIndex: number
```

### API
```
GET /api/v1/search/suggestions?q={query}&limit=8
Response: [{ text, type, icon }]

GET /api/v1/search/recent?limit=5
Response: [{ query, timestamp }]

DELETE /api/v1/search/recent/{id}
```

---

**Last Updated:** 2026-07-17