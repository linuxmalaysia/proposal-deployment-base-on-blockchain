"""
Unit & Integration Tests for RCF & DAC FastAPI Web Application & Render Deployment.

Governed by DSOM Protocol // OKF v0.2 Standard.
"""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from fastapi.testclient import TestClient
from dca_service.web_app import app

client = TestClient(app)
ROOT_DIR = Path(__file__).resolve().parent.parent


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "rcf-dac-web-app"


def test_user_registration_endpoint():
    payload = {
        "name": "Prof. Dr. Harisfazillah Jamel",
        "role": "Lead Principal Investigator (PI)",
        "dept": "Centre of Excellence in DeepTech & Nanotechnology",
        "email": "harisfazillah@university.edu.my",
    }
    response = client.post("/api/register-user", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "user" in data
    assert data["user"]["did"].startswith("did:univ:")
    assert data["user"]["name"] == payload["name"]


def test_asset_registration_base64_decoding():
    raw_content = b"raw_laboratory_binary_data_stream_content_12345"
    b64_content = base64.b64encode(raw_content).decode("utf-8")
    expected_digest = f"sha256:{hashlib.sha256(raw_content).hexdigest()}"

    payload = {
        "title": "Graphene-Enhanced Solid State Lithium-Air Battery Cell",
        "trl": 3,
        "abstract": "Energy density exceeding 650 Wh/kg with 1,500 cycle life.",
        "file_name": "battery_lab_test_report.pdf",
        "file_content": b64_content,
    }
    response = client.post("/api/register-asset", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["asset"]["sha256_digest"] == expected_digest


def test_asset_registration_fallback_when_content_none():
    payload = {
        "title": "Graphene Battery Cell",
        "trl": 3,
        "abstract": "Energy density exceeding 650 Wh/kg.",
        "file_name": "report.pdf",
        "file_content": None,
    }
    expected_digest = f"sha256:{hashlib.sha256(b'report.pdf').hexdigest()}"
    response = client.post("/api/register-asset", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["asset"]["sha256_digest"] == expected_digest


def test_cloverleaf_score_calculator_qualified():
    payload = {"tech": 48, "market": 65, "comm": 46, "mgmt": 44}
    response = client.post("/api/calculate-cloverleaf", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_score"] == 203
    assert data["is_investment_grade"] is True
    assert "INVESTMENT-READY" in data["status_label"]


def test_cloverleaf_score_calculator_under_qualified():
    payload = {"tech": 20, "market": 30, "comm": 20, "mgmt": 20}
    response = client.post("/api/calculate-cloverleaf", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_score"] == 90
    assert data["is_investment_grade"] is False
    assert "DEVELOPMENT REQUIRED" in data["status_label"]


def test_revenue_split_calculator_decimal_exactness():
    payload = {"amount": "500000.00", "revenue_type": "licensing"}
    response = client.post("/api/calculate-revenue", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_ingested_myr"] == 500000.0
    splits = data["distribution_splits"]
    assert len(splits) == 4
    amounts = [s["amount_myr"] for s in splits]
    assert amounts == [150000.0, 100000.0, 150000.0, 100000.0]
    assert sum(amounts) == 500000.0


def test_revenue_split_calculator_invalid_type_rejected():
    payload = {"amount": "500000.00", "revenue_type": "invalid_stream_type"}
    response = client.post("/api/calculate-revenue", json=payload)
    assert response.status_code == 422


def test_investor_data_room_authentication():
    # Unauthenticated request (no auth header) -> 401
    res_unauth = client.get("/api/investor-assets")
    assert res_unauth.status_code == 401

    # Unauthorized token request -> 403
    res_forbidden = client.get(
        "/api/investor-assets", headers={"Authorization": "Bearer unauthorized"}
    )
    assert res_forbidden.status_code == 403

    # Valid accredited investor token -> 200
    res_ok = client.get(
        "/api/investor-assets", headers={"Authorization": "Bearer valid_investor_token_123"}
    )
    assert res_ok.status_code == 200
    data = res_ok.json()
    assert "data_room_assets" in data
    assert len(data["data_room_assets"]) >= 2


def test_render_yaml_validity():
    render_yaml = ROOT_DIR / "render.yaml"
    assert render_yaml.exists()
    text = render_yaml.read_text(encoding="utf-8")
    assert "runtime: python" in text
    assert 'buildCommand: "uv sync"' in text
    assert "uvicorn src.dca_service.web_app:app" in text
    assert "PYTHON_VERSION" in text


def test_how_to_render_deployment_doc_okf_frontmatter():
    doc_path = ROOT_DIR / "docs" / "how-to" / "deploy-rcf-dac-web-app-on-render.md"
    assert doc_path.exists()
    text = doc_path.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert 'okf_version: "0.2"' in text
    assert 'type: "howto"' in text
    assert "Deploying the RCF & DAC Interactive Web Application on Render.com" in text
    assert "```text" in text
    assert "```bash" in text
    assert "low-latency" in text
    assert "typed validation" in text
    assert "Interactive API documentation" in text
    assert "users must include `uv sync` explicitly" in text
