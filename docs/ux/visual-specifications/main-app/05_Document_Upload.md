# Nebula Search Engine — Document Upload Screen Visual Specification

## 1. Screen Overview

### Purpose
Enable users to upload documents for indexing and searching. Supports drag-and-drop, file browser, and batch uploads.

### Primary Actions
1. Drag and drop files onto upload zone
2. Click to browse and select files
3. View upload progress and status

### Secondary Actions
- Cancel upload
- View uploaded files
- Configure upload settings (OCR, indexing options)
- Clear completed uploads

---

## 2. Layout

### Desktop (≥1024px)
```
┌─────────────┬──────────────────────────────────────────────────┐
│             │  Top Bar                                         │
│  Sidebar    │  [← Documents]  [Upload Files]                   │
│  (240px)    ├──────────────────────────────────────────────────┤
│             │                                                  │
│  🔍 Search  │  ┌──────────────────────────────────────────┐   │
│  💬 AI      │  │                                          │   │
│  📁 Docs    │  │     📁 Drop files here or                │   │
│  📊 Analytics│  │        click to browse                  │   │
│  🕐 History │  │                                          │   │
│  🔔 Notifs  │  │  Supports: PDF, DOCX, TXT, MD,          │   │
│             │  │  Images (OCR), CSV                       │   │
│  ⚙️ Settings│  │  Max size: 50MB per file                 │   │
│  👤 Profile │  │                                          │   │
│             │  └──────────────────────────────────────────┘   │
│  User Info  │                                                  │
│             │  Upload Queue (2 files)                          │
│             │  ┌──────────────────────────────────────────┐   │
│             │  │ 📄 report.pdf  ████████░░ 80%  [Cancel] │   │
│             │  │ 📄 data.csv    ████░░░░░░ 40%  [Cancel] │   │
│             │  └──────────────────────────────────────────┘   │
│             │                                                  │
│             │  Recent Uploads (3)                              │
│             │  ┌──────────────────────────────────────────┐   │
│             │  │ ✓ notes.md       2m ago  Indexed         │   │
│             │  │ ✓ presentation.pptx  5m ago  Indexed     │   │
│             │  │ ✓ image.png      10m ago  OCR Complete   │   │
│             │  └──────────────────────────────────────────┘   │
│             │                                                  │
└─────────────┴──────────────────────────────────────────────────┘
```

### Layout Template
- **Template:** Template 2 (Sidebar + Content)
- **Content padding:** 24px
- **Max content width:** 800px (centered)

---

## 3. Component Placement

### Drop Zone
```
Height: 320px (desktop), 240px (mobile)
Border: 2px dashed --color-border (gray-300)
Border-radius: 16px
Background: --color-bg-primary
Display: flex, flex-direction: column, align center, justify center
Gap: 16px
Padding: 40px
Cursor: pointer
Transition: all 200ms

Content (centered):
  Icon: 📁 64×64px, text-tertiary
  Title: "Drop files here or click to browse" — text-lg, semibold, text-primary
  Subtitle: "Supports: PDF, DOCX, TXT, MD, Images (OCR), CSV" — text-sm, text-tertiary
  Size limit: "Max size: 50MB per file" — text-xs, text-tertiary
  Browse button: [Browse Files] — secondary button, 40px height

Drag over state:
  Border: 2px solid primary-500
  Background: primary-50
  Scale: 1.02
  Icon: changes to upload arrow
  Text: "Drop to upload"

Disabled state:
  Opacity: 0.5
  Cursor: not-allowed
```

### Upload Queue
```
Section title: "Upload Queue" — text-lg, semibold, margin-bottom 12px
Only visible when files are uploading

Each file item:
  Height: 56px
  Padding: 0 16px
  Background: --color-bg-primary
  Border: 1px solid --color-border
  Border-radius: 8px
  Margin-bottom: 8px
  Display: flex, align center, gap 12px

  Content:
    File icon: 24×24px (PDF, DOCX, etc.)
    File name: text-sm, font-medium, flex 1, truncate
    Progress bar: flex: 0 0 200px, height 6px, bg gray-200, fill primary-500, radius 3px
    Percentage: text-xs, text-tertiary, width 40px
    Cancel button: 32×32px icon button, text-tertiary (hover: error-500)
    Status: text-xs (Uploading..., Indexing..., Complete)
```

### Recent Uploads
```
Section title: "Recent Uploads" — text-lg, semibold, margin-bottom 12px
"View all →" link

Each file item:
  Height: 48px
  Padding: 0 12px
  Border-radius: 6px
  Display: flex, align center, gap 12px
  Hover: bg gray-50

  Content:
    Status icon: ✓ (success) or ⚠️ (warning) — 16×16px
    File icon: 20×20px
    File name: text-sm, font-medium, flex 1, truncate
    Time: text-xs, text-tertiary
    Status label: text-xs (Indexed, OCR Complete, Error)
    Actions: [⋮] 32×32px
```

---

## 4. Typography

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Drop zone title | 18px | 600 | text-primary |
| Drop zone subtitle | 14px | 400 | text-tertiary |
| File name | 14px | 500 | text-primary |
| Progress % | 12px | 400 | text-tertiary |
| Status text | 12px | 400 | text-tertiary |
| Section title | 18px | 600 | text-primary |
| Recent file name | 14px | 500 | text-primary |
| Recent time | 12px | 400 | text-tertiary |

---

## 5. Colors

### Light Mode
- **Drop zone:** #ffffff bg, #d1d5db border
- **Drag over:** #eff6ff bg, #3b82f6 border
- **Progress fill:** #3b82f6
- **Progress bg:** #e5e7eb
- **Success icon:** #22c55e
- **Error icon:** #ef4444
- **Queue item:** #ffffff bg, #e5e7eb border

### Dark Mode
- **Drop zone:** #1e293b bg, #475569 border
- **Drag over:** #1e3a8a bg, #3b82f6 border
- **Progress fill:** #60a5fa
- **Progress bg:** #334155
- **Success icon:** #4ade80
- **Error icon:** #f87171
- **Queue item:** #1e293b bg, #334155 border

---

## 6. Interaction States

### Drop Zone
| State | Border | Background | Scale |
|-------|--------|------------|-------|
| Default | dashed gray-300 | white | 1 |
| Hover | dashed gray-400 | gray-50 | 1 |
| Drag over | solid primary-500 | primary-50 | 1.02 |
| Uploading | dashed gray-300 | white | 1 |
| Disabled | dashed gray-200 | gray-100 | 1 |

### File Items
| State | Background |
|-------|------------|
| Default | transparent |
| Hover | gray-50 |
| Error | error-50 |

---

## 7. Animations

- **File card appears:** Slide in from top 200ms, opacity 0→1
- **Progress bar:** Smooth width transition 300ms
- **Completion:** Checkmark scales 0→1 with bounce 300ms
- **Drag over:** Border + bg transition 150ms
- **Cancel:** Item slides out right 200ms
- **Error state:** Shake 400ms

---

## 8. Responsive

- **Desktop:** 320px drop zone, 2-column queue
- **Tablet:** 280px drop zone, single column queue
- **Mobile:** 200px drop zone, full-width, compact queue items

---

## 9. Accessibility

### Keyboard
```
Tab: Browse button → queue items → recent items
Enter/Space: Activate browse / select file
Escape: Cancel upload
```

### ARIA
```html
<div role="button" tabindex="0" aria-label="Upload files. Drop files or press Enter to browse."
  aria-describedby="upload-formats">
  <input type="file" multiple accept=".pdf,.docx,.txt" class="sr-only" />
</div>
<div role="progressbar" aria-valuenow="80" aria-valuemin="0" aria-valuemax="100">
<div role="status" aria-live="polite">Uploading report.pdf - 80% complete</div>
```

---

## 10. Developer Notes

### Component States
```
files: File[]
uploads: UploadProgress[] (id, name, progress, status)
isDragOver: boolean
recentUploads: Upload[]
```

### API
```
POST /api/v1/documents/upload
Content-Type: multipart/form-data
Response: { id, name, status: "uploading" }

GET /api/v1/documents/upload-status/{id}
Response: { progress: 80, status: "indexing" }
```

---

**Last Updated:** 2026-07-17