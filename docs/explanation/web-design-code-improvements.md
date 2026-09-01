---
okf_version: "0.2"
type: "explanation"
title: "Project Web Interface & Accessibility Improvement Plan"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "web-design-code-improvements"
  - "accessibility"
  - "ui-ux"
  - "playwright"
  - "fastapi"
  - "html-css"
description: "Architectural audit findings and code improvement specifications for the RCF & DAC interactive web portal based on Vercel Web Interface Guidelines."
resource: "file:///docs/explanation/web-design-code-improvements.md"
sources:
  - ".agents/skills/web-design-guidelines/SKILL.md"
  - "src/dca_service/web_app.py"
  - "index.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
---

# Project Web Interface & Accessibility Improvement Plan

## Overview

Following the adoption of the **`web-design-guidelines` Skill**, an exhaustive UI/UX and accessibility audit was performed across all web interfaces of the **Research Commercialisation Fund (RCF) & Digital Asset Custodian (DAC)** platform.

This document details the audit findings, identified compliance gaps across HTML templates and CSS styles, and the comprehensive code modifications executed in `src/dca_service/web_app.py`, `index.md`, and `assets/css/style.css`.

---

## Audit Summary & Identified UI/UX Findings

The static and Playwright live browser audit evaluated four primary web views:
1. **Interactive Homepage & Module Portal** (`index.md` / `/`)
2. **System Login Portal** (`/login`)
3. **Institutional User Management Dashboard** (`/user-management`)
4. **Database Status & Network Diagnostic Page** (`/db-status`)

### Table of Audit Findings

| Component / Location | Category | Identified Finding / Guideline Violation | Required Code Modification |
| :--- | :--- | :--- | :--- |
| `web_app.py:978` (Login) | **Forms & Auth** | Inputs missing `autocomplete` attributes (`username`, `current-password`). | Add `autocomplete="username"` and `autocomplete="current-password"`. |
| `web_app.py:979` (Login) | **Forms & Auth** | Username & Email inputs missing `spellcheck="false"`. | Add `spellcheck="false"` to non-prose text inputs. |
| `web_app.py:975` (Login) | **Accessibility** | Dynamic alert box `#alertBox` lacks ARIA live announcement. | Add `aria-live="polite"` and `role="alert"`. |
| `web_app.py:1072` (User Mgmt) | **Accessibility** | Interactive buttons missing explicit `aria-label` tags. | Add descriptive `aria-label` attributes to `#logoutBtn`, `#createUserBtn`, etc. |
| `web_app.py:1085` (User Mgmt) | **Forms** | Input controls missing explicit `autocomplete` and `name` attributes. | Add `autocomplete="name"`, `autocomplete="email"`, `autocomplete="organization"`. |
| `web_app.py:1080` (User Mgmt) | **Accessibility** | Status & output cards (`#user-reg-output`, `#createUserAlert`, `#unauthAlert`) missing live regions. | Add `aria-live="polite"` to dynamic result containers. |
| `web_app.py:1570` (DB Status) | **Typography** | Diagnostic metrics and latency values lack tabular number formatting. | Apply `font-variant-numeric: tabular-nums` to numbers/latency figures. |
| `index.md` (Homepage) | **Typography** | Hardcoded periods (`...`) used instead of Unicode ellipsis (`…`). | Convert `...` to `…` across button text and status messages. |
| `assets/css/style.css` | **Focus States** | Lacked standardized focus-visible rings for keyboard traversal. | Implement `:focus-visible` styling (`outline: 2px solid #0066cc; outline-offset: 2px;`). |
| `assets/css/style.css` | **Animation** | Lacked `@media (prefers-reduced-motion: reduce)` override rules. | Add reduced motion media query disabling smooth transitions for user preference. |
| `assets/css/style.css` | **Touch & Mobile** | Missing `touch-action: manipulation` on buttons and input controls. | Apply `touch-action: manipulation` across interactive controls. |

---

## Detailed UI Code Enhancements

### 1. Form Autocomplete & Accessibility Labeling (`/login` & `/user-management`)

All input fields were updated with explicit label associations, `autocomplete` specifications, `spellcheck="false"`, and `aria-label` attributes:

```html
<!-- Login Form Inputs -->
<input type="text" id="username" name="username" autocomplete="username" spellcheck="false" required aria-label="System Username">
<input type="password" id="password" name="password" autocomplete="current-password" required aria-label="System Password">

<!-- User Registration Form Inputs -->
<input type="text" id="newUsername" name="username" autocomplete="username" spellcheck="false" required aria-label="New User Username">
<input type="email" id="newEmail" name="email" autocomplete="email" spellcheck="false" required aria-label="New User Email Address">
```

### 2. Dynamic Asynchronous State Announcements (`aria-live="polite"`)

All client-side feedback cards, login alerts, and output boxes were upgraded to include `aria-live="polite"` and `role="status"`/`role="alert"`:

```html
<div id="alertBox" role="alert" aria-live="polite" style="display: none;"></div>
<div id="createUserAlert" role="alert" aria-live="polite" style="display: none;"></div>
<div id="user-reg-output" role="status" aria-live="polite" style="display: none;"></div>
```

### 3. Tabular Numbers & Typography Refinements

CSS rules and inline styles were applied to ensure financial figures, scores, latency displays, and table columns render using tabular numbers (`tabular-nums`):

```css
/* Tabular Numbers for Scores, Metrics, and Financial Figures */
.score-number, .latency-display, table th, table td, .tabular-nums {
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum";
}

/* Headline Balance */
h1, h2, h3 {
  text-wrap: balance;
  scroll-margin-top: 2rem;
}
```

### 4. High-Contrast Focus Visible Rings & Reduced Motion Support

Added comprehensive focus ring styles and reduced motion media queries in `assets/css/style.css`:

```css
/* Focus Visible Ring Rules */
button:focus-visible,
a:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible {
  outline: 2px solid #0066cc !important;
  outline-offset: 2px !important;
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.25) !important;
}

/* Touch Action Manipulation for Instant Mobile Response */
button, input, select, textarea, .btn, .role-select-btn {
  touch-action: manipulation;
}

/* Reduced Motion Override */
@media (prefers-reduced-motion: reduce) {
  *, ::before, ::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

---

## Playwright E2E Verification Strategy

To guarantee that these UI improvements remain intact and unregressed, the Playwright E2E test suite in `tests/test_playwright_e2e.py` was extended with specialized Web Design Guidelines assertions:

1. **Accessibility & ARIA Validation:** Asserts presence of `aria-label` attributes on buttons and `aria-live="polite"` on output containers.
2. **Form Control Verification:** Asserts `autocomplete` attributes (`username`, `current-password`, `email`) and `spellcheck="false"`.
3. **Keyboard Focus Ring Verification:** Simulates keyboard traversal (`Tab` key) and validates computed focus ring properties on interactive inputs.
4. **Typography & Tabular Numbers Assertions:** Validates that Unicode ellipsis (`…`) and `font-variant-numeric: tabular-nums` are rendered properly.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
