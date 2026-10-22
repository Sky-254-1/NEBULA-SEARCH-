# Nebula Search Engine — Settings Screen Visual Specification

## 1. Screen Overview

### Purpose
Centralized configuration hub for user preferences, privacy controls, AI model settings, and integrations.

### Primary Actions
1. Browse and modify settings categories
2. Save changes
3. Reset to defaults

### Secondary Actions
- Export/import settings
- View keyboard shortcuts
- Clear data

---

## 2. Layout

### Desktop (≥1024px)
```
┌─────────────┬──────────────────────────────────────────────────┐
│             │  Top Bar                                         │
│  Sidebar    │  Settings                                        │
│  (240px)    ├──────────────────────────────────────────────────┤
│             │                                                  │
│  🔍 Search  │  ┌──────────┬──────────────────────────────┐    │
│  💬 AI      │  │ Settings │  General Settings             │    │
│  📁 Docs    │  │          │                              │    │
│  📊 Analytics│  │ General  │  Theme                       │    │
│  🕐 History │  │ Privacy  │  ○ Light  ○ Dark  ○ System   │    │
│  🔔 Notifs  │  │ Notifs   │                              │    │
│             │  │ AI       │  Language                     │    │
│  ⚙️ Settings│  │ Integrat.│  [English ▼]                 │    │
│  👤 Profile │  │          │                              │    │
│             │  │          │  Timezone                     │    │
│  User Info  │  │          │  [(UTC+0) UTC ▼]             │    │
│             │  │          │                              │    │
│             │  │          │  Results per page             │    │
│             │  │          │  [20 ▼]                      │    │
│             │  │          │                              │    │
│             │  │          │  [Save Changes] [Reset]      │    │
│             │  └──────────┴──────────────────────────────┘    │
│             │                                                  │
└─────────────┴──────────────────────────────────────────────────┘
```

### Layout Template
- **Template:** Template 2 (Sidebar + Content)
- Settings sidebar: 200px secondary sidebar
- Content: flex-1, max-width 720px

---

## 3. Component Placement

### Settings Sidebar (Secondary)
```
Width: 200px
Border-right: 1px solid --color-border
Padding: 16px 0

Items:
  ⚙️ General — icon + label, 40px height
  🔒 Privacy — 40px height
  🔔 Notifications — 40px height
  🤖 AI Models — 40px height
  🔗 Integrations — 40px height
  ⌨️ Shortcuts — 40px height
  
Active item: primary-600 text, primary-50 bg, 3px left border primary-500
Hover item: gray-50 bg
```

### General Settings Content
```
Section title: "General Settings" — text-xl, semibold, margin-bottom 24px

Theme Selection:
  Label: "Theme" — text-sm, font-medium, text-secondary
  Radio group: 3 options, horizontal, gap 12px
    [○ Light] [○ Dark] [○ System]
    Each option: 40px height pill, border gray-200, radius 8px, padding 0 16px
    Selected: bg primary-50, border primary-500, text primary-600

Language:
  Label: "Language" — text-sm, font-medium
  Select: [English ▼] — 40px height, radius 8px

Timezone:
  Label: "Timezone" — text-sm, font-medium
  Select: [(UTC+0) UTC ▼] — 40px height, radius 8px

Results per page:
  Label: "Results per page" — text-sm, font-medium
  Select: [20 ▼] — 40px height, radius 8px

Date format:
  Label: "Date format" — text-sm, font-medium
  Radio: [MM/DD/YYYY] [DD/MM/YYYY] [YYYY-MM-DD]
```

### Privacy Settings
```
Section title: "Privacy Settings" — text-xl, semibold

Incognito Mode:
  Toggle + description
  "Browse without saving search history"

Data Retention:
  Select: [30 days ▼] / 90 days / 365 days / Forever

Analytics:
  Toggle: "Help improve Nebula by sending anonymous usage data"

Crash Reports:
  Toggle: "Automatically send crash reports"

Personalization:
  Toggle: "Personalize search results based on usage"

Clear Data:
  [Clear Search History] — destructive button
  [Delete All Data] — destructive button, confirmation dialog
```

### Notifications Settings
```
Email Notifications: Toggle
Push Notifications: Toggle
Search Alerts: Toggle + frequency select [Daily ▼]
AI Suggestions: Toggle
Security Alerts: Toggle (always on, grayed out)
Marketing: Toggle
```

### AI Model Settings
```
Default Model: Select [GPT-4 ▼]
Temperature: Slider (0-1), default 0.7
Max Tokens: Number input, default 1000
Streaming: Toggle (on)
Citations: Toggle (on)
Auto-Summarize: Toggle (off)
```

### Save/Reset Row
```
Margin-top: 32px
Padding-top: 24px
Border-top: 1px solid --color-border
Display: flex, gap 12px

[Save Changes] — primary button, 40px
[Reset to Defaults] — ghost button, 40px, gray-700 text

Save button states:
  Default: primary-600
  Hover: primary-700
  Saving: spinner
  Saved: green checkmark, "Saved!" for 2s
  Disabled: opacity 0.5 (no changes)
```

---

## 4. Typography

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Section title | 20px | 600 | text-primary |
| Field label | 14px | 500 | text-secondary |
| Field value | 14px | 400 | text-primary |
| Toggle label | 14px | 400 | text-secondary |
| Toggle description | 13px | 400 | text-tertiary |
| Sidebar item | 14px | 500 | text-secondary |
| Sidebar active | 14px | 600 | primary-600 |

---

## 5. Colors

Standard light/dark color tokens. Toggle switches use primary-500 for active state.

---

## 6. Interaction States

### Toggle Switch
| State | Track | Knob |
|-------|-------|------|
| Off | gray-200 | white |
| On | primary-500 | white |
| Focus | primary-300 ring | — |
| Disabled | gray-100 | gray-300 |

### Save Button
| State | Background | Text |
|-------|-----------|------|
| Default | primary-600 | white |
| Hover | primary-700 | white |
| Saving | primary-600 | spinner |
| Saved | secondary-600 | white |
| Disabled | gray-200 | gray-400 |

---

## 7. Animations

- **Section transition:** Content cross-fade 150ms
- **Toggle switch:** Knob slide 200ms ease-out
- **Save button:** Spinner while saving, checkmark on success
- **Sidebar selection:** Background transition 150ms

---

## 8. Responsive

- **Desktop:** Settings sidebar + content
- **Tablet:** Settings sidebar collapses to top tabs
- **Mobile:** Single column, sections stacked, tabs as horizontal scroll

---

## 9. Accessibility

### Keyboard
```
Ctrl+,: Open settings
Ctrl+S: Save
Tab: Through form fields
Shift+Tab: Previous field
Escape: Close settings
1-5: Jump to section
```

### ARIA
```html
<nav aria-label="Settings sections" role="tablist">
  <button role="tab" aria-selected="true">General</button>
</nav>
<section role="tabpanel" aria-label="General settings">
  <fieldset>
    <legend>Theme</legend>
  </fieldset>
</section>
```

---

## 10. Developer Notes

### Component Hierarchy
```
SettingsPage
├── SettingsSidebar
│   └── SettingsNavItem × 7
├── SettingsContent
│   ├── GeneralSection
│   ├── PrivacySection
│   ├── NotificationsSection
│   ├── AIModelsSection
│   ├── IntegrationsSection
│   ├── ShortcutsSection
│   └── ActionRow (Save + Reset)
```

### State
```
activeSection: string
settings: { theme, language, timezone, resultsPerPage, ... }
hasChanges: boolean
isSaving: boolean
```

### API
```
GET /api/v1/settings
Response: { theme, language, ... }

PUT /api/v1/settings
Request: { theme: "dark", language: "en", ... }
Response: { saved: true }

POST /api/v1/settings/reset
Response: { reset: true }
```

---

**Last Updated:** 2026-07-17