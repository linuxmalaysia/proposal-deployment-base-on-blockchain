---
okf_version: "0.2"
type: "agent_skill"
title: "User Registration & W3C DID Minting Control Skill"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "user-registration"
  - "w3c-did"
  - "rbac"
  - "admin-control"
description: "Enforce strict role restrictions on user creation (/api/users) and W3C DID minting (/api/register-user)."
resource: "file:///.agents/skills/user-registration-did-minting/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "README.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
name: "user-registration-did-minting"
---

# User Registration & W3C DID Minting Control Skill

## Overview
Governs user registration and decentralised identifier (DID) minting permissions.

## Access Rules
- W3C DID minting (`/api/register-user`) is strictly restricted to the `admin` role.
- For account creation (`/api/users`), `admin` can create any role EXCEPT `superuser`.
- The `superuser` role can ONLY create `admin` accounts.


---
### Deep State of Mind (DSOM) AI Protocol Compliance
* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix
---
