# Nebula Search Engine — Component Library

## Executive Summary

This document defines all reusable UI components for Nebula Search Engine, including their specifications, variants, states, and accessibility requirements. It serves as the single source of truth for frontend implementation.

**Goal:** Ensure consistency, accessibility, and maintainability across all user interfaces.

## Critical UI Gap Components

### 1. Document Upload UI

**Purpose:** Enable users to upload documents with clear feedback and progress indication.

**Anatomy:**
```
┌─────────────────────────────────────┐
│                                     │
│     📁 Drop files here or          │
│        click to browse             │
│                                     │
│     Supports: PDF, DOCX, TXT,      │
│     MD, Images (OCR)               │
│                                     │
│     Max size: 50MB per file        │
│                                     │
└─────────────────────────────────────┘

Progress Bar:
████████████████░░░░░░░░  65%

Status: Indexing... (ETA: 30s)
```

**Variants:**
1. **Default:** Dashed border, centered content
2. **Drag Over:** Solid border, highlighted background
3. **Uploading:** Progress bar, file list
4. **Success:** Checkmark, file count
5. **Error:** Red border, error message

**Specifications:**
- **Size:** 400px height (desktop), 300px (mobile)
- **Border:** 2px dashed gray-300
- **Drag Over:** 2px solid primary-500
- **Icon:** Upload icon (24px)
- **Text:** text-base, gray-600
- **Padding:** 40px all sides

**States:**
- `idle`: Waiting for file
- `dragover`: File hovering
- `uploading`: Progress 0-100%
- `success`: Upload complete
- `error`: Upload failed

**Accessibility:**
- Keyboard accessible (Enter to browse)
- Screen reader: "Upload files. Press Enter to browse."
- File input properly labeled
- Progress announced to screen readers

**Responsive:**
- Desktop: Large dropzone (400px)
- Tablet: Medium dropzone (350px)
- Mobile: Full-width, compact (200px)

**Code Example:**
```jsx
<DropZone
  accept={['.pdf', '.docx', '.txt', '.md']}
  maxSize={50 * 1024 * 1024}
  multiple
  onUpload={(files) => handleUpload(files)}
  progress={uploadProgress}
  status={uploadStatus}
/>
```

---

### 2. Settings Page

**Purpose:** Centralized configuration for user preferences, privacy, and system settings.

**Layout:**
```
┌──────────┬──────────────────────────────┐
│ Settings │  General Settings            │
│          │  ──────────────────────────  │
│ General  │                              │
│ Privacy  │  [Form fields]               │
│ Notifs   │                              │
│ AI       │  [Save] [Reset]              │
│ Integrations │                          │
│          │                              │
│          │                              │
└──────────┴──────────────────────────────┘
```

**Sections:**

#### 2.1 General Settings
- **Theme:** Light / Dark / System (radio buttons)
- **Language:** Dropdown (50+ languages)
- **Timezone:** Auto-detected dropdown
- **Date Format:** MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD
- **Search Engine:** Default search behavior
- **Results per page:** 10, 20, 50, 100

#### 2.2 Privacy Settings
- **Incognito Mode:** Toggle (default: off)
- **Data Retention:** 30/90/365 days / Forever
- **Analytics:** Opt-in/out toggle
- **Crash Reports:** Opt-in/out toggle
- **Personalization:** Opt-in/out toggle
- **Clear Data:** "Delete all my data" button

#### 2.3 Notification Settings
- **Email Notifications:** Toggle
- **Push Notifications:** Toggle
- **Search Alerts:** Toggle (daily/weekly)
- **AI Suggestions:** Toggle
- **Security Alerts:** Toggle (always on)
- **Marketing:** Toggle (default: off)

#### 2.4 AI Model Settings
- **Model Selection:** Dropdown (GPT-4, Claude, Local)
- **Temperature:** Slider (0-1, default: 0.7)
- **Max Tokens:** Number input (100-4000, default: 1000)
- **Streaming:** Toggle (default: on)
- **Citations:** Toggle (default: on)
- **Auto-summarize:** Toggle (default: off)

**Specifications:**
- **Sidebar width:** 240px (desktop), collapsible
- **Section padding:** 24px
- **Form field spacing:** 20px
- **Label width:** 180px (desktop), 100% (mobile)
- **Input height:** 40px (md)

**States:**
- `loading`: Skeleton screens
- `saving`: Spinner + "Saving..."
- `saved`: "Saved!" toast
- `error`: Error message inline

**Accessibility:**
- All inputs have labels
- Toggle switches have ARIA labels
- Section headings use semantic HTML
- Error messages link to problematic fields

**Keyboard Shortcuts:**
- Ctrl+,: Open settings
- Ctrl+S: Save changes
- Esc: Close settings

---

### 3. Search Bar Component

**Purpose:** Universal search input with suggestions, filters, and voice input.

**Anatomy:**
```
┌─────────────────────────────────────────────┐
│ 🔍 Search anything...        [🎤] [⚙️]    │
└─────────────────────────────────────────────┘

Dropdown:
┌─────────────────────────────────────────────┐
│ Recent Searches                      [Clear]│
│   - nebula search engine           [×]     │
│   - AI powered search              [×]     │
│                                             │
│ Suggestions                        [→]     │
│   - nebula search engine features           │
│   - nebula search engine pricing            │
│                                             │
│ Commands                        [Ctrl+K]    │
│   > Upload document                         │
│   > View analytics                          │
└─────────────────────────────────────────────┘
```

**Variants:**
1. **Landing:** Large (64px height), centered
2. **Header:** Medium (48px height), left-aligned
3. **Command Palette:** Full-screen overlay
4. **Inline:** Expanded within page

**States:**
- `idle`: Placeholder text
- `focused`: Border highlight, suggestions visible
- `typing`: Debounced suggestions
- `loading`: Spinner inside input
- `results`: Results dropdown visible

**Specifications:**
- **Height:** 48px (desktop), 44px (mobile)
- **Border radius:** 8px
- **Border:** 1px gray-200
- **Focus border:** 2px primary-500
- **Padding:** 0 16px
- **Font size:** 16px (body)
- **Icon size:** 20px
- **Dropdown max height:** 400px

**Accessibility:**
- Role: search
- ARIA label: "Search"
- ARIA describedby: "Search suggestions"
- Keyboard: Enter to search, ↑↓ to navigate suggestions
- Screen reader: Announces suggestion count

**Keyboard Shortcuts:**
- Ctrl+K: Focus search
- Escape: Close suggestions
- Enter: Execute search
- ↑↓: Navigate suggestions
- Tab: Accept suggestion

---

### 4. AI Response Card

**Purpose:** Display AI-generated responses with citations and actions.

**Anatomy:**
```
┌─────────────────────────────────────────────┐
│ 🤖 AI Summary                    [👍] [👎] │
│                                             │
│ Nebula Search Engine is a next-generation   │
│ search platform that combines traditional   │
│ keyword search with semantic vector search  │
│ capabilities [1][2].                        │
│                                             │
│ Sources:                                    │
│ [1] docs/01_Project_Vision.md              │
│ [2] docs/02_Design_Principles.md           │
│                                             │
│ 💡 Follow-up:                               │
│ [What is hybrid search?] [How does it work?]│
│                                             │
│ [Copy] [Save] [Share]                       │
└─────────────────────────────────────────────┘
```

**Components:**
1. **AI Badge:** "AI" label with icon
2. **Response Text:** Streamed content
3. **Citations:** Numbered reference links
4. **Sources:** Expandable source list
5. **Follow-up:** Interactive chips
6. **Actions:** Copy, save, share, feedback

**Specifications:**
- **Padding:** 24px
- **Border radius:** 12px
- **Border:** 1px primary-200
- **Background:** primary-50
- **Font size:** 14px (body)
- **Line height:** 1.6
- **Badge:** 24px height, primary-500 bg

**States:**
- `streaming`: Typing indicator
- `complete`: Full response
- `error`: Error message + retry
- `loading`: Skeleton (3 lines)

**Accessibility:**
- ARIA label: "AI generated response"
- Live region for streaming
- Citations are links with descriptive text
- Feedback buttons have labels

---

### 5. Search Result Card

**Purpose:** Display individual search results with metadata and actions.

**Anatomy:**
```
┌─────────────────────────────────────────────┐
│ [Favicon] Title of Document                 │
│ https://example.com/docs/page               │
│                                             │
│ Excerpt from the document that matches the  │
│ search query with highlighted terms...      │
│                                             │
│ Type: PDF | Size: 2.4 MB | Modified: 2d ago│
│ [Save] [Share] [Preview]                    │
└─────────────────────────────────────────────┘
```

**Variants:**
1. **Web Result:** URL, favicon, snippet
2. **Document:** File type icon, metadata
3. **Image:** Thumbnail, dimensions
4. **Video:** Thumbnail, duration, channel

**Specifications:**
- **Padding:** 16px
- **Border radius:** 8px
- **Min height:** 120px
- **Hover:** Background gray-50
- **Focus:** 2px primary-500 ring

**States:**
- `default`: Hover state
- `selected`: Blue background
- `saved`: Star icon filled
- `hover`: Subtle background change

**Accessibility:**
- Title is a link (semantic)
- Favicon has alt text
- Metadata uses `<dl>` list
- Actions are buttons with labels

---

## Common Components

### Buttons

**Variants:**

1. **Primary Button**
   - Background: primary-600
   - Text: white
   - Hover: primary-700
   - Height: 40px (md)
   - Padding: 0 20px
   - Radius: 8px

2. **Secondary Button**
   - Background: white
   - Border: 1px gray-300
   - Text: gray-700
   - Hover: gray-50
   - Height: 40px (md)

3. **Ghost Button**
   - Background: transparent
   - Text: gray-700
   - Hover: gray-100
   - Height: 40px (md)

4. **Destructive Button**
   - Background: error-600
   - Text: white
   - Hover: error-700
   - Height: 40px (md)

**States:**
- Default
- Hover
- Active (scale 0.98)
- Focus (2px ring)
- Disabled (opacity 50%)
- Loading (spinner)

**Sizes:**
- sm: 32px height
- md: 40px height
- lg: 48px height

**Accessibility:**
- Minimum touch target: 44x44px
- Focus indicator visible
- Loading state announced
- Disabled state clear

---

### Form Inputs

**Text Input**
- Height: 40px
- Border: 1px gray-300
- Focus: 2px primary-500 ring
- Padding: 0 12px
- Radius: 8px

**Textarea**
- Min height: 120px
- Padding: 12px
- Border: 1px gray-300
- Focus: 2px primary-500 ring
- Radius: 8px

**Select**
- Same as text input
- Custom chevron icon
- Options max height: 300px

**Checkbox**
- Size: 20x20px
- Border: 2px gray-400
- Checked: primary-600 bg
- Focus: 2px ring

**Radio**
- Size: 20x20px
- Same as checkbox styling

**Toggle Switch**
- Width: 44px
- Height: 24px
- Knob: 20px circle
- Transition: 200ms

**Accessibility:**
- All inputs have labels
- Error messages linked
- Required fields marked
- Helper text provided

---

### Dropdowns & Menus

**Dropdown Menu**
- Min width: 200px
- Max height: 400px
- Shadow: shadow-lg
- Border radius: 8px
- Z-index: 1000

**Menu Items**
- Height: 40px
- Padding: 0 12px
- Hover: gray-100
- Focus: primary-50

**Specifications:**
- Items separated by 4px gap
- Dividers for sections
- Icons aligned left
- Shortcuts aligned right
- Sticky header/footer

---

### Dialogs & Modals

**Modal Dialog**
```
┌─────────────────────────────────────────────┐
│ Title                           [Close ×]   │
├─────────────────────────────────────────────┤
│                                             │
│ Content                                     │
│                                             │
│                                             │
├─────────────────────────────────────────────┤
│              [Cancel] [Confirm]              │
└─────────────────────────────────────────────┘
```

**Specifications:**
- Width: 500px (sm), 700px (md), 900px (lg)
- Max height: 90vh
- Padding: 24px
- Border radius: 12px
- Backdrop: rgba(0,0,0,0.5)
- Animation: Fade + scale 250ms

**Accessibility:**
- Role: dialog
- aria-modal: true
- aria-labelledby: title ID
- Trap focus within modal
- Close on Escape
- Return focus on close

---

### Toast Notifications

**Anatomy:**
```
┌─────────────────────────────────────────────┐
│ ✓ Success message                           │
│ Action completed successfully.    [Close ×] │
└─────────────────────────────────────────────┘
```

**Variants:**
- Success (green)
- Error (red)
- Warning (yellow)
- Info (blue)

**Specifications:**
- Width: 400px (max)
- Padding: 16px
- Border radius: 8px
- Shadow: shadow-lg
- Animation: Slide in from right (300ms)
- Auto-dismiss: 5s (configurable)

**Position:**
- Top right (desktop)
- Top center (mobile)
- Stack: Max 3 visible

---

### Progress Indicators

**Linear Progress Bar**
- Height: 8px
- Background: gray-200
- Fill: primary-600
- Radius: 4px
- Animation: 200ms

**Circular Progress**
- Size: 40px (sm), 48px (md), 64px (lg)
- Stroke width: 4px
- Color: primary-600

**Skeleton Loader**
- Background: gray-200
- Shimmer: linear-gradient animation
- Radius: 4px
- Height: matches content

---

### Cards

**Standard Card**
- Padding: 24px
- Border radius: 12px
- Border: 1px gray-200
- Shadow: shadow-sm
- Hover shadow: shadow-md

**Image Card**
- Aspect ratio: 16:9 (default)
- Border radius: 12px
- Image object-fit: cover

**Specifications:**
- Min width: 300px
- Max width: 100%
- Gap: 16px (in grid)

---

### Tables

**Data Table**
```
┌──────────────────────────────────────────────┐
│ Header 1          Header 2       Header 3   │
├──────────────────────────────────────────────┤
│ Row 1 col 1       Row 1 col 2    Row 1 col 3│
│ Row 2 col 1       Row 2 col 2    Row 2 col 3│
└──────────────────────────────────────────────┘
```

**Specifications:**
- Header height: 48px
- Row height: 56px
- Padding: 0 16px
- Border bottom: 1px gray-200
- Hover: gray-50

**Features:**
- Sortable columns (click header)
- Selectable rows (checkboxes)
- Inline editing
- Row actions (dropdown)
- Pagination (bottom)
- Bulk actions (when rows selected)

**Accessibility:**
- Table headers use `<th>`
- Scope attributes set
- Row selection with checkboxes
- Keyboard navigation (Tab, Shift+Space)

---

## Empty States

### No Search Results

```
┌─────────────────────────────────────────────┐
│                                             │
│              🔍                            │
│                                             │
│      No results found for "query"           │
│                                             │
│   Try adjusting your search or filters      │
│                                             │
│   [Clear filters] [Search suggestions]      │
│                                             │
└─────────────────────────────────────────────┘
```

### No Documents

```
┌─────────────────────────────────────────────┐
│                                             │
│              📁                            │
│                                             │
│      No documents uploaded yet              │
│                                             │
│   Upload your first document to get started │
│                                             │
│   [Upload Document]                         │
│                                             │
└─────────────────────────────────────────────┘
```

**Specifications:**
- Illustration: 120x120px
- Title: text-xl, semibold
- Description: text-sm, gray-600
- CTA button: primary
- Max width: 400px

---

## Implementation Checklist

### All Components Must Have:

- [ ] Responsive layout (mobile, tablet, desktop)
- [ ] Keyboard navigation
- [ ] Focus indicators (visible)
- [ ] ARIA labels/roles
- [ ] Screen reader testing
- [ ] Color contrast > 4.5:1
- [ ] Touch target ≥ 44x44px
- [ ] Loading states
- [ ] Error states
- [ ] Empty states
- [ ] Disabled states
- [ ] Hover states (desktop)
- [ ] Active states
- [ ] Documentation
- [ ] Storybook story (if applicable)

---

**Document Owner:** Design System Team  
**Last Updated:** 2026-07-16  
**Next Review:** 2026-10-16  
**Status:** Approved