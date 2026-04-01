# Evaluation Dashboard -- UI Design Specification

> Visual design specification for the "Evaluation" tab added to the RAG with Guardrails interface.
> All values reference CSS custom properties from `frontend/src/styles/design-tokens.css`.
> BEM class naming matches existing `components.css` conventions.

---

## 1. Overview

The Evaluation tab is the third navigation item in the header pill bar (Chat | Documents | **Evaluation**). It occupies the full `app-main` area and scrolls vertically. The view has four distinct states: **empty**, **loading**, **error**, and **results**.

### Layout Structure

```
+------------------------------------------------------------------+
| HEADER  [Chat] [Documents] [Evaluation]                          |
+------------------------------------------------------------------+
| .eval                                                            |
|   .eval__controls          -- upload + run bar (always visible)  |
|   .eval__overview          -- 4 metric cards + overall score     |
|   .eval__breakdown         -- per-question table                 |
+------------------------------------------------------------------+
```

The `.eval` container uses `max-width: var(--max-content-width)` (1280px) centered with auto margins, matching the content constraint pattern used throughout the application.

---

## 2. Navigation Integration

Add a third tab to the existing `.header__nav` pill bar.

```html
<nav class="header__nav">
  <button class="header__nav-item" ...>Chat</button>
  <button class="header__nav-item" ...>Documents</button>
  <button class="header__nav-item header__nav-item--active" ...>
    <!-- Beaker / flask icon, 16x16 -->
    <svg ...>...</svg>
    Evaluation
  </button>
</nav>
```

The `ViewTab` union type in `types/ui.ts` must be extended:

```ts
export type ViewTab = 'chat' | 'documents' | 'evaluation';
```

No new tokens are needed. The existing `header__nav-item` and `header__nav-item--active` classes handle all visual states.

---

## 3. Evaluation Controls Section

This section is always visible at the top of the eval view regardless of state. It contains the dataset upload area, run button, and status line.

Run-based API integration:
- On click "Run Evaluation": `POST /evaluations` with dataset payload/file, receive `run_id`
- While running: poll `GET /evaluations/{run_id}` every 2-3s for status
- On completion: fetch `GET /evaluations/{run_id}/results` and render overview + table

### 3.1 HTML Structure

```html
<section class="eval__controls">
  <div class="eval__controls-row">

    <!-- File upload -->
    <div class="eval__upload">
      <label class="eval__upload-target" for="eval-dataset-input">
        <svg class="eval__upload-icon" ...><!-- upload-cloud icon 20x20 --></svg>
        <span class="eval__upload-label">
          <strong>Upload test dataset</strong>
          <span class="eval__upload-hint">JSON with questions + ground_truths</span>
        </span>
      </label>
      <input
        id="eval-dataset-input"
        class="eval__upload-input"
        type="file"
        accept=".json"
      />
      <!-- Shown after file selected -->
      <div class="eval__upload-file">
        <span class="eval__upload-file-name">eval_dataset.json</span>
        <span class="eval__upload-file-meta">12 questions</span>
        <button class="eval__upload-remove" aria-label="Remove file">
          <svg ...><!-- x icon 14x14 --></svg>
        </button>
      </div>
    </div>

    <!-- Run button -->
    <button class="eval__run-btn" disabled>
      <svg ...><!-- play icon 16x16 --></svg>
      Run Evaluation
    </button>

    <!-- Loading variant -->
    <button class="eval__run-btn eval__run-btn--loading" disabled>
      <span class="eval__run-spinner"></span>
      Evaluating...
    </button>

  </div>

  <!-- Status line (below the row) -->
  <div class="eval__status">
    <span class="eval__status-dot eval__status-dot--idle"></span>
    <span class="eval__status-text">No evaluation run yet</span>
  </div>

  <!-- Status variants -->
  <div class="eval__status">
    <span class="eval__status-dot eval__status-dot--running"></span>
    <span class="eval__status-text">
      Run #ev_20260331_001 evaluating 12 questions... <span class="eval__status-elapsed">00:23</span>
    </span>
  </div>

  <div class="eval__status">
    <span class="eval__status-dot eval__status-dot--complete"></span>
    <span class="eval__status-text">
      Last run: <time class="eval__status-time">Mar 31, 2026 at 2:14 PM</time>
    </span>
  </div>

  <div class="eval__status">
    <span class="eval__status-dot eval__status-dot--error"></span>
    <span class="eval__status-text eval__status-text--error">
      Evaluation failed for run #ev_20260331_001: server returned 500
    </span>
  </div>
</section>
```

### 3.2 Visual Specifications

| Element | Property | Value |
|---|---|---|
| `.eval__controls` | background | `var(--color-bg-primary)` |
| | border | `1px solid var(--color-border-default)` |
| | border-radius | `var(--radius-xl)` (12px) |
| | padding | `var(--space-5)` (20px) |
| | box-shadow | `var(--shadow-sm)` |
| `.eval__upload-target` | background | `var(--color-bg-secondary)` |
| | border | `1px dashed var(--color-border-default)` |
| | border-radius | `var(--radius-lg)` (8px) |
| | padding | `var(--space-3) var(--space-4)` |
| | hover border-color | `var(--color-primary-400)` |
| | hover background | `var(--color-primary-50)` |
| `.eval__run-btn` | background | `var(--color-primary-500)` |
| | color | white |
| | font-size | `var(--text-sm)` (13px) |
| | font-weight | `var(--weight-semibold)` (600) |
| | padding | `var(--space-2) var(--space-5)` |
| | border-radius | `var(--radius-lg)` (8px) |
| | height | 40px |
| `.eval__status-dot` | width/height | 8px |
| | border-radius | `var(--radius-full)` |
| `.eval__status-dot--idle` | background | `var(--color-secondary-400)` |
| `.eval__status-dot--running` | background | `var(--color-primary-500)` + pulse animation |
| `.eval__status-dot--complete` | background | `var(--color-confidence-high)` |
| `.eval__status-dot--error` | background | `var(--color-error-500)` |

---

## 4. Evaluation Overview Section (Metric Cards)

A row of four metric cards with an overall score badge anchored to the right. The cards are evenly distributed via CSS Grid.

### 4.1 HTML Structure

```html
<section class="eval__overview">

  <!-- Overall score pill -->
  <div class="eval__overall">
    <span class="eval__overall-label">Overall Score</span>
    <span class="eval__overall-value eval__overall-value--high">82%</span>
  </div>

  <!-- Metric cards grid -->
  <div class="eval__metrics">

    <article class="metric-card metric-card--high">
      <div class="metric-card__header">
        <h3 class="metric-card__name">Faithfulness</h3>
        <span class="metric-card__badge metric-card__badge--high">High</span>
      </div>
      <div class="metric-card__body">
        <div class="metric-card__gauge">
          <svg class="metric-card__ring" viewBox="0 0 80 80" aria-hidden="true">
            <circle class="metric-card__ring-track" cx="40" cy="40" r="34" />
            <circle class="metric-card__ring-fill metric-card__ring-fill--high"
                    cx="40" cy="40" r="34"
                    stroke-dasharray="213.6"
                    stroke-dashoffset="38.4" />
          </svg>
          <span class="metric-card__score">82%</span>
        </div>
        <p class="metric-card__description">
          Are generated claims supported by retrieved context?
        </p>
      </div>
    </article>

    <article class="metric-card metric-card--high">
      <div class="metric-card__header">
        <h3 class="metric-card__name">Answer Relevancy</h3>
        <span class="metric-card__badge metric-card__badge--high">High</span>
      </div>
      <div class="metric-card__body">
        <div class="metric-card__gauge">
          <svg class="metric-card__ring" viewBox="0 0 80 80" aria-hidden="true">
            <circle class="metric-card__ring-track" cx="40" cy="40" r="34" />
            <circle class="metric-card__ring-fill metric-card__ring-fill--high"
                    cx="40" cy="40" r="34"
                    stroke-dasharray="213.6"
                    stroke-dashoffset="42.7" />
          </svg>
          <span class="metric-card__score">80%</span>
        </div>
        <p class="metric-card__description">
          Does the answer address the question asked?
        </p>
      </div>
    </article>

    <article class="metric-card metric-card--medium">
      <div class="metric-card__header">
        <h3 class="metric-card__name">Context Precision</h3>
        <span class="metric-card__badge metric-card__badge--medium">Medium</span>
      </div>
      <div class="metric-card__body">
        <div class="metric-card__gauge">
          <svg class="metric-card__ring" viewBox="0 0 80 80" aria-hidden="true">
            <circle class="metric-card__ring-track" cx="40" cy="40" r="34" />
            <circle class="metric-card__ring-fill metric-card__ring-fill--medium"
                    cx="40" cy="40" r="34"
                    stroke-dasharray="213.6"
                    stroke-dashoffset="85.4" />
          </svg>
          <span class="metric-card__score">60%</span>
        </div>
        <p class="metric-card__description">
          Are the retrieved chunks relevant to the question?
        </p>
      </div>
    </article>

    <article class="metric-card metric-card--high">
      <div class="metric-card__header">
        <h3 class="metric-card__name">Context Recall</h3>
        <span class="metric-card__badge metric-card__badge--high">High</span>
      </div>
      <div class="metric-card__body">
        <div class="metric-card__gauge">
          <svg class="metric-card__ring" viewBox="0 0 80 80" aria-hidden="true">
            <circle class="metric-card__ring-track" cx="40" cy="40" r="34" />
            <circle class="metric-card__ring-fill metric-card__ring-fill--high"
                    cx="40" cy="40" r="34"
                    stroke-dasharray="213.6"
                    stroke-dashoffset="21.4" />
          </svg>
          <span class="metric-card__score">90%</span>
        </div>
        <p class="metric-card__description">
          Did we retrieve all needed information?
        </p>
      </div>
    </article>

  </div>
</section>
```

### 4.2 Radial Gauge Calculations

The ring uses an SVG circle with `r="34"`, giving circumference `2 * PI * 34 = 213.628`. The `stroke-dashoffset` is calculated as:

```
offset = circumference * (1 - score)
```

For example, a score of 0.82: `213.6 * (1 - 0.82) = 38.4`.

The ring is rotated -90deg via CSS transform so the fill starts at 12 o'clock.

### 4.3 Visual Specifications

| Element | Property | Value |
|---|---|---|
| `.eval__metrics` | display | grid |
| | grid-template-columns | `repeat(4, 1fr)` |
| | gap | `var(--space-4)` (16px) |
| `.metric-card` | background | `var(--color-bg-primary)` |
| | border | `1px solid var(--color-border-default)` |
| | border-radius | `var(--radius-xl)` (12px) |
| | padding | `var(--space-5)` (20px) |
| | box-shadow | `var(--shadow-sm)` |
| | transition | `all var(--duration-fast) var(--ease-out)` |
| | hover box-shadow | `var(--shadow-md)` |
| | hover transform | `translateY(-2px)` |
| `.metric-card__name` | font-size | `var(--text-sm)` (13px) |
| | font-weight | `var(--weight-semibold)` |
| | color | `var(--color-text-primary)` |
| `.metric-card__score` | font-family | `var(--font-mono)` |
| | font-size | `var(--text-xl)` (20px) |
| | font-weight | `var(--weight-bold)` |
| `.metric-card__ring` | width/height | 80px |
| | transform | `rotate(-90deg)` |
| `.metric-card__ring-track` | stroke | `var(--color-bg-tertiary)` |
| | stroke-width | 6 |
| | fill | none |
| `.metric-card__ring-fill--high` | stroke | `var(--color-confidence-high)` |
| `.metric-card__ring-fill--medium` | stroke | `var(--color-confidence-medium)` |
| `.metric-card__ring-fill--low` | stroke | `var(--color-confidence-low)` |
| `.metric-card__badge--high` | color | `var(--color-confidence-high)` |
| | background | `var(--color-confidence-high-bg)` |
| `.metric-card__badge--medium` | color | `var(--color-confidence-medium)` |
| | background | `var(--color-confidence-medium-bg)` |
| `.metric-card__badge--low` | color | `var(--color-confidence-low)` |
| | background | `var(--color-confidence-low-bg)` |
| `.eval__overall` | background | `var(--color-bg-primary)` |
| | border | `1px solid var(--color-border-default)` |
| | border-radius | `var(--radius-xl)` |
| | padding | `var(--space-4) var(--space-6)` |
| | text-align | center |
| `.eval__overall-value` | font-family | `var(--font-mono)` |
| | font-size | `var(--text-3xl)` (30px) |
| | font-weight | `var(--weight-bold)` |

---

## 5. Per-Question Breakdown Table

### 5.1 HTML Structure

```html
<section class="eval__breakdown">
  <div class="eval__breakdown-header">
    <h2 class="eval__breakdown-title">Per-Question Results</h2>
    <span class="eval__breakdown-count">12 questions</span>
  </div>

  <div class="eval__table-wrapper">
    <table class="eval-table">
      <thead class="eval-table__head">
        <tr class="eval-table__row">
          <th class="eval-table__th eval-table__th--question">#</th>
          <th class="eval-table__th eval-table__th--question">Question</th>
          <th class="eval-table__th eval-table__th--answer">Answer</th>
          <th class="eval-table__th eval-table__th--score">Faith.</th>
          <th class="eval-table__th eval-table__th--score">Relev.</th>
          <th class="eval-table__th eval-table__th--score">Prec.</th>
          <th class="eval-table__th eval-table__th--score">Recall</th>
        </tr>
      </thead>
      <tbody class="eval-table__body">

        <!-- Collapsed row -->
        <tr class="eval-table__row eval-table__row--clickable" aria-expanded="false">
          <td class="eval-table__td eval-table__td--index">
            <span class="eval-table__index">1</span>
          </td>
          <td class="eval-table__td eval-table__td--question">
            What is retrieval-augmented generation?
          </td>
          <td class="eval-table__td eval-table__td--answer">
            <span class="eval-table__truncated">
              Retrieval-augmented generation (RAG) is a technique that...
            </span>
          </td>
          <td class="eval-table__td eval-table__td--score">
            <span class="eval-table__score eval-table__score--high">92%</span>
          </td>
          <td class="eval-table__td eval-table__td--score">
            <span class="eval-table__score eval-table__score--high">88%</span>
          </td>
          <td class="eval-table__td eval-table__td--score">
            <span class="eval-table__score eval-table__score--medium">65%</span>
          </td>
          <td class="eval-table__td eval-table__td--score">
            <span class="eval-table__score eval-table__score--high">95%</span>
          </td>
        </tr>

        <!-- Expanded detail row (shown when parent is aria-expanded="true") -->
        <tr class="eval-table__row eval-table__row--detail">
          <td class="eval-table__td" colspan="7">
            <div class="eval-detail">
              <div class="eval-detail__section">
                <h4 class="eval-detail__label">Full Answer</h4>
                <p class="eval-detail__text">
                  Retrieval-augmented generation (RAG) is a technique that
                  combines a language model with external knowledge retrieval
                  to produce more accurate, grounded responses...
                </p>
              </div>
              <div class="eval-detail__section">
                <h4 class="eval-detail__label">Ground Truth</h4>
                <p class="eval-detail__text eval-detail__text--ground-truth">
                  RAG is an AI framework that retrieves relevant documents
                  from an external knowledge base and uses them to augment
                  the prompt sent to a large language model...
                </p>
              </div>
              <div class="eval-detail__section">
                <h4 class="eval-detail__label">Retrieved Contexts</h4>
                <div class="eval-detail__contexts">
                  <div class="eval-detail__context">
                    <span class="eval-detail__context-index">1</span>
                    <p class="eval-detail__context-text">
                      RAG combines information retrieval with text generation...
                    </p>
                  </div>
                  <div class="eval-detail__context">
                    <span class="eval-detail__context-index">2</span>
                    <p class="eval-detail__context-text">
                      The retrieval component searches a vector store for
                      relevant document chunks...
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </td>
        </tr>

      </tbody>
    </table>
  </div>
</section>
```

### 5.2 Visual Specifications

| Element | Property | Value |
|---|---|---|
| `.eval__table-wrapper` | overflow-x | auto |
| | border | `1px solid var(--color-border-default)` |
| | border-radius | `var(--radius-xl)` |
| | background | `var(--color-bg-primary)` |
| `.eval-table` | width | 100% |
| | border-collapse | collapse |
| | font-size | `var(--text-sm)` (13px) |
| `.eval-table__th` | padding | `var(--space-3) var(--space-4)` |
| | font-weight | `var(--weight-semibold)` |
| | color | `var(--color-text-secondary)` |
| | text-align | left |
| | background | `var(--color-bg-secondary)` |
| | border-bottom | `1px solid var(--color-border-default)` |
| | white-space | nowrap |
| `.eval-table__th--score` | text-align | center |
| | width | 80px |
| `.eval-table__td` | padding | `var(--space-3) var(--space-4)` |
| | border-bottom | `1px solid var(--color-border-default)` |
| | vertical-align | middle |
| `.eval-table__row--clickable:hover` | background | `var(--color-bg-secondary)` |
| | cursor | pointer |
| `.eval-table__score` | font-family | `var(--font-mono)` |
| | font-weight | `var(--weight-semibold)` |
| | font-size | `var(--text-sm)` |
| | display | inline-flex |
| | padding | `var(--space-0-5) var(--space-2)` |
| | border-radius | `var(--radius-md)` |
| `.eval-table__score--high` | color | `var(--color-confidence-high)` |
| | background | `var(--color-confidence-high-bg)` |
| `.eval-table__score--medium` | color | `var(--color-confidence-medium)` |
| | background | `var(--color-confidence-medium-bg)` |
| `.eval-table__score--low` | color | `var(--color-confidence-low)` |
| | background | `var(--color-confidence-low-bg)` |
| `.eval-table__truncated` | display | `-webkit-box` |
| | `-webkit-line-clamp` | 1 |
| | max-width | 280px |
| | overflow | hidden |
| `.eval-detail` | padding | `var(--space-4) var(--space-6)` |
| | background | `var(--color-bg-secondary)` |
| | border-radius | `var(--radius-lg)` |
| `.eval-detail__label` | font-size | `var(--text-xs)` |
| | font-weight | `var(--weight-semibold)` |
| | text-transform | uppercase |
| | letter-spacing | 0.05em |
| | color | `var(--color-text-tertiary)` |
| `.eval-detail__text` | font-size | `var(--text-sm)` |
| | line-height | `var(--leading-relaxed)` |
| | color | `var(--color-text-primary)` |
| `.eval-detail__text--ground-truth` | background | `var(--color-primary-50)` |
| | border-left | `3px solid var(--color-primary-300)` |
| | padding | `var(--space-3)` |
| | border-radius | `0 var(--radius-md) var(--radius-md) 0` |
| `.eval-detail__context` | display | flex, gap `var(--space-3)` |
| `.eval-detail__context-index` | font-family | `var(--font-mono)` |
| | font-size | `var(--text-xs)` |
| | color | `var(--color-text-tertiary)` |
| | width | 20px, flex-shrink 0 |

---

## 6. Empty State

Shown when no evaluation has been run and no results exist.

### 6.1 HTML Structure

```html
<div class="eval__empty">
  <div class="eval__empty-icon">
    <!-- Beaker/flask icon, 32x32 -->
    <svg ...>...</svg>
  </div>
  <h2 class="eval__empty-title">No evaluation results yet</h2>
  <p class="eval__empty-description">
    Upload a test dataset with questions and ground truths, then run an
    evaluation to measure your RAG pipeline's quality.
  </p>
  <div class="eval__empty-steps">
    <div class="eval__empty-step">
      <span class="eval__empty-step-num">1</span>
      <span class="eval__empty-step-text">Prepare a JSON file with questions and expected answers</span>
    </div>
    <div class="eval__empty-step">
      <span class="eval__empty-step-num">2</span>
      <span class="eval__empty-step-text">Upload your dataset using the control above</span>
    </div>
    <div class="eval__empty-step">
      <span class="eval__empty-step-num">3</span>
      <span class="eval__empty-step-text">Click "Run Evaluation" to measure faithfulness, relevancy, precision, and recall</span>
    </div>
  </div>
</div>
```

### 6.2 Visual Specifications

Follows the exact pattern of `.chat__empty` in the existing system.

| Element | Property | Value |
|---|---|---|
| `.eval__empty` | display | flex column, center aligned |
| | gap | `var(--space-4)` |
| | padding | `var(--space-8)` |
| | text-align | center |
| `.eval__empty-icon` | width/height | 64px |
| | border-radius | `var(--radius-2xl)` |
| | background | `linear-gradient(135deg, var(--color-primary-50), var(--color-primary-100))` |
| | border | `1px solid var(--color-primary-200)` |
| | color | `var(--color-primary-500)` |
| `.eval__empty-title` | font-size | `var(--text-xl)` |
| | font-weight | `var(--weight-semibold)` |
| | color | `var(--color-text-primary)` |
| `.eval__empty-description` | font-size | `var(--text-base)` |
| | color | `var(--color-text-secondary)` |
| | max-width | 28rem |
| `.eval__empty-step` | display | flex, gap `var(--space-3)`, left-aligned |
| `.eval__empty-step-num` | 24px circle | `var(--color-primary-500)` bg, white text |
| | font-size | `var(--text-xs)` |
| | font-weight | `var(--weight-bold)` |

---

## 7. Loading State

Shown while the evaluation is running (typically 30-60 seconds). The controls section shows the running status with run id. The results area shows skeleton placeholders while status is polled.

### 7.1 HTML Structure

```html
<!-- Skeleton metric cards -->
<section class="eval__overview">
  <div class="eval__metrics">
    <div class="metric-card metric-card--skeleton">
      <div class="skeleton skeleton--text-short" style="width: 50%"></div>
      <div class="metric-card__body">
        <div class="skeleton" style="width: 80px; height: 80px; border-radius: var(--radius-full)"></div>
        <div class="skeleton skeleton--text" style="margin-top: var(--space-2)"></div>
      </div>
    </div>
    <!-- Repeat 3 more times -->
  </div>
</section>

<!-- Skeleton table -->
<section class="eval__breakdown">
  <div class="eval__table-wrapper">
    <div class="eval__skeleton-rows">
      <div class="skeleton skeleton--card"></div>
      <div class="skeleton skeleton--card"></div>
      <div class="skeleton skeleton--card"></div>
      <div class="skeleton skeleton--card"></div>
      <div class="skeleton skeleton--card"></div>
    </div>
  </div>
</section>

<!-- Progress overlay (optional, centered over results area) -->
<div class="eval__loading-overlay">
  <div class="eval__loading-content">
    <div class="eval__loading-spinner"></div>
    <p class="eval__loading-text">Running Ragas evaluation...</p>
    <p class="eval__loading-subtext">Polling run status every 2-3 seconds (typically 30-60s)</p>
    <div class="eval__loading-progress">
      <div class="eval__loading-progress-bar">
        <div class="eval__loading-progress-fill eval__loading-progress-fill--indeterminate"></div>
      </div>
    </div>
  </div>
</div>
```

### 7.2 Visual Specifications

| Element | Property | Value |
|---|---|---|
| `.eval__loading-overlay` | position | absolute, inset 0 |
| | background | `var(--color-bg-primary)` at 80% opacity |
| | display | flex, center aligned |
| | z-index | `var(--z-overlay)` |
| | backdrop-filter | `blur(4px)` |
| `.eval__loading-spinner` | width/height | 40px |
| | border | `3px solid var(--color-bg-tertiary)` |
| | border-top-color | `var(--color-primary-500)` |
| | border-radius | `var(--radius-full)` |
| | animation | `spin 0.8s linear infinite` |
| `.eval__loading-text` | font-size | `var(--text-md)` |
| | font-weight | `var(--weight-semibold)` |
| | color | `var(--color-text-primary)` |
| `.eval__loading-subtext` | font-size | `var(--text-sm)` |
| | color | `var(--color-text-tertiary)` |
| `.eval__loading-progress` | width | 200px |
| `.eval__loading-progress-bar` | height | 4px |
| | background | `var(--color-bg-tertiary)` |
| | border-radius | `var(--radius-full)` |
| | overflow | hidden |
| `.eval__loading-progress-fill--indeterminate` | Same as `.upload__progress-fill--indeterminate` |

---

## 8. Responsive Behavior

| Breakpoint | Layout Change |
|---|---|
| >= 1024px | 4 metric cards in a row, full table visible |
| 768px - 1023px | 2x2 metric card grid, table scrolls horizontally |
| < 768px | 1 metric card per row (stacked), controls stack vertically, table scrolls |

---

## 9. API Integration Contract

Frontend request/response flow for run-based evaluation:

1. `POST /evaluations`
   - Request: dataset upload or JSON payload
   - Response: `{ "run_id": "ev_20260331_001", "status": "queued" | "running" }`
2. `GET /evaluations/{run_id}`
   - Response: `{ "run_id": "...", "status": "queued" | "running" | "complete" | "error", "started_at": "...", "completed_at": "...", "error_message": null | "..." }`
3. `GET /evaluations/{run_id}/results` (when complete)
   - Response: `EvalResult`

UI behavior:
- Disable run button while active run status is `queued` or `running`
- Show run id in status text
- Transition to error state when status is `error`
- Render results only after `complete` + successful `/results` fetch

---

## 10. Accessibility Requirements

- All metric scores are exposed as text (not just visual gauges)
- Table uses semantic `<table>`, `<thead>`, `<tbody>`, `<th scope="col">`
- Expandable rows use `aria-expanded` attribute, toggled via Enter/Space
- Focus order follows visual order: controls, then overview, then table
- Color-coded scores always include a text label (percentage) so color is never the sole indicator
- Status dot states are announced via adjacent text, not color alone
- File upload input has a visible label associated via `for`/`id`
- The run button has clear disabled state with reduced opacity (0.4)
- All interactive elements meet minimum 44x44px touch target (or 24px with sufficient surrounding space per WCAG 2.5.8)

---

## 11. TypeScript Type Additions

Add to `frontend/src/types/ui.ts`:

```ts
// ---------------------------------------------------------------------------
// Evaluation types
// ---------------------------------------------------------------------------

export type EvalStatus = 'idle' | 'queued' | 'running' | 'complete' | 'error';

export interface EvalMetricScores {
  faithfulness: number;
  answer_relevancy: number;
  context_precision: number;
  context_recall: number;
}

export interface EvalPerQuestion {
  question: string;
  answer: string;
  ground_truth: string;
  contexts: string[];
  faithfulness: number;
  answer_relevancy: number;
  context_precision: number;
  context_recall: number;
}

export interface EvalResult {
  metrics: EvalMetricScores;
  per_question: EvalPerQuestion[];
  timestamp: string;         // ISO 8601
}

export interface EvalRun {
  run_id: string;
  status: Exclude<EvalStatus, 'idle'>;
  started_at?: string;       // ISO 8601
  completed_at?: string;     // ISO 8601
  error_message?: string | null;
}

export interface EvalDataset {
  questions: string[];
  ground_truths: string[];
}

// Update the ViewTab type
export type ViewTab = 'chat' | 'documents' | 'evaluation';
```
