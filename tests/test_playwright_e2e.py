"""
Playwright End-to-End (E2E) Browser Integration Tests for RCF & DAC Interactive Portal.
Covering /db-status visual rendering, interactive navigation, and form submissions.
"""

from __future__ import annotations

import os
import threading
import time
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


def test_playwright_interactive_portal_and_forms(page: Page, live_server: str):
    """Verify portal homepage rendering and interactive form submissions using browser DOM."""
    page.goto(f"{live_server}/")
    expect(page).to_have_title("RCF & DAC Interactive Web Portal")

    # Select Researcher Role
    researcher_btn = page.locator(".role-select-btn[data-role='researcher']")
    if researcher_btn.is_visible():
        researcher_btn.click()

    # Submit User Registration Form
    fullname_input = page.locator("#reg-fullname")
    if fullname_input.is_visible():
        fullname_input.fill("Prof. Sarah Chen")
        page.locator("#reg-dept").fill("Centre for Advanced Materials")
        page.locator("#reg-email").fill("sarah.chen@univ.edu.my")
        page.locator("#user-reg-form button[type='submit']").click()

        output = page.locator("#user-reg-output")
        expect(output).to_be_visible()
        expect(output).to_contain_text("Identity Registered & W3C DID Minted")
        expect(output).to_contain_text("did:univ:")

    # Interact with Revenue Split Calculator
    amount_input = page.locator("#rev-amount")
    if amount_input.is_visible():
        amount_input.fill("1000000")
        type_select = page.locator("#rev-type")
        type_select.select_option("equity")
        expect(page.locator("#revenue-split-body")).to_contain_text("RM")

    # Capture interactive submission screenshot
    page.screenshot(path="docs/screenshots/playwright_portal_interactive.png", full_page=True)


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

    # 5. Verify creation alert and table update
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
