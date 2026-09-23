# Nebula Search Engine — Login Screen Visual Specification

## 1. Screen Overview

### Purpose
Authenticate existing users and provide access to the full Nebula Search Engine experience.

### Primary Actions
1. Enter email/username and password
2. Submit login credentials
3. Navigate to signup (if no account)

### Secondary Actions
- Forgot password recovery
- Social login (Google, GitHub, Microsoft)
- Remember me toggle
- Show/hide password toggle

---

## 2. Layout

### Desktop (≥1024px)
```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│                                                          │
│                                                          │
│               ┌─────────────────────────────┐            │
│               │                             │            │
│               │         [Nebula Logo]       │            │
│               │                             │            │
│               │     Welcome back            │            │
│               │     Sign in to your account │            │
│               │                             │            │
│               │     ┌─────────────────┐     │            │
│               │     │ Email           │     │            │
│               │     └─────────────────┘     │            │
│               │                             │            │
│               │     ┌─────────────────┐     │            │
│               │     │ Password   [👁] │     │            │
│               │     └─────────────────┘     │            │
│               │                             │            │
│               │     □ Remember me           │            │
│               │                             │            │
│               │     [Sign In]               │            │
│               │                             │            │
│               │     ─── or continue with ───│            │
│               │                             │            │
│               │     [G] [GitHub] [M]        │            │
│               │                             │            │
│               │     Don't have an account?  │            │
│               │     [Create one]            │            │
│               │                             │            │
│               └─────────────────────────────┘            │
│                                                          │
│                                                          │
│              Footer: Privacy | Terms | Docs              │
└──────────────────────────────────────────────────────────┘
```

### Layout Template
- **Template:** Template 1 (Centered Card)
- **Page background:** `--color-bg-secondary`
- **Card width:** 400px (desktop), 360px (tablet), full-width with 24px margins (mobile)
- **Card padding:** 32px
- **Card background:** `--color-bg-primary`
- **Card shadow:** `--shadow-xl`
- **Card radius:** `--radius-xl` (16px)

---

## 3. Component Placement

### Logo
```
Position: Center, top of card
Size: 40px height
Margin-bottom: 24px
Link to: /
```

### Heading
```
"Welcome back"
  font: --text-2xl (24px), --font-semibold (600)
  color: --color-text-primary
  text-align: center
  margin-bottom: 4px

"Sign in to your account"
  font: --text-sm (14px), --font-normal (400)
  color: --color-text-tertiary
  text-align: center
  margin-bottom: 24px
```

### Form Fields
```
Email Input:
  Label: "Email" (--text-sm, --font-medium, --color-text-secondary)
  Input height: 44px (touch target)
  Border: 1px solid --color-border
  Border-radius: 8px
  Padding: 0 12px
  Font: --text-base (16px)
  Placeholder: "you@example.com"
  Type: email
  Autocomplete: email
  Margin-bottom: 16px
  Focus: 2px primary-500 ring

Password Input:
  Label: "Password" (--text-sm, --font-medium, --color-text-secondary)
  Input height: 44px
  Border: 1px solid --color-border
  Border-radius: 8px
  Padding: 0 40px 0 12px (right padding for toggle)
  Font: --text-base (16px)
  Type: password
  Autocomplete: current-password
  Margin-bottom: 12px
  Focus: 2px primary-500 ring
  Toggle: 44×44px icon button (eye icon), right-aligned inside input
```

### Remember Me + Forgot Password
```
Row layout (flex, space-between, align center):
  Left: Checkbox (20×20px) + "Remember me" (--text-sm, --color-text-secondary)
  Right: "Forgot password?" link (--text-sm, --color-primary-500)
  Margin-bottom: 24px
```

### Submit Button
```
Full width button:
  Width: 100%
  Height: 44px
  Background: --color-primary-600
  Color: white
  Font: --text-base (16px), --font-semibold (600)
  Border-radius: 8px
  Border: none
  Cursor: pointer
  Margin-bottom: 24px

States:
  Default: bg primary-600
  Hover: bg primary-700
  Active: scale(0.98)
  Loading: show spinner, disable button
  Disabled: opacity 0.5 (when form invalid)
```

### Social Login Divider
```
"or continue with"
  Display: flex with lines
  Line: 1px solid --color-border, flex: 1
  Text: --text-sm, --color-text-tertiary, padding 0 16px
  Margin-bottom: 16px
```

### Social Login Buttons
```
Row of 3 icon buttons:
  Size: 44×44px each
  Border: 1px solid --color-border
  Border-radius: 8px
  Background: transparent
  Icon size: 20×20px
  Gap: 12px
  Justify-content: center

Hover: bg gray-50
Focus: 2px primary-500 ring
```

### Sign Up Link
```
Text: "Don't have an account?" (--text-sm, --color-text-tertiary)
Link: "Create one" (--text-sm, --color-primary-500, font-medium)
Text-align: center
Margin-top: 24px
```

---

## 4. Typography

| Element | Size | Weight | Line Height | Color |
|---------|------|--------|-------------|-------|
| Logo alt text | — | — | — | — |
| "Welcome back" | 24px | 600 | 1.3 | text-primary |
| "Sign in to your account" | 14px | 400 | 1.5 | text-tertiary |
| Form labels | 14px | 500 | 1.5 | text-secondary |
| Input text | 16px | 400 | 1.5 | text-primary |
| Input placeholder | 16px | 400 | 1.5 | text-disabled |
| Remember me | 14px | 400 | 1.5 | text-secondary |
| Forgot password | 14px | 500 | 1.5 | primary-500 |
| Sign in button | 16px | 600 | 1.5 | white |
| Social divider | 14px | 400 | 1.5 | text-tertiary |
| Sign up text | 14px | 400 | 1.5 | text-tertiary |
| Sign up link | 14px | 500 | 1.5 | primary-500 |
| Error message | 13px | 400 | 1.5 | error-600 |

---

## 5. Color Usage

### Light Mode
- **Page bg:** #f9fafb
- **Card bg:** #ffffff
- **Card border:** #e5e7eb
- **Input border:** #d1d5db
- **Input bg:** #ffffff
- **Input focus:** #3b82f6 ring
- **Primary button:** #2563eb bg, #ffffff text
- **Social buttons:** transparent bg, #d1d5db border
- **Error text:** #ef4444
- **Success text:** #22c55e

### Dark Mode
- **Page bg:** #0f172a
- **Card bg:** #1e293b
- **Card border:** #334155
- **Input border:** #475569
- **Input bg:** #1e293b
- **Input focus:** #3b82f6 ring
- **Primary button:** #3b82f6 bg, #ffffff text
- **Social buttons:** transparent bg, #475569 border
- **Error text:** #f87171
- **Success text:** #4ade80

---

## 6. Interaction States

### Form Inputs
| State | Border | Background | Shadow |
|-------|--------|------------|--------|
| Default | gray-300 | white | none |
| Hover | gray-400 | white | none |
| Focus | primary-500 | white | 0 0 0 3px primary-100 |
| Filled | gray-300 | white | none |
| Error | error-500 | error-50 | 0 0 0 3px error-100 |
| Disabled | gray-200 | gray-100 | none |

### Submit Button
| State | Background | Text | Transform |
|-------|-----------|------|-----------|
| Default | primary-600 | white | scale(1) |
| Hover | primary-700 | white | scale(1) |
| Active | primary-700 | white | scale(0.98) |
| Loading | primary-600 | white (spinner) | scale(1) |
| Disabled | gray-300 | gray-500 | scale(1) |

### Social Buttons
| State | Border | Background |
|-------|--------|------------|
| Default | gray-300 | transparent |
| Hover | gray-400 | gray-50 |
| Focus | primary-500 | gray-50 |
| Active | gray-400 | gray-100 |

---

## 7. Animations

### Page Load
```
Card: Fade in + translateY(20px → 0), 400ms ease-out
Logo: Fade in, 300ms ease-out
Form fields: Stagger in, 100ms delay each, 300ms ease-out
Button: Fade in, 400ms delay, 300ms ease-out
```

### Form Validation
```
Error state:
  - Input border: 200ms transition to error-500
  - Error message: slide down 200ms ease-out
  - Shake animation on submit with errors: 400ms

Success state:
  - Button: brief scale(1.02) pulse
  - Redirect: fade out 200ms
```

### Password Toggle
```
Icon swap: 150ms ease-out
No animation on input type change (security)
```

---

## 8. Responsive Layout

### Desktop (≥1024px)
- Card: 400px centered
- Full layout as described

### Laptop (1024-1279px)
- Same as desktop
- Card: 400px

### Tablet (768-1023px)
- Card: 360px
- Top margin: 80px (not vertically centered)
- Social buttons: 3 in a row

### Phone (<768px)
- Card: calc(100% - 32px) margins
- Card padding: 24px
- Top margin: 40px
- Social buttons: 3 in a row, full-width
- No vertical centering (scrollable)

### Ultra-wide (≥1920px)
- Card: 400px centered
- Larger vertical space

---

## 9. Accessibility

### Keyboard Navigation
```
Tab order:
  1. Skip to main content
  2. Email input
  3. Password input
  4. Show password toggle
  5. Remember me checkbox
  6. Forgot password link
  7. Sign in button
  8. Social login buttons (3)
  9. Create account link

Shortcuts:
  Enter: Submit form (from any field)
  Tab: Next field
  Shift+Tab: Previous field
  Escape: Clear focused field
```

### ARIA Attributes
```html
<main role="main">
<form aria-label="Sign in form">
  <label for="email">Email</label>
  <input 
    id="email" 
    type="email" 
    autocomplete="email"
    aria-required="true"
    aria-describedby="email-error"
    aria-invalid="false"
  />
  <div id="email-error" role="alert" aria-live="polite"></div>
  
  <label for="password">Password</label>
  <input 
    id="password" 
    type="password" 
    autocomplete="current-password"
    aria-required="true"
    aria-describedby="password-error"
    aria-invalid="false"
  />
  <button aria-label="Toggle password visibility" aria-pressed="false">
    <EyeIcon aria-hidden="true" />
  </button>
  
  <button type="submit" aria-label="Sign in to your account">
    Sign In
  </button>
</form>
```

### Focus Management
- Auto-focus email input on page load
- After error, focus first invalid field
- After successful login, redirect to dashboard
- Focus trap not needed (no modal)

### Error Handling
```html
<div role="alert" aria-live="assertive">
  <p id="email-error" style="color: var(--color-error-600);">
    <ErrorIcon aria-hidden="true" />
    Please enter a valid email address.
  </p>
</div>
```

### Contrast
- Labels: #4b5563 on #ffffff = 7:1 ✓ (AAA)
- Input text: #111827 on #ffffff = 14:1 ✓ (AAA)
- Error text: #ef4444 on #fef2f2 = 4.5:1 ✓ (AA)
- Primary button: #ffffff on #2563eb = 7.2:1 ✓ (AAA)
- Forgot password: #3b82f6 on #ffffff = 4.5:1 ✓ (AA)

### Touch Targets
- All inputs: 44px height ✓
- Show password: 44×44px ✓
- Checkbox: 20×20px (with 44×44px touch area via padding) ✓
- Submit button: 44px height ✓
- Social buttons: 44×44px ✓

---

## 10. Developer Implementation Notes

### Component Hierarchy
```
LoginPage
├── SkipLinks
├── AuthCard (Template 1)
│   ├── Logo (link to /)
│   ├── Heading
│   │   ├── Title (h1)
│   │   └── Subtitle (p)
│   ├── LoginForm
│   │   ├── EmailField
│   │   │   ├── Label
│   │   │   ├── Input (type=email)
│   │   │   └── ErrorMessage
│   │   ├── PasswordField
│   │   │   ├── Label
│   │   │   ├── Input (type=password)
│   │   │   ├── ToggleButton
│   │   │   └── ErrorMessage
│   │   ├── RememberForgotRow
│   │   │   ├── Checkbox + Label
│   │   │   └── ForgotLink
│   │   ├── SubmitButton
│   │   └── SocialLogin
│   │       ├── Divider
│   │       ├── GoogleButton
│   │       ├── GitHubButton
│   │       └── MicrosoftButton
│   └── SignupLink
└── Footer
```

### State Management
- `email: string`
- `password: string`
- `rememberMe: boolean`
- `showPassword: boolean`
- `isLoading: boolean`
- `errors: { email?: string, password?: string, general?: string }`
- `isFormValid: boolean` (derived)

### Form Validation Rules
```
Email:
  - Required: "Email is required"
  - Format: "Please enter a valid email address"
  - Max length: 254 characters

Password:
  - Required: "Password is required"
  - Min length: 8 characters
  - Max length: 128 characters

General:
  - Invalid credentials: "Invalid email or password"
  - Account locked: "Account temporarily locked. Try again in 15 minutes."
  - Network error: "Connection error. Please try again."
```

### API Integration
```
POST /api/v1/auth/login
Request: { email, password, remember_me }
Response: { access_token, refresh_token, user }
Error: 401 { error: "invalid_credentials" }
      429 { error: "rate_limited", retry_after: 900 }
```

### Security Notes
- Rate limiting: 5 attempts per minute per IP
- Lockout: 15 minutes after 10 failed attempts
- Password field: autocomplete="current-password"
- Token storage: httpOnly cookies preferred
- CSRF protection: token in header

### Performance Targets
- Form render: < 100ms
- Submit response: < 500ms (P95)
- Page load: < 1s FCP

---

**Design System References:**
- Layout Template: Template 1 (Centered Card)
- Components: Form Inputs, Buttons, Checkbox, Social Buttons
- Animations: Page Load, Form Validation
- Navigation: Minimal (no sidebar)

**Last Updated:** 2026-07-17