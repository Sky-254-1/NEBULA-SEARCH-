# Nebula Search Engine — Email Verification Screen Visual Specification

## 1. Screen Overview

### Purpose
Verify user's email address after registration to activate the account.

### Primary Actions
1. Enter verification code from email
2. Submit verification
3. Request new verification code

### Secondary Actions
- Change email address
- Contact support
- Skip (if allowed by plan)

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
│               │     Verify your email       │            │
│               │                             │            │
│               │     We've sent a 6-digit     │            │
│               │     code to j***@example.com│            │
│               │                             │            │
│               │     ┌──┐ ┌──┐ ┌──┐ ┌──┐    │            │
│               │     │  │ │  │ │  │ │  │    │            │
│               │     └──┘ └──┘ └──┘ └──┘    │            │
│               │     ┌──┐ ┌──┐              │            │
│               │     │  │ │  │              │            │
│               │     └──┘ └──┘              │            │
│               │                             │            │
│               │     [Verify Email]          │            │
│               │                             │            │
│               │     Didn't receive?         │            │
│               │     [Resend in 60s]         │            │
│               │                             │            │
│               │     [Change email]          │            │
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
Title: "Verify your email" — text-2xl, semibold, centered
Description: "We've sent a 6-digit code to j***@example.com"
  — text-sm, text-tertiary, centered, margin-bottom 32px
```

### OTP Input (6 digits)
```
Container: flex, gap 8px, justify-content center
Each digit box:
  Width: 48px
  Height: 56px
  Border: 2px solid --color-border
  Border-radius: 8px
  Font: text-2xl (24px), semibold
  Text-align: center
  Background: --color-bg-primary
  Caret-color: primary-500

Focus:
  Border: 2px solid primary-500
  Box-shadow: 0 0 0 3px primary-100

Filled:
  Border: 2px solid primary-500
  Background: primary-50

Error:
  Border: 2px solid error-500
  Background: error-50
  Animation: shake 400ms

Auto-advance: On digit entry, focus next box
Paste support: Paste 6-digit code fills all boxes
```

### Submit Button
```
Full width, 44px height
Primary-600 bg, white text
Radius: 8px
Text: "Verify Email"
Disabled: when not all 6 digits entered
Loading: spinner while verifying
```

### Resend Section
```
Text: "Didn't receive the code?" — text-sm, text-tertiary
Link: "Resend in 60s" — text-sm, primary-500
  Disabled during cooldown (gray-400)
  Shows countdown: "Resend in 45s"
  Active: "Resend code"
Margin-top: 20px
```

### Change Email Link
```
Text: "Change email address" — text-sm, primary-500
Centered, margin-top: 8px
Opens inline edit or modal
```

---

## 4. Typography

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Title | 24px | 600 | text-primary |
| Description | 14px | 400 | text-tertiary |
| OTP digits | 24px | 600 | text-primary |
| Button | 16px | 600 | white |
| Resend text | 14px | 400 | text-tertiary |
| Resend link | 14px | 500 | primary-500 |
| Change email | 14px | 500 | primary-500 |

---

## 5. Colors

Same as Login screen. Additional:
- **OTP default:** #ffffff bg, #d1d5db border
- **OTP focus:** #ffffff bg, #3b82f6 border, #dbeafe ring
- **OTP filled:** #eff6ff bg, #3b82f6 border
- **OTP error:** #fef2f2 bg, #ef4444 border
- **OTP success:** #f0fdf4 bg, #22c55e border

---

## 6. Interaction States

### OTP Boxes
| State | Border | Background | Text |
|-------|--------|------------|------|
| Empty | gray-300 | white | — |
| Focus | primary-500 | white | — |
| Filled | primary-500 | primary-50 | text-primary |
| Error | error-500 | error-50 | text-primary |
| Disabled | gray-200 | gray-100 | gray-400 |

### Auto-Submit
When all 6 digits entered, auto-submit after 300ms delay
(Optional: user can also click button)

---

## 7. Animations

- **OTP focus:** Border transition 150ms
- **Auto-advance:** Next box focus 50ms after digit
- **Error:** Shake animation 400ms on wrong code
- **Success:** All boxes turn green 200ms, then redirect
- **Resend countdown:** Smooth number update each second

---

## 8. Responsive

- Desktop: 48×56px OTP boxes
- Tablet: 44×52px OTP boxes
- Mobile: 40×48px OTP boxes, gap 6px
- Ultra-wide: Same as desktop

---

## 9. Accessibility

### Keyboard
```
Tab: OTP box 1 → 2 → 3 → 4 → 5 → 6 → Verify → Resend
Auto-advance: After typing digit, focus moves to next box
Backspace: Clear current, focus previous
Paste: Ctrl+V fills all 6 boxes
```

### ARIA
```html
<label id="otp-label" class="sr-only">Enter 6-digit verification code</label>
<div role="group" aria-labelledby="otp-label">
  <input type="text" inputmode="numeric" pattern="[0-9]" maxlength="1" 
    aria-label="Digit 1 of 6" autocomplete="one-time-code" />
  <!-- 6 inputs total -->
</div>
<div role="status" aria-live="polite" id="otp-status"></div>
```

### autocomplete
Use `autocomplete="one-time-code"` for SMS/code autofill support

---

## 10. Developer Notes

### Component States
```
otp: string[] (6 items)
isLoading: boolean
error: string | null
resendCooldown: number (seconds)
email: string (masked)
```

### API
```
POST /api/v1/auth/verify-email
Request: { code: "123456" }
Response: { verified: true, redirect: "/dashboard" }
Error: 400 { error: "invalid_code" }
        429 { error: "rate_limited" }

POST /api/v1/auth/resend-verification
Request: { email }
Response: { message: "Code sent" }
```

### OTP Input Implementation
```typescript
// Each input
<input
  ref={(el) => inputRefs.current[index] = el}
  type="text"
  inputMode="numeric"
  maxLength={1}
  value={otp[index]}
  onChange={(e) => {
    const digit = e.target.value.replace(/[^0-9]/g, '');
    setOtp(prev => { const next = [...prev]; next[index] = digit; return next; });
    if (digit && index < 5) inputRefs.current[index + 1]?.focus();
  }}
  onKeyDown={(e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  }}
  onPaste={(e) => {
    const pasted = e.clipboardData.getData('text').replace(/[^0-9]/g, '');
    if (pasted.length === 6) setOtp(pasted.split(''));
  }}
/>
```

---

**Last Updated:** 2026-07-17