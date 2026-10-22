# Nebula Search Engine — Navigation Patterns

## Purpose

Defines all navigation patterns used across screens. These ensure consistent navigation behavior regardless of screen size.

---

## 1. Desktop Sidebar Navigation

### Structure
```
┌──────────────────────┐
│ Nebula Logo    [≡]   │  ← 56px header
├──────────────────────┤
│                      │
│ 🔍 Search            │  ← Active: 3px left border primary-500
│ 💬 AI Assistant      │     Icon: 24px, Label: 14px medium
│ 📁 Documents         │     Height: 48px, Padding: 0 16px
│ 📊 Analytics         │     Hover: bg-tertiary
│ 🕐 History           │     Gap between items: 4px
│ 🔔 Notifications     │
│                      │
├──────────────────────┤
│                      │
│ ⚙️ Settings          │  ← Bottom section
│ 👤 Profile           │
│                      │
├──────────────────────┤
│ User Avatar + Name   │  ← 64px footer
│ [Logout]             │
└──────────────────────┘
```

### States
- **Default:** Gray-600 icon, gray-700 text
- **Hover:** bg-tertiary background
- **Active:** primary-500 left border, primary-600 text, primary-50 bg
- **Collapsed:** 64px width, icons only, tooltip on hover

### Collapse Behavior
- Toggle button in sidebar header
- Smooth transition: 250ms ease-out
- Width: 240px → 64px
- Labels fade out, icons remain
- Tooltip appears on hover (300ms delay)

---

## 2. Mobile Bottom Navigation

### Structure
```
┌──────────────────────────────────────────────┐
│                                              │
│              Content Area                    │
│                                              │
├──────────────────────────────────────────────┤
│  🔍    💬    📁    📊    👤                  │
│ Search  AI   Docs  Analytics Profile         │
│                                              │
└──────────────────────────────────────────────┘
```

### Specifications
- **Height:** 56px + env(safe-area-inset-bottom)
- **Background:** --color-bg-primary
- **Border-top:** 1px solid --color-border
- **Max tabs:** 5
- **Tab width:** Equal distribution (20% each)
- **Icon size:** 24×24px
- **Label size:** 10-11px, --font-medium
- **Active indicator:** 3px top border, primary-500
- **Active color:** primary-600 text
- **Inactive color:** gray-400 text

### States
- **Default:** Gray icon + label
- **Active:** Primary icon + label, top border indicator
- **Hover (if touch):** Slight background change
- **Badge:** 16px red dot, top-right of icon, for notifications

---

## 3. Tablet Collapsible Sidebar

### Behavior
- **Default:** Hidden, hamburger menu in top bar
- **Open:** Overlay from left, 280px width
- **Backdrop:** rgba(0,0,0,0.5), click to close
- **Animation:** Slide in 250ms ease-out
- **Auto-hide:** On scroll down, show on scroll up

### Trigger Areas
- Hamburger icon in top bar (44×44px)
- Swipe from left edge (30px trigger zone)
- Keyboard shortcut: Ctrl+B

---

## 4. Top Bar Navigation

### Structure (Desktop)
```
┌──────────────────────────────────────────────────────────────┐
│ [☰] [Nebula Logo]  [🔍 Search anything... Ctrl+K]  [⋮] [👤]│
└──────────────────────────────────────────────────────────────┘
```

### Sections
1. **Left:** Hamburger (sidebar toggle) + Logo (48px width)
2. **Center:** Search bar (flex-1, max 640px)
3. **Right:** Actions (notifications, settings) + User avatar

### Height
- Desktop: 64px
- Tablet: 56px
- Mobile: 56px

### Scrolling Behavior
- Sticky top: position: sticky, top: 0
- z-index: --z-sticky (1020)
- On scroll: Add subtle shadow (shadow-sm)
- Background: --color-bg-primary with backdrop-filter: blur(12px)

---

## 5. Breadcrumb Navigation

### Structure
```
Home  ›  Documents  ›  Project Reports  ›  Q4 Analysis
```

### Specifications
- **Font:** --text-sm, --color-text-tertiary
- **Separator:** "›" or "/", gray-400
- **Last item:** --color-text-primary, --font-medium (not a link)
- **Links:** --color-primary-500, hover: underline
- **Padding:** 8px 0, 16px bottom margin

### Responsive
- Desktop: Full breadcrumb
- Tablet: Truncate middle items with "..."
- Mobile: Show only last 2 items

---

## 6. Tab Navigation

### Structure
```
┌──────────────────────────────────────────────┐
│ [General] [Privacy] [Notifications] [AI]     │
│ ───────────────                              │  ← Active indicator
└──────────────────────────────────────────────┘
```

### Specifications
- **Tab height:** 40px
- **Tab padding:** 0 16px
- **Font:** --text-sm, --font-medium
- **Active:** primary-600 text, 2px bottom border primary-500
- **Inactive:** gray-500 text
- **Hover:** gray-100 background
- **Gap between tabs:** 4px
- **Scrollable:** On mobile, horizontal scroll with hidden scrollbar

---

## 7. Command Palette (Ctrl+K)

### Structure
```
┌──────────────────────────────────────────────┐
│ 🔍 Type a command or search...               │
├──────────────────────────────────────────────┤
│                                              │
│ Recent Searches                              │
│  🕐 nebula search engine features            │
│  🕐 AI powered search                        │
│                                              │
│ Commands                                     │
│  > Upload document                           │
│  > View analytics                            │
│  > Toggle dark mode                          │
│  > New chat                                  │
│                                              │
│ Suggestions                                  │
│  → nebula search engine pricing              │
│  → nebula search engine documentation        │
│                                              │
├──────────────────────────────────────────────┤
│ Press ↑↓ to navigate, Enter to select, Esc to close│
└──────────────────────────────────────────────┘
```

### Specifications
- **Overlay:** Full-screen, backdrop rgba(0,0,0,0.3)
- **Dialog width:** 640px (desktop), 90vw (mobile)
- **Dialog max-height:** 60vh
- **Dialog position:** Top 20% of viewport
- **Input height:** 56px
- **Input font:** --text-lg
- **Item height:** 44px
- **Item padding:** 0 16px
- **Selected item:** primary-50 background
- **Z-index:** --z-modal (1050)
- **Animation:** Fade in 150ms + scale 0.95→1

### Keyboard
- Ctrl+K: Open
- Escape: Close
- ↑↓: Navigate items
- Enter: Select/Execute
- Tab: Next section

---

## 8. Quick Navigation (Ctrl+1-6)

| Shortcut | Destination |
|----------|-------------|
| Ctrl+1 | Search |
| Ctrl+2 | AI Assistant |
| Ctrl+3 | Documents |
| Ctrl+4 | Analytics |
| Ctrl+5 | History |
| Ctrl+6 | Notifications |

---

## 9. Contextual Navigation

### Right-Click Menu
```
┌──────────────────────┐
│ Open in new tab      │
│ Open in split view   │
├──────────────────────┤
│ Copy link            │
│ Copy text            │
├──────────────────────┤
│ Save to...           │
│ Share...             │
├──────────────────────┤
│ Delete               │  ← Red text for destructive
└──────────────────────┘
```

### Specifications
- **Min width:** 200px
- **Max width:** 320px
- **Item height:** 36px
- **Padding:** 0 12px
- **Shadow:** shadow-lg
- **Radius:** 8px
- **Z-index:** --z-popover (1060)

---

## 10. Skip Links (Accessibility)

```
[Skip to main content]  [Skip to search]  [Skip to navigation]
```

- Position: Top of page, hidden until focused
- Focus: Slide down from top, primary-500 bg, white text
- z-index: --z-max (9999)
- Tab order: 1st interactive elements on page

---

**Last Updated:** 2026-07-17