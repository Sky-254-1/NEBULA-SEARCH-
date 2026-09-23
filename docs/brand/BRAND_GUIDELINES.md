# Nebula Search — Brand Guidelines

## Brand Story & Personality

**Tagline**: *Search the Universe of Knowledge*

Nebula Search is the intelligent search engine that helps you explore information like never before. Powered by advanced AI and hybrid search technology (keyword + semantic + vector), Nebula delivers context-aware results that understand meaning, not just keywords.

### Core Personality Traits

- **Intelligent**: Powered by AI, but accessible to everyone
- **Cosmic**: Expansive, exploration-focused, universe of knowledge
- **Reliable**: Consistent, accurate, trustworthy results
- **Modern**: Clean, contemporary design with cutting-edge tech

---

## Logo System

### Primary Mark (Concept D: Neural Nodes Search Lens)

The primary logo mark features:

- **Dark Cosmic Background**: `#0b0c10` — deep space, mystery, depth
- **Neural Network Nodes**: 7 nodes representing the hybrid search engine
- **Connecting Lines**: Symbolizing connections between ideas, semantic understanding
- **Magnifying Glass Lens**: Represents search, discovery, exploration
- **Gradient Stroke**: Purple → Blue → Indigo brand signature

### Lockup Variations

#### Horizontal (Primary)
```
[LOGO MARK] Nebula
```

#### Stacked
```
[LOGO MARK]
  Nebula
```

#### Icon Only
```
[LOGO MARK] (32px minimum)
```

### Clear Space

The logo requires clear space equal to **1× the icon height** on all sides:

```
[LOGO MARK]
  (1x space)
  (1x space)
```

### Minimum Sizes

| Usage | Minimum Size | Notes |
|-------|-------------|-------|
| Favicon | 16×16 | Never scale below 16px |
| UI / Header | 24×24 | NebulaLogo component default |
| Header Branding | 32×32 | NebulaLogo size={32} |
| Marketing | 48×48 | NebulaLogo size={48} |
| Print | 64×64 | Highest resolution |

---

## Color Palette

### Primary Gradient (Brand Signature)

| Color | Hex | Usage |
|-------|-----|-------|
| Purple | `#7c5cfc` | Brand primary, gradients start |
| Blue | `#3b82f6` | Brand primary, gradients middle |
| Indigo | `#6366f1` | Brand primary, gradients end |

**Gradient Direction**: Top-left to bottom-right (45°)

### Background Colors

| Color | Hex | Usage |
|-------|-----|-------|
| Dark Cosmic | `#0b0c10` | PWA background, deep dark mode |
| UI Dark | `#0f172a` | Component backgrounds in dark mode |
| UI Light | `#f8fafc` | Component backgrounds in light mode |
| White | `#ffffff` | Text on dark, overlay backgrounds |

### Semantic Colors

| Color | Hex | Usage |
|-------|-----|-------|
| Success | `#10b981` | Success states, positive actions |
| Warning | `#f59e0b` | Warnings, pending states |
| Error | `#ef4444` | Errors, destructive actions |
| Info | `#3b82f6` | Information, neutral highlights |

### Neutral Grays

| Color | Hex | Usage |
|-------|-----|-------|
| Gray 900 | `#1e293b` | Primary text |
| Gray 700 | `#475569` | Secondary text |
| Gray 500 | `#64748b` | Tertiary text, placeholders |
| Gray 300 | `#94a3b8` | Borders, dividers |
| Gray 200 | `#cbd5e1` | Light borders |
| Gray 100 | `#e2e8f0` | Backgrounds, cards |

---

## Typography

### Font Families

- **Display/Headings**: Inter (existing import)
- **Body/UI**: Inter 400/500/600
- **Mono**: JetBrains Mono (existing) for code/search queries

### Type Scale

| Level | Size | Weight | Usage |
|-------|------|--------|-------|
| Display | 48px | 800 | Hero headings |
| H1 | 36px | 700 | Section headings |
| H2 | 28px | 700 | Subsection headings |
| H3 | 22px | 600 | Card headings |
| Body Large | 16px | 400 | Primary body text |
| Body | 14px | 400 | Default body text |
| Body Small | 12px | 400 | Captions, meta text |
| Caption | 10px | 500 | Labels, hints |

### Line Heights

- Display: 1.1
- H1-H3: 1.25
- Body: 1.5
- Captions: 1.33

---

## Iconography

### Style

- **Stroke Width**: 2px (default), 3px (emphasis)
- **Rounding**: 4px (default), 8px (buttons, cards)
- **Corners**: Rounded (not square)
- **Fill**: None (stroked) or solid gradient fills

### Neural Network Pattern

The logo mark uses a specific neural network pattern:

- **Central Node**: 3 nodes at 45° angles
- **Ring Nodes**: 6 nodes in a circle
- **Connections**: 12 straight lines (2px)
- **Pulse Lines**: 4 dashed lines (1px, 2px gap)

---

## Photography & Illustration Style

### Themes

- **Cosmic**: Deep space, stars, nebulae
- **Gradient**: Purple-to-blue transitions
- **Dark**: Minimal, high-contrast
- **Abstract**: Geometric shapes, networks

### Do's

- ✅ Use dark backgrounds with gradient accents
- ✅ Show neural networks and data visualization
- ✅ High-contrast, bold typography
- ✅ Modern, clean UI elements

### Don'ts

- ❌ Bright, colorful backgrounds (clashes with brand)
- ❌ Stock photography (use abstract/vector)
- ❌ Low-contrast combinations
- ❌ Squared corners (use 4-8px rounding)

---

## Voice & Tone

### Brand Voice

- **Intelligent**: Knowledgeable, precise, helpful
- **Approachable**: Friendly, not robotic
- **Confident**: Authority in search technology
- **Curious**: Encouraging exploration

### Tone Guidelines

| Context | Tone | Example |
|---------|------|---------|
| Search Results | Neutral, helpful | "Showing 10 results for..." |
| AI Responses | Knowledgeable, friendly | "Here's what I found..." |
| Onboarding | Encouraging, educational | "Let's get you started..." |
| Error States | Calm, solution-oriented | "Something went wrong. Try again?" |

---

## Application Guidelines

### Where to Use

1. **Header**: Logo mark + wordmark (horizontal lockup)
2. **Landing Page**: Large logo mark above hero heading
3. **Auth Pages**: Centered logo mark above forms
4. **Mobile App**: Icon-only in navigation
5. **PWA Manifest**: 192/512px icons
6. **Favicon**: 64px SVG

### Where NOT to Use

- ❌ Changing the color gradient (always use brand gradient)
- ❌ Stretching or distorting the mark
- ❌ Placing on conflicting backgrounds
- ❌ Using with non-brand colors

---

## File Naming & Assets

### SVG Files

- `frontend/public/icons/icon-512.svg` — Master icon (512×512)
- `frontend/public/icons/icon-192.svg` — PWA icon (simplified)
- `frontend/public/favicon.svg` — Browser favicon

### Component

- `frontend/src/components/NebulaLogo.tsx` — Reusable React component

### Documentation

- `docs/brand/BRAND_GUIDELINES.md` — This file
- `docs/brand/logo-usage.md` — Logo usage rules

---

## Contact

For questions about brand usage, consult the design team or refer to this guidelines document.

---

*Version 1.0 — August 2026*
