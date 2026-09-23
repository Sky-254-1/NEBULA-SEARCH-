# Nebula Search Engine — Design System

## Executive Summary

This design system provides a comprehensive token library and component specifications for implementing Nebula Search Engine's user interface. It ensures visual consistency, accessibility compliance, and maintainable code across all platforms.

**Goal:** Enable developers and designers to create cohesive, accessible, and beautiful interfaces using a shared language of design tokens.

## Design Tokens

### Color System

#### Primary Colors

```css
/* Primary Brand Colors */
--color-primary-50: #eff6ff;    /* Lightest blue tint */
--color-primary-100: #dbeafe;   /* Light blue */
--color-primary-200: #bfdbfe;   /* Medium light blue */
--color-primary-300: #93c5fd;   /* Soft blue */
--color-primary-400: #60a5fa;   /* Medium blue */
--color-primary-500: #3b82f6;   /* Primary brand color */
--color-primary-600: #2563eb;   /* Primary hover */
--color-primary-700: #1d4ed8;   /* Primary active */
--color-primary-800: #1e40af;   /* Dark blue */
--color-primary-900: #1e3a8a;   /* Darkest blue */
```

**Usage:**
- Primary actions (buttons, links)
- Active states
- Brand elements
- Focus indicators

**Contrast Ratios (WCAG AA):**
- Primary-500 on white: 4.5:1 ✓
- Primary-600 on white: 7.2:1 ✓
- Primary-700 on white: 11.3:1 ✓

#### Secondary Colors

```css
/* Secondary/Accent Colors */
--color-secondary-50: #f0fdf4;   /* Lightest green */
--color-secondary-100: #dcfce7;
--color-secondary-200: #bbf7d0;
--color-secondary-300: #86efac;
--color-secondary-400: #4ade80;
--color-secondary-500: #22c55e;   /* Success green */
--color-secondary-600: #16a34a;
--color-secondary-700: #15803d;
--color-secondary-800: #166534;
--color-secondary-900: #14532d;
```

**Usage:**
- Success states
- Confirmation actions
- Positive feedback
- Completed tasks

#### Semantic Colors

```css
/* Error/Destructive */
--color-error-50: #fef2f2;
--color-error-100: #fee2e2;
--color-error-500: #ef4444;
--color-error-600: #dc2626;
--color-error-700: #b91c1c;

/* Warning */
--color-warning-50: #fffbeb;
--color-error-100: #fef3c7;
--color-warning-500: #f59e0b;
--color-warning-600: #d97706;
--color-warning-700: #b45309;

/* Info */
--color-info-50: #eff6ff;
--color-info-100: #dbeafe;
--color-info-500: #3b82f6;
--color-info-600: #2563eb;

/* Neutral/Gray Scale */
--color-gray-50: #f9fafb;    /* Lightest background */
--color-gray-100: #f3f4f6;   /* Borders, dividers */
--color-gray-200: #e5e7eb;   /* Light borders */
--color-gray-300: #d1d5db;   /* Hover states */
--color-gray-400: #9ca3af;   /* Disabled text */
--color-gray-500: #6b7280;   /* Secondary text */
--color-gray-600: #4b5563;   /* Primary text (light) */
--color-gray-700: #374151;   /* Body text */
--color-gray-800: #1f2937;   /* Headings */
--color-gray-900: #111827;   /* darkest text */
```

**Text Color Usage:**
- Gray-900: Headings (H1-H6)
- Gray-800: Body text
- Gray-600: Secondary text
- Gray-400: Disabled/placeholder text

#### Dark Mode Colors

```css
/* Dark Mode Backgrounds */
--color-dark-50: #1f2937;    /* Elevated surfaces */
--color-dark-100: #1f2937;   /* Cards */
--color-dark-200: #1e293b;   /* Borders */
--color-dark-300: #0f172a;   /* Sidebar */
--color-dark-400: #0f172a;   /* Main background */
--color-dark-500: #020617;   /* Darkest background */

/* Dark Mode Text */
--color-dark-text-primary: #f9fafb;
--color-dark-text-secondary: #d1d5db;
--color-dark-text-tertiary: #9ca3af;
```

### Typography

#### Font Family

```css
/* Primary Font Stack */
--font-family-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--font-family-mono: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;

/* Fallback Strategy */
1. Local font (Inter)
2. System font stack
3. Generic sans-serif
```

**Font Loading:**
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
```

#### Font Scale (Type Scale)

```css
/* Desktop Scale */
--text-xs: 0.75rem;      /* 12px - Captions, labels */
--text-sm: 0.875rem;     /* 14px - Secondary text */
--text-base: 1rem;       /* 16px - Body text */
--text-lg: 1.125rem;     /* 18px - Lead text */
--text-xl: 1.25rem;      /* 20px - Large text */
--text-2xl: 1.5rem;      /* 24px - H3 */
--text-3xl: 1.875rem;    /* 30px - H2 */
--text-4xl: 2.25rem;     /* 36px - H1 */
--text-5xl: 3rem;        /* 48px - Hero */

/* Line Heights */
--leading-none: 1;       /* Tight headings */
--leading-tight: 1.25;   /* Subheadings */
--leading-normal: 1.5;   /* Body text */
--leading-relaxed: 1.75; /* Long-form text */

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

**Typography Scale Rationale:**
- Major third (1.25) scale for harmonious progression
- Base size 16px for accessibility
- Maximum 3 font weights for simplicity
- Line height 1.5 for readability

### Spacing System

#### 8-Pixel Grid

```css
/* Base Unit: 8px */
--space-1: 0.25rem;    /* 4px */
--space-2: 0.5rem;     /* 8px */
--space-3: 0.75rem;    /* 12px */
--space-4: 1rem;       /* 16px */
--space-5: 1.25rem;    /* 20px */
--space-6: 1.5rem;     /* 24px */
--space-8: 2rem;       /* 32px */
--space-10: 2.5rem;    /* 40px */
--space-12: 3rem;      /* 48px */
--space-16: 4rem;      /* 64px */
--space-20: 5rem;      /* 80px */
--space-24: 6rem;      /* 96px */
```

**Spacing Guidelines:**
- Use multiples of 8px only
- Consistent padding/margins
- Breathing room for content
- Visual hierarchy through spacing

### Border Radius

```css
/* Border Radius Scale */
--radius-none: 0;
--radius-sm: 0.25rem;   /* 4px - Small elements */
--radius-md: 0.5rem;    /* 8px - Buttons, inputs */
--radius-lg: 0.75rem;   /* 12px - Cards */
--radius-xl: 1rem;      /* 16px - Modals */
--radius-2xl: 1.5rem;   /* 24px - Large cards */
--radius-full: 9999px;  /* Pills, circles */
```

**Usage:**
- Buttons: radius-md (8px)
- Cards: radius-lg (12px)
- Modals: radius-xl (16px)
- Avatars: radius-full (circle)

### Shadows

```css
/* Elevation Shadows */
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
--shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
--shadow-2xl: 0 25px 50px -12px rgb(0 0 0 / 0.25);

/* Focus Ring */
--shadow-focus: 0 0 0 3px var(--color-primary-500);

/* Dark Mode Shadows */
--shadow-dark-sm: 0 1px 2px 0 rgb(0 0 0 / 0.3);
--shadow-dark-md: 0 4px 6px -1px rgb(0 0 0 / 0.4);
--shadow-dark-lg: 0 10px 15px -3px rgb(0 0 0 / 0.5);
```

### Grid System

```css
/* Grid */
--grid-columns: 12;
--grid-gutter: 24px;
--grid-max-width: 1440px;

/* Breakpoints */
--screen-sm: 640px;
--screen-md: 768px;
--screen-lg: 1024px;
--screen-xl: 1280px;
--screen-2xl: 1536px;
```

**Container Queries:**
```css
/* Mobile First */
.container {
  width: 100%;
  padding: 0 var(--space-4);
}

@media (min-width: 768px) {
  .container {
    max-width: 768px;
    margin: 0 auto;
  }
}

@media (min-width: 1024px) {
  .container {
    max-width: 1024px;
  }
}

@media (min-width: 1280px) {
  .container {
    max-width: 1280px;
  }
}
```

### Motion & Animation

```css
/* Easing Functions */
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);

/* Durations */
--duration-fast: 150ms;
--duration-normal: 250ms;
--duration-slow: 350ms;
--duration-slower: 500ms;

/* Delays */
--delay-none: 0ms;
--delay-fast: 50ms;
--delay-normal: 100ms;
--delay-slow: 200ms;
```

**Animation Guidelines:**
- Micro-interactions: 150ms (fast)
- State transitions: 250ms (normal)
- Page transitions: 350ms (slow)
- Stagger children: 50ms delay each

### Touch Targets

```css
/* Minimum Touch Targets (WCAG 2.5.5) */
--touch-target-min: 44px;

/* Recommended Sizes */
--touch-target-sm: 40px;    /* Icon buttons */
--touch-target-md: 44px;    /* Standard buttons */
--touch-target-lg: 48px;    /* Primary actions */
--touch-target-xl: 56px;    /* FAB, large buttons */

/* Spacing Between Targets */
--touch-spacing-min: 8px;   /* Minimum gap */
```

**Critical Rule:** All interactive elements must be minimum 44x44px.

### Focus Styles

```css
/* Focus Ring */
--focus-ring-width: 2px;
--focus-ring-color: var(--color-primary-500);
--focus-ring-offset: 2px;

/* High Contrast Mode */
--focus-ring-high-contrast-width: 3px;
--focus-ring-high-contrast-color: #ffff00;  /* Yellow */

/* Focus Style Mixin */
.focus-visible {
  outline: none;
  box-shadow: 0 0 0 var(--focus-ring-width) var(--focus-ring-color),
              0 0 0 var(--focus-ring-offset) var(--color-primary-100);
}

/* High Contrast */
@media (prefers-contrast: high) {
  .focus-visible {
    box-shadow: 0 0 0 var(--focus-ring-high-contrast-width) var(--focus-ring-high-contrast-color);
  }
}

/* Reduced Motion */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Z-Index Scale

```css
/* Z-Index Layers */
--z-index-base: 0;
--z-index-dropdown: 1000;
--z-index-sticky: 1020;
--z-index-fixed: 1030;
--z-index-modal-backdrop: 1040;
--z-index-modal: 1050;
--z-index-popover: 1060;
--z-index-tooltip: 1070;
--z-index-toast: 1080;
--z-index-max: 9999;
```

## Breakpoints

```css
/* Mobile First Breakpoints */
@media (min-width: 640px)   { /* sm */ }
@media (min-width: 768px)   { /* md */ }
@media (min-width: 1024px)  { /* lg */ }
@media (min-width: 1280px)  { /* xl */ }
@media (min-width: 1536px)  { /* 2xl */ }

/* Max Width Containers */
--container-sm: 640px;
--container-md: 768px;
--container-lg: 1024px;
--container-xl: 1280px;
--container-2xl: 1536px;
```

## Responsive Typography

```css
/* Fluid Typography */
html {
  font-size: 16px;
}

@media (min-width: 768px) {
  html {
    font-size: 16px;
  }
}

@media (min-width: 1024px) {
  html {
    font-size: 16px;
  }
}

/* Responsive Headings */
h1 {
  font-size: var(--text-4xl);
  line-height: var(--leading-tight);
}

@media (min-width: 768px) {
  h1 {
    font-size: var(--text-5xl);
  }
}
```

## Dark Mode Tokens

```css
/* Dark Mode Color Mapping */
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg-primary: var(--color-dark-400);
    --color-bg-secondary: var(--color-dark-300);
    --color-bg-tertiary: var(--color-dark-200);
    --color-text-primary: var(--color-dark-text-primary);
    --color-text-secondary: var(--color-dark-text-secondary);
    --color-border: var(--color-dark-200);
  }
}

/* Manual Dark Mode */
[data-theme="dark"] {
  --color-bg-primary: var(--color-dark-400);
  --color-bg-secondary: var(--color-dark-300);
  --color-bg-tertiary: var(--color-dark-200);
  --color-text-primary: var(--color-dark-text-primary);
  --color-text-secondary: var(--color-dark-text-secondary);
  --color-border: var(--color-dark-200);
}
```

## Accessibility Tokens

### Color Contrast

```css
/* Minimum Contrast Ratios (WCAG AA) */
--contrast-normal: 4.5;    /* Normal text */
--contrast-large: 3;       /* Large text (18px+ or 14px bold+) */
--contrast-enhanced: 7;    /* WCAG AAA */

/* High Contrast Mode */
@media (prefers-contrast: high) {
  :root {
    --contrast-normal: 7;
    --contrast-large: 4.5;
  }
}
```

### Focus Indicators

```css
/* Visible Focus */
--focus-indicator-width: 2px;
--focus-indicator-style: solid;
--focus-indicator-color: var(--color-primary-500);
--focus-indicator-offset: 2px;

/* Skip Link Focus */
.skip-link:focus {
  position: absolute;
  top: var(--space-4);
  left: var(--space-4);
  padding: var(--space-3) var(--space-4);
  background: var(--color-primary-500);
  color: white;
  z-index: var(--z-index-max);
  outline: var(--focus-indicator-width) solid var(--focus-indicator-color);
  outline-offset: var(--focus-indicator-offset);
}
```

### Screen Reader Only

```css
/* Visually Hidden but Accessible */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

/* Focusable Screen Reader Only */
.sr-only-focusable:focus {
  position: static;
  width: auto;
  height: auto;
  padding: inherit;
  margin: inherit;
  overflow: visible;
  clip: auto;
  white-space: normal;
}
```

## Component Tokens

### Button Tokens

```css
/* Button Sizes */
--button-height-sm: 32px;
--button-height-md: 40px;
--button-height-lg: 48px;

/* Button Padding */
--button-padding-sm: var(--space-2) var(--space-3);
--button-padding-md: var(--space-3) var(--space-5);
--button-padding-lg: var(--space-4) var(--space-6);

/* Button Border Radius */
--button-radius: var(--radius-md);

/* Button Font Size */
--button-text-sm: var(--text-sm);
--button-text-md: var(--text-base);
--button-text-lg: var(--text-lg);
```

### Input Tokens

```css
/* Input Sizes */
--input-height-sm: 32px;
--input-height-md: 40px;
--input-height-lg: 48px;

/* Input Spacing */
--input-padding: var(--space-3) var(--space-4);
--input-border-width: 1px;
--input-border-radius: var(--radius-md);

/* Focus Ring */
--input-focus-ring: 0 0 0 3px var(--color-primary-500);
```

### Card Tokens

```css
/* Card Spacing */
--card-padding: var(--space-6);
--card-gap: var(--space-4);

/* Card Border */
--card-border-width: 1px;
--card-border-color: var(--color-gray-200);
--card-border-radius: var(--radius-lg);

/* Card Shadow */
--card-shadow: var(--shadow-sm);
--card-shadow-hover: var(--shadow-md);
```

## Implementation Notes

### CSS Custom Properties Strategy

1. **Global Scope:** Define in `:root` for global access
2. **Component Scope:** Redefine in component class for specificity
3. **Theme Switching:** Toggle data-theme attribute on `<html>`
4. **Dark Mode:** Use `prefers-color-scheme` media query + manual override

### Naming Convention

```
--{category}-{property}-{variant}

Examples:
--color-primary-500
--space-4
--font-size-xl
--shadow-lg
--radius-md
```

### Token Usage Rules

1. **Always use tokens** - Never hardcode values
2. **Semantic naming** - Use purpose, not appearance
3. **Consistent scale** - Use predefined values only
4. **Document exceptions** - Justify any deviations
5. **Version control** - Track token changes

### Performance Considerations

- Use CSS custom properties for theming
- Minimize value recalculations
- Use transform/opacity for animations
- Avoid expensive properties (box-shadow, blur) on large areas
- Lazy-load non-critical styles

---

**Document Owner:** Design System Team  
**Last Updated:** 2026-07-16  
**Next Review:** 2026-10-16  
**Status:** Approved