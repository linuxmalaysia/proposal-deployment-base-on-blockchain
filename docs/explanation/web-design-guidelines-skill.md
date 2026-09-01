---
okf_version: "0.2"
type: "explanation"
title: "Web Interface Guidelines & AI Agent Skill Architecture"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "web-design-guidelines"
  - "ui-ux"
  - "accessibility"
  - "a11y"
  - "antigravity"
  - "jules"
description: "Comprehensive guide to the web-design-guidelines agent skill, covering automated UI auditing, WCAG accessibility rules, focus management, forms, typography, and Jules/Antigravity integration."
resource: "file:///docs/explanation/web-design-guidelines-skill.md"
sources:
  - ".agents/skills/web-design-guidelines/SKILL.md"
  - "README.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
---

# Web Interface Guidelines & AI Agent Skill Architecture

## Executive Summary

The **`web-design-guidelines` Skill** establishes a standardized, automated operational protocol for evaluating web applications and user interfaces against industry-leading Web Interface Guidelines, W3C WCAG accessibility standards, focus state management rules, form design principles, and typography best practices.

Integrated into the **Deep State of Mind (DSOM) AI Protocol**, this skill empowers Google Jules and Google Antigravity agents to perform static code analysis and live Playwright headless browser E2E inspections across web templates, ensuring high signal-to-noise quality audits and zero-friction compliance.

---

## Skill Mechanics & Workflow Architecture

When invoked by prompt triggers such as `"review my UI"`, `"check accessibility"`, or `"audit design"`, the agent executes a structured 4-stage audit workflow:

```text
┌────────────────────────┐      ┌────────────────────────┐
│  1. Skill Discovery    │ ───► │  2. Guideline Fetch    │
│  (.agents/skills/)     │      │  (Latest Ruleset)      │
└────────────────────────┘      └────────────────────────┘
                                            │
                                            ▼
┌────────────────────────┐      ┌────────────────────────┐
│  4. Terse Report       │ ◄─── │  3. Static & Live      │
│  (file:line format)    │      │  Playwright Audit      │
└────────────────────────┘      └────────────────────────┘
```

1. **Rule Set Fetching:** Retrieves fresh guidelines from the authoritative source endpoint (`https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md`).
2. **Code Inspection:** Reads targeted HTML, CSS, JavaScript, and Jinja/FastAPI template files.
3. **Live Browser Verification:** Executes Playwright headless browser sessions (`tests/test_playwright_e2e.py`) to verify rendered computed styles, DOM attributes, keyboard focus states, and dynamic live region updates.
4. **Terse Reporting:** Outputs findings in a concise `file:line` format for direct VS Code developer click-through.

---

## Core Guideline Categories

### 1. Accessibility (a11y)

* **Explicit Labeling:** Icon-only buttons MUST possess explicit `aria-label` or `aria-labelledby` attributes. All form controls require matching `<label for="id">` associations.
* **Semantic Hierarchy:** HTML semantic tags (`<button>`, `<a>`, `<label>`, `<table>`) take absolute priority over generic `<div>` click handlers. Headings follow hierarchical order (`<h1>` through `<h6>`).
* **Live Updates:** Asynchronous state modifications (toasts, validation warnings, status changes) require `aria-live="polite"` containers.
* **Media & Anchor Margins:** Decorative icons specify `aria-hidden="true"`. Heading anchors incorporate `scroll-margin-top` for fixed header offset preservation.

### 2. Focus States & Keyboard Traversal

* **Visible Focus:** Interactive controls enforce visible focus indicators using CSS `:focus-visible` ring parameters or distinct outline styles.
* **Focus Outline Rules:** Blocking or stripping focus outlines via `outline: none` without a high-contrast focus-visible replacement is explicitly prohibited.
* **Mouse vs Keyboard:** Use `:focus-visible` over `:focus` to prevent outline rings on standard mouse clicks.

### 3. Form Control Standards

* **Autocomplete & Names:** Every input field specifies explicit `autocomplete` attributes (`username`, `current-password`, `name`, `email`, or `off` for non-auth controls) and a descriptive `name` property.
* **Input Types & Modes:** Form fields leverage proper input types (`email`, `tel`, `url`, `number`, `range`) and `inputmode="decimal"` for numeric inputs.
* **Interaction Protection:** Blocking paste operations (`onPaste` with `preventDefault`) is prohibited.
* **Spelling Hygiene:** Non-prose fields (emails, usernames, authentication codes) specify `spellcheck="false"`.

### 4. Animation & Reduced Motion

* **Reduced Motion Honor:** All keyframe animations and structural CSS transitions respect `@media (prefers-reduced-motion: reduce)`.
* **Compositor Efficiency:** Animations target GPU-accelerated `transform` and `opacity` properties exclusively, avoiding `transition: all`.

### 5. Typography & Formatting Standards

* **Ellipsis Character:** Standardize on Unicode ellipsis character (`…`) rather than three consecutive periods (`...`).
* **Numeric Columns:** Tables, financial figures, and latency displays mandate `font-variant-numeric: tabular-nums` to prevent layout shift during updates.
* **Headline Balance:** Headings enforce `text-wrap: balance` or `text-pretty` to prevent single-word typographical widows.

---

## Jules & Antigravity Dual Integration

Under the DSOM Protocol, Google Jules and Google Antigravity seamlessly coordinate skill execution:

* **Spatial Memory Integration:** Audit results and UI improvements are indexed into `.agents/brain/task.md` and `.agents/brain/walkthrough.md`.
* **Playwright Automated Verification:** Rather than relying solely on static text analysis, Playwright E2E browser tests dynamically assert element visibility, focus visibility, keyboard navigation, and ARIA state transitions.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
