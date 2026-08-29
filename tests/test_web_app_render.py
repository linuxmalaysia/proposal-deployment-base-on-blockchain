"""
Unit & Integration Tests for RCF & DAC FastAPI Web Application & Render Deployment.

Governed by DSOM Protocol // OKF v0.2 Standard.
"""

from __future__ import annotations

from pathlib import Path
from fastapi.testclient import TestClient
from dca_service.web_app import app

client = TestClient(app)
ROOT_DIR = Path(__file__).resolve().parent.parent


def test_health_check_endpoint():
    """Verify health check endpoint returns correct status and service metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "rcf-dac-web-app"


def test_user_registration_endpoint():
    """Verify user registration endpoint mints W3C DID and stores user record."""
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


def test_asset_registration_endpoint():
    """Verify asset registration endpoint generates SHA-256 digest and asset DID."""
    payload = {
        "title": "Graphene-Enhanced Solid State Lithium-Air Battery Cell",
        "trl": 3,
        "abstract": "Energy density exceeding 650 Wh/kg with 1,500 cycle life.",
        "file_name": "battery_lab_test_report.pdf",
        "file_content": "simulated_binary_data_report_content",
    }
    response = client.post("/api/register-asset", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "asset" in data
    assert data["asset"]["asset_id"].startswith("did:univ:asset-")
    assert data["asset"]["sha256_digest"].startswith("sha256:")


def test_cloverleaf_score_calculator_qualified():
    """Verify Cloverleaf calculator identifies investment-ready projects above threshold."""
    payload = {"tech": 48, "market": 65, "comm": 46, "mgmt": 44}
    response = client.post("/api/calculate-cloverleaf", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_score"] == 203
    assert data["is_investment_grade"] is True
    assert "INVESTMENT-READY" in data["status_label"]


def test_cloverleaf_score_calculator_under_qualified():
    """Verify Cloverleaf calculator flags projects requiring development below threshold."""
    payload = {"tech": 20, "market": 30, "comm": 20, "mgmt": 20}
    response = client.post("/api/calculate-cloverleaf", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_score"] == 90
    assert data["is_investment_grade"] is False
    assert "DEVELOPMENT REQUIRED" in data["status_label"]


def test_revenue_split_calculator():
    """Verify revenue split calculator applies correct policy-based distribution percentages."""
    payload = {"amount": 500000.0, "revenue_type": "licensing"}
    response = client.post("/api/calculate-revenue", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_ingested_myr"] == 500000.0
    splits = data["distribution_splits"]
    assert len(splits) == 4
    # Check Licensing split: 30% Treasury, 20% Dept, 30% Inventor, 20% RCF
    amounts = [s["amount_myr"] for s in splits]
    assert amounts == [150000.0, 100000.0, 150000.0, 100000.0]


def test_investor_data_room_endpoint():
    """Verify investor data room endpoint returns NDA-gated asset listings."""
    response = client.get("/api/investor-assets")
    assert response.status_code == 200
    data = response.json()
    assert "data_room_assets" in data
    assert len(data["data_room_assets"]) >= 2


def test_render_yaml_validity():
    """Verify Render deployment configuration contains required runtime and build settings."""
    render_yaml = ROOT_DIR / "render.yaml"
    assert render_yaml.exists()
    text = render_yaml.read_text(encoding="utf-8")
    assert "runtime: python" in text
    assert "buildCommand: \"uv sync\"" in text
    assert "uvicorn src.dca_service.web_app:app" in text
    assert "PYTHON_VERSION" in text


def test_how_to_render_deployment_doc_okf_frontmatter():
    """Verify Render deployment documentation contains valid OKF v0.2 frontmatter metadata."""
    doc_path = ROOT_DIR / "docs" / "how-to" / "deploy-rcf-dac-web-app-on-render.md"
    assert doc_path.exists()
    text = doc_path.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert 'okf_version: "0.2"' in text
    assert 'type: "howto"' in text
    assert "Deploying the RCF & DAC Interactive Web Application on Render.com" in text
