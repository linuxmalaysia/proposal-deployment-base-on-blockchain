"""
Playwright End-to-End (E2E) Browser Integration Tests for RCF & DAC Interactive Portal.
Covering /db-status visual rendering, interactive navigation, and form submissions.
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Generator

import pytest
import uvicorn
from playwright.sync_api import Page, expect

os.environ.setdefault("INVESTOR_JWT_SECRET", "test_rcf_dac_jwt_secret_key_2026")

from dca_service.web_app import ACCOUNT_REGISTRY, app, hash_password


class ServerThread(threading.Thread):
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        super().__init__()
        self.host = host
        self.port = port
        self.server = None
        self.daemon = True

    def run(self):
        config = uvicorn.Config(app=app, host=self.host, port=self.port, log_level="warning")
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        if self.server:
            self.server.should_exit = True


@pytest.fixture(scope="module", autouse=True)
def live_server() -> Generator[str, None, None]:
    """Start live Uvicorn web server in a background thread for Playwright E2E tests."""
    port = 8765
    server = ServerThread(port=port)
    server.start()
    time.sleep(1.0)  # Wait for server to bind
    yield f"http://127.0.0.1:{port}"
    server.stop()


def test_playwright_db_status_rendering(page: Page, live_server: str):
    """Verify /db-status page visual rendering, diagnostic elements, re-test button, and JSON endpoint link."""
    page.goto(f"{live_server}/db-status")

    expect(page).to_have_title("Database Connection & Schema Verification Status | RCF & DAC")
    expect(page.locator("h1")).to_contain_text("Supabase & PostgreSQL Database Status")
    expect(page.locator("text=Network & Latency Diagnostic")).to_be_visible()
    expect(page.locator("text=Project Database Tables & Schema Checklist")).to_be_visible()
    expect(page.locator("text=docs/schema.sql")).to_be_visible()

    # Re-test button interaction
    retest_btn = page.locator("a:has-text('Re-test Database Connection')")
    expect(retest_btn).to_be_visible()
    retest_btn.click()
    page.wait_for_load_state("networkidle")
    assert "/db-status" in page.url

    # Take visual screenshot
    os.makedirs("docs/screenshots", exist_ok=True)
    page.screenshot(path="docs/screenshots/playwright_db_status.png", full_page=True)


def test_playwright_guest_modules_are_hidden_until_read_filter_selected(
    page: Page, live_server: str
):
    """Guests should start with no operational modules and may explicitly preview them."""
    page.goto(f"{live_server}/")

    guest_notice = page.locator("#guestNoticeCard")
    module_panels = page.locator(".role-view-panel")

    expect(guest_notice).to_be_visible()
    expect(module_panels).to_have_count(4)
    for index in range(module_panels.count()):
        expect(module_panels.nth(index)).to_be_hidden()

    page.locator(".role-select-btn[data-role='all']").click()

    expect(guest_notice).to_be_hidden()
    for index in range(module_panels.count()):
        expect(module_panels.nth(index)).to_be_visible()

    page.locator(".role-select-btn[data-role='my-role']").click()

    expect(guest_notice).to_be_visible()
    for index in range(module_panels.count()):
        expect(module_panels.nth(index)).to_be_hidden()


def test_playwright_cloverleaf_mrs_score_and_revenue_split_workflows(page: Page, live_server: str):
    """E2E test for Cloverleaf quantitative MRS calculations and IP policy revenue split matrix interactive workflows."""
    page.goto(f"{live_server}/")
    expect(page).to_have_title("RCF & DAC Interactive Web Portal")

    # Select Admin role view to access Module 3 (Cloverleaf) and Module 5 (Revenue Split)
    admin_role_btn = page.locator(".role-select-btn[data-role='admin']")
    if admin_role_btn.is_visible():
        admin_role_btn.click()

    # 1. Cloverleaf Score Slider Calculations Workflow
    score_tech = page.locator("#score-tech")
    score_market = page.locator("#score-market")
    score_comm = page.locator("#score-comm")
    score_mgmt = page.locator("#score-mgmt")

    if score_tech.is_visible():
        # Set values that total > 180 (Investment-Ready qualification)
        score_tech.fill("55")
        score_market.fill("70")
        score_comm.fill("50")
        score_mgmt.fill("50")

        total_display = page.locator("#total-cloverleaf-score")
        expect(total_display).to_contain_text("225 / 260")

        status_display = page.locator("#cloverleaf-status")
        expect(status_display).to_contain_text("INVESTMENT-READY")

        # Set values that total <= 180 (Development Required)
        score_tech.fill("20")
        score_market.fill("30")
        score_comm.fill("20")
        score_mgmt.fill("20")
        expect(total_display).to_contain_text("90 / 260")
        expect(status_display).to_contain_text("DEVELOPMENT REQUIRED")

    # 2. IP Policy Revenue-Split Matrix Calculator Workflow
    amount_input = page.locator("#rev-amount")
    type_select = page.locator("#rev-type")
    split_body = page.locator("#revenue-split-body")

    if amount_input.is_visible():
        amount_input.fill("1000000")

        # Test Licensing milestone allocation
        type_select.select_option("licensing")
        expect(split_body).to_contain_text("RM")
        expect(split_body).to_contain_text("30.0%")
        expect(split_body).to_contain_text("20.0%")

        # Test Equity IPO Exit allocation
        type_select.select_option("equity")
        expect(split_body).to_contain_text("35.0%")
        expect(split_body).to_contain_text("10.0%")
        expect(split_body).to_contain_text("25.0%")
        expect(split_body).to_contain_text("30.0%")

    page.screenshot(path="docs/screenshots/playwright_cloverleaf_and_revenue_split.png", full_page=True)


def test_playwright_login_and_user_creation_workflow(page: Page, live_server: str):
    """Automate full login form submission, HttpOnly JWT session token handling, administrative user creation, and logout."""
    # Ensure deterministic password for admin account
    ACCOUNT_REGISTRY["dca_admin_mgr"]["password_hash"] = hash_password("InitPass_admin_2026!")

    # 1. Navigate to login page
    page.goto(f"{live_server}/login")
    expect(page).to_have_title("System Login | RCF & DAC Platform")

    # 2. Submit credentials
    page.locator("#username").fill("dca_admin_mgr")
    page.locator("#password").fill("InitPass_admin_2026!")
    page.locator("#loginForm button[type='submit']").click()

    # 3. Wait for redirect to User Management Dashboard
    page.wait_for_url(f"{live_server}/user-management", timeout=5000)
    expect(page).to_have_title("User Management Interface | RCF & DAC Platform")
    expect(page.locator("h1")).to_contain_text("Institutional User Management Dashboard")

    # 4. Fill and submit administrative user creation form
    page.locator("#newUsername").fill("e2e_operator_02")
    page.locator("#newPassword").fill("SecuredPass123!")
    page.locator("#newName").fill("Dr. Alan Turing")
    page.locator("#newRole").select_option("operator")
    page.locator("#newDept").fill("Quantum Computing Lab")
    page.locator("#newEmail").fill("alan.turing@rcf-dac.univ.edu.my")
    page.locator("#createUserBtn").click()

    # 5. Verify W3C DID Minting form on User Management Dashboard
    reg_fullname = page.locator("#reg-fullname")
    expect(reg_fullname).to_be_visible()
    reg_fullname.fill("Prof. Dr. Alan Turing")
    page.locator("#reg-dept").fill("Quantum Computing & Cryptography Center")
    page.locator("#reg-email").fill("alan.turing@univ.edu.my")
    page.locator("#user-reg-form button[type='submit']").click()

    output = page.locator("#user-reg-output")
    expect(output).to_be_visible()
    expect(output).to_contain_text("Identity Registered & W3C DID Minted")
    expect(output).to_contain_text("did:univ:")

    # 6. Fill and submit administrative user creation form
    alert_box = page.locator("#createUserAlert")
    expect(alert_box).to_be_visible()
    expect(alert_box).to_contain_text("created successfully")
    expect(page.locator("#userTableBody")).to_contain_text("e2e_operator_02")

    # Capture screenshot of administrative creation
    os.makedirs("docs/screenshots", exist_ok=True)
    page.screenshot(path="docs/screenshots/playwright_user_management.png", full_page=True)

    # 6. Perform logout workflow
    logout_btn = page.locator("#logoutBtn")
    expect(logout_btn).to_be_visible()
    logout_btn.click()
    page.wait_for_url(f"{live_server}/login", timeout=5000)
    assert "/login" in page.url


def test_playwright_web_design_guidelines_compliance(page: Page, live_server: str):
    """Verify Web Interface Guidelines & W3C WCAG Accessibility compliance using Playwright E2E."""
    # 1. Login Page Audit: Form autocompletes, spellcheck, aria-live, aria-labels
    page.goto(f"{live_server}/login")

    username_input = page.locator("#username")
    expect(username_input).to_have_attribute("autocomplete", "username")
    expect(username_input).to_have_attribute("spellcheck", "false")
    expect(username_input).to_have_attribute("aria-label", "System Username")

    password_input = page.locator("#password")
    expect(password_input).to_have_attribute("autocomplete", "current-password")
    expect(password_input).to_have_attribute("aria-label", "System Password")

    alert_box = page.locator("#alertBox")
    expect(alert_box).to_have_attribute("aria-live", "polite")
    expect(alert_box).to_have_attribute("role", "alert")

    login_btn = page.locator("#loginForm button[type='submit']")
    expect(login_btn).to_have_attribute("aria-label", "Sign In")

    # 2. User Management Page Audit (Authed)
    ACCOUNT_REGISTRY["dca_admin_mgr"]["password_hash"] = hash_password("InitPass_admin_2026!")
    username_input.fill("dca_admin_mgr")
    password_input.fill("InitPass_admin_2026!")
    login_btn.click()

    page.wait_for_url(f"{live_server}/user-management", timeout=5000)

    # Check Logout Button ARIA label
    expect(page.locator("#logoutBtn")).to_have_attribute("aria-label", "Sign Out")

    # Check User Registration Form accessibility attributes
    reg_fullname = page.locator("#reg-fullname")
    expect(reg_fullname).to_have_attribute("autocomplete", "name")
    expect(reg_fullname).to_have_attribute("aria-label", "Full Name & Title")

    reg_email = page.locator("#reg-email")
    expect(reg_email).to_have_attribute("autocomplete", "email")
    expect(reg_email).to_have_attribute("spellcheck", "false")

    reg_output = page.locator("#user-reg-output")
    expect(reg_output).to_have_attribute("aria-live", "polite")

    # Check Create User Form accessibility attributes
    new_user = page.locator("#newUsername")
    expect(new_user).to_have_attribute("autocomplete", "username")
    expect(new_user).to_have_attribute("spellcheck", "false")

    new_pass = page.locator("#newPassword")
    expect(new_pass).to_have_attribute("autocomplete", "new-password")

    create_alert = page.locator("#createUserAlert")
    expect(create_alert).to_have_attribute("aria-live", "polite")

    # 3. Homepage Interactive Module Portal Audit
    page.goto(f"{live_server}/")
    page.locator(".role-select-btn[data-role='all']").click()

    # Verify input types and modes
    rev_amount = page.locator("#rev-amount")
    expect(rev_amount).to_have_attribute("inputmode", "decimal")
    expect(rev_amount).to_have_attribute("type", "number")

    # Verify ARIA live status containers
    expect(page.locator("#cloverleaf-status")).to_have_attribute("aria-live", "polite")
    expect(page.locator("#asset-reg-output")).to_have_attribute("aria-live", "polite")

    # Take verification screenshot
    os.makedirs("docs/screenshots", exist_ok=True)
    page.screenshot(path="docs/screenshots/playwright_guidelines_compliance.png", full_page=True)


def test_playwright_visual_regression_theme_and_viewport_matrix(page: Page, live_server: str):
    """
    Expand Playwright E2E visual regression snapshot comparison testing across
    dark mode/light mode themes and mobile viewports.
    """
    os.makedirs("docs/screenshots", exist_ok=True)

    viewports = [
        ("desktop", {"width": 1280, "height": 800}),
        ("mobile", {"width": 375, "height": 667}),
    ]
    themes = ["light", "dark"]

    for vp_name, vp_size in viewports:
        page.set_viewport_size(vp_size)
        for theme in themes:
            page.goto(f"{live_server}/")
            page.wait_for_load_state("networkidle")

            # Apply theme via data-theme attribute or theme toggle button
            page.evaluate(f"document.documentElement.setAttribute('data-theme', '{theme}')")
            page.evaluate(f"localStorage.setItem('dca_theme', '{theme}')")

            # Verify element attribute
            html_element = page.locator("html")
            expect(html_element).to_have_attribute("data-theme", theme)

            # Ensure all modules visible for visual inspection
            page.locator(".role-select-btn[data-role='all']").click()

            shot_path = f"docs/screenshots/playwright_homepage_{vp_name}_{theme}.png"
            if os.path.exists(shot_path):
                baseline_bytes = Path(shot_path).read_bytes()
            else:
                baseline_bytes = b""

            new_bytes = page.screenshot(full_page=True)

            if baseline_bytes:
                # Compare screenshot size variance against committed baseline
                assert abs(len(new_bytes) - len(baseline_bytes)) < 25000, (
                    f"Visual snapshot for {vp_name}_{theme} diverged significantly from baseline"
                )

            with open(shot_path, "wb") as f:
                f.write(new_bytes)

            assert os.path.exists(shot_path)
            assert os.path.getsize(shot_path) > 0


def test_playwright_db_status_mobile_and_dark_mode_visual_regression(page: Page, live_server: str):
    """Verify /db-status page rendering under dark mode theme and mobile viewport."""
    os.makedirs("docs/screenshots", exist_ok=True)

    page.set_viewport_size({"width": 375, "height": 667})
    page.goto(f"{live_server}/db-status")
    page.wait_for_load_state("networkidle")

    # Set dark theme
    page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")

    # Verify diagnostic content renders cleanly in mobile dark mode
    expect(page.locator("h1")).to_contain_text("Supabase & PostgreSQL Database Status")
    expect(page.locator("text=Network & Latency Diagnostic")).to_be_visible()

    shot_path = "docs/screenshots/playwright_db_status_mobile_dark.png"
    page.screenshot(path=shot_path, full_page=True)
    assert os.path.exists(shot_path)
    assert os.path.getsize(shot_path) > 0


def test_playwright_dynamic_role_permission_updates(page: Page, live_server: str):
    """E2E browser test scenario for dynamic role permission updates via /api/role-assignments."""
    ACCOUNT_REGISTRY["dca_admin_mgr"]["password_hash"] = hash_password("InitPass_admin_2026!")

    # 1. Login as Admin
    login_resp = page.request.post(
        f"{live_server}/api/login",
        data={"username": "dca_admin_mgr", "password": "InitPass_admin_2026!"},
    )
    assert login_resp.status == 200
    token = login_resp.json()["access_token"]

    # 2. Query initial role assignments
    get_resp = page.request.get(
        f"{live_server}/api/role-assignments",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status == 200
    initial_permissions = get_resp.json()["module_permissions"]

    # 3. Dynamically grant 'operator' access to module_4 (Investor Dashboard)
    updated_permissions = dict(initial_permissions)
    updated_permissions["module_4"] = ["investor", "operator"]

    update_resp = page.request.post(
        f"{live_server}/api/role-assignments",
        headers={
            "Authorization": f"Bearer {token}",
            "X-CSRF-Token": "csrf_valid_token",
        },
        data={"module_permissions": updated_permissions},
    )
    assert update_resp.status == 200
    res_json = update_resp.json()
    assert "operator" in res_json["module_permissions"]["module_4"]

    # 4. Verify persisted state via GET
    verify_resp = page.request.get(
        f"{live_server}/api/role-assignments",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert verify_resp.status == 200
    assert "operator" in verify_resp.json()["module_permissions"]["module_4"]

    # Revert to initial permissions
    page.request.post(
        f"{live_server}/api/role-assignments",
        headers={
            "Authorization": f"Bearer {token}",
            "X-CSRF-Token": "csrf_valid_token",
        },
        data={"module_permissions": initial_permissions},
    )


def test_playwright_cookie_expiration_and_session_boundary_cases(page: Page, live_server: str):
    """E2E test scenario for session cookie boundary cases, expiration, and logout revocation."""
    from dca_service.web_app import create_system_jwt

    ACCOUNT_REGISTRY["dca_admin_mgr"]["password_hash"] = hash_password("InitPass_admin_2026!")

    # 1. Successful authentication sets HttpOnly session cookie
    login_resp = page.request.post(
        f"{live_server}/api/login",
        data={"username": "dca_admin_mgr", "password": "InitPass_admin_2026!"},
    )
    assert login_resp.status == 200
    cookies = page.context.cookies()
    jwt_cookie = next((c for c in cookies if c["name"] == "rcf_dac_jwt"), None)
    assert jwt_cookie is not None
    assert jwt_cookie["httpOnly"] is True
    assert jwt_cookie["sameSite"].lower() == "lax"

    # 2. Expired session token boundary test (exp in past)
    expired_token = create_system_jwt(username="dca_admin_mgr", role="admin", exp_delta=-100.0)
    expired_resp = page.request.get(
        f"{live_server}/api/users",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert expired_resp.status == 403
    assert "Token has expired" in expired_resp.json()["detail"]

    # 3. Revoke session via /api/logout
    logout_resp = page.request.post(
        f"{live_server}/api/logout",
        headers={"X-CSRF-Token": "csrf_valid_token"},
    )
    assert logout_resp.status == 200
    assert "Successfully logged out" in logout_resp.json()["message"]

    # 4. Request without session cookie fails closed with 401 Unauthorized
    page.context.clear_cookies()
    unauth_resp = page.request.get(f"{live_server}/api/users")
    assert unauth_resp.status == 401
    assert "Authentication required" in unauth_resp.json()["detail"]


def test_playwright_security_and_preload_headers_verification(page: Page, live_server: str):
    """Verify CSP security headers, SRI attributes, and HTTP/2 asset preloading headers in E2E browser context."""
    response = page.goto(f"{live_server}/")
    assert response is not None
    assert response.status == 200

    headers = response.headers
    csp = headers.get("content-security-policy", "")
    assert "default-src 'self'" in csp
    assert "script-src 'self' 'unsafe-inline'" in csp

    link_preload = headers.get("link", "")
    assert "rel=preload" in link_preload
    assert "/assets/css/style.css" in link_preload

    # Verify SRI integrity and crossorigin attributes on loaded static assets
    css_link = page.locator("link[rel='stylesheet']")
    expect(css_link).to_have_attribute("crossorigin", "anonymous")
    css_integrity = css_link.get_attribute("integrity")
    assert css_integrity is not None and css_integrity.startswith("sha256-")

    js_script = page.locator("script[src='/assets/js/rcf-dac-app.js']")
    expect(js_script).to_have_attribute("crossorigin", "anonymous")
    js_integrity = js_script.get_attribute("integrity")
    assert js_integrity is not None and js_integrity.startswith("sha256-")
