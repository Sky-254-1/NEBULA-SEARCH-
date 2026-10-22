# Nebula Search Engine — Tablet Screen Specifications

## Overview

Tablet screens bridge the gap between mobile and desktop, offering enhanced layouts while maintaining touch-friendly interactions.

---

## Breakpoints

| Orientation | Min Width | Max Width |
|-------------|-----------|-----------|
| Portrait | 768px | 1023px |
| Landscape | 1024px | 1279px |

---

## Common Tablet Patterns

### Navigation (Portrait)
```
┌──────────────────────────────────────────────┐
│  [≡] [Nebula Logo]    [🔍] [🔔] [👤]       │  ← 56px
├──────────────────────────────────────────────┤
│                                              │
│              Content Area                    │
│              (2-column layout)               │
│                                              │
│                                              │
└──────────────────────────────────────────────┘
```
- **Sidebar:** Hidden by default, overlay on hamburger click
- **Bottom nav:** Hidden (sidebar overlay instead)
- **Top bar:** 56px height
- **Content:** 2-column grid with 20px gaps

### Navigation (Landscape)
```
┌─────────────┬────────────────────────────────┐
│  Sidebar    │  Top Bar (56px)                │
│  (collapsed)│  [Nebula] [🔍] [🔔] [👤]     │
│  64px icons ├────────────────────────────────┤
│             │                                │
│  🔍         │  Content Area                  │
│  💬         │  (3-column layout)             │
│  📁         │                                │
│  📊         │                                │
│  🕐         │                                │
│             │                                │
│  ⚙️         │                                │
└─────────────┴────────────────────────────────┘
```
- **Sidebar:** 64px collapsed (icons only, expand on tap)
- **Content:** 3-column grid with 20px gaps

---

## 1. Tablet Dashboard (Portrait)

```
┌──────────────────────────────────────────────┐
│  [≡] Nebula                      [🔔] [👤]  │
├──────────────────────────────────────────────┤
│  Good afternoon, Alex!                       │
│                                              │
│  ┌──────────┐ ┌──────────┐                  │
│  │ 12       │ │ 8        │                  │
│  │ Searches │ │ Saved    │                  │
│  └──────────┘ └──────────┘                  │
│  ┌──────────┐                               │
│  │ 2.4GB    │                               │
│  │ Storage  │                               │
│  └──────────┘                               │
│                                              │
│  Recent Searches              [View all →]  │
│  ┌──────────────────────────────────────┐   │
│  │ 🕐 AI architecture          2h ago   │   │
│  │ 🕐 Document search          5h ago   │   │
│  │ 🕐 API docs              yesterday  │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  Documents                                   │
│  ┌────────┐ ┌────────┐ ┌────────┐          │
│  │ Doc 1  │ │ Doc 2  │ │ Doc 3  │          │
│  └────────┘ └────────┘ └────────┘          │
└──────────────────────────────────────────────┘
```

### Adaptations
- **Stats:** 3 cards in row → 2 cards + 1 below
- **Recent items:** Full-width list
- **Documents:** 3 column grid
- **Touch targets:** 44px minimum

---

## 2. Tablet Search Results (Landscape)

```
┌────────┬─────────────────────────────────────┐
│ 🔍     │  Top Bar                           │
│ 💬     │  [Nebula] [🔍 query...]  [🔔] [👤] │
│ 📁     ├─────────────────────────────────────┤
│ 📊     │  Filters: [All] [Docs] [Web] →     │
│ 🕐     │                                     │
│        │  ┌─ AI Summary ────────────────┐   │
│ ⚙️     │  │ Hybrid search combines...   │   │
│        │  └──────────────────────────────┘   │
│        │                                     │
│        │  ┌─ Result 1 ──┐ ┌─ Result 2 ──┐  │
│        │  │ Title       │ │ Title       │  │
│        │  │ Snippet...  │ │ Snippet...  │  │
│        │  └─────────────┘ └─────────────┘  │
│        │                                     │
│        │  [Load More]                       │
└────────┴─────────────────────────────────────┘
```

### Adaptations
- **Sidebar:** 64px collapsed (icons only)
- **Results:** 2-column grid
- **AI Summary:** Compact, collapsible
- **Right panel:** Overlay (toggle)

---

## 3. Tablet AI Chat (Landscape)

```
┌────────┬─────────────────────────────────────┬────────┐
│ 🔍     │ Chat Header                        │ Sources│
│ 💬     │ [← New Chat] [GPT-4 ▼]    [⋮]    │        │
│ 📁     ├─────────────────────────────────────┤ [1]    │
│ 📊     │ Messages                           │ [2]    │
│ 🕐     │ 💬 What is hybrid search?          │ [3]    │
│        │ ┌──────────────────────────┐       │        │
│ ⚙️     │ │ Hybrid search combines..│       │        │
│        │ └──────────────────────────┘       │        │
│        │                                     │        │
│        ├─────────────────────────────────────┤        │
│        │ [Type a message...]         [▶]   │        │
└────────┴─────────────────────────────────────┴────────┘
```

### Adaptations
- **Three-column layout** (sidebar + chat + sources)
- **Sources panel:** 280px (vs 360px desktop)
- **Messages:** 80% max width

---

## Foldable Devices

### Folded (Phone Mode)
Same as mobile specifications (320-599px)

### Unfolded (Tablet Mode)
Same as tablet portrait (800-1024px)

### Half-Fold (Dual Screen)
```
┌───────────────────┬───────────────────┐
│                   │                   │
│   Content Panel 1 │  Content Panel 2  │
│                   │                   │
│   (e.g., Chat)    │  (e.g., Sources)  │
│                   │                   │
└───────────────────┴───────────────────┘
```

### CSS Spanning
```css
@media (spanning: right-fold) {
  .chat-panel { width: calc(50vw - var(--fold-gap)); }
  .sources-panel { width: calc(50vw - var(--fold-gap)); }
}
```

---

## Tablet Testing Checklist

- [ ] iPad Mini (768px)
- [ ] iPad Air (820px)
- [ ] iPad Pro (1024px)
- [ ] Samsung Tab S8 (800px)
- [ ] Galaxy Z Fold (unfolded: 1700px)
- [ ] Pixel Fold (unfolded: 1500px)

---

**Last Updated:** 2026-07-17