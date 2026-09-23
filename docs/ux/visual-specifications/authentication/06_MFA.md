# Nebula Search Engine — MFA (Multi-Factor Authentication) Screen Visual Specification

## 1. Screen Overview

### Purpose
Provide an additional layer of security by requiring a second authentication factor.

### Primary Actions
1. Enter authentication code from authenticator app or SMS
2. Verify and complete login
3. Trust this device (optional)

### Secondary Actions
- Use recovery code
- Request new SMS code
- Go back to login

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
│               │     Two-factor authentication│           │
│               │                             │            │
│               │     Enter the 6-digit code  │            │
│               │     from your authenticator │            │
│               │     app.                    │            │
│               │                             │            │
│               │     ┌──┐ ┌──┐ ┌──┐ ┌──┐    │            │
│               │     │  │ │  │ │  │ │  │    │            │
│               │     └──┘ └──┘ └──┘ └──┘    │            │
│               │     ┌──┐ ┌──┐              │            │
│               │     │  │ │  │              │            │
│               │     └──┘ └──┘              │            │
│               │                             │            │
│               │     [Verify]                │            │
│               │                             │            │
│               │     □ Trust this device     │            │
│               │       for 30 days           │            │
│               │                             │            │
│               │     [Use recovery code]     │            │
│               │     [Request SMS instead]   │            │
│               │                             │            │
│               └─────────────────────────────┘            │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Layout Template
- **Template:** Template 1 (Centered Card)
- **Card width:** 400px

---

## 3. Component Placement

### Logo & Heading
```
Logo: 40px, centered, margin-bottom 24px
Title: "Two-factor authentication" — text-2xl, semibold, centered
Description: "Enter the 6-digit code from your authenticator app."
  — text-sm, text-tertiary, centered, margin-bottom 32px
```

### OTP Input (6 digits)
```
Same as Email Verification OTP:
  - 6 individual digit boxes
  - 48×56px each (desktop)
  - Auto-advance on entry
  - Paste support
  - inputMode="numeric"
```

### Submit Button
```
Full width, 44px height
Primary-600 bg, white text
Radius: 8px
Text: "Verify"
Disabled: when not all 6 digits entered
Loading: spinner while verifying
```

### Trust Device Checkbox
```
Checkbox: 20×20px
Label: "Trust this device for 30 days" — text-sm, text-secondary
Margin-top: 16px
Margin-bottom: 24px
```

### Alternative Options
```
"Use recovery code" — text-sm, primary-500, centered
"Request SMS instead" — text-sm, primary-500, centered
Stacked vertically, gap 8px
Margin-top: 16px
```

---

## 4. Typography

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Title | 24px | 600 | text-primary |
| Description | 14px | 400 | text-tertiary |
| OTP digits | 24px | 600 | text-primary |
| Button | 16px | 600 | white |
| Trust device | 14px | 400 | text-secondary |
| Alternative links | 14px | 500 | primary-500 |

---

## 5. Colors

Same as Email Verification screen.

---

## 6. Interaction States

### OTP Boxes
Same as Email Verification:
- Default: gray-300 border
- Focus: primary-500 border + ring
- Filled: primary-50 bg, primary-500 border
- Error: error-50 bg, error-500 border + shake

### Auto-Submit
Auto-submit when all 6 digits entered (300ms delay)

---

## 7. Animations

- Same OTP animations as Email Verification
- Trust device checkbox: 200ms toggle animation
- Recovery code link: opens inline input with slide-down 200ms

---

## 8. Responsive

- Desktop: 48×56px OTP boxes
- Tablet: 44×52px
- Mobile: 40×48px

---

## 9. Accessibility

### Keyboard
```
Tab: OTP 1 → 6 → Verify → Trust device → Recovery → SMS
Auto-advance: Same as Email Verification
```

### ARIA
```html
<label id="mfa-label" class="sr-only">Enter 6-digit authentication code</label>
<div role="group" aria-labelledby="mfa-label">
  <!-- 6 OTP inputs -->
</div>
<div role="status" aria-live="polite" id="mfa-status"></div>
```

---

## 10. Developer Notes

### Component States
```
otp: string[] (6)
isLoading: boolean
error: string | null
trustDevice: boolean
showRecovery: boolean
```

### API
```
POST /api/v1/auth/mfa/verify
Request: { code: "123456", trust_device: true }
Response: { verified: true, token: "..." }
Error: 400 { error: "invalid_code" }
        429 { error: "rate_limited" }

POST /api/v1/auth/mfa/recovery
Request: { code: "recovery-code-here" }
Response: { verified: true, token: "..." }

POST /api/v1/auth/mfa/sms
Request: { phone: "+1234567890" }
Response: { message: "Code sent" }
```

### Security
- Rate limit: 5 attempts per minute
- Lockout: 10 failed attempts = 30 min lockout
- Recovery codes: 10 codes, each single-use
- Trust device: stored as signed cookie, 30-day expiry

---

**Last Updated:** 2026-07-17