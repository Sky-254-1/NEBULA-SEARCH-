# Nebula Search Engine — Landing Page Visual Specification

## 1. Screen Overview

### Purpose
Convert first-time visitors into engaged users. Demonstrate the power, speed, and privacy of Nebula Search Engine immediately.

### Primary Actions
1. Execute a search (guest users, limited results)
2. Sign up for an account
3. Log in to existing account

### Secondary Actions
- View feature highlights
- Read documentation/privacy policy
- Watch demo video (if applicable)
- Change theme (dark/light toggle)

---

## 2. Layout

### Desktop (≥1024px)
```
┌──────────────────────────────────────────────────────────┐
│ [Logo]                     [Dark/Light] [Login] [Sign Up]│  ← 64px, transparent
├──────────────────────────────────────────────────────────┤
│                                                          │
│                                                          │
│              ┌────────────────────────────┐              │
│              │                            │              │
│              │   Search the universe      │              │
│              │   of knowledge.            │              │
│              │                            │              │
│              │   ┌──────────────────┐     │              │
│              │   │ 🔍 What would    │     │              │  ← 64px height
│              │   │ you like to know?│     │              │     max-width: 640px
│              │   │              [🎤]│     │              │
│              │   └──────────────────┘     │              │
│              │                            │              │
│              │   [Trending] [Privacy]     │              │
│              └────────────────────────────┘              │
│                                                          │
│                                                          │
│   ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐              │
│   │ Card  │  │ Card  │  │ Card  │  │ Card  │              │  ← Features section
│   └──────┘  └──────┘  └──────┘  └──────┘              │
│                                                          │
│   ┌──────────────────────────────────────────────────┐  │
│   │ Footer: Privacy | Terms | Docs | © Nebula       │  │
│   └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Grid System
- 12-column grid, 24px gutter
- Max content width: 1200px
- Hero section: center-aligned, full-width

### Key Layout Specifications
| Element | Position | Size |
|---------|----------|------|
| Top bar | Top, fixed | 64px height |
| Hero area | Center | 60vh min-height |
| Search bar | Center of hero | 640px width, 64px height |
| Feature cards | Below hero (scroll) | 280px each, 4-column grid |
| Footer | Bottom | 80px height |

---

## 3. Component Placement

### Top Navigation Bar
```
Left:    Nebula Logo (32px height, linked to /)
Right:   [🌙 Dark/Light toggle] (44×44px icon button)
         [Log in] (secondary button, 40px)
         [Sign up] (primary button, 40px)
```

- Background: Transparent (adds --color-bg-primary with 90% opacity + backdrop-blur on scroll)
- Padding: 0 24px
- Logo + nav items: flex, space-between

### Hero Section
```
Vertical centering using flexbox:
  Top margin: auto
  Content: Centered column
  Bottom margin: auto

Content stack (centered, gap 24px):
  1. Headline: "Search the universe of knowledge."
     - font: --text-5xl (48px), --font-extrabold (800)
     - line-height: 1.1
     - color: --color-text-primary
     - max-width: 720px
     - text-align: center
     
  2. Subheadline: "Private, AI-powered search that respects your privacy."
     - font: --text-xl (20px), --font-normal (400)
     - line-height: 1.5
     - color: --color-text-tertiary
     - max-width: 560px
     - text-align: center

  3. Search Bar (see below)

  4. Trust indicators row:
     - "🔒 Private by design. No tracking. No data selling."
     - font: --text-sm, --color-text-tertiary
     - Icon + text, centered
```

### Search Bar (Landing Variant)
```
Container:
  width: 640px
  height: 64px
  border-radius: 16px (radius-xl)
  border: 2px solid --color-border
  background: --color-bg-primary
  box-shadow: --shadow-lg
  padding: 0 8px 0 24px
  display: flex
  align-items: center
  gap: 12px

Focus state:
  border: 2px solid --color-primary-500
  box-shadow: 0 0 0 4px --color-primary-100, --shadow-xl
  transform: scale(1.02)
  transition: all 200ms ease-out

Children (left to right):
  - Search icon: 24×24px, --color-text-tertiary
  - Input: flex: 1, height 100%, font-size 18px
    placeholder: "What would you like to know?" --color-text-disabled
    border: none, outline: none
  - Voice button: 44×44px icon button (mic icon)
  - [Optional] AI toggle: 44×44px pill toggle
  - Divider: 1px solid --color-border, height 32px
  - Search button: 48×48px, primary-500, white icon
    
Dropdown (on focus/typing):
  - Position: absolute below search bar
  - Width: 100%
  - Max-height: 400px
  - Background: --color-bg-primary
  - Border: 1px solid --color-border
  - Border-radius: 0 0 12px 12px
  - Box-shadow: --shadow-lg
  - z-index: 1000
```

### Feature Cards Section
```
Section padding: 80px 24px
Background: --color-bg-secondary

Grid: 4 columns, gap 24px
  Desktop: 4 columns
  Tablet: 2 columns
  Mobile: 1 column

Card specifications:
  Width: 100%
  Min-height: 200px
  Padding: 32px
  Background: --color-bg-primary
  Border-radius: 12px
  Border: 1px solid --color-border
  Box-shadow: --shadow-sm

Card content:
  - Icon: 48×48px, primary-500 (e.g., shield, lightning, brain, globe)
  - Title: --text-xl (20px), --font-semibold, margin-top 16px
  - Description: --text-base, --color-text-secondary, margin-top 8px
  - CTA link: --text-sm, --color-primary-500

Card hover:
  - translateY(-4px)
  - box-shadow: --shadow-lg
  - transition: 250ms ease-out
```

### Footer
```
Height: 80px
Background: --color-bg-primary
Border-top: 1px solid --color-border
Padding: 24px

Content (flex, space-between):
  Left: "© 2026 Nebula Search. All rights reserved." --text-sm --color-text-tertiary
  Center: Privacy Policy | Terms of Service | Documentation (links, --text-sm, --color-primary-500)
  Right: [GitHub icon] [Twitter icon] [Email icon] (32×32px icon buttons)
```

---

## 4. Typography

| Element | Size | Weight | Line Height | Color |
|---------|------|--------|-------------|-------|
| Hero headline | 48px (3rem) | 800 | 1.1 | text-primary |
| Hero subheadline | 20px (1.25rem) | 400 | 1.5 | text-tertiary |
| Search input | 18px (1.125rem) | 400 | 1.5 | text-primary |
| Feature card title | 20px (1.25rem) | 600 | 1.3 | text-primary |
| Feature card desc | 16px (1rem) | 400 | 1.5 | text-secondary |
| Footer links | 14px (0.875rem) | 500 | 1.5 | primary-500 |
| Footer copyright | 14px (0.875rem) | 400 | 1.5 | text-tertiary |
| Trust text | 14px (0.875rem) | 500 | 1.5 | text-tertiary |

---

## 5. Color Usage

### Light Mode
- **Background:** #ffffff (primary), #f9fafb (feature section)
- **Text:** #111827 (headline), #4b5563 (body), #6b7280 (tertiary)
- **Search bar:** #ffffff bg, #e5e7eb border
- **Feature cards:** #ffffff bg, #e5e7eb border
- **Buttons:** #3b82f6 (primary), #ffffff text
- **Footer:** #ffffff bg, #f3f4f6 border

### Dark Mode
- **Background:** #0f172a (primary), #1e293b (feature section)
- **Text:** #f9fafb (headline), #d1d5db (body), #9ca3af (tertiary)
- **Search bar:** #1e293b bg, #334155 border
- **Feature cards:** #1e293b bg, #334155 border
- **Buttons:** #3b82f6 (primary), #ffffff text
- **Footer:** #0f172a bg, #1e293b border

---

## 6. Interaction States

### Search Bar
| State | Border | Background | Shadow |
|-------|--------|------------|--------|
| Default | gray-200 | white | shadow-lg |
| Hover | gray-300 | white | shadow-lg |
| Focus | primary-500 | white | focus ring + shadow-xl |
| Typing | primary-500 | white | focus ring |
| Loading | primary-500 | white | spin icon in input |
| Disabled | gray-200 | gray-100 | none |

### Buttons
| State | Primary Btn | Secondary Btn |
|-------|-------------|---------------|
| Default | bg primary-600, white text | transparent, border gray-300, gray-700 text |
| Hover | bg primary-700 | bg gray-50 |
| Active | scale(0.98) | scale(0.98) |
| Focus | 2px primary-500 ring | 2px primary-500 ring |
| Disabled | opacity 0.5 | opacity 0.5 |

---

## 7. Animations

### Page Load
```
Header: Fade in 300ms ease-out
Hero text: Fade in up 500ms ease-out, 100ms delay
Search bar: Fade in + scale 400ms ease-out, 200ms delay
Cards: Stagger in 300ms each, 50ms delay between
```

### Search Focus
```
Border transition: 200ms ease-out
Scale: 1 → 1.02, 200ms ease-out
Dropdown: 200ms, opacity + translateY
```

### Scroll Behavior
- Top bar gains background + blur on scroll past 100px
- Feature cards animate in on scroll (Intersection Observer)
  - opacity: 0 → 1
  - translateY: 20px → 0
  - duration: 400ms

---

## 8. Responsive Layout

### Desktop (≥1024px)
- Full layout as described above
- Search bar: 640px
- Feature cards: 4-column grid

### Laptop (1024-1279px)
- Same as desktop, slightly smaller spacing
- Feature cards: 3-column grid
- Search bar: 560px

### Tablet (768-1023px)
- Top bar: 56px height
- Search bar: 480px width
- Feature cards: 2-column grid
- Hero text: 36px (2.25rem)
- Subheadline: 18px

### Phone (<768px)
- Top bar: 56px, logo + hamburger
- Search bar: calc(100% - 32px), 56px height
- Hero text: 32px (2rem)
- Subheadline: 16px
- Feature cards: 1 column
- Navigation buttons full-width stacked

### Ultra-wide (≥1920px)
- Content max-width: 1440px (centered)
- Feature cards: 4 columns with more padding
- Hero text: 56px (3.5rem)

---

## 9. Accessibility

### Keyboard Navigation
```
Tab order:
  1. Skip to main content (hidden link)
  2. Nebula Logo (home link)
  3. Search bar
  4. Voice search button
  5. Login button
  6. Sign up button
  7. Feature cards (through tab)
  8. Footer links

Shortcuts:
  Ctrl+K: Focus search bar (global)
  /: Focus search bar
  Escape: Clear search / close dropdown
  ↓↑: Navigate suggestions
```

### ARIA Attributes
```html
<header role="banner">
<nav role="navigation" aria-label="Main navigation">
<main role="main">
<search role="search">
  <input aria-label="Search Nebula" aria-describedby="search-help">
  <div id="search-help" class="sr-only">Type to search. Press Enter to execute.</div>
</search>
<section aria-label="Features">
<footer role="contentinfo">
```

### Focus Order
1. Skip link (first tab)
2. Logo (home)
3. Search input
4. Voice button
5. Login button
6. Sign up button
7. Feature card links
8. Footer links

### Contrast
- Hero text: #111827 on #ffffff = 14:1 ✓ (AAA)
- Search placeholder: #9ca3af on #ffffff = 3.2:1 (acceptable for placeholder)
- Body text: #4b5563 on #ffffff = 7:1 ✓ (AAA)
- Primary button: #ffffff on #2563eb = 7.2:1 ✓ (AAA)

### Touch Targets
- Login/Signup buttons: 40px height (ok in desktop, but ensure 44px on mobile)
- Voice button: 44×44px ✓
- Feature card links: minimum 44×44px touch area
- Nav buttons on mobile: 44px minimum height

---

## 10. Developer Implementation Notes

### Component Hierarchy
```
AppShell
├── SkipLinks
├── TopBar
│   ├── Logo (link to /)
│   ├── ThemeToggle
│   ├── LoginButton (secondary)
│   └── SignupButton (primary)
├── HeroSection
│   ├── Headline (h1)
│   ├── Subheadline (p)
│   ├── SearchBar (landing variant)
│   │   ├── SearchIcon
│   │   ├── Input (with autocomplete)
│   │   ├── VoiceButton
│   │   ├── SearchButton
│   │   └── SuggestionsDropdown
│   └── TrustIndicators
├── FeatureCards
│   ├── FeatureCard × 4
│   │   ├── Icon
│   │   ├── Title
│   │   ├── Description
│   │   └── CTALink
└── Footer
    ├── Copyright
    ├── Links
    └── SocialIcons
```

### State Management
- `searchQuery: string`
- `isSearchFocused: boolean`
- `suggestions: string[]`
- `isLoading: boolean`
- `theme: 'light' | 'dark' | 'system'`
- `scrolledPastHero: boolean` (for top bar background)

### Performance Targets
- LCP: < 1.5s
- FCP: < 0.8s
- CLS: < 0.05
- TTI: < 2s

### Image Assets Needed
- Nebula Logo (SVG, 32px height variant)
- Feature card icons (SVG, 48×48px)
- Search icon (SVG, 24×24px)
- Mic icon (SVG, 24×24px)
- Theme icons (SVG, 20×20px)
- Social icons (SVG, 20×20px)

---

**Design System References:** 
- Layout Template: Template 3 (Full-Width Minimal)
- Components: Search Bar (Landing variant), Buttons, Feature Cards
- Animations: Page Load, Search Focus, Scroll-Triggered
- Navigation: Top Bar

**Last Updated:** 2026-07-17