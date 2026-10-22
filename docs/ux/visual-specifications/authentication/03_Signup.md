# Nebula Search Engine — Signup Screen Visual Specification

## 1. Screen Overview

### Purpose
Allow new users to create an account and begin using Nebula Search Engine.

### Primary Actions
1. Enter registration details (name, email, password)
2. Submit registration form
3. Navigate to login (if already have account)

### Secondary Actions
- Social signup (Google, GitHub, Microsoft)
- Show password requirements
- Accept terms of service
- Theme toggle

---

## 2. Layout

### Desktop (≥1024px)
```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│                                                          │
│               ┌─────────────────────────────┐            │
│               │                             │            │
│               │         [Nebula Logo]       │            │
│               │                             │            │
│               │     Create your account     │            │
│               │     Start searching smarter │            │
│               │                             │            │
│               │     ┌─────────────────┐     │            │
│               │     │ Full Name       │     │            │
│               │     └─────────────────┘     │            │
│               │                             │            │
│               │     ┌─────────────────┐     │            │
│               │     │ Email           │     │            │
│               │     └─────────────────┘     │            │
│               │                             │            │
│               │     ┌─────────────────┐     │            │
│               │     │ Password   [👁] │     │            │
│               │     └─────────────────┘     │            │
│               │     ○○○○○○○○ Strength      │            │
│               │                             │            │
│               │     ┌─────────────────┐     │            │
│               │     │ Confirm Password│     │            │
│               │     └─────────────────┘     │            │
│               │                             │            │
│               │     □ I agree to the        │            │
│               │       Terms & Privacy Policy│            │
│               │                             │            │
│               │     [Create Account]        │            │
│               │                             │            │
│               │     ─── or continue with ───│            │
│               │                             │            │
│               │     [G] [GitHub] [M]        │            │
│               │                             │            │
│               │     Already have an account?│            │
│               │     [Sign in]               │            │
│               │                             │            │
│               └─────────────────────────────┘            │
│                                                          │
│              Footer: Privacy | Terms | Docs              │
└──────────────────────────────────────────────────────────┘
```

### Layout Template
- **Template:** Template 1 (Centered Card)
- **Card width:** 420px (slightly wider for more fields)
- **Card padding:** 32px

---

## 3. Component Placement

### Logo & Heading (same as Login)
```
Logo: 40px height, centered, margin-bottom 24px
Title: "Create your account" — text-2xl (24px), semibold, centered
Subtitle: "Start searching smarter" — text-sm, text-tertiary, centered, margin-bottom 24px
```

### Form Fields
```
Full Name Input:
  Label: "Full Name" (text-sm, medium, text-secondary)
  Input: 44px height, border gray-300, radius 8px
  Placeholder: "John Doe"
  Autocomplete: name
  Margin-bottom: 16px

Email Input:
  Label: "Email" (text-sm, medium, text-secondary)
  Input: 44px height, border gray-300, radius 8px
  Placeholder: "you@example.com"
  Type: email
  Autocomplete: email
  Margin-bottom: 16px

Password Input:
  Label: "Password" (text-sm, medium, text-secondary)
  Input: 44px height, border gray-300, radius 8px
  Type: password
  Autocomplete: new-password
  Show/hide toggle: 44×44px
  Margin-bottom: 8px

Password Strength Indicator:
  Height: 4px
  Background: gray-200
  Fill: gradient (red → yellow → green)
  Border-radius: 2px
  Margin-bottom: 16px
  Width: 100%
  Labels below: "Weak" — "Fair" — "Good" — "Strong" (text-xs, text-tertiary)

Confirm Password Input:
  Label: "Confirm Password" (text-sm, medium, text-secondary)
  Input: 44px height, border gray-300, radius 8px
  Type: password
  Autocomplete: new-password
  Margin-bottom: 16px
  Match indicator: checkmark or X icon on blur
```

### Terms Checkbox
```
Checkbox: 20×20px, border 2px gray-400, checked bg primary-600
Label: "I agree to the" text-sm, text-secondary
Link: "Terms of Service" and "Privacy Policy" text-sm, primary-500
Margin-bottom: 24px
```

### Submit Button
```
Full width: 100%, height 44px
Background: primary-600, hover primary-700
Text: white, text-base, semibold
Radius: 8px
Disabled: opacity 0.5 (when form invalid or not agreed to terms)
```

### Social Login & Login Link
```
Same pattern as Login screen (divider + 3 buttons + link)
```

---

## 4. Typography

| Element | Size | Weight | Line Height | Color |
|---------|------|--------|-------------|-------|
| "Create your account" | 24px | 600 | 1.3 | text-primary |
| Subtitle | 14px | 400 | 1.5 | text-tertiary |
| Form labels | 14px | 500 | 1.5 | text-secondary |
| Input text | 16px | 400 | 1.5 | text-primary |
| Password strength label | 12px | 400 | 1.5 | text-tertiary |
| Terms text | 14px | 400 | 1.5 | text-secondary |
| Terms links | 14px | 500 | 1.5 | primary-500 |
| Password requirements | 13px | 400 | 1.5 | text-tertiary |

## 5. Color Usage

### Light Mode
- **Strength bar:** #ef4444 (weak), #f59e0b (fair), #3b82f6 (good), #22c55e (strong)
- **Password match:** #22c55e (match), #ef4444 (no match)
- **All other colors:** Same as Login screen

### Dark Mode
- **Strength bar:** #f87171 (weak), #fbbf24 (fair), #60a5fa (good), #4ade80 (strong)
- **All other colors:** Same as Login screen dark mode

---

## 6. Interaction States

### Password Strength Transitions
```
Empty: No bar visible
< 8 chars: Red, "Weak — Add more characters"
8+ chars (no variety): Orange, "Fair — Add a number"
8+ chars + number: Blue, "Good — Add a symbol"
12+ chars + number + symbol: Green, "Strong"
Mixed case + all above: Green, "Very strong"
```

### Confirm Password Match
```
On blur:
  Match: Green checkmark icon, "Passwords match" text
  No match: Red X icon, "Passwords don't match" text
  Empty: No indicator
```

---

## 7. Animations

- **Page load:** Same stagger pattern as Login
- **Strength bar:** Smooth width transition 200ms ease-out
- **Password match:** Icon fade-in 150ms
- **Form submit:** Button loading spinner, redirect on success
- **Error shake:** 400ms on validation errors

---

## 8. Responsive Layout

### Desktop (≥1024px)
- Card: 420px centered
- Full layout

### Tablet (768-1023px)
- Card: 380px
- Top margin: 60px

### Phone (<768px)
- Card: calc(100% - 32px)
- Card padding: 24px
- Top margin: 24px
- Password strength: compact layout

### Ultra-wide (≥1920px)
- Card: 420px centered

---

## 9. Accessibility

### Keyboard Navigation
```
Tab order:
  1. Skip link
  2. Full Name input
  3. Email input
  4. Password input
  5. Show password toggle
  6. Confirm Password input
  7. Terms checkbox
  8. Create Account button
  9. Social buttons
  10. Sign in link
```

### ARIA
```html
<label for="password">Password</label>
<input id="password" type="password" autocomplete="new-password" 
  aria-describedby="password-requirements password-strength"
  aria-required="true" />
<div id="password-requirements" class="text-xs">
  8+ characters, 1 uppercase, 1 number, 1 symbol
</div>
<div id="password-strength" role="status" aria-live="polite">
  Password strength: Good
</div>
```

### Form Validation
```
Full Name:
  Required: "Name is required"
  Min length: 2 characters

Email:
  Required: "Email is required"
  Format: "Please enter a valid email"
  Unique: "This email is already registered"

Password:
  Required: "Password is required"
  Min length: "At least 8 characters"
  Complexity: "Include uppercase, number, and symbol"

Confirm Password:
  Required: "Please confirm your password"
  Match: "Passwords don't match"
```

---

## 10. Developer Notes

### Component Hierarchy
```
SignupPage
├── SkipLinks
├── AuthCard
│   ├── Logo
│   ├── Heading (title + subtitle)
│   ├── SignupForm
│   │   ├── NameField
│   │   ├── EmailField
│   │   ├── PasswordField
│   │   │   ├── Input + Toggle
│   │   │   └── StrengthIndicator
│   │   ├── ConfirmPasswordField
│   │   │   ├── Input
│   │   │   └── MatchIndicator
│   │   ├── TermsCheckbox
│   │   ├── SubmitButton
│   │   └── SocialLogin
│   └── LoginLink
└── Footer
```

### API
```
POST /api/v1/auth/register
Request: { name, email, password }
Response: { user, message: "Verification email sent" }
Error: 409 { error: "email_exists" }
```

---

**Design System References:** Template 1, Form Inputs, Buttons, Checkbox, Strength Bar
**Last Updated:** 2026-07-17