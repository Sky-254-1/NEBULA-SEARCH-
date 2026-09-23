# Nebula Search Engine — User Profile Screen Visual Specification

## 1. Screen Overview

### Purpose
View and edit personal profile information, manage account security, and view activity summary.

### Primary Actions
1. Edit profile details (name, email, avatar)
2. Change password
3. View account activity

### Secondary Actions
- Delete account
- Export data
- View API keys

---

## 2. Layout

### Desktop Layout
```
┌─────────────┬──────────────────────────────────────────────────┐
│  Sidebar    │  Top Bar                                         │
│  (240px)    ├──────────────────────────────────────────────────┤
│             │                                                  │
│             │  ┌──────────────────────────────────────────┐   │
│             │  │  Profile                    [Edit]       │   │
│             │  │  ┌─────┐                                │   │
│             │  │  │ Av  │  Alex Johnson                  │   │
│             │  │  │ atar│  alex@example.com              │   │
│             │  │  └─────┘  Member since Jan 2026         │   │
│             │  └──────────────────────────────────────────┘   │
│             │                                                  │
│             │  ┌──────────────────────────────────────────┐   │
│             │  │  Account Security                        │   │
│             │  │  Password: ********    [Change]          │   │
│             │  │  MFA: [Enable]                           │   │
│             │  │  Sessions: 2 active    [Manage]          │   │
│             │  └──────────────────────────────────────────┘   │
│             │                                                  │
│             │  ┌──────────────────────────────────────────┐   │
│             │  │  Activity Summary                        │   │
│             │  │  Searches: 1,234 total                   │   │
│             │  │  Documents: 47 uploaded                  │   │
│             │  │  AI Queries: 892                         │   │
│             │  │  Storage: 2.4 GB of 10 GB               │   │
│             │  └──────────────────────────────────────────┘   │
│             │                                                  │
│             │  [Export Data] [Delete Account]                  │
│             │                                                  │
└─────────────┴──────────────────────────────────────────────────┘
```

### Layout Template
- **Template:** Template 2 (Sidebar + Content)
- **Content max-width:** 720px

---

## 3. Component Placement

### Profile Card
```
Background: --color-bg-primary
Border: 1px solid --color-border
Border-radius: 12px
Padding: 24px
Margin-bottom: 20px

Layout: flex, gap 20px
  Left: Avatar (80×80px, radius-full, object-fit cover)
  Right:
    Name: "Alex Johnson" — text-xl, semibold
    Email: "alex@example.com" — text-sm, text-tertiary
    Member since: "Member since Jan 2026" — text-xs, text-tertiary
    [Edit Profile] — secondary button, 36px height, margin-top 8px
```

### Security Card
```
Same card style
Sections with labels and values:
  Password: "********" [Change] link
  MFA: [Enable] toggle or [Disable] link
  Sessions: "2 active sessions" [Manage] link
  API Keys: "3 keys" [Manage] link
```

### Activity Card
```
Same card style
Stats in a 2×2 grid:
  Searches: value + label
  Documents: value + label
  AI Queries: value + label
  Storage: value + progress bar
```

### Danger Zone
```
Border: 1px solid error-200
Border-radius: 12px
Padding: 20px
Background: error-50

[Export My Data] — secondary button
[Delete Account] — destructive button, opens confirmation modal
```

---

## 4. Typography

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Name | 20px | 600 | text-primary |
| Email | 14px | 400 | text-tertiary |
| Section title | 18px | 600 | text-primary |
| Stat value | 24px | 700 | text-primary |
| Stat label | 14px | 400 | text-tertiary |
| Danger zone title | 16px | 600 | error-600 |

---

## 5. Colors

Standard light/dark tokens. Danger zone uses error-50 bg, error-200 border.

---

## 6. Interaction States

Standard button and link states.

---

## 7. Animations

- **Card load:** Stagger fade-in 300ms
- **Edit modal:** Standard modal animation 250ms
- **Avatar hover:** Subtle overlay "Change photo"

---

## 8. Responsive

- **Desktop:** Full layout
- **Tablet:** Cards full-width
- **Mobile:** Stacked, compact stats grid (2 columns)

---

## 9. Accessibility

### Keyboard
```
Tab: Through all fields and actions
Enter: Edit, change, manage actions
```

### ARIA
```html
<article aria-label="Profile information">
<article aria-label="Account security">
<article aria-label="Activity summary">
<section aria-label="Danger zone">
```

---

## 10. Developer Notes

### API
```
GET /api/v1/user/profile
PUT /api/v1/user/profile
POST /api/v1/user/change-password
DELETE /api/v1/user/account
GET /api/v1/user/activity
```

---

**Last Updated:** 2026-07-17