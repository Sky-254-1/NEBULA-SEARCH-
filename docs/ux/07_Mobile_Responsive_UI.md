# Nebula Search Engine — Mobile & Responsive UI

## Executive Summary

This document defines the mobile-first responsive design specifications for Nebula Search Engine, ensuring optimal experiences across phones, tablets, and foldable devices.

**Goal:** Deliver a native-app-quality experience on mobile devices while maintaining full functionality and accessibility.

## Mobile-First Strategy

### Approach

**Progressive Enhancement:**
1. **Mobile (320px+):** Core features, simplified UI
2. **Tablet (768px+):** Enhanced layout, side panels
3. **Desktop (1024px+):** Full features, multi-column

**Breakpoint System:**
```css
/* Mobile First */
--breakpoint-sm: 640px;    /* Large phones */
--breakpoint-md: 768px;    /* Tablets */
--breakpoint-lg: 1024px;   /* Small laptops */
--breakpoint-xl: 1280px;   /* Desktops */
--breakpoint-2xl: 1536px;  /* Large screens */
```

## Mobile Screen Specifications

### Phone (320px - 639px)

**Viewport:**
- Minimum supported: 320px width (iPhone SE)
- Recommended: 375px+ (iPhone 12/13/14)
- Maximum: 639px

**Layout:**
- Single column
- Full-width components
- Bottom navigation (56px height)
- Floating action buttons (FAB)
- Bottom sheets for modals

**Typography:**
- Base: 16px (minimum for accessibility)
- H1: 28px
- H2: 24px
- H3: 20px
- Body: 16px
- Small: 14px

**Spacing:**
- Base unit: 8px
- Component padding: 16px
- Section spacing: 24px
- Page margins: 16px

### Tablet (640px - 1023px)

**Viewport:**
- iPad Mini: 768px
- iPad Air/Pro: 820px - 1024px
- Android tablets: 800px - 1024px

**Layout:**
- Two-column adaptive
- Collapsible sidebar (240px)
- Persistent filters panel
- Multi-column grids

**Typography:**
- Base: 16px
- H1: 36px
- H2: 30px
- H3: 24px
- Body: 16px

### Foldable Devices

**Postures:**
1. **Folded (phone mode):** 320px - 599px
2. **Unfolded (tablet mode):** 800px - 1024px+
3. **Half-fold (dual-screen):** Treat as two viewports

**Adaptive Behavior:**
```css
/* Foldable - folded */
@media (max-width: 599px) {
  .app { /* phone layout */ }
}

/* Foldable - unfolded */
@media (min-width: 800px) {
  .app { /* tablet layout */ }
}

/* Span both screens */
@media (spanning: right-fold) {
  .app { /* dual-screen layout */ }
}
```

## Critical UI Components - Mobile

### Search Bar (Mobile)

**Specifications:**
- Height: 44px (minimum touch target)
- Full-width with 16px margins
- Search icon: 20px (left)
- Voice icon: 24px (right)
- Border radius: 8px
- Border: 1px gray-200
- Focus: 2px primary-500 ring

**States:**
- **Idle:** Placeholder "Search..."
- **Focused:** Expand suggestions
- **Typing:** Show debounced suggestions
- **Results:** Full results page

**Touch Targets:**
- Search bar: 44px height ✓
- Search icon: 24x24px (centered in 44px)
- Voice icon: 24x24px (centered in 44px)
- Clear button: 44x44px ✓

**Code:**
```jsx
<SearchBar
  style={{
    height: '44px',
    width: 'calc(100% - 32px)',
    margin: '16px',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    padding: '0 16px',
  }}
/>
```

### Bottom Navigation (Mobile)

**Specifications:**
```
┌─────────────────────────────────────┐
│                                     │
│         Main Content                │
│                                     │
│                                     │
├─────────────────────────────────────┤
│ 🔍  💬  📁  📊  👤  │ 56px height │
│Search AI Docs Analytics Profile     │
└─────────────────────────────────────┘
```

**Requirements:**
- Height: 56px (minimum)
- 5 tabs maximum
- Icon size: 24px
- Label: 12px below icon
- Active indicator: 4px top border
- Safe area: env(safe-area-inset-bottom)

**Touch Targets:**
- Each tab: 44x44px minimum (ideally full width / 5 = ~64px each)
- Spacing: 0 (tabs evenly distributed)
- Icon: 24x24px centered

**Code:**
```jsx
<nav style={{
  position: 'fixed',
  bottom: 0,
  left: 0,
  right: 0,
  height: '56px',
  paddingBottom: 'env(safe-area-inset-bottom)',
  borderTop: '1px solid #e5e7eb',
  display: 'flex',
  justifyContent: 'space-around',
  alignItems: 'center',
}}>
  {tabs.map(tab => (
    <button key={tab.id} style={{
      flex: 1,
      height: '56px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '4px',
    }}>
      <Icon name={tab.icon} size={24} />
      <span style={{ fontSize: '12px' }}>{tab.label}</span>
    </button>
  ))}
</nav>
```

### Document Upload (Mobile)

**Specifications:**
- Height: 250px (shorter on mobile)
- Border: 2px dashed gray-300
- Text: 14px
- Icon: 40px
- Padding: 24px

**States:**
- Idle: Dashed border, centered
- Drag over: Solid primary border
- Uploading: Progress bar (bottom)
- Success: Green background

**Touch Targets:**
- Upload zone: 250px height (tappable anywhere)
- Browse button: 44px height

### AI Chat (Mobile)

**Layout:**
```
┌─────────────────────────────────────┐
│ ← AI Assistant          [⋮] [Clear] │
├─────────────────────────────────────┤
│                                     │
│  User message (right aligned)       │
│  ┌──────────────────────────────┐   │
│  │ Hello! Can you help me?      │   │
│  └──────────────────────────────┘   │
│                                     │
│           AI response               │
│  ┌──────────────────────────────┐   │
│  │ Of course! What do you need? │   │
│  └──────────────────────────────┘   │
│                                     │
├─────────────────────────────────────┤
│ [Type a message...]      [🎤] [Send]│
└─────────────────────────────────────┘
```

**Specifications:**
- Messages: Full-width cards
- User: Right-aligned, primary-500 bg
- AI: Left-aligned, gray-100 bg
- Input: 48px height (includes safe area)
- Send button: 48x48px

## Touch Interaction Patterns

### Swipe Gestures

**Card Swipe:**
```javascript
<SwipeableCard
  onSwipeLeft={() => deleteItem(item)}
  onSwipeRight={() => archiveItem(item)}
  swipeThreshold={100}
>
  <Content />
</SwipeableCard>
```

**Directions:**
- Swipe left: Delete/archive
- Swipe right: Favorite/save
- Swipe up: Next item
- Swipe down: Previous item

### Pull to Refresh

```javascript
<PullToRefresh
  onRefresh={fetchLatestResults}
  pullDistance={80}
  releaseThreshold={120}
>
  {children}
</PullToRefresh>
```

**Feedback:**
- Pull distance 0-80px: Arrow icon
- Pull distance 80-120px: "Release to refresh"
- Pull distance > 120px: "Release" + spin
- Refreshing: Spinner + "Loading..."

### Infinite Scroll

```javascript
<InfiniteScroll
  loadMore={loadMoreResults}
  hasMore={hasMore}
  loader={<LoadingSpinner />}
  endMessage={<p>No more results</p>}
>
  {results.map(result => (
    <SearchResultCard key={result.id} result={result} />
  ))}
</InfiniteScroll>
```

**Trigger:** Scroll to 80% of page height

### Bottom Sheets

```javascript
<BottomSheet
  isOpen={filtersOpen}
  onClose={() => setFiltersOpen(false)}
  height="60vh"
  snapPoints={[300, 500, 'full']}
>
  <Filters />
</BottomSheet>
```

**Use Cases:**
- Filters
- Advanced search
- Document preview
- Share dialog

## Responsive Components

### Search Results

**Mobile (1 column):**
```
┌─────────────────────────────────────┐
│ Result 1                            │
│ Title + URL                         │
│ Snippet text...                     │
│ Type: PDF | 2.4 MB                  │
├─────────────────────────────────────┤
│ Result 2                            │
│ Title + URL                         │
│ Snippet text...                     │
│ Type: DOCX | 1.1 MB                 │
└─────────────────────────────────────┘
```

**Tablet (2 columns):**
```
┌────────────────────┬────────────────────┐
│ Result 1           │ Result 2           │
│ Title + URL        │ Title + URL        │
│ Snippet...         │ Snippet...         │
│ Type: PDF | 2.4MB  │ Type: DOCX | 1.1MB│
├────────────────────┼────────────────────┤
│ Result 3           │ Result 4           │
│ Title + URL        │ Title + URL        │
│ Snippet...         │ Snippet...         │
│ Type: PDF | 1.8MB  │ Type: PDF | 3.2MB │
└────────────────────┴────────────────────┘
```

**Desktop (3 columns + sidebar):**
```
┌──────────┬────────────────────────────────────┐
│ Filters  │ Results                    [1-10]  │
│          │ ┌──────────┬──────────┬──────────┐│
│ Category │ │ Result 1 │ Result 2 │ Result 3 ││
│ Date     │ │ Title    │ Title    │ Title    ││
│ Type     │ │ Snippet  │ Snippet  │ Snippet  ││
│ Size     │ │ Metadata │ Metadata │ Metadata ││
└──────────┴──────────┴──────────┴──────────┘│
```

### Settings

**Mobile:**
```
┌─────────────────────────────────────┐
│ ← Settings                          │
├─────────────────────────────────────┤
│ [General] [Privacy] [AI]            │
│                                     │
│ General                             │
│ ┌─────────────────────────────────┐ │
│ │ Theme                           │ │
│ │ [Light] [Dark] [System]         │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Language                            │
│ [English ▼]                         │
│                                     │
│ Results per page                    │
│ [20 ▼]                              │
│                                     │
│ [Save Changes]                      │
└─────────────────────────────────────┘
```

**Desktop:**
```
┌──────────┬──────────────────────────────┐
│Settings  │ General Settings             │
│          │                              │
│General   │ Theme: [Light] [Dark] [Auto] │
│Privacy   │                              │
│Notifs    │ Language: [English ▼]        │
│AI        │                              │
│Integrations│ Results/page: [20 ▼]     │
│          │                              │
│          │ [Save] [Reset]               │
└──────────┴──────────────────────────────┘
```

## Responsive Typography

### Fluid Type Scale

```css
html {
  font-size: 16px;
}

h1 {
  font-size: clamp(1.75rem, 5vw, 3rem);
}

h2 {
  font-size: clamp(1.5rem, 4vw, 2.25rem);
}

h3 {
  font-size: clamp(1.25rem, 3vw, 1.75rem);
}

body {
  font-size: clamp(0.875rem, 2vw, 1rem);
}
```

### Responsive Headings

| Screen | H1 | H2 | H3 | Body |
|--------|----|----|-----|------|
| Mobile | 28px | 24px | 20px | 16px |
| Tablet | 32px | 28px | 24px | 16px |
| Desktop | 36px | 30px | 24px | 16px |

## Responsive Images

### Image Optimization

```jsx
<Picture>
  <source
    media="(max-width: 639px)"
    srcSet="image-320w.webp"
    type="image/webp"
  />
  <source
    media="(max-width: 1023px)"
    srcSet="image-768w.webp"
    type="image/webp"
  />
  <img
    src="image-1440w.webp"
    alt="Description"
    loading="lazy"
    decoding="async"
  />
</Picture>
```

**Formats:**
- Modern: WebP, AVIF
- Fallback: JPEG, PNG
- Sizes: 320w, 768w, 1024w, 1440w

### Lazy Loading

```jsx
<img
  src="image.jpg"
  alt="Description"
  loading="lazy"
  decoding="async"
  fetchpriority="low"
/>
```

**Priority:**
- Above fold: `fetchpriority="high"`
- Below fold: `loading="lazy"`
- Critical images: Preload in head

## Orientation Handling

### Portrait Mode (Primary)

**Layout:**
- Bottom navigation
- Full-width components
- Stacked content
- FAB for actions

### Landscape Mode

**Layout:**
- Side navigation (if space permits)
- Multi-column (if width > 800px)
- Adjusted spacing

**Orientation Lock Warning:**
```javascript
if (screen.orientation && screen.orientation.locked) {
  alert(
    'For best experience, unlock screen orientation. ' +
    'Nebula works best in portrait mode on mobile.'
  );
}
```

## Offline Mode

### Offline Indicator

```
┌─────────────────────────────────────┐
│ ⚠️ You're offline                   │
│ Showing cached results              │
│ [Retry]                             │
└─────────────────────────────────────┘
```

**Position:** Top of screen (below header)
**Style:** Yellow background, 40px height
**Dismissible:** Yes (stores preference)

### Offline Features

**Available Offline:**
- View cached searches (last 24h)
- Browse saved documents
- Access downloaded files
- Edit drafts (sync later)

**Unavailable Offline:**
- New AI queries
- Web search
- Upload new documents
- Share/sync

### Sync Queue

```javascript
// Actions queued when offline
const syncQueue = [
  { action: 'upload', file: 'doc.pdf', timestamp: '...' },
  { action: 'save', searchId: '123', timestamp: '...' },
];

// Process when online
window.addEventListener('online', () => {
  processSyncQueue();
});
```

## Performance Optimization

### Mobile Performance

**Targets:**
- FCP < 1.5s (3G network)
- TTI < 3s
- Bundle size < 150KB (mobile)
- Images < 100KB each

**Optimizations:**
1. Code splitting by route
2. Lazy load components
3. Compress images (WebP)
4. Minimize re-renders
5. Cache aggressively

### Network Awareness

```javascript
const connection = navigator.connection;

// Adjust quality based on connection
if (connection.effectiveType === 'slow-2g') {
  // Disable images, show text only
  setShowImages(false);
} else if (connection.effectiveType === '4g') {
  // Full experience
  setShowImages(true);
}

// Save data mode
if (connection.saveData) {
  setLowDataMode(true);
}
```

## Testing Checklist

### Device Testing

**Phones:**
- [ ] iPhone SE (320px)
- [ ] iPhone 12/13/14 (390px)
- [ ] iPhone 14 Pro Max (430px)
- [ ] Samsung Galaxy S21 (360px)
- [ ] Google Pixel 7 (412px)

**Tablets:**
- [ ] iPad Mini (768px)
- [ ] iPad Air (820px)
- [ ] iPad Pro (1024px)
- [ ] Samsung Tab S8 (800px)

**Foldables:**
- [ ] Galaxy Z Fold (600px folded, 1700px unfolded)
- [ ] Pixel Fold (600px folded, 1500px unfolded)

### Testing Checklist

- [ ] All touch targets ≥ 44x44px
- [ ] Content readable at 320px width
- [ ] No horizontal scrolling
- [ ] Orientation changes work smoothly
- [ ] Keyboard appears without layout shift
- [ ] Bottom nav visible and accessible
- [ ] FAB doesn't overlap content
- [ ] Modals slide up from bottom
- [ ] Pull to refresh works
- [ ] Infinite scroll works
- [ ] Swipe gestures work
- [ ]Offline mode functional
- [ ] Performance acceptable on 3G
- [ ] Images optimized
- [ ] Font sizes scalable to 200%

---

**Document Owner:** Mobile Team  
**Last Updated:** 2026-07-16  
**Next Review:** 2026-10-16  
**Status:** Approved