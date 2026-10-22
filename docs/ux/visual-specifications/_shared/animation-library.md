# Nebula Search Engine — Animation & Motion Library

## Purpose

Defines all animations and motion patterns used across screens. Ensures consistent, purposeful motion that enhances UX without causing distraction or accessibility issues.

---

## Principles

1. **Purposeful motion** — Every animation serves a functional purpose
2. **Fast by default** — 150-250ms for most interactions
3. **Reduced motion respected** — `prefers-reduced-motion` media query honored
4. **Performance first** — Use `transform` and `opacity` only, no layout-triggering properties
5. **Natural easing** — Cubic bezier curves, not linear

---

## Micro-Interactions

### 1. Button Press
```
Trigger: Click/Tap
Duration: 150ms
Easing: ease-out
Animation: scale(1 → 0.97)
Property: transform
```

### 2. Hover Lift
```
Trigger: Hover (desktop only)
Duration: 200ms
Easing: ease-out
Animation: translateY(0 → -2px), shadow-sm → shadow-md
Property: transform, box-shadow
```

### 3. Focus Ring
```
Trigger: Keyboard focus
Duration: 150ms
Easing: ease-out
Animation: box-shadow 0 0 0 0 primary-500 → 0 0 0 2px primary-500
Property: box-shadow
```

### 4. Toggle Switch
```
Trigger: Click/Tap
Duration: 200ms
Easing: ease-out
Animation: knob translateX(0 → 20px)
Property: transform
```

---

## Component Animations

### 5. Modal/Dialog Open
```
Trigger: Action
Duration: 250ms
Easing: ease-out
Backdrop: opacity(0 → 0.5)
Content: scale(0.95 → 1) + opacity(0 → 1)
Property: transform, opacity
```

### 6. Dropdown Open
```
Trigger: Click
Duration: 200ms
Easing: ease-out
Animation: opacity(0 → 1) + translateY(-8px → 0)
Property: transform, opacity
```

### 7. Toast Notification
```
Appear (Slide In Right):
  Duration: 300ms
  Easing: ease-out
  Animation: translateX(100% → 0)

Dismiss (Slide Out Right):
  Duration: 200ms
  Easing: ease-in
  Animation: translateX(0 → 100%) + opacity(1 → 0)
```

### 8. Skeleton Loader
```
Duration: 1.5s (loop)
Easing: ease-in-out
Animation: shimmer sweep left-to-right
  background-position: -200% 0 → 200% 0
Keyframes:
  0% { background-position: -200% 0 }
  100% { background-position: 200% 0 }
Gradient: gray-200 → gray-100 → gray-200
```

### 9. Progress Bar
```
Determinate:
  Duration: 300ms
  Easing: ease-out
  Animation: width(0% → 100%)

Indeterminate:
  Duration: 2s (loop)
  Easing: ease-in-out
  Animation: bar sweeps left-to-right, 30% width
```

### 10. Card Hover
```
Trigger: Hover
Duration: 250ms
Easing: ease-out
Animation: shadow-sm → shadow-md, border subtle color shift
Property: box-shadow, border-color
```

---

## Page & Layout Animations

### 11. Page Transition
```
Route Change:
  Duration: 300ms (content), 150ms (header)
  Easing: ease-out
  Content: opacity(0 → 1), translateY(8px → 0)
  Header: opacity(1), stays fixed
```

### 12. Sidebar Collapse
```
Trigger: Toggle button
Duration: 250ms
Easing: ease-out
Animation: width(240px → 64px) or (64px → 240px)
Property: width
Labels: opacity(1 → 0) with 100ms delay
```

### 13. Sidebar Panel (Mobile)
```
Trigger: Hamburger menu
Duration: 300ms
Easing: ease-out
Panel: translateX(-100% → 0)
Backdrop: opacity(0 → 1)
```

### 14. Bottom Sheet (Mobile)
```
Trigger: Action
Duration: 300ms
Easing: ease-out
Animation: translateY(100% → 0)
Backdrop: opacity(0 → 0.5)
Property: transform, opacity
```

### 15. Tab Switch
```
Trigger: Click tab
Duration: 200ms
Easing: ease-out
Animation: content opacity(1 → 0 → 1), indicator translateX
Property: opacity, transform
```

---

## Search & AI Animations

### 16. Search Bar Focus
```
Trigger: Focus
Duration: 200ms
Easing: ease-out
Animation: 
  - border: gray-200 → primary-500
  - shadow: none → 0 0 0 3px primary-500 (focus ring)
  - scale: 1 → 1.02 (subtle expansion)
Property: border-color, box-shadow, transform
```

### 17. Search Results Enter
```
Trigger: Results load
Duration: 300ms stagger (50ms per item)
Easing: ease-out
Animation: 
  - opacity(0 → 1)
  - translateY(12px → 0)
Property: opacity, transform
Number of items: First 3 animate in, rest batch in groups of 5
```

### 18. AI Streaming Response
```
Trigger: AI response
Duration: Continuous
Animation: 
  - Cursor blink: 1s infinite
  - Text appears character by character (30ms per char)
  - Smooth scroll to follow text
Fade: 500ms fade-in for each new complete sentence
```

### 19. AI Typing Indicator
```
Trigger: AI processing
Duration: 1.2s loop
Animation: 3 dots bounce
  Dot 1: translateY(0 → -4px → 0) delay 0ms
  Dot 2: translateY(0 → -4px → 0) delay 200ms
  Dot 3: translateY(0 → -4px → 0) delay 400ms
```

### 20. Suggestion Chips
```
Trigger: Appear
Duration: 200ms stagger (50ms per chip)
Easing: ease-out
Animation: scale(0.9 → 1) + opacity(0 → 1)
```

---

## Document Animations

### 21. File Upload Progress
```
Trigger: File selected
Duration: Per file progress
Animation:
  - File card slides in from top: translateY(-20px → 0), opacity(0 → 1)
  - Progress bar fills: width 0% → 100%
  - Completion: checkmark icon scales 0 → 1 with bounce
```

### 22. Drag Over State
```
Trigger: File hovers over dropzone
Duration: 150ms
Easing: ease-out
Animation:
  - Border: dashed gray-300 → solid primary-500
  - Background: transparent → primary-50
  - Scale: 1 → 1.02 (subtle)
```

### 23. Document List Item
```
Trigger: Hover/Select
Duration: 150ms
Animation: background gray-50, left border 3px primary-500
```

### 24. Preview Panel Open
```
Trigger: Click document
Duration: 300ms
Easing: ease-out
Animation: slide from right, width(0 → 360px), opacity(0 → 1)
```

---

## Notification Animations

### 25. Notification Badge
```
Trigger: New notification
Duration: 300ms
Animation: scale(0 → 1.2 → 1) with bounce
Easing: ease-bounce
```

### 26. Notification Dropdown
```
Trigger: Click bell icon
Duration: 250ms
Animation: opacity(0 → 1), translateY(-8px → 0)
```

---

## Error & State Animations

### 27. Shake (Error)
```
Trigger: Form validation error
Duration: 400ms
Animation: translateX(0 → -8px → 8px → -6px → 6px → -4px → 4px → 0)
Iterations: 1
```

### 28. Pulse (Attention)
```
Trigger: Important notification/alert
Duration: 2s loop
Animation: scale(1 → 1.05 → 1), opacity(1 → 0.8 → 1)
```

### 29. Retry/Refetch
```
Trigger: Manual retry
Duration: 1s
Animation: icon rotation 360deg, opacity 0.5 → 1
```

---

## Implementation Notes

### CSS Keyframes (Example)
```css
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@keyframes slideInRight {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

@keyframes fadeInUp {
  from { transform: translateY(12px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.8; }
}
```

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### Performance Guidelines
- Always animate `transform` and `opacity` — never `width`, `height`, `top`, `left`
- Use `will-change: transform` on animated elements sparingly
- Avoid animating `box-shadow` on large areas
- Use `requestAnimationFrame` for JS-driven animations
- Keep GPU-composited layers minimal

---

**Last Updated:** 2026-07-17