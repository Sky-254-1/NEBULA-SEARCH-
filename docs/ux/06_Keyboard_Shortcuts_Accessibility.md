# Nebula Search Engine — Keyboard Shortcuts & Accessibility

## Executive Summary

This document defines the complete keyboard shortcut system and accessibility requirements for Nebula Search Engine. It ensures the application is fully operable without a mouse and compliant with WCAG 2.2 AA standards.

**Goal:** Enable power users to operate at maximum efficiency while ensuring full accessibility for users with disabilities.

## Keyboard Shortcuts System

### Global Shortcuts (Available Everywhere)

| Shortcut | Action | Context | Priority |
|----------|--------|---------|----------|
| `Ctrl+K` | Open command palette / Focus search | Global | Critical |
| `Ctrl+/` | Show keyboard shortcuts help | Global | High |
| `Ctrl+,` | Open settings | Global | High |
| `Ctrl+N` | New search / New chat | Global | High |
| `Ctrl+W` | Close current tab/modal | Global | High |
| `Ctrl+Q` | Quick add document | Global | Medium |
| `Escape` | Close modal/dropdown/menu | Global | Critical |
| `Tab` | Next interactive element | Global | Critical |
| `Shift+Tab` | Previous interactive element | Global | Critical |
| `Enter` | Activate/Submit | Global | Critical |
| `Space` | Toggle/Select (when focused) | Global | High |
| `Arrow Keys` | Navigate lists/menus | Global | High |

### Search Page Shortcuts

| Shortcut | Action | Notes |
|----------|--------|-------|
| `Ctrl+K` | Focus search bar | From anywhere |
| `Enter` | Execute search | In search bar |
| `↓` | Next suggestion | In dropdown |
| `↑` | Previous suggestion | In dropdown |
| `Tab` | Accept suggestion | In dropdown |
| `Escape` | Clear search / Close | In search bar |
| `Ctrl+F` | Find in results | On results page |
| `/` | Focus filters | On results page |
| `S` | Save search | When results focused |
| `A` | Toggle AI summary | When results focused |
| `1-9` | Jump to result # | When results focused |

### AI Assistant Shortcuts

| Shortcut | Action | Notes |
|----------|--------|-------|
| `Ctrl+Shift+A` | Open AI assistant | From anywhere |
| `Ctrl+Enter` | Send message | In chat input |
| `Shift+Enter` | New line in message | In chat input |
| `↑` | Edit previous message | In chat input |
| `↓` | Edit next message | In chat input |
| `C` | Copy last response | When response focused |
| `R` | Regenerate response | When response focused |
| `F` | Give feedback | When response focused |
| `/` | Focus search in context | In assistant |

### Document Library Shortcuts

| Shortcut | Action | Notes |
|----------|--------|-------|
| `Ctrl+U` | Upload document | From anywhere |
| `N` | New folder | In library |
| `R` | Rename selected | In library |
| `D` | Delete selected | In library |
| `S` | Share selected | In library |
| `E` | Export selected | In library |
| `F` | Open preview | In library |
| `Space` | Toggle selection | In library list |
| `Ctrl+A` | Select all | In library |
| `Esc` | Deselect all | In library |

### Settings Shortcuts

| Shortcut | Action | Notes |
|----------|--------|-------|
| `Ctrl+,` | Open settings | Global |
| `Ctrl+S` | Save settings | In settings |
| `Ctrl+R` | Reset settings | In settings |
| `Escape` | Close settings | In settings |
| `Tab` | Next field | In settings form |
| `Shift+Tab` | Previous field | In settings form |
| `1-5` | Jump to section | In settings |

### Navigation Shortcuts

| Shortcut | Action | Notes |
|----------|--------|-------|
| `Ctrl+1` | Go to Search | Global |
| `Ctrl+2` | Go to AI Assistant | Global |
| `Ctrl+3` | Go to Documents | Global |
| `Ctrl+4` | Go to Analytics | Global |
| `Ctrl+5` | Go to History | Global |
| `Ctrl+6` | Go to Notifications | Global |
| `Alt+1-6` | Quick switch tabs | When sidebar focused |

### Power User Shortcuts

| Shortcut | Action | Notes |
|----------|--------|-------|
| `Ctrl+Shift+F` | Advanced search filters | In search |
| `Ctrl+Shift+H` | Search history | Global |
| `Ctrl+Shift+S` | Saved searches | Global |
| `Ctrl+Shift+U` | Upload multiple | In documents |
| `Ctrl+Shift+E` | Export all data | In settings |
| `Ctrl+Shift+D` | Developer tools | Global (if admin) |

### Command Palette Commands

**Search Commands:**
- `> search [query]` - Execute search
- `> ai [question]` - Ask AI assistant
- `> upload` - Upload document
- `> recent` - View recent searches
- `> saved` - View saved searches

**Navigation Commands:**
- `> goto search` - Navigate to search
- `> goto documents` - Navigate to documents
- `> goto settings` - Navigate to settings
- `> goto analytics` - Navigate to analytics

**Action Commands:**
- `> new chat` - Start new AI conversation
- `> toggle theme` - Switch light/dark mode
- `> toggle incognito` - Enable/disable incognito
- `> clear history` - Clear search history
- `> export data` - Export user data

## Accessibility Requirements

### WCAG 2.2 AA Compliance

**Level A (Required):**
- ✅ All functionality available via keyboard
- ✅ No keyboard traps
- ✅ No time limits on interactions
- ✅ Pause/stop/hide moving content
- ✅ No content that flashes > 3 times/second
- ✅ Skip navigation links
- ✅ Page titled descriptively
- ✅ Focus order is logical
- ✅ Link purpose clear from text
- ✅ Form labels present
- ✅ Error identification and suggestions
- ✅ Required fields marked
- ✅ Error prevention for legal/financial actions

**Level AA (Required):**
- ✅ Captions for live audio/video
- ✅ Audio description for video
- ✅ Contrast ratio 4.5:1 (normal text)
- ✅ Contrast ratio 3:1 (large text)
- ✅ Resize text to 200% without loss
- ✅ Not depend on color alone
- ✅ Consistent navigation
- ✅ Consistent identification
- ✅ Labels or instructions provided
- ✅ Error suggestions (where possible)
- ✅ Help available
- ✅ Accessible authentication (no CAPTCHA)

**Level AAA (Target):**
- ⏳ Contrast ratio 7:1 (normal text)
- ⏳ Contrast ratio 4.5:1 (large text)
- ⏳ Resize text to 350% without loss
- ⏳ No timeout for user inactivity

### Perceivable Requirements

**Text Alternatives:**
- All images have alt text
- Icons have aria-label or aria-hidden
- Complex images have long descriptions
- Decorative images marked aria-hidden="true"

**Adaptable Content:**
- Semantic HTML structure
- Proper heading hierarchy (H1-H6)
- Proper list structure
- Proper table headers (scope attributes)
- Reading order matches visual order

**Distinguishable:**
- Minimum contrast 4.5:1 (normal text)
- Minimum contrast 3:1 (large text, 18px+ or 14px bold+)
- Text resizable to 200% without assistive tech
- Images of text avoided (use actual text)
- No horizontal scrolling at 320px width (except maps, charts)

### Operable Requirements

**Keyboard Accessible:**
- All interactive elements keyboard accessible
- Logical tab order (matches visual layout)
- No keyboard traps (Escape always exits)
- Shortcuts configurable
- Disabled shortcuts don't interfere

**Enough Time:**
- No time limits unless critical
- User can extend time limits
- User can turn off time limits
- Auto-save forms before timeout
- Clear warnings before timeouts

**Seizures Safe:**
- No content flashes > 3 times/second
- Warn users before flashing content
- Provide mechanism to disable animation

**Navigable:**
- Skip to main content link
- Skip to search link
- Skip to navigation link
- Numbered headings for screen readers
- Clear focus indicator (2-3px solid)
- Focus not obscured (minimum 2px visible)

### Understandable Requirements

**Readable:**
- Primary language declared (lang attribute)
- Reading level: Grade 8-10
- Rare/unusual words defined
- Abbreviations expanded on first use

**Predictable:**
- Navigation consistent across pages
- Components consistent (same function = same behavior)
- No automatic context changes on focus
- No automatic context changes on input
- Context changes user-initiated only

**Input Assistance:**
- Labels for all form inputs
- Instructions provided
- Error prevention (inline validation)
- Error suggestions (where possible)
- Error messages clear and helpful

### Robust Requirements

**Compatible:**
- Valid HTML5 (WCAG check)
- Valid ARIA usage
- Tested with assistive technologies:
  - NVDA (Windows)
  - JAWS (Windows)
  - VoiceOver (macOS, iOS)
  - TalkBack (Android)
  - Narrator (Windows)

## Focus Management

### Focus Indication

**Visual Focus Indicator:**
- 2px solid blue ring (primary-500)
- 2px offset from element
- High contrast mode: 3px yellow ring
- Visible on all interactive elements

**Focus Styles (CSS):**
```css
.focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px var(--color-primary-500),
              0 0 0 4px var(--color-primary-100);
}

@media (prefers-contrast: high) {
  .focus-visible {
    box-shadow: 0 0 0 3px #ffff00;
  }
}
```

### Focus Trapping

**When to Trap Focus:**
- Modal dialogs
- Dropdown menus
- Command palette
- Media players

**Focus Trap Behavior:**
- Tab cycles within trapped elements
- Shift+Tab cycles backwards
- Focus returns to trigger on close
- Escape closes trap

### Skip Links

**Required Skip Links:**
1. Skip to main content
2. Skip to search
3. Skip to navigation
4. Skip to footer

**Implementation:**
```html
<a href="#main" class="skip-link">Skip to main content</a>
<a href="#search" class="skip-link">Skip to search</a>
<a href="#nav" class="skip-link">Skip to navigation</a>

<style>
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  padding: 8px 16px;
  background: primary-500;
  color: white;
  z-index: 9999;
}

.skip-link:focus {
  top: 0;
}
</style>
```

## Screen Reader Announcements

### Live Regions

**Polite Live Region (Non-urgent):**
- Search result count changes
- AI response updates
- Upload progress updates
- Toast notifications

**Assertive Live Region (Urgent):**
- Error messages
- Time warnings
- Security alerts
- Critical failures

**Implementation:**
```html
<div aria-live="polite" aria-atomic="true" class="sr-only">
  {announcementText}
</div>

<div aria-live="assertive" aria-atomic="true" class="sr-only">
  {urgentMessage}
</div>
```

### ARIA Labels

**Search Bar:**
```html
<div role="search">
  <label for="search-input">Search</label>
  <input
    id="search-input"
    type="search"
    aria-label="Search documents and web"
    aria-describedby="search-help"
    autocomplete="off"
  />
  <span id="search-help" class="sr-only">
    Type to search. Press Enter to execute. Use arrow keys to navigate suggestions.
  </span>
</div>
```

**AI Response:**
```html
<div role="region" aria-label="AI generated response" aria-live="polite">
  <div class="ai-badge">AI</div>
  <div class="response-text">{streamedText}</div>
  <div class="citations">
    <a href="#source-1">[1]</a>
    <a href="#source-2">[2]</a>
  </div>
</div>
```

**Buttons:**
```html
<button aria-label="Upload document">
  <UploadIcon aria-hidden="true" />
</button>

<button aria-label="Copy to clipboard">
  <CopyIcon aria-hidden="true" />
</button>
```

## Color Contrast Requirements

### Minimum Contrast Ratios

| Text Type | Minimum | Enhanced |
|-----------|---------|----------|
| Normal text (< 18px) | 4.5:1 | 7:1 |
| Large text (≥ 18px) | 3:1 | 4.5:1 |
| UI components | 3:1 | 4.5:1 |
| Graphs/charts | 3:1 | 4.5:1 |

### Color Blindness Considerations

**Types Supported:**
- Protanopia (red-blind)
- Deuteranopia (green-blind)
- Tritanopia (blue-blind)
- Achromatopsia (monochromacy)

**Guidelines:**
- Don't use color alone to convey information
- Use icons + color
- Use patterns + color
- Provide text alternatives
- Test with simulators

**Example:**
```html
<!-- Bad: Color only -->
<span style="color: red;">Error</span>
<span style="color: green;">Success</span>

<!-- Good: Color + icon + text -->
<span role="alert" style="color: red;">
  <ErrorIcon aria-hidden="true" />
  Error: Invalid email
</span>
<span role="status" style="color: green;">
  <SuccessIcon aria-hidden="true" />
  Success: Saved
</span>
```

## Touch Target Sizes (Mobile)

### Minimum Sizes

| Element | Minimum | Recommended |
|---------|---------|-------------|
| Icon buttons | 44x44px | 48x48px |
| Text buttons | 44x44px | 48x48px |
| Form inputs | 44px height | 48px height |
| Checkboxes/Radios | 24x24px | 28x28px + padding |
| Toggle switches | 44x24px | 48x28px |
| Navigation items | 44px height | 56px height |
| FAB (Floating Action Button) | 56x56px | 64x64px |

### Spacing Between Targets

| Scenario | Minimum Gap |
|----------|-------------|
| Adjacent buttons | 8px |
| List items | 8px |
| Form fields | 16px |
| Cards | 16px |
| FAB to content | 16px |

**Critical Rule:** All interactive elements must have minimum 44x44px touch target.

**Example:**
```css
/* Bad: 24px icon button */
<button class="icon-btn">
  <SearchIcon />  <!-- 24x24px -->
</button>

/* Good: 44px touch target */
<button class="icon-btn" style="width: 44px; height: 44px;">
  <SearchIcon style="width: 24px; height: 24px;" aria-hidden="true" />
</button>
```

## Form Accessibility

### Labels and Instructions

**Required:**
```html
<!-- Good: Explicit label -->
<label for="email">Email</label>
<input id="email" type="email" autocomplete="email" />

<!-- Good: Implicit label -->
<label>
  Email
  <input type="email" autocomplete="email" />
</label>

<!-- Bad: No label -->
<input type="email" placeholder="Email" />
```

**Instructions:**
```html
<label for="password">
  Password
  <span class="sr-only">(8+ characters, 1 uppercase, 1 number)</span>
</label>
<input
  id="password"
  type="password"
  aria-describedby="password-help"
  minlength="8"
/>
<p id="password-help">8+ characters, 1 uppercase letter, 1 number</p>
```

### Error Handling

**Error Messages:**
```html
<div role="alert" aria-live="polite">
  <p id="email-error" style="color: var(--color-error-600);">
    <ErrorIcon aria-hidden="true" />
    Please enter a valid email address.
  </p>
</div>

<input
  id="email"
  type="email"
  aria-invalid="true"
  aria-describedby="email-error"
/>
```

**Error Suggestions:**
```html
<input
  id="search"
  type="search"
  value="Nebula Sarch"  <!-- Typo -->
  aria-invalid="true"
  aria-describedby="search-error search-suggestions"
/>

<p id="search-error">Did you mean "Nebula Search"?</p>
<ul id="search-suggestions">
  <li><a href="/search?q=nebula+search">Nebula Search</a></li>
</ul>
```

### Required Fields

```html
<label for="name">
  Name
  <span aria-label="required">*</span>
</label>
<input id="name" type="text" required aria-required="true" />

<!-- Or -->
<label for="name">
  Name
  <span class="required-indicator" aria-hidden="true">*</span>
  <span class="sr-only">(required)</span>
</label>
```

## Responsive Considerations

### Breakpoint Accessibility

| Breakpoint | Min Width | Considerations |
|------------|-----------|----------------|
| Mobile | 320px | Touch targets ≥ 44px, large text |
| Tablet | 768px | Keyboard navigation enabled |
| Desktop | 1024px | Hover states, multi-column |

### Orientation Changes

**Portrait:**
- Bottom navigation
- Full-width cards
- Swipeable content

**Landscape:**
- Side navigation
- Multi-column layout
- Keyboard shortcuts emphasized

**Alert:**
```js
// Warn users if orientation locked
screen.orientation.addEventListener('change', () => {
  if (screen.orientation.type.includes('landscape')) {
    announce('Landscape mode. Swipe to navigate.');
  }
});
```

## Motion & Animation

### Reduced Motion

**Respect User Preference:**
```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

**Provide Reduced Motion Option:**
```html
<div role="checkbox" aria-checked="false" tabindex="0">
  <label>Reduce motion</label>
</div>
```

**Animation Guidelines:**
- Essential animations only (loading, feedback)
- No auto-playing carousels
- Provide pause/stop controls
- Keep animations < 200ms (or reduce-motion)

## Testing Checklist

### Keyboard Navigation Testing

- [ ] Can navigate entire app with Tab/Shift+Tab
- [ ] Focus order is logical and predictable
- [ ] No keyboard traps (can always Escape)
- [ ] All interactive elements focusable
- [ ] Focus indicator clearly visible
- [ ] Skip links work correctly
- [ ] Modal focus trapping works
- [ ] Focus returns after modal close

### Screen Reader Testing

- [ ] Test with NVDA (Windows)
- [ ] Test with JAWS (Windows)
- [ ] Test with VoiceOver (macOS)
- [ ] Test with TalkBack (Android)
- [ ] All images have alt text
- [ ] Form inputs have labels
- [ ] Errors announced
- [ ] Live regions announce updates
- [ ] Headings create logical outline
- [ ] Links have descriptive text

### Color Contrast Testing

- [ ] Use WebAIM contrast checker
- [ ] Normal text: 4.5:1 minimum
- [ ] Large text: 3:1 minimum
- [ ] UI components: 3:1 minimum
- [ ] Test in high contrast mode
- [ ] Test with color blindness simulators

### Touch Target Testing

- [ ] All buttons ≥ 44x44px
- [ ] Adequate spacing between targets
- [ ] Test on actual devices (iOS, Android)
- [ ] Test with different screen sizes
- [ ] Verify no accidental taps

### Responsive Testing

- [ ] Test at 320px width
- [ ] Test at 768px width
- [ ] Test at 1024px width
- [ ] Test portrait and landscape
- [ ] Test font resizing to 200%
- [ ] Test zoom to 400%

## Implementation Notes

### React Focus Hook

```typescript
// hooks/useFocusTrap.ts
export function useFocusTrap(containerRef: RefObject<HTMLElement>) {
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    function handleTab(e: KeyboardEvent) {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    }

    container.addEventListener('keydown', handleTab);
    return () => container.removeEventListener('keydown', handleTab);
  }, [containerRef]);
}
```

### Screen Reader Announcement Hook

```typescript
// hooks/useAnnounce.ts
export function useAnnounce() {
  const [message, setMessage] = useState('');

  const announce = useCallback((text: string, priority: 'polite' | 'assertive' = 'polite') => {
    setMessage('');
    setTimeout(() => setMessage(text), 100);
  }, []);

  return { announce, message };
}
```

---

**Document Owner:** Accessibility Team  
**Last Updated:** 2026-07-16  
**Next Review:** 2026-10-16  
**Status:** Approved