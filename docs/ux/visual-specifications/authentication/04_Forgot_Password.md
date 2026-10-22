# Nebula Search Engine — Forgot Password Screen Visual Specification

## 1. Screen Overview

### Purpose
Allow users to reset their password via email verification.

### Primary Actions
1. Enter email address
2. Submit reset request
3. Check email for reset link

### Secondary Actions
- Return to login
- Contact support

---

## 2. Layout

### Desktop Layout
```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│               ┌─────────────────────────────┐            │
│               │                             │            │
│               │         [Nebula Logo]       │            │
│               │                             │            │
│               │     Forgot your password?   │            │
│               │     No worries. We'll send   │            │
│               │     you reset instructions. │            │
│               │                             │            │
│               │     ┌─────────────────┐     │            │
│               │     │ Email           │     │            │
│               │     └─────────────────┘     │            │
│               │                             │            │
│               │     [Send Reset Link]       │            │
│               │                             │            │
│               │     ← Back to login         │            │
│               │                             │            │
│               └─────────────────────────────┘            │
│                                                          │
│              Footer: Privacy | Terms | Docs              │
└──────────────────────────────────────────────────────────┘
```

### Success State Layout (after submission)
```
┌─────────────────────────────────────────────┐
│                                             │
│         [Nebula Logo]                       │
│                                             │
│     ✉️ Check your email                    │
│                                             │
│     We've sent a password reset link to     │
│     j***@example.com                        │
│                                             │
│     Didn't receive it? [Resend]             │
│                                             │
│     ← Back to login                         │
│                                             │
└─────────────────────────────────────────────┘
```

### Layout Template
- **Template:** Template 1 (Centered Card)
- **Card width:** 400px

---

## 3. Component Placement

### Logo & Heading
```
Logo: 40px, centered, margin-bottom 24px
Title: "Forgot your password?" — text-2xl, semibold, centered
Description: "No worries. We'll send you reset instructions."
  — text-sm, text-tertiary, centered, margin-bottom 24px, max-width 320px
```

### Email Input
```
Label: "Email"
Height: 44px
Border: 1px gray-300
Radius: 8px
Placeholder: "you@example.com"
Type: email
Autocomplete: email
Margin-bottom: 20px
```

### Submit Button
```
Full width, 44px height
Primary-600 bg, white text
Radius: 8px
Text: "Send Reset Link"
Disabled when email empty or invalid
Loading state: spinner
```

### Back Link
```
Text: "← Back to login"
Link to: /login
Text-sm, primary-500, font-medium
Centered, margin-top: 20px
```

### Success State (after submit)
```
Email icon: 64×64px, primary-100 bg, primary-500 icon, centered
Title: "Check your email" — text-xl, semibold, centered
Description: "We've sent a password reset link to" + masked email
Resend link: "Didn't receive it? [Resend]" — text-sm, timer 60s cooldown
Back link: "← Back to login"
```

---

## 4. Typography

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Title | 24px | 600 | text-primary |
| Description | 14px | 400 | text-tertiary |
| Email label | 14px | 500 | text-secondary |
| Input text | 16px | 400 | text-primary |
| Button text | 16px | 600 | white |
| Back link | 14px | 500 | primary-500 |
| Success title | 20px | 600 | text-primary |
| Success desc | 14px | 400 | text-secondary |

---

## 5. Colors & States

Same color scheme as Login screen. Additional:
- **Email icon area:** #dbeafe bg (primary-100), #3b82f6 icon (primary-500)
- **Resend link:** primary-500, disabled state gray-400
- **Timer text:** text-tertiary, text-xs

---

## 6. Animations

- **Page load:** Standard fade-in-up 400ms
- **State transition (form → success):** 
  - Form fades out 200ms
  - Success state fades in 300ms
  - Email icon scales in (0 → 1) with bounce
- **Resend cooldown:** Smooth countdown timer update
- **Error shake:** 400ms on invalid email

---

## 7. Responsive

- Desktop: 400px card
- Tablet: 360px card
- Mobile: Full-width card with margins
- Success state: Same responsive behavior

---

## 8. Accessibility

### Keyboard
- Tab: Email → Submit → Back
- Enter: Submit

### ARIA
```html
<form aria-label="Password reset form">
<input type="email" aria-describedby="email-help" aria-required="true">
<div role="alert" aria-live="polite" id="reset-status"></div>
</form>
```

### Focus
- Auto-focus email input
- After success: focus "Back to login" link

---

## 9. Developer Notes

### Component States
```
email: string
isSubmitted: boolean
isLoading: boolean
error: string | null
resendCooldown: number (seconds)
```

### API
```
POST /api/v1/auth/forgot-password
Request: { email }
Response: { message: "Reset link sent" }
Error: 404 { error: "email_not_found" }
        429 { error: "rate_limited", retry_after: 60 }
```

### Rate Limiting
- 1 request per 60 seconds per email
- 3 requests per hour per IP
- Resend cooldown: 60 seconds

---

**Last Updated:** 2026-07-17