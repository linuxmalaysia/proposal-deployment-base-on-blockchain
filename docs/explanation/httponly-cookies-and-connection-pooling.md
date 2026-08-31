---
okf_version: "0.2"
type: "explanation"
title: "HttpOnly Cookie Session Security, Connection Pooling Metrics, and High-Throughput Caching"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "security"
  - "httponly-cookies"
  - "connection-pooling"
  - "performance"
  - "diataxis"
description: "Architecture explanation of browser session isolation via HttpOnly cookies, connection pool metrics, and high-throughput API caching"
resource: "file:///docs/explanation/httponly-cookies-and-connection-pooling.md"
sources:
  - "src/dca_service/web_app.py"
  - "tests/test_playwright_e2e.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
---

# HttpOnly Cookie Session Security, Connection Pooling Metrics, and High-Throughput Caching

This document provides a conceptual explanation of the security enhancements, connection pool metrics, high-throughput caching strategies, and end-to-end testing workflows implemented in the Digital Asset Custodian (DAC) & Research Commercialisation Fund (RCF) web platform.

---

## 1. Browser Session Isolation via HttpOnly, Secure, SameSite Cookies

### The Problem with Client-Side Token Storage
In traditional Single Page Applications (SPAs), storing JSON Web Tokens (JWTs) in `localStorage` or `sessionStorage` exposes tokens to Cross-Site Scripting (XSS) attacks. If an attacker injects malicious JavaScript into the DOM, they can read client-side storage, exfiltrate the JWT bearer token, and hijack user sessions.

### Security Architecture: Defense-in-Depth
To mitigate XSS exfiltration risks, the platform adopts browser session cookie isolation while retaining backward compatibility for API clients:

1. **HttpOnly Flag:** The `rcf_dac_jwt` session cookie is marked `HttpOnly`, rendering it completely invisible and inaccessible to client-side JavaScript (`document.cookie` returns empty for this token).
2. **SameSite Lax Enforcement:** Restricts cross-site request forgery (CSRF) by preventing the browser from sending the session cookie on top-level cross-site GET requests from untrusted origins.
3. **Secure Flag Configuration:** Enforces transmission exclusively over encrypted HTTPS connections in production (`COOKIE_SECURE=true`), while supporting configurable development/test environments.
4. **Dual Authentication Extraction:** The API adapter (`extract_current_user_payload`) seamlessly checks both the `Authorization: Bearer <token>` header (for programmatic REST clients) and the `rcf_dac_jwt` cookie (for interactive web browser users).
5. **Session Revocation via `/api/logout`:** Clears the `HttpOnly` cookie server-side upon user logout, revoking session access.

---

## 2. Supabase & PostgreSQL Connection Pool Metrics Monitoring

### Connection Pool Bottlenecks in Serverless & Microservice Deployments
Under high concurrency or serverless auto-scaling (e.g. Render Web Services), creating new database connections per HTTP request incurs severe SSL handshake and connection checkout latency. Furthermore, Supabase and Percona PostgreSQL databases impose connection limits.

### Metrics Tracking Architecture
The platform introduces `ConnectionPoolMetrics` to track database driver health, connection checkout latency, and query volume in real time:

- **Connection Acquisition Latency:** Measures the round-trip time required to check out a pooled PostgreSQL connection (`avg_checkout_latency_ms`).
- **Utilization Tracking:** Computes real-time pool utilization percentage based on active and peak connection bounds (`max_pool_size`, `min_pool_size`).
- **Failure Diagnostics:** Logs connection acquisition failures (`failed_connection_attempts`) to detect database exhaustion or network partition early.
- **Monitoring Endpoints:** Exposes diagnostic metrics via `/api/db-pool-metrics` and embeds real-time pool telemetry directly into `/api/db-status`.

---

## 3. High-Throughput API In-Memory TTL Caching

To prevent redundant database queries on high-frequency API endpoints (such as investor asset listings and database status checks), the application implements thread-safe, in-memory Time-To-Live (TTL) caching:

- **Configurable TTL Duration:** Defaulting to 5.0 seconds (`INVESTOR_ASSETS_CACHE_TTL`, `DB_STATUS_CACHE_TTL`), balancing sub-second data freshness with database query suppression.
- **Cache Invalidation on Mutation:** Write operations (such as registering a new asset via `/api/register-asset`) immediately clear the in-memory cache (`_INVESTOR_ASSETS_CACHE = None`), ensuring newly registered data is reflected on subsequent queries without lag.
- **Cache Bypass Capability:** Support for `bypass_cache=true` parameters allowing administrators to force real-time queries when required.

---

## 4. Automated End-to-End (E2E) Browser Testing via Playwright

To guarantee robust frontend resilience under continuous integration (CI):

- **Headless Browser Workflows:** Playwright test suites (`tests/test_playwright_e2e.py`) launch headless Chromium browsers against a live Uvicorn application server.
- **Full Form Automation:** Automates full user authentication (`/login`), HttpOnly cookie session establishment, navigation to `/user-management`, administrative user creation, table verification, and logout execution.
- **Visual Evidence Screenshots:** Captures full-page screenshots (`docs/screenshots/playwright_user_management.png`) to verify layout rendering and UI state transitions.
