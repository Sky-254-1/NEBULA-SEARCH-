# Nebula Search Engine — AI Chat Workspace Visual Specification

## 1. Screen Overview

### Purpose
Provide a full conversational AI interface for research, analysis, and knowledge discovery with streaming responses, source citations, and context management.

### Primary Actions
1. Type/ask questions to AI assistant
2. View streaming AI responses with citations
3. Upload files for AI context
4. Manage conversation history

### Secondary Actions
- Select AI model
- Copy/save/share responses
- Provide feedback (thumbs up/down)
- View conversation history
- Regenerate responses
- Toggle right panel (sources, citations, context)

---

## 2. Layout

### Desktop (≥1024px) — Split Panel Layout
```
┌─────────────┬──────────────────────────────────────────────────┬──────────────┐
│             │  Chat Header (56px)                              │              │
│  Sidebar    │  [← New Chat]  [Model: GPT-4 ▼]  [⋮] [Users]   │  Right Panel │
│  (240px)    ├──────────────────────────────────────────────────┤  (360px)     │
│             │                                                  │              │
│  🔍 Search  │  Messages Area (scrollable, flex: 1)            │  Sources     │
│  💬 AI      │                                                  │  ──────────  │
│  📁 Docs    │  ┌─────────────────────────────────────────┐    │  [1] doc1.md│
│  📊 Analytics│  │ 💬 What is hybrid search?         12:30 │    │  [2] doc2.pdf│
│  🕐 History │  │ └─────────────────────────────────┘    │    │              │
│  🔔 Notifs  │  │                                         │    │  Citations   │
│             │  │ ┌─────────────────────────────────┐    │    │  ──────────  │
│  ⚙️ Settings│  │ 🤖                               │    │    │  "Hybrid ..."│
│  👤 Profile │  │ Hybrid search combines keyword... │    │    │              │
│             │  │ [1][2]                            │    │    │  Context     │
│  User Info  │  │ └─────────────────────────────────┘    │    │  ──────────  │
│             │  │                                         │    │  Files: 3    │
│             │  │ 💡 [Tell me more] [How is it different?]│    │              │
│             │  │                                         │    │              │
│             │  ├─────────────────────────────────────────┤    │              │
│             │  │ [📎]  [Type a message...]     [🎤] [▶] │    │              │
│             │  │        Input area (80px)                │    │              │
│             │  └─────────────────────────────────────────┘    │              │
└─────────────┴──────────────────────────────────────────────────┴──────────────┘
```

### Layout Template
- **Template:** Template 4 (Split Panel)
- **Chat width:** flex-1
- **Right panel width:** 360px
- **Sidebar width:** 240px

---

## 3. Component Placement

### Chat Header
```
Height: 56px
Padding: 0 16px
Border-bottom: 1px solid --color-border
Display: flex, align center, gap 8px

Left:
  [← Back / New Chat] — 40×40px icon button
  
Center (flex: 1):
  Model selector dropdown: [GPT-4 ▼] — 32px height, ghost button style
  Model status indicator: small green dot if online
  
Right:
  [Users] — Avatar stack (if collaborative), or hidden
  [⋮] — More options (clear chat, export, settings)
```

### Messages Area
```
Flex: 1
Overflow-y: auto
Padding: 16px 24px
Display: flex, flex-direction: column
Gap: 16px
Scroll-behavior: smooth
Auto-scroll to bottom on new message

Message spacing:
  User: align-self: flex-end
  AI: align-self: flex-start
  System: align-self: center
```

### Message Bubbles

**User Message:**
```
Max-width: 75%
Padding: 12px 16px
Border-radius: 16px 16px 4px 16px
Background: primary-600 (light), primary-500 (dark)
Text color: white
Font: text-base (16px), line-height: 1.5
Timestamp: text-xs, opacity 0.7, margin-top 4px
```

**AI Message:**
```
Max-width: 75%
Padding: 16px
Border-radius: 16px 16px 16px 4px
Background: gray-100 (light), bg-tertiary (dark)
Text color: text-primary
Font: text-base (16px), line-height: 1.6

Header:
  🤖 Avatar (28×28px) + "Nebula AI" — text-sm, font-semibold, margin-bottom 8px

Content:
  Streaming text: cursor blink animation
  Code blocks: bg gray-900, text-sm, radius 8px, padding 12px, copy button
  Lists: bulleted/numbered with proper spacing

Citations:
  [1] [2] — inline links, primary-500, font-medium
  Tools: inline code or search results

Follow-ups:
  Chips below message, margin-top: 12px
  [What is...] [How does...] [Tell me more]

Actions bar (bottom of message):
  [Copy] [👍] [👎] [Regenerate] [Share] — 32×32px icon buttons
  Margin-top: 8px
```

**Streaming AI Message:**
```
Same as AI message but:
  - Cursor: blinking | animation, 1s loop
  - Text appears gradually
  - Show cancel button after 2s if still streaming
  - Progress indicator: "Generating..." text-xs, text-tertiary
```

### Input Area
```
Height: auto (min 56px, max 160px)
Padding: 12px 16px
Border-top: 1px solid --color-border
Background: --color-bg-primary

Layout: flex, gap 8px
  Left: [📎 Attach] — 40×40px icon button
  Center: Textarea (flex: 1, no resize, no border, font 16px, placeholder: "Ask anything...")
  Right: [🎤 Voice] [▶ Send] — 40×40px buttons

Send button states:
  Default: primary-600 bg, white icon, 40×40px
  Disabled: gray-200 bg, gray-400 icon (when empty)
  Active: scale(0.95)

Textarea:
  Border: none, outline: none
  Background: transparent
  Font: 16px, text-primary
  Placeholder: "Ask anything..." text-tertiary
  max-height: 120px
  overflow-y: auto
  line-height: 1.5
  Resize: none
  Rows: 1 (expands with content)
```

### Right Panel (Sources / Citations)
```
Width: 360px
Border-left: 1px solid --color-border
Background: --color-bg-primary
Overflow-y: auto
Padding: 16px

Tab header:
  [Sources] [Citations] [Context]
  Tab height: 36px
  
Sources tab:
  List of referenced documents
  Each: file icon + name + excerpt, clickable

Citations tab:
  Numbered list of citations
  Each: citation text + link to source

Context tab:
  Uploaded files list
  Each: file name, size, status
  [Upload] button at bottom
```

---

## 4. Typography

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| User message | 16px | 400 | white |
| AI message | 16px | 400 | text-primary |
| AI header | 14px | 600 | text-primary |
| Timestamp | 12px | 400 | text-tertiary |
| Follow-up chips | 13px | 500 | primary-600 |
| Input text | 16px | 400 | text-primary |
| Model name | 14px | 500 | text-primary |
| Citation link | 14px | 500 | primary-500 |
| Right panel tab | 13px | 600 | text-secondary |
| Code text | 13px | 400 | gray-100 |

---

## 5. Color Usage

### Light Mode
- **Chat bg:** #ffffff
- **User bubble:** #2563eb (primary-600)
- **AI bubble:** #f3f4f6 (gray-100)
- **Input area:** #ffffff, border-top #e5e7eb
- **Right panel:** #ffffff, border-left #e5e7eb
- **Follow-up chip:** #ffffff bg, #e5e7eb border
- **Code block:** #111827 bg
- **Streaming cursor:** #3b82f6

### Dark Mode
- **Chat bg:** #0f172a
- **User bubble:** #3b82f6 (primary-500)
- **AI bubble:** #1e293b (bg-secondary)
- **Input area:** #0f172a, border-top #334155
- **Right panel:** #0f172a, border-left #334155
- **Follow-up chip:** #1e293b bg, #334155 border
- **Code block:** #020617 bg
- **Streaming cursor:** #60a5fa

---

## 6. Interaction States

### Messages
| State | Effect |
|-------|--------|
| Hover (AI) | Subtle bg change, show actions bar |
| Selected | primary-50 bg + left border |

### Input Area
| State | Border |
|-------|--------|
| Default | none |
| Focus | subtle ring or none (clean) |

### Send Button
| State | Background | Icon |
|-------|-----------|------|
| Empty | gray-200 | gray-400 |
| Has text | primary-600 | white |
| Loading | primary-600 | spinner |
| Hover | primary-700 | white |
| Active | scale(0.95) | white |

---

## 7. Animations

### Message Appearance
```
User message: Slide in from right 200ms ease-out
AI message: Slide in from left 200ms ease-out
Streaming: Character by character, 30ms per char
Follow-up chips: Stagger in 200ms, 50ms delay each
```

### Auto-scroll
```
Smooth scroll to bottom: 300ms ease-out
User scrolls up: pause auto-scroll
New message: resume auto-scroll
```

### Right Panel
```
Open: Slide in from right 300ms ease-out
Close: Slide out 200ms ease-in
Tab switch: Content cross-fade 150ms
```

### Typing Indicator
```
3 dots: bounce animation, 1.2s loop, 200ms stagger
Appears when AI starts processing
Replaced by streaming text when first token arrives
```

---

## 8. Responsive Layout

### Desktop (≥1024px)
- Full 3-column layout
- Right panel visible
- 75% max message width

### Laptop (1024-1279px)
- Right panel: hidden by default, toggle with button
- Same message widths

### Tablet (768-1023px)
- Sidebar collapsed
- Right panel: full-screen overlay on toggle
- Messages: 85% max width
- Input: fixed at bottom

### Phone (<768px)
- Bottom navigation (show AI tab active)
- Right panel: full-screen modal
- Messages: 90% max width
- Input: fixed bottom with keyboard avoidance
- Chat header: compact
- User avatar in header: hidden

---

## 9. Accessibility

### Keyboard
```
Ctrl+Shift+A: Open AI assistant (global)
Ctrl+Enter: Send message
Shift+Enter: New line in input
↑: Edit previous message (when input empty)
↓: Edit next message
Escape: Close right panel / clear selection
C: Copy last AI response
R: Regenerate last response
F: Focus input area
```

### ARIA
```html
<section role="region" aria-label="AI Chat">
  <div role="log" aria-live="polite" aria-label="Chat messages">
    <article aria-label="User message">
    <article aria-label="AI response" role="status">
  </div>
  <form aria-label="Message input">
    <textarea aria-label="Type your message" aria-describedby="input-help">
  </form>
</section>
```

### Focus Management
- Auto-focus input on page load and new chat
- Focus input after sending message
- Focus first follow-up chip after AI response
- Trap focus in right panel when open

---

## 10. Developer Notes

### Component Hierarchy
```
AIChatWorkspace
├── AppShell (sidebar + top bar)
├── ChatView (flex column)
│   ├── ChatHeader
│   │   ├── NewChatButton
│   │   ├── ModelSelector
│   │   └── OptionsMenu
│   ├── MessagesList (scrollable)
│   │   ├── UserMessage × N
│   │   │   ├── Text
│   │   │   └── Timestamp
│   │   ├── AIMessage × N
│   │   │   ├── Avatar + Name
│   │   │   ├── ResponseText (streaming)
│   │   │   ├── Citations
│   │   │   ├── FollowUpChips
│   │   │   └── ActionBar
│   │   ├── TypingIndicator
│   │   └── EmptyState ("Start a conversation")
│   └── InputArea
│       ├── AttachButton
│       ├── MessageInput (textarea)
│       ├── VoiceButton
│       └── SendButton
└── RightPanel
    ├── PanelTabs
    ├── SourcesList
    ├── CitationsList
    └── ContextFiles
```

### State
```
messages: Message[]
currentMessage: string
isStreaming: boolean
selectedModel: string
rightPanelOpen: boolean
rightPanelTab: 'sources' | 'citations' | 'context'
uploadedFiles: File[]
```

### API
```
POST /api/v1/ai/chat
Request: { messages: [...], model: "gpt-4", stream: true }
Response: Streaming SSE with token events

POST /api/v1/ai/chat/regenerate
Request: { message_id: "..." }
Response: Same streaming format

POST /api/v1/ai/chat/feedback
Request: { message_id, feedback: "positive" | "negative" }
```

### Streaming Implementation
```typescript
// EventSource or fetch with ReadableStream
// Events:
//   - token: { type: "token", text: "..." }
//   - citations: { type: "citations", sources: [...] }
//   - follow_up: { type: "follow_up", questions: [...] }
//   - done: { type: "done" }
//   - error: { type: "error", message: "..." }
```

---

**Last Updated:** 2026-07-17