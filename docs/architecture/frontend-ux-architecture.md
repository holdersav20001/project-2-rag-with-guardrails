# RAG with Guardrails -- Frontend UX Architecture

**Date:** 2026-03-31
**Stack:** React 18 + TypeScript + Vite
**Backend:** FastAPI (Python)
**CSS Strategy:** CSS Modules + CSS Custom Properties design system

---

## 1. CSS Architecture Decision: CSS Modules + Design Tokens

### Why CSS Modules (not Tailwind, not styled-components)

| Option | Verdict | Rationale |
|--------|---------|-----------|
| **CSS Modules** | **Selected** | Zero-runtime, scoped by default, works out-of-the-box with Vite, co-locates styles with components, no build plugin needed beyond what Vite ships, produces clean class names in dev |
| Tailwind | Rejected | Adds a build dependency and config overhead for a project with ~8 components. The real value of Tailwind is team velocity at scale -- overkill here. Also clutters JSX with utility strings, making the component logic harder to read in portfolio reviews |
| styled-components | Rejected | Runtime CSS-in-JS adds bundle weight and hydration cost for no benefit in a Vite SPA. Also, the library's maintenance trajectory is uncertain |

### Design Token Layer

A single `tokens.css` file imported at the app root provides the shared design language. CSS Modules in each component consume these tokens via `var(--token)`. This gives the benefits of a design system without a runtime dependency.

---

## 2. Component Hierarchy and Layout Structure

```
App
 |
 +-- AppLayout                      (grid shell: sidebar + main)
      |
      +-- Sidebar                   (document management, always visible on desktop)
      |    +-- DocumentUpload       (drag-and-drop + file picker)
      |    +-- DocumentList         (uploaded files with status badges)
      |
      +-- MainPanel                 (chat area, takes remaining width)
           |
           +-- Header               (app title, theme toggle, status indicator)
           |
           +-- ChatInterface        (scrollable message history + input)
           |    +-- MessageList     (renders array of Message components)
           |    |    +-- Message    (single message bubble)
           |    |         +-- UserMessage        (right-aligned, query text)
           |    |         +-- AssistantMessage   (left-aligned, answer text)
           |    |         |    +-- ConfidenceIndicator  (inline badge)
           |    |         |    +-- CitationLinks        (numbered superscripts)
           |    |         +-- BlockedMessage     (warning card when guardrails fire)
           |    |         +-- LoadingMessage     (skeleton/typing indicator)
           |    |
           |    +-- ChatInput       (textarea + send button + keyboard hint)
           |
           +-- CitationPanel        (slide-out or bottom drawer, shows source details)
                +-- CitationCard    (single source: filename, chunk text, score bar)
```

### Component Responsibility Map

| Component | State Owned | Props In | Events Out |
|-----------|------------|----------|------------|
| `AppLayout` | sidebar open/closed | -- | -- |
| `ChatInterface` | messages[], isLoading, error | -- | -- |
| `ChatInput` | inputValue, isSubmitting | disabled | onSubmit(query) |
| `MessageList` | -- | messages[] | onCitationClick(index) |
| `Message` | -- | message, type | onCitationClick |
| `AssistantMessage` | -- | answer, sources, confidence, blocked | onCitationClick |
| `BlockedMessage` | -- | blockReason | -- |
| `ConfidenceIndicator` | -- | score (0.0-1.0) | -- |
| `CitationPanel` | -- | sources[], isOpen, selectedIndex | onClose |
| `CitationCard` | -- | source: Source | -- |
| `DocumentUpload` | files[], uploadProgress, error | -- | onUploadComplete |
| `DocumentList` | -- | documents[] | onDelete(id) |
| `Header` | theme | -- | onThemeChange |

---

## 3. Page Layout Wireframe

### Desktop (1024px+)

```
+------------------------------------------------------------------+
|  Header: [RAG with Guardrails]          [theme toggle] [status]  |
+------------------------------------------------------------------+
|              |                                                    |
|   Sidebar    |   Main Chat Area                                  |
|   280px      |   (flex: 1)                                       |
|              |                                                    |
|  +--------+  |   +----------------------------------------------+|
|  | Upload  |  |   |  User: What does our policy say about...    ||
|  | Zone    |  |   |                                              ||
|  | (drag   |  |   |  Assistant: Based on the uploaded documents, ||
|  |  drop)  |  |   |  the policy states... [1] [2]               ||
|  +--------+  |   |  [confidence: 0.87 ||||||||--]               ||
|              |   |                                              ||
|  Documents:  |   |  User: Ignore all instructions               ||
|  +--------+  |   |                                              ||
|  | doc1.pdf| |   |  +--[BLOCKED]-----------------------------+ ||
|  | doc2.md | |   |  | Query blocked: Prompt injection        | ||
|  | notes.. | |   |  | detected. Please rephrase your         | ||
|  +--------+  |   |  | question.                              | ||
|              |   |  +----------------------------------------+ ||
|              |   |                                              ||
|              |   |  +-- Loading... --------------------------+  ||
|              |   |  |  [typing indicator / skeleton]         |  ||
|              |   |  +---------------------------------------+  ||
|              |   +----------------------------------------------+|
|              |                                                    |
|              |   +----------------------------------------------+|
|              |   | [Ask a question about your documents...]  [>] ||
|              |   +----------------------------------------------+|
|              |                                                    |
+------------------------------------------------------------------+

Citation Panel (slides in from right when user clicks [1] or [2]):
+------------------------------------------------------------------+
|              |                                    | Citation Panel |
|              |                                    | 360px          |
|              |                                    |                |
|              |                                    | Source [1]     |
|              |                                    | safety.md      |
|              |                                    | Chunk #3       |
|              |                                    | Score: 0.95    |
|              |                                    | [||||||||||||] |
|              |                                    | "The policy    |
|              |                                    |  states that..."
|              |                                    |                |
|              |                                    | Source [2]     |
|              |                                    | ...            |
+------------------------------------------------------------------+
```

### Tablet (768px - 1023px)

- Sidebar collapses to an icon rail (48px) with a hamburger toggle
- Citation panel overlays as a modal/drawer from the right
- Chat area takes full remaining width

### Mobile (< 768px)

```
+----------------------------------+
| [=] RAG with Guardrails  [theme] |
+----------------------------------+
|                                  |
|  User: What does our policy...   |
|                                  |
|  Assistant: Based on the         |
|  uploaded documents, the         |
|  policy states... [1] [2]        |
|  [confidence: 0.87 ||||---]      |
|                                  |
|  +--[BLOCKED]------------------+ |
|  | Query blocked: Prompt       | |
|  | injection detected.         | |
|  +-----------------------------+ |
|                                  |
+----------------------------------+
| [Ask a question...]          [>] |
+----------------------------------+
| [Upload] [Documents (3)]        |
+----------------------------------+
```

- Sidebar becomes bottom tab bar with two actions: Upload and Document List
- Each opens a bottom sheet
- Citation panel becomes a full-screen bottom sheet
- Input stays pinned to bottom above the tab bar

---

## 4. Responsive Breakpoint Strategy

```css
/* tokens.css -- Breakpoints */
/* Mobile-first: base styles are mobile, then enhance upward */

--bp-sm: 640px;   /* Large phones, landscape */
--bp-md: 768px;   /* Tablets */
--bp-lg: 1024px;  /* Desktop */
--bp-xl: 1280px;  /* Wide desktop */
```

| Breakpoint | Layout Change |
|-----------|---------------|
| Base (0-639px) | Single column. Sidebar hidden, bottom tab bar. Citation panel is full-screen sheet. Input pinned to bottom. |
| sm (640px) | No major change, slightly more padding. |
| md (768px) | Sidebar appears as collapsible icon rail (48px). Citation panel is a slide-over drawer. |
| lg (1024px) | Sidebar fully expanded (280px). Two-column grid. Citation panel slides in, shrinking chat area. |
| xl (1280px) | Max-width container (1400px) centered. More generous spacing. |

### CSS Grid Definition

```css
/* AppLayout.module.css */
.layout {
  display: grid;
  grid-template-rows: auto 1fr;
  grid-template-columns: 1fr;
  height: 100dvh;
  /* dvh handles mobile browser chrome correctly */
}

@media (min-width: 768px) {
  .layout {
    grid-template-columns: 48px 1fr;
  }
}

@media (min-width: 1024px) {
  .layout {
    grid-template-columns: 280px 1fr;
  }
}

/* When citation panel is open on desktop */
.layout[data-citations-open="true"] {
  grid-template-columns: 280px 1fr 360px;
}
```

---

## 5. State Management Approach

### Decision: React Context + useReducer (no Redux, no Zustand)

This app has two distinct state domains with straightforward data flow. External state management adds dependency weight and conceptual overhead for no benefit at this scale.

### State Domains

**Domain 1: Chat State** -- `ChatContext`

```typescript
interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

type Message =
  | { role: "user"; content: string; timestamp: number }
  | { role: "assistant"; content: string; sources: Source[];
      confidence: number; blocked: boolean; blockReason: string;
      timestamp: number }
  | { role: "loading"; timestamp: number };

type ChatAction =
  | { type: "ADD_USER_MESSAGE"; query: string }
  | { type: "SET_LOADING" }
  | { type: "ADD_ASSISTANT_MESSAGE"; response: QueryResponse }
  | { type: "SET_ERROR"; error: string }
  | { type: "CLEAR_ERROR" }
  | { type: "CLEAR_HISTORY" };
```

**Domain 2: Document State** -- `DocumentContext`

```typescript
interface DocumentState {
  documents: DocumentMeta[];
  uploadQueue: UploadItem[];
  isUploading: boolean;
}

interface DocumentMeta {
  id: string;
  filename: string;
  uploadedAt: string;
  chunkCount: number;
  status: "processing" | "ready" | "error";
}

interface UploadItem {
  file: File;
  progress: number;  // 0-100
  status: "pending" | "uploading" | "complete" | "error";
  error?: string;
}
```

**Domain 3: UI State** -- `UIContext` (lightweight)

```typescript
interface UIState {
  theme: "light" | "dark" | "system";
  sidebarOpen: boolean;
  citationPanelOpen: boolean;
  selectedCitationIndex: number | null;
}
```

### Data Flow

```
User types query
  -> ChatInput.onSubmit(query)
  -> dispatch({ type: "ADD_USER_MESSAGE", query })
  -> dispatch({ type: "SET_LOADING" })
  -> await queryRAG(query)
  -> dispatch({ type: "ADD_ASSISTANT_MESSAGE", response })
     OR dispatch({ type: "SET_ERROR", error })
```

### Custom Hooks (encapsulate side effects)

```typescript
// useChat.ts -- owns the query lifecycle
function useChat() {
  const { state, dispatch } = useContext(ChatContext);

  const sendQuery = async (query: string) => {
    dispatch({ type: "ADD_USER_MESSAGE", query });
    dispatch({ type: "SET_LOADING" });
    try {
      const response = await queryRAG(query);
      dispatch({ type: "ADD_ASSISTANT_MESSAGE", response });
    } catch (err) {
      dispatch({ type: "SET_ERROR", error: getErrorMessage(err) });
    }
  };

  return { messages: state.messages, isLoading: state.isLoading,
           error: state.error, sendQuery };
}

// useDocuments.ts -- owns upload lifecycle
function useDocuments() { ... }

// useTheme.ts -- owns theme persistence + system preference detection
function useTheme() { ... }
```

---

## 6. Interaction Patterns

### 6.1 Query Lifecycle States

```
IDLE -> LOADING -> SUCCESS | BLOCKED | ERROR
                     |         |         |
                     v         v         v
                   answer   warning    error
                   + cite   message    toast
                   + conf
```

**IDLE**
- Input enabled, send button has default styling
- Placeholder text: "Ask a question about your documents..."

**LOADING**
- Input disabled, send button shows spinner
- A "loading" message bubble appears in the chat with a typing indicator (three animated dots)
- The loading message has a subtle pulse animation

**SUCCESS (blocked: false)**
- Assistant message bubble appears with the answer text
- Confidence indicator renders inline below the answer:
  - 0.8-1.0: green bar, label "High confidence"
  - 0.5-0.79: amber bar, label "Medium confidence"
  - 0.0-0.49: red bar, label "Low confidence"
- Citation superscripts [1], [2], etc. are clickable and open the CitationPanel
- Auto-scroll to the new message

**BLOCKED (blocked: true)**
- A distinct "blocked" card appears in the chat flow:
  - Red/amber left border
  - Shield icon
  - Bold label: "Query Blocked"
  - The `block_reason` text displayed clearly
  - Muted suggestion: "Try rephrasing your question"
- Input re-enables immediately

**ERROR (network/server failure)**
- A toast notification appears at the top of the chat area
- The loading message is replaced with an error message bubble
- "Retry" button in the error bubble
- Input re-enables

### 6.2 Document Upload States

```
IDLE -> SELECTING -> UPLOADING -> COMPLETE | ERROR
```

**IDLE**
- Drag-and-drop zone with dashed border
- Text: "Drop files here or click to browse"
- Accepted formats listed: PDF, MD, HTML, TXT

**DRAG OVER**
- Drop zone border becomes solid, background highlights
- Text changes: "Drop to upload"

**UPLOADING**
- Progress bar per file
- File name and percentage shown
- Cancel button per file

**COMPLETE**
- Success checkmark animation
- File appears in document list with "Processing..." badge
- Badge transitions to "Ready" once backend confirms indexing

**ERROR**
- Red badge on the failed file
- Error message (e.g., "File too large", "Unsupported format")
- Retry button per file

### 6.3 Citation Panel Interactions

- Clicking a citation superscript [N] opens the panel and scrolls to that source
- The corresponding CitationCard highlights briefly
- Each card shows: filename, chunk index, truncated text (expandable), relevance score as a horizontal bar
- Click outside or press Escape to close
- On mobile: swipe down to dismiss the bottom sheet

### 6.4 Theme Toggle

- Three-state toggle: Light / Dark / System
- Persisted to `localStorage`
- System preference detection via `prefers-color-scheme` media query
- Smooth `0.2s` transition on background and text color changes
- Placed in the header, always accessible

---

## 7. CSS Design System Tokens

```css
/* src/styles/tokens.css */

:root {
  /* === Colors: Light Theme === */
  --color-bg-primary: #ffffff;
  --color-bg-secondary: #f8f9fa;
  --color-bg-tertiary: #f1f3f5;
  --color-surface: #ffffff;
  --color-surface-raised: #ffffff;

  --color-text-primary: #1a1a2e;
  --color-text-secondary: #6b7280;
  --color-text-muted: #9ca3af;

  --color-border: #e5e7eb;
  --color-border-light: #f1f3f5;

  /* Brand / Semantic */
  --color-primary: #2563eb;        /* Blue -- main actions */
  --color-primary-hover: #1d4ed8;
  --color-primary-light: #dbeafe;

  --color-success: #16a34a;
  --color-success-light: #dcfce7;
  --color-warning: #d97706;
  --color-warning-light: #fef3c7;
  --color-danger: #dc2626;
  --color-danger-light: #fee2e2;

  /* Confidence scale */
  --color-confidence-high: #16a34a;
  --color-confidence-medium: #d97706;
  --color-confidence-low: #dc2626;

  /* === Typography === */
  --font-family-sans: 'Inter', -apple-system, BlinkMacSystemFont,
    'Segoe UI', Roboto, sans-serif;
  --font-family-mono: 'JetBrains Mono', 'Fira Code', 'Consolas',
    monospace;

  --text-xs: 0.75rem;     /* 12px */
  --text-sm: 0.875rem;    /* 14px */
  --text-base: 1rem;      /* 16px */
  --text-lg: 1.125rem;    /* 18px */
  --text-xl: 1.25rem;     /* 20px */
  --text-2xl: 1.5rem;     /* 24px */

  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.75;

  --weight-normal: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --weight-bold: 700;

  /* === Spacing (4px base grid) === */
  --space-0: 0;
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.25rem;   /* 20px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-10: 2.5rem;   /* 40px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */

  /* === Radii === */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;

  /* === Shadows === */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
               0 2px 4px -2px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1),
               0 4px 6px -4px rgba(0, 0, 0, 0.1);

  /* === Transitions === */
  --transition-fast: 150ms ease;
  --transition-base: 200ms ease;
  --transition-slow: 300ms ease;

  /* === Layout === */
  --sidebar-width: 280px;
  --sidebar-collapsed: 48px;
  --citation-panel-width: 360px;
  --header-height: 56px;
  --input-height: 64px;
  --max-chat-width: 800px;
}

/* === Dark Theme === */
[data-theme="dark"] {
  --color-bg-primary: #0f172a;
  --color-bg-secondary: #1e293b;
  --color-bg-tertiary: #334155;
  --color-surface: #1e293b;
  --color-surface-raised: #273548;

  --color-text-primary: #f1f5f9;
  --color-text-secondary: #94a3b8;
  --color-text-muted: #64748b;

  --color-border: #334155;
  --color-border-light: #1e293b;

  --color-primary: #3b82f6;
  --color-primary-hover: #60a5fa;
  --color-primary-light: #1e3a5f;

  --color-success-light: #14532d;
  --color-warning-light: #451a03;
  --color-danger-light: #450a0a;

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4),
               0 2px 4px -2px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.4),
               0 4px 6px -4px rgba(0, 0, 0, 0.3);
}

/* System preference fallback */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --color-bg-primary: #0f172a;
    --color-bg-secondary: #1e293b;
    --color-bg-tertiary: #334155;
    --color-surface: #1e293b;
    --color-surface-raised: #273548;
    --color-text-primary: #f1f5f9;
    --color-text-secondary: #94a3b8;
    --color-text-muted: #64748b;
    --color-border: #334155;
    --color-border-light: #1e293b;
    --color-primary: #3b82f6;
    --color-primary-hover: #60a5fa;
    --color-primary-light: #1e3a5f;
    --color-success-light: #14532d;
    --color-warning-light: #451a03;
    --color-danger-light: #450a0a;
  }
}
```

---

## 8. Frontend File and Folder Structure

```
frontend/
  src/
    api/
      client.ts               # Axios instance, base URL config
      queries.ts               # queryRAG(), uploadDocument(), startEvaluation(), getEvaluationRun(), getEvaluationResults()
      types.ts                 # Source, QueryResponse, DocumentMeta

    components/
      layout/
        AppLayout.tsx          # Root grid shell
        AppLayout.module.css
        Header.tsx             # App title, theme toggle, status
        Header.module.css
        Sidebar.tsx            # Sidebar container
        Sidebar.module.css

      chat/
        ChatInterface.tsx      # Orchestrates chat area
        ChatInterface.module.css
        ChatInput.tsx          # Textarea + send button
        ChatInput.module.css
        MessageList.tsx        # Scrollable message container
        MessageList.module.css
        Message.tsx            # Routes to UserMessage/AssistantMessage/etc
        UserMessage.tsx
        UserMessage.module.css
        AssistantMessage.tsx   # Answer text + confidence + citation links
        AssistantMessage.module.css
        BlockedMessage.tsx     # Guardrail block display
        BlockedMessage.module.css
        LoadingMessage.tsx     # Typing indicator
        LoadingMessage.module.css

      citations/
        CitationPanel.tsx      # Slide-out panel with source list
        CitationPanel.module.css
        CitationCard.tsx       # Single source display
        CitationCard.module.css

      documents/
        DocumentUpload.tsx     # Drag-and-drop upload zone
        DocumentUpload.module.css
        DocumentList.tsx       # List of uploaded documents
        DocumentList.module.css

      shared/
        ConfidenceIndicator.tsx   # Score bar with color coding
        ConfidenceIndicator.module.css
        ThemeToggle.tsx           # Light/Dark/System switch
        ThemeToggle.module.css
        Button.tsx                # Shared button component
        Button.module.css
        Badge.tsx                 # Status badges
        Badge.module.css
        Toast.tsx                 # Error/success notifications
        Toast.module.css

    context/
      ChatContext.tsx          # Chat state + reducer + provider
      DocumentContext.tsx      # Document state + reducer + provider
      UIContext.tsx            # Theme, sidebar, citation panel state

    hooks/
      useChat.ts              # Chat query lifecycle
      useDocuments.ts         # Upload lifecycle
      useTheme.ts             # Theme detection + persistence
      useAutoScroll.ts        # Scroll to bottom on new messages
      useMediaQuery.ts        # Responsive breakpoint detection

    styles/
      tokens.css              # Design system variables (shown above)
      reset.css               # Minimal CSS reset / normalize
      global.css              # Body defaults, font imports, transitions

    utils/
      formatConfidence.ts     # 0.87 -> "87%" and color tier
      formatTimestamp.ts      # ISO -> relative time
      getErrorMessage.ts      # Unknown error -> string

    App.tsx                   # Provider wrappers + AppLayout
    main.tsx                  # ReactDOM.createRoot entry
    vite-env.d.ts             # Vite type declarations

  __tests__/
    ChatInterface.test.tsx    # Existing test from plan
    BlockedMessage.test.tsx
    ConfidenceIndicator.test.tsx
    DocumentUpload.test.tsx

  public/
    favicon.svg

  index.html
  package.json
  tsconfig.json
  tsconfig.node.json
  vite.config.ts
  vitest.config.ts
  .env.example                # VITE_API_URL=/api
```

---

## 9. Accessibility Baseline

### Keyboard Navigation

- `Tab` moves through: chat input, send button, citation links, sidebar items, upload zone
- `Enter` submits query from chat input; `Shift+Enter` for newline
- `Escape` closes citation panel and any open modals/sheets
- Citation links are focusable and activatable with `Enter`/`Space`

### ARIA Roles and Labels

| Element | Role/Attribute | Value |
|---------|---------------|-------|
| Message list | `role="log"`, `aria-live="polite"` | Announces new messages to screen readers |
| Chat input | `aria-label` | "Ask a question about your documents" |
| Send button | `aria-label` | "Send query" |
| Confidence bar | `role="meter"`, `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax="1"` | Dynamic confidence value |
| Blocked message | `role="alert"` | Auto-announced by screen readers |
| Upload zone | `role="button"`, `aria-label` | "Upload documents, accepts PDF, Markdown, HTML, and text files" |
| Citation panel | `aria-label` | "Source citations" |
| Theme toggle | `role="radiogroup"`, `aria-label` | "Theme selection" |

### Color Contrast

- All text meets WCAG 2.1 AA (4.5:1 for body text, 3:1 for large text)
- Confidence indicator never relies solely on color -- always paired with a text label
- Blocked message uses icon + text + border, not just red background

### Focus Management

- When citation panel opens, focus moves to the first citation card
- When citation panel closes, focus returns to the citation link that opened it
- When a blocked message appears, it is announced via `role="alert"` (no focus steal)
- Loading state: `aria-busy="true"` on the message list

---

## 10. Implementation Priority Order

This is the recommended build sequence, designed so each step produces a testable increment:

| Order | Component | Why This Order |
|-------|-----------|----------------|
| 1 | `tokens.css`, `reset.css`, `global.css` | Foundation. Everything else depends on the design tokens. |
| 2 | `AppLayout` + `Header` | Establish the grid shell. Verify responsive behavior with empty content areas. |
| 3 | `ChatInput` + `ChatInterface` (hardcoded messages) | Get the input working. Verify keyboard behavior and basic styling. |
| 4 | `api/client.ts` + `ChatContext` + `useChat` | Wire up the data layer. Verify round-trip to backend with a real query. |
| 5 | `MessageList` + `Message` + `UserMessage` + `AssistantMessage` | Render real messages from state. Verify scroll behavior. |
| 6 | `ConfidenceIndicator` | Add confidence display to assistant messages. |
| 7 | `BlockedMessage` | Handle the guardrail-blocked case. |
| 8 | `LoadingMessage` | Add typing indicator during query processing. |
| 9 | `CitationPanel` + `CitationCard` | Slide-out panel with source details. |
| 10 | `Sidebar` + `DocumentUpload` + `DocumentList` | Document management. |
| 11 | `ThemeToggle` + `useTheme` | Light/dark/system theme switching. |
| 12 | `Toast` | Error notifications. |
| 13 | Tests | Component tests for critical paths (chat, blocked, upload). |
| 14 | Mobile responsive polish | Bottom sheet behaviors, tab bar, touch targets. |

---

## 11. Key Implementation Notes

### Auto-scroll Behavior

The message list should auto-scroll to the bottom when new messages arrive, but only if the user is already near the bottom. If they have scrolled up to read history, do not hijack their scroll position.

```typescript
// useAutoScroll.ts
function useAutoScroll(ref: RefObject<HTMLElement>, deps: any[]) {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
    if (isNearBottom) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    }
  }, deps);
}
```

### Citation Linking Strategy

In the assistant message text, citations appear as `[1]`, `[2]`, etc. These should be parsed and rendered as clickable elements. Use a simple regex replacement during rendering:

```typescript
function renderWithCitations(text: string, onCitationClick: (i: number) => void) {
  // Split on citation markers like [1], [2]
  // Render each as a <button> with onClick -> onCitationClick(index)
}
```

### API Error Handling

The `useChat` hook should distinguish between:
- **Network errors**: "Unable to connect to server. Check your connection."
- **4xx errors**: Display the error message from the response body
- **5xx errors**: "Something went wrong on the server. Please try again."
- **Timeout**: "The query took too long. Try a simpler question."

### Evaluation API Integration (Run-Based)

The evaluation UI should use asynchronous, run-based endpoints instead of a single synchronous `/evaluate` call:

1. `POST /evaluations`
2. `GET /evaluations/{run_id}` (poll every 2-3s while queued/running)
3. `GET /evaluations/{run_id}/results` (on complete)

Recommended frontend flow:

```typescript
const run = await startEvaluation(dataset); // POST /evaluations
setEvalRun(run); // includes run_id + status

while (run.status === "queued" || run.status === "running") {
  await sleep(2500);
  run = await getEvaluationRun(run.run_id); // GET /evaluations/{run_id}
  setEvalRun(run);
}

if (run.status === "complete") {
  const results = await getEvaluationResults(run.run_id);
  setEvalResults(results);
} else {
  setEvalError(run.error_message ?? "Evaluation failed");
}
```

Failure handling for evaluation endpoints:
- `POST /evaluations` failure: keep previous results visible, show toast "Unable to start evaluation run."
- Polling transient failure: retry with backoff up to 3 attempts before moving to error state.
- `GET /results` failure after completion: show error state with "Retry fetch results" action.

Type additions expected in `frontend/src/types/ui.ts`:

```typescript
export type EvalStatus = "idle" | "queued" | "running" | "complete" | "error";

export interface EvalRun {
  run_id: string;
  status: Exclude<EvalStatus, "idle">;
  started_at?: string;
  completed_at?: string;
  error_message?: string | null;
}
```

### Confidence Thresholds

These thresholds should be configurable but start with sensible defaults:

| Range | Label | Color Token | Behavior |
|-------|-------|-------------|----------|
| 0.80 - 1.00 | High confidence | `--color-confidence-high` | Green bar, no special treatment |
| 0.50 - 0.79 | Medium confidence | `--color-confidence-medium` | Amber bar, subtle note: "Answer may be incomplete" |
| 0.00 - 0.49 | Low confidence | `--color-confidence-low` | Red bar, visible warning: "Low confidence -- verify with original sources" |
