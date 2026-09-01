---
okf_version: "0.2"
type: "agent_skill"
title: "Vercel Web Interface Guidelines UI Review Skill"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "web-design-guidelines"
  - "ui-ux"
  - "accessibility"
  - "a11y"
  - "antigravity"
  - "playwright"
description: "Review UI code for Web Interface Guidelines compliance, accessibility standards, focus management, forms, typography, and UX principles."
resource: "file:///.agents/skills/web-design-guidelines/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "README.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
name: "web-design-guidelines"
---

# Vercel Web Interface Guidelines UI Review Skill

## Overview

The `web-design-guidelines` skill enables AI agents (Google Jules and Google Antigravity) and developers to audit web interfaces for strict compliance with established Web Interface Guidelines, W3C WCAG accessibility standards, and modern UX design principles.

## Use When Asked To

- "Review my UI"
- "Check accessibility" or "audit design"
- "Review UX"
- "Check my site against best practices"

## Guidelines Source

Latest rules fetched from:
`https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md`

## Rules Summary

### 1. Accessibility (a11y)
- Icon-only buttons need `aria-label`.
- Form controls need `<label>` (with matching `for` attribute) or `aria-label`.
- Interactive elements need keyboard event handlers (`onKeyDown`/`onKeyUp`).
- Use `<button>` for actions, `<a>`/`<Link>` for navigation (not `<div onClick>`).
- Images need `alt` (or `alt=""` if decorative).
- Decorative icons need `aria-hidden="true"`.
- Async updates (toasts, alert boxes, validation messages) need `aria-live="polite"`.
- Use semantic HTML (`<button>`, `<a>`, `<label>`, `<table>`) before ARIA.
- Headings hierarchical `<h1>`–`<h6>`; include skip link for main content.
- `scroll-margin-top` on heading anchors.
- Meaningful media needs captions, transcripts, or descriptions.

### 2. Focus States
- Interactive elements need visible focus: `:focus-visible` ring or equivalent outline.
- Never `outline-none` or `outline: none` without focus replacement.
- Use `:focus-visible` over `:focus` to avoid focus rings on mouse click.
- Group focus with `:focus-within` for compound controls.
- Sticky headers/footers/overlays must not cover focused elements.

### 3. Forms
- Inputs need `autocomplete` and meaningful `name` attribute.
- Use correct `type` (`email`, `tel`, `url`, `number`, `range`) and `inputmode`.
- Never block paste (`onPaste` with `preventDefault`).
- Labels clickable (`for` / `htmlFor` wrapping control).
- Disable spellcheck on emails, codes, usernames (`spellcheck="false"`).
- Checkboxes/radios: label + control share single hit target.
- Submit button stays enabled until request starts; spinner or loading text during request.
- Inline errors next to fields; focus first error on submit.
- Placeholders end with `…` and show example pattern.
- `autocomplete="off"` on non-auth fields to avoid password manager triggers.

### 4. Animation
- Honor `prefers-reduced-motion` (provide reduced variant or disable).
- Animate `transform`/`opacity` only (compositor-friendly).
- Never `transition: all`—list properties explicitly.
- Set correct `transform-origin`.
- SVG: transforms on `<g>` wrapper with `transform-box: fill-box; transform-origin: center`.
- Animations interruptible—respond to user input mid-animation.

### 5. Typography
- Use `…` instead of `...`.
- Curly quotes `“` `”` over straight quotes `"`.
- Non-breaking spaces for units and brands: `10&nbsp;MB`, `RM&nbsp;500,000`, `⌘&nbsp;K`.
- Loading states end with `…`: "Loading…", "Saving…".
- `font-variant-numeric: tabular-nums` for number columns/comparisons.
- Use `text-wrap: balance` or `text-pretty` on headings.

### 6. Content Handling & Performance
- Text containers handle long content: `truncate`, `line-clamp-*`, or `overflow-wrap: break-word`.
- Flex children need `min-w-0` to allow text truncation.
- Handle empty states—don't render broken UI for empty strings/arrays.
- Large lists (>50 items) virtualized.
- Images need explicit `width` and `height` to prevent CLS.

### 7. Touch & Layout
- `touch-action: manipulation` (prevents double-tap zoom delay).
- `-webkit-tap-highlight-color` set intentionally.
- `overscroll-behavior: contain` in modals/drawers/sheets.
- Full-bleed layouts need `env(safe-area-inset-*)`.
- Dark Mode: `color-scheme: dark` on `<html>` for dark themes.

## Jules & Antigravity Enhancements

In addition to static file inspection, Google Jules and Google Antigravity leverage headless browser automation via Playwright E2E integration (`tests/test_playwright_e2e.py`) to dynamically inspect DOM trees, verify computed focus rings, check ARIA accessibility roles, and validate interactive forms live in real-time.

## Output Format

Group findings by file in `file:line` format:

```
## src/dca_service/web_app.py

src/dca_service/web_app.py:982 - icon button missing aria-label
src/dca_service/web_app.py:995 - dynamic alert box missing aria-live="polite"
src/dca_service/web_app.py:1012 - input missing autocomplete attribute
```

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
