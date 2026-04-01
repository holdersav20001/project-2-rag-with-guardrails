# RAG with Guardrails -- UI Design Specification

> Complete visual design system for the React 18 + TypeScript + Vite frontend.
> All values reference CSS custom properties defined in `frontend/src/styles/design-tokens.css`.

---

## 1. Color Palette

### 1.1 Primary (Blue)

The primary palette drives all interactive elements -- buttons, links, focus rings, and active navigation.

| Token              | Hex       | Usage                                      |
|--------------------|-----------|-------------------------------------------|
| `primary-50`       | `#eef4ff` | Hover backgrounds, tinted areas            |
| `primary-100`      | `#d9e6ff` | Citation toggle background, avatar bg      |
| `primary-200`      | `#bcd4fe` | Light borders on interactive elements      |
| `primary-300`      | `#8ebafd` | Hover borders                              |
| `primary-400`      | `#5996fa` | Focus ring color                           |
| `primary-500`      | `#3371f7` | Main interactive accent, send button       |
| `primary-600`      | `#1d53ec` | Button hover, link color                   |
| `primary-700`      | `#1640d9` | Pressed state, logo gradient end           |
| `primary-800`      | `#1835b0` | Deep accent (rare)                         |
| `primary-900`      | `#19318b` | Darkest primary (rare)                     |

### 1.2 Secondary (Slate)

Neutral scale for text, borders, backgrounds, and surface hierarchy.

| Token               | Hex       | Usage                                  |
|---------------------|-----------|---------------------------------------|
| `secondary-50`      | `#f8fafc` | Page background, chat background       |
| `secondary-100`     | `#f1f5f9` | Input backgrounds, tertiary surfaces   |
| `secondary-200`     | `#e2e8f0` | Default borders                        |
| `secondary-300`     | `#cbd5e1` | Hover borders, dividers                |
| `secondary-400`     | `#94a3b8` | Tertiary text, placeholders            |
| `secondary-500`     | `#64748b` | Secondary text                         |
| `secondary-600`     | `#475569` | Primary text (secondary weight)        |
| `secondary-700`     | `#334155` | Strong secondary text                  |
| `secondary-800`     | `#1e293b` | Near-black text                        |
| `secondary-900`     | `#0f172a` | Primary text, headings                 |

### 1.3 Semantic -- Confidence Levels

These three colours are the most distinctive visual element of the guardrails system.

| Level    | Score range | Colour    | Hex       | Background  |
|----------|-------------|-----------|-----------|-------------|
| High     | >= 0.70     | Emerald   | `#10b981` | `#ecfdf5`   |
| Medium   | 0.40 - 0.69 | Amber     | `#f59e0b` | `#fffbeb`   |
| Low      | < 0.40      | Red       | `#ef4444` | `#fef2f2`   |

### 1.4 Semantic -- System Feedback

| Type    | Colour    | Hex       | Background |
|---------|-----------|-----------|------------|
| Success | Emerald   | `#10b981` | `#ecfdf5`  |
| Warning | Amber     | `#f59e0b` | `#fffbeb`  |
| Error   | Red       | `#ef4444` | `#fef2f2`  |
| Info    | Blue      | `#3b82f6` | `#eff6ff`  |

### 1.5 Surfaces

| Surface          | Light      | Dark       |
|------------------|-----------|------------|
| Primary bg       | `#ffffff` | `#0f172a`  |
| Secondary bg     | `#f8fafc` | `#1e293b`  |
| Tertiary bg      | `#f1f5f9` | `#334155`  |
| User message bg  | Primary-500 | Primary-500 |
| AI message bg    | `#ffffff` | `#1e293b`  |
| Blocked bg       | `#fef2f2` | `rgba(239,68,68,0.10)` |

---

## 2. Typography

### 2.1 Font Families

| Role      | Family                                  | Fallback                      |
|-----------|-----------------------------------------|-------------------------------|
| Primary   | **Inter**                               | ui-sans-serif, system-ui      |
| Monospace | **JetBrains Mono**                      | Fira Code, ui-monospace       |

Inter was chosen for its excellent legibility at small sizes, OpenType features (tabular numbers, contextual alternates), and wide weight range. JetBrains Mono is used for confidence scores, code snippets, and technical metadata.

### 2.2 Size Scale

| Token      | Size     | Px  | Usage                                     |
|------------|----------|-----|------------------------------------------|
| `text-xs`  | 0.75rem  | 12  | Badges, timestamps, metadata              |
| `text-sm`  | 0.8125rem| 13  | Secondary labels, nav items               |
| `text-base`| 0.875rem | 14  | Body text, message content                |
| `text-md`  | 1rem     | 16  | Header title, emphasized body             |
| `text-lg`  | 1.125rem | 18  | Section headers                           |
| `text-xl`  | 1.25rem  | 20  | Empty state titles                        |
| `text-2xl` | 1.5rem   | 24  | Page titles (upload view)                 |
| `text-3xl` | 1.875rem | 30  | Reserved for hero/marketing               |

Base body is 14px rather than 16px because this is a dense information UI. Chat message bubbles and the upload page title use 14px and 24px respectively.

### 2.3 Weights

| Token         | Value | Usage                                      |
|---------------|-------|--------------------------------------------|
| `regular`     | 400   | Body text, descriptions                     |
| `medium`      | 500   | Nav items, labels, secondary emphasis       |
| `semibold`    | 600   | Filenames, badge text, section titles       |
| `bold`        | 700   | Page titles, logo, format badge labels      |

### 2.4 Line Heights

| Token      | Value | Usage                         |
|------------|-------|-------------------------------|
| `tight`    | 1.25  | Headings, badges              |
| `normal`   | 1.5   | Default body text             |
| `relaxed`  | 1.625 | Message bubbles, source text  |

---

## 3. Spacing System

4px base grid. Every margin, padding, and gap is a multiple of 4.

| Token     | Value   | Px  | Common usage                              |
|-----------|---------|-----|------------------------------------------|
| `space-0-5` | 0.125rem | 2  | Tight badge padding                     |
| `space-1`   | 0.25rem  | 4  | Icon gaps, minimal spacing              |
| `space-1-5` | 0.375rem | 6  | Nav item icon gap                       |
| `space-2`   | 0.5rem   | 8  | Inline gaps, small padding              |
| `space-3`   | 0.75rem  | 12 | Bubble padding, card padding            |
| `space-4`   | 1rem     | 16 | Section padding, message gaps           |
| `space-5`   | 1.25rem  | 20 | Rare intermediate                       |
| `space-6`   | 1.5rem   | 24 | Header horizontal padding               |
| `space-8`   | 2rem     | 32 | Empty state padding, upload page top    |
| `space-10`  | 2.5rem   | 40 | Large section gaps                      |
| `space-12`  | 3rem     | 48 | Drop zone vertical padding              |
| `space-16`  | 4rem     | 64 | Reserved for very large gaps            |

---

## 4. Component Visual Specifications

### 4.1 Header / Navigation

```
+------------------------------------------------------------------+
|  [Logo] RAG Guardrails    [ Chat | Documents ]     [theme-toggle] |
+------------------------------------------------------------------+
```

- **Height**: 56px (`--header-height`)
- **Background**: `--color-bg-primary` (white / dark slate)
- **Bottom border**: 1px solid `--color-border-default`
- **Logo**: 28x28px rounded rectangle with a gradient from primary-500 to primary-700, white bold letter "R" centred
- **Product name**: 16px semibold, primary text colour, -0.01em letter-spacing
- **Tab group**: pill-shaped container with `--color-bg-tertiary` background, 8px border-radius. Each tab is 13px medium weight. Active tab has white background, xs shadow, primary text colour. Inactive tabs are secondary text with hover brightening.
- **Theme toggle**: 36x36px button with 6px radius, 1px border. Sun icon (light) / moon icon (dark). On hover: subtle background fill.

### 4.2 Chat Interface

**Layout**: Full remaining height below header. Vertical flex: scrollable message area (flex: 1) + fixed input bar at bottom.

**Message area**: `--color-bg-chat` background (slate-50 / dark slate-900). Messages centred in a max-width: 768px column. 24px top/bottom padding. 16px gap between messages.

**User message bubble**:
- Background: `--color-primary-500` (vivid blue)
- Text: white, 14px regular, line-height 1.625
- Border radius: 12px on three corners, 4px bottom-right (tail)
- Max width: 75% of column
- Right-aligned (flex-direction: row-reverse on the message row)

**AI message bubble**:
- Background: white (dark: slate-800)
- Text: primary text colour, 14px regular, line-height 1.625
- Border: 1px solid `--color-border-default`
- Border radius: 12px on three corners, 4px bottom-left (tail)
- Shadow: xs
- Max width: 75%
- Left-aligned

**Avatar circles**: 32x32px, fully rounded. User avatar: primary-500 bg with white initials. AI avatar: linear gradient primary-100 to primary-200, 1px primary-200 border, primary-700 icon.

**AI message footer** (below bubble, left-padded 4px):
- Confidence badge: pill, monospace, coloured by level (see section 4.4)
- Citations toggle: small pill button "3 sources" with book icon, primary-50 bg, primary-200 border, primary-600 text

**Input bar**:
- Container: white bg, top border 1px solid default
- Inner wrapper: centred max-width 768px, flex row, secondary-bg, 1px border, 12px border-radius, 8px vertical padding + 12px horizontal
- Textarea: no border, transparent bg, auto-grows to 8 lines max, 14px
- Focus state: border becomes primary-400, focus ring shadow `0 0 0 3px rgba(51,113,247,0.25)`
- Send button: 36x36px, primary-500 bg, white arrow-up icon, 8px radius. Hover: scale(1.05) + primary-600. Disabled: 40% opacity.

**Empty state** (no messages yet):
- Centred vertically in message area
- 64x64px rounded icon container (gradient primary-50 to primary-100, primary-200 border)
- Title: "Ask anything about your documents" -- 20px semibold
- Description: "Upload documents to your knowledge base, then ask questions. Answers will include citations and confidence scores." -- 14px secondary text, max-width 384px
- 3-4 suggestion chips: "What does our policy say about...", "Summarize the key findings in...", "Compare section 3 and section 7 of..." -- 13px, secondary text, white bg, default border, 8px radius. Hover: primary-600 text, primary-300 border, primary-50 bg.

**Typing indicator**: three grey dots (6px each) bouncing in sequence inside an AI-shaped bubble. Dots are tertiary text colour. Staggered 160ms delay per dot.

### 4.3 Citation Panel

```
+------------------------------+
|  Sources (3)            [X]  |
+------------------------------+
|                              |
|  +------------------------+  |
|  | report.pdf   chunk #2  |  |
|  | "The quarterly results  |  |
|  | showed a 15% increase   |  |
|  | in..."                  |  |
|  | Relevance  [=======] 92%| |
|  +------------------------+  |
|                              |
|  +------------------------+  |
|  | policy.md    chunk #5  |  |
|  | "Data retention must    |  |
|  | comply with..."         |  |
|  | Relevance  [=====] 74%  | |
|  +------------------------+  |
|                              |
+------------------------------+
```

- **Width**: 352px on desktop, full width on mobile (stacks below chat)
- **Background**: white / dark slate-900
- **Left border**: 1px solid default
- **Animation**: slides in from right, 350ms, ease-out
- **Header**: "Sources" label (13px semibold) + count badge (pill, primary-50 bg, primary-600 text) + close button (28x28, tertiary text)

**Source card**:
- Background: secondary-50 (dark: secondary-100)
- Border: 1px solid default, 8px radius
- Padding: 12px
- Hover: primary-300 border, primary-50 bg, sm shadow
- **Filename**: 13px semibold, with a small document icon (matching file-type colour)
- **Chunk badge**: "chunk #2", xs text, tertiary colour, tertiary bg, pill
- **Text excerpt**: 12px secondary text, 3-line clamp with ellipsis, line-height 1.625
- **Relevance bar**: 4px track (tertiary bg), coloured fill (high=emerald, medium=amber, low=red), width proportional to score. Label "Relevance" left, percentage right in monospace semibold, coloured by level.

### 4.4 Confidence Indicator

Two variants are provided. Use the **badge** variant inline in message footers and the **bar** variant in detail views.

**Badge variant** (default):
- Pill shape (9999px radius)
- 4px vertical padding, 8px horizontal
- 6px coloured dot + score as percentage in monospace semibold 12px
- Background and text colour determined by level:
  - High (>=70%): emerald-500 text on emerald-50 bg
  - Medium (40-69%): amber-500 text on amber-50 bg
  - Low (<40%): red-500 text on red-50 bg
- Entry animation: scale-in with spring easing

**Bar variant**:
- 6px track height, full-width, tertiary bg, fully rounded
- Coloured fill with a subtle gradient (lighter at the left end)
- Percentage label right of the bar in matching colour
- Fill width transition: 350ms ease-out (animates on mount)

### 4.5 Blocked Message

Visually distinct from normal AI responses to clearly signal a guardrail activation.

- **Icon**: 32px red-tinted circle (error-50 bg, error border at 20% opacity) with a shield-alert icon in error-500
- **Bubble**: Same shape as AI bubble (rounded with bottom-left tail), but:
  - Background: `--color-bg-blocked` (red-50 / dark: rgba red 10%)
  - Border: 1px solid rgba(239,68,68,0.2)
- **Label inside bubble**: "BLOCKED" in 12px uppercase semibold, error-500, with shield icon, 0.05em letter-spacing
- **Reason text**: 14px primary text colour, relaxed line-height
- **Detail box** (optional, for technical reason): 12px monospace, secondary text, very light red bg, 6px radius, 8px/12px padding
- **Entry animation**: fade-up, then a subtle horizontal shake (4px amplitude, 500ms) with 150ms delay

### 4.6 Document Upload

**Page layout**: centred column, max-width 768px, 32px top padding.

**Title area**: "Knowledge Base" in 24px bold, "Upload documents to build your searchable knowledge base" in 14px secondary text.

**Drop zone**:
- 2px dashed border, default colour, 12px radius
- Secondary bg, 48px vertical padding
- Centre: 48px icon container (primary-100 bg, primary-500 upload-cloud icon) + "Drag and drop files here, or click to browse" (14px, "click to browse" in primary-600 semibold)
- **Active (dragging over)**: solid border primary-400, primary-50 bg, focus ring shadow
- **Error state**: error-500 border, error-50 bg

**Format badges** (below drop zone):
- Row of pills: PDF (red), MD (purple), HTML (orange), TXT (blue)
- Each: 12px monospace semibold uppercase, tinted bg + border matching colour

**File list** (after upload):
- Each row: 36px file-type icon (coloured square, ext label) + filename (13px semibold) + file size (12px tertiary) + progress bar or status icon
- Progress bar: 4px, primary-500 fill, tertiary track. On complete: fill turns success-500. On error: fill turns error-500.
- Status icons: checkmark circle (success), X circle (error), spinning circle (loading)

**Empty state** (no files uploaded):
- 48px muted folder icon, "No documents uploaded yet" in secondary text

---

## 5. Icon Recommendations

Use **Lucide React** (`lucide-react`) for all icons. It is MIT-licensed, tree-shakable, and consistent with the design language. Key icons:

| Usage                | Icon name           |
|----------------------|---------------------|
| Send message         | `ArrowUp`           |
| AI avatar            | `Sparkles`          |
| User avatar          | `User`              |
| Chat nav             | `MessageSquare`     |
| Documents nav        | `FolderOpen`        |
| Upload cloud         | `UploadCloud`       |
| File (generic)       | `FileText`          |
| PDF file             | `FileType`          |
| Close panel          | `X`                 |
| Citations/sources    | `BookOpen`          |
| Confidence high      | `ShieldCheck`       |
| Confidence medium    | `ShieldAlert`       |
| Confidence low       | `ShieldX`           |
| Blocked              | `ShieldBan`         |
| Theme: light         | `Sun`               |
| Theme: dark          | `Moon`              |
| Checkmark (success)  | `CheckCircle2`      |
| Error                | `XCircle`           |
| Loading              | `Loader2`           |
| Chunk indicator      | `Hash`              |
| Relevance            | `BarChart3`         |
| Empty state (chat)   | `MessagesSquare`    |
| Empty state (docs)   | `FolderSearch`      |

Default icon size: 16px for inline, 20px for navigation, 24px for empty states, 28px for the upload cloud.

---

## 6. Animation & Transition Specifications

All animations respect `prefers-reduced-motion: reduce` by collapsing to near-zero duration.

| Element                 | Animation         | Duration | Easing                     | Trigger          |
|-------------------------|-------------------|----------|----------------------------|------------------|
| New chat message        | fade-up           | 200ms    | ease-out (0.16,1,0.3,1)   | On mount         |
| Citation panel open     | slide-in-right    | 350ms    | ease-out                   | Toggle open      |
| Citation panel close    | slide-out-right   | 350ms    | ease-out                   | Toggle close     |
| Confidence badge        | scale-in          | 200ms    | spring (0.34,1.56,0.64,1) | On mount         |
| Blocked message         | shake             | 500ms    | ease-in-out, 150ms delay   | After fade-up    |
| Typing indicator dots   | bounce-dot        | 1400ms   | ease-in-out, looping       | While loading    |
| Skeleton loaders        | pulse             | 2000ms   | ease-in-out, looping       | While loading    |
| Upload progress         | width transition  | 200ms    | ease-out                   | Progress update  |
| Send button hover       | scale             | 100ms    | ease-out                   | Mouse enter      |
| Source card hover       | border + shadow   | 100ms    | ease-out                   | Mouse enter      |
| Confidence bar fill     | width             | 350ms    | ease-out                   | On mount         |
| All focus rings         | box-shadow        | 100ms    | ease-out                   | Focus-visible    |
| Theme toggle content    | opacity + rotate  | 200ms    | ease-in-out                | Theme change     |

---

## 7. Dark Mode Color Mapping

Dark mode inverts the luminance scale while preserving hue relationships. Surfaces become dark slate, text becomes light. Accent colours shift brighter to maintain contrast against dark backgrounds.

Complete token overrides are in `design-tokens.css` under `[data-theme="dark"]`. The key principles:

1. **Surfaces**: white -> slate-900 (#0f172a), slate-50 -> slate-800 (#1e293b), slate-100 -> slate-700 (#334155)
2. **Text**: slate-900 -> slate-100, slate-600 -> slate-400, slate-400 -> slate-600
3. **Borders**: slate-200 -> slate-700, slate-300 -> slate-600
4. **Primary accent**: shifts from 500 to 400 (brighter blue on dark bg)
5. **Semantic colours**: shifted one stop lighter (emerald-500 -> emerald-400, etc.)
6. **Semantic backgrounds**: semi-transparent overlays instead of solid tints (e.g. `rgba(16,185,129,0.12)` instead of `#ecfdf5`)
7. **Shadows**: increased opacity to remain visible on dark surfaces

The toggle mechanism: clicking the theme button sets `data-theme="dark"` on `<html>` and persists to `localStorage`. On first load, if no preference is stored, the system defers to `prefers-color-scheme`.

---

## 8. Loading & Skeleton States

### 8.1 Chat Loading (AI is generating)

- Typing indicator replaces the next AI message position
- Three dots bounce in an AI-styled bubble
- Duration: visible until the streaming response starts

### 8.2 Chat Skeleton (initial page load)

- 3 skeleton message rows: alternating left/right alignment
- Each: skeleton avatar circle (32px) + skeleton bubble (variable width, 4.5rem height)
- Pulse animation, staggered 100ms per row

### 8.3 Citation Panel Skeleton

- 3 skeleton cards stacked vertically
- Each: 6rem height, 8px radius, pulse animation

### 8.4 Upload Progress

- Per-file progress bar (4px height, primary fill, smooth width transition)
- Indeterminate variant for processing phase (40% width bar slides left-to-right endlessly)
- Completion: fill colour transitions from primary to success-500

### 8.5 Empty States

| View      | Visual                                                              |
|-----------|---------------------------------------------------------------------|
| Chat      | Gradient icon + title + description + suggestion chips              |
| Documents | Muted folder-search icon + "No documents uploaded yet" + "Upload your first document to get started" |

---

## 9. Accessibility

- **Colour contrast**: all text/background combinations meet WCAG AA (4.5:1 for body text, 3:1 for large text). The confidence colours were specifically chosen from Tailwind's palette to pass on both light and dark backgrounds.
- **Focus indicators**: 2px solid primary-400 outline with 2px offset on `:focus-visible`. Additional focus ring shadow on the input wrapper.
- **Keyboard navigation**: all interactive elements are reachable via Tab. Enter/Space activates buttons. Escape closes the citation panel. Arrow keys navigate suggestion chips.
- **Screen reader support**: all icons paired with `aria-label` or `sr-only` text. Confidence scores announced as "Confidence: 87 percent, high". Blocked messages announced as alerts (`role="alert"`).
- **Touch targets**: minimum 36x36px for all interactive elements (exceeds the 44px recommendation on larger buttons like Send).
- **Reduced motion**: `prefers-reduced-motion: reduce` media query collapses all animation durations to near-zero.

---

## 10. File Structure

```
frontend/src/
  styles/
    design-tokens.css   -- All CSS custom properties (light + dark)
    reset.css           -- Minimal CSS reset
    animations.css      -- Keyframes and animation utility classes
    components.css      -- All component styles
    index.css           -- Import aggregator (entry point)
  types/
    ui.ts               -- Shared TypeScript types and helpers
  components/
    Header.tsx          -- (to implement)
    ChatInterface.tsx   -- (to implement)
    MessageBubble.tsx   -- (to implement)
    CitationPanel.tsx   -- (to implement)
    SourceCard.tsx      -- (to implement)
    ConfidenceBadge.tsx -- (to implement)
    BlockedMessage.tsx  -- (to implement)
    DocumentUpload.tsx  -- (to implement)
    TypingIndicator.tsx -- (to implement)
    SkeletonLoader.tsx  -- (to implement)
    EmptyState.tsx      -- (to implement)
```

---

## 11. Implementation Notes

1. **Import the design system** by adding `import './styles/index.css'` in `main.tsx`.
2. **Use BEM-style class names** as defined in `components.css`. If you adopt CSS Modules later, the class names map directly.
3. **Confidence helper**: use `getConfidenceLevel(score)` from `types/ui.ts` to derive the `--high`, `--medium`, or `--low` modifier class.
4. **Score formatting**: use `formatScore(score)` for display (e.g., `0.87` -> `"87%"`).
5. **Responsive**: the system is mobile-first. The citation panel stacks below chat on screens narrower than 768px. The header collapses the product name on mobile.
6. **Font loading**: add Inter and JetBrains Mono via Google Fonts or self-host. Add the `<link>` tags in `index.html` before the stylesheet.
