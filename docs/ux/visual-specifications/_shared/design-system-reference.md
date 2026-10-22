# Nebula Search Engine — Design System Reference for Visual Specifications

## Purpose

This document consolidates the complete design token library from the UX documentation into a single quick-reference for use across all visual specifications. All screen specs reference these tokens.

## Color System

### Light Mode
```
Backgrounds:
  --color-bg-primary:      #ffffff        (Main page background)
  --color-bg-secondary:    #f9fafb        (Sidebar, cards)
  --color-bg-tertiary:     #f3f4f6        (Hover states, elevated)
  
Text:
  --color-text-primary:    #111827        (Headings)
  --color-text-secondary:  #4b5563        (Body text)
  --color-text-tertiary:   #6b7280        (Labels, secondary info)
  --color-text-disabled:   #9ca3af        (Disabled state)
  --color-text-inverse:    #ffffff        (On primary/dark bg)
  
Brand:
  --color-primary-50:      #eff6ff        (AI card bg, selected)
  --color-primary-100:     #dbeafe        (Light highlight)
  --color-primary-200:     #bfdbfe        (Borders)
  --color-primary-400:     #60a5fa        (Hover links)
  --color-primary-500:     #3b82f6        (Primary actions, links)
  --color-primary-600:     #2563eb        (Button hover)
  --color-primary-700:     #1d4ed8        (Button active)

Semantic:
  --color-success:         #22c55e        (Success states)
  --color-warning:         #f59e0b        (Warning states)  
  --color-error:           #ef4444        (Error states)
  --color-info:            #3b82f6        (Info states)
  
Borders & Dividers:
  --color-border:          #e5e7eb        (Default border)
  --color-border-light:    #f3f4f6        (Subtle divider)
  --color-border-focus:    #3b82f6        (Focus ring)
  
Shadows:
  --shadow-sm:  0 1px 2px rgba(0,0,0,0.05)
  --shadow-md:  0 4px 6px -1px rgba(0,0,0,0.10)
  --shadow-lg:  0 10px 15px -3px rgba(0,0,0,0.10)
  --shadow-xl:  0 20px 25px -5px rgba(0,0,0,0.10)
```

### Dark Mode
```
Backgrounds:
  --color-bg-primary:      #0f172a        (Main background)
  --color-bg-secondary:    #1e293b        (Sidebar, cards)
  --color-bg-tertiary:     #1f2937        (Elevated surfaces)
  --color-bg-elevated:     #334155        (Modals, dropdowns)
  
Text:
  --color-text-primary:    #f9fafb        (Headings, body)
  --color-text-secondary:  #d1d5db        (Secondary text)
  --color-text-tertiary:   #9ca3af        (Labels, captions)
  --color-text-disabled:   #6b7280        (Disabled)
  
Brand (adjusted):
  --color-primary-400:     #60a5fa        (Primary text, links)
  --color-primary-500:     #3b82f6        (Buttons)
  --color-primary-600:     #2563eb        (Button hover)
  --color-primary-700:     #1d4ed8        (Active)
  
Borders:
  --color-border:          #334155        (Default border)
  --color-border-light:    #1e293b        (Subtle)
  
Shadows:
  --shadow-sm:  0 1px 2px rgba(0,0,0,0.30)
  --shadow-md:  0 4px 6px -1px rgba(0,0,0,0.40)
  --shadow-lg:  0 10px 15px -3px rgba(0,0,0,0.50)
```

## Typography Scale

### Desktop (≥1024px)
```
--text-xs:     0.75rem  (12px)  — 400/500, 1.5    — Captions, labels
--text-sm:     0.875rem (14px)  — 400/500, 1.5    — Secondary text
--text-base:   1rem     (16px)  — 400,     1.5    — Body text
--text-lg:     1.125rem (18px)  — 500,     1.5    — Lead text
--text-xl:     1.25rem  (20px)  — 600,     1.4    — Large text
--text-2xl:    1.5rem   (24px)  — 600,     1.3    — H3
--text-3xl:    1.875rem (30px)  — 700,     1.25   — H2
--text-4xl:    2.25rem  (36px)  — 700,     1.2    — H1
--text-5xl:    3rem     (48px)  — 800,     1.1    — Hero
```

### Mobile (<768px)
```
--text-xs:     0.75rem  (12px)
--text-sm:     0.8125rem(13px)
--text-base:   0.9375rem(15px)
--text-lg:     1rem     (16px)
--text-xl:     1.125rem (18px)
--text-2xl:    1.25rem  (20px)
--text-3xl:    1.5rem   (24px)
--text-4xl:    1.75rem  (28px)
--text-5xl:    2rem     (32px)
```

### Weights
```
--font-normal:    400    (Body, labels)
--font-medium:    500    (Subheadings, buttons)
--font-semibold:  600    (H3, H4, strong emphasis)
--font-bold:      700    (H1, H2)
--font-extrabold: 800    (Hero text)
```

## Spacing (8px Grid)

```
--space-1:  0.25rem  (4px)    — Micro spacing
--space-2:  0.5rem   (8px)    — Tight spacing
--space-3:  0.75rem  (12px)   — Compact spacing
--space-4:  1rem     (16px)   — Standard padding
--space-5:  1.25rem  (20px)   — Comfortable
--space-6:  1.5rem   (24px)   — Section spacing
--space-8:  2rem     (32px)   — Large spacing
--space-10: 2.5rem   (40px)   — X-large
--space-12: 3rem     (48px)   — Section margins
--space-16: 4rem     (64px)   — Page sections
--space-20: 5rem     (80px)   — Hero spacing
--space-24: 6rem     (96px)   — Max spacing
```

## Border Radius

```
--radius-sm:    0.25rem (4px)    — Badges, tags
--radius-md:    0.5rem  (8px)    — Buttons, inputs, cards
--radius-lg:    0.75rem (12px)   — Cards, panels
--radius-xl:    1rem    (16px)   — Modals, dialogs
--radius-2xl:   1.5rem  (24px)   — Large cards
--radius-full:  9999px           — Avatars, pills
```

## Z-Index Scale

```
--z-base:          0
--z-dropdown:      1000
--z-sticky:        1020
--z-fixed:         1030
--z-modal-bg:      1040
--z-modal:         1050
--z-popover:       1060
--z-tooltip:       1070
--z-toast:         1080
--z-max:           9999
```

## Touch Targets (WCAG 2.5.5)

| Element | Minimum | Recommended |
|---------|---------|-------------|
| Icon buttons | 44×44px | 48×48px |
| Text buttons | 44×44px | 48×48px |
| Form inputs | 44px height | 48px height |
| Checkboxes/Radios | 24×24px + padding | 28×28px + 8px |
| Toggle switches | 44×24px | 48×28px |
| Navigation items | 44px height | 56px height |
| FAB | 56×56px | 64×64px |

## Breakpoints

```
--screen-sm:    640px   (Large phones)
--screen-md:    768px   (Tablets portrait)
--screen-lg:    1024px  (Tablets landscape, small laptops)
--screen-xl:    1280px  (Desktops)
--screen-2xl:   1536px  (Large screens, ultra-wide)
```

## Motion Tokens

```
Durations:
  --duration-fast:     150ms   (Micro-interactions: button press, hover)
  --duration-normal:   250ms   (State transitions: modal, drawer)
  --duration-slow:     350ms   (Page transitions, panel slides)
  --duration-slower:   500ms   (Background animations)

Easing:
  --ease-out:     cubic-bezier(0, 0, 0.2, 1)     (Standard exit)
  --ease-in:      cubic-bezier(0.4, 0, 1, 1)     (Standard enter)  
  --ease-in-out:  cubic-bezier(0.4, 0, 0.2, 1)   (Standard both)
  --ease-bounce:  cubic-bezier(0.68, -0.55, 0.265, 1.55)
```

## Component Height Tokens

```
Button heights:    32px (sm), 40px (md), 48px (lg)
Input heights:     32px (sm), 40px (md), 48px (lg)
Top bar height:    64px (desktop), 56px (mobile)
Bottom nav:        56px (mobile only)
Sidebar width:     240px (collapsed icons), 280px (expanded labels)
Right panel:       360px (AI chat, document preview)
```

---

**Last Updated:** 2026-07-17
**References:** docs/ux/04_Design_System.md, docs/ux/05_Component_Library.md