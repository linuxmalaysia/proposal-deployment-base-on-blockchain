"""
Unit & Integration Tests for RCF & DAC FastAPI Web Application & Render Deployment.

Governed by DSOM Protocol // OKF v0.2 Standard.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from unittest.mock import patch

# Configure environment secret before importing web_app module
TEST_JWT_SECRET = b"test_rcf_dac_jwt_secret_key_2026"
os.environ["INVESTOR_JWT_SECRET"] = TEST_JWT_SECRET.decode()

from fastapi.testclient import TestClient
from dca_service.web_app import app, USER_REGISTRY, base64url_encode

client = TestClient(app)
ROOT_DIR = Path(__file__).resolve().parent.parent


def create_investor_jwt(
    sub: str = "investor_01",
    exp_delta: float = 3600.0,
    iss: str = "https://auth.rcf-dac.univ.edu.my",
    aud: str = "rcf-dac-data-room",
    *,
    accredited_investor: bool = True,
    custom_exp: Any = None,
    raw_payload: Any = None,
    secret: bytes = TEST_JWT_SECRET,
) -> str:
    """Create a signed HMAC-SHA256 JWT for testing accredited investor authentication."""
    header = {"alg": "HS256", "typ": "JWT"}
    if raw_payload is not None:
        payload_bytes = json.dumps(raw_payload, separators=(",", ":")).encode()
    else:
        exp_val = custom_exp if custom_exp is not None else int(time.time() + exp_delta)
        payload = {
            "sub": sub,
            "iss": iss,
            "aud": aud,
            "exp": exp_val,
            "accredited_investor": accredited_investor,
        }
        payload_bytes = json.dumps(payload, separators=(",", ":")).encode()

    header_b64 = base64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = base64url_encode(payload_bytes)
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(secret, signing_input, hashlib.sha256).digest()
    sig_b64 = base64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "rcf-dac-web-app"


def test_user_registration_endpoint_and_unique_did_generation():
    payload = {
        "name": "Prof. Dr. Harisfazillah Jamel",
        "role": "Lead Principal Investigator (PI)",
        "dept": "Centre of Excellence in DeepTech & Nanotechnology",
        "email": "harisfazillah@university.edu.my",
    }
    # First registration
    res1 = client.post("/api/register-user", json=payload)
    assert res1.status_code == 201
    did1 = res1.json()["user"]["did"]

    # Second registration with identical payload
    res2 = client.post("/api/register-user", json=payload)
    assert res2.status_code == 201
    did2 = res2.json()["user"]["did"]

    # Verify unique DIDs and non-overwriting of USER_REGISTRY
    assert did1 != did2
    assert did1 in USER_REGISTRY
    assert did2 in USER_REGISTRY


def test_asset_registration_base64_explicit_encoding():
    raw_content = b"raw_laboratory_binary_data_stream_content_12345"
    b64_content = base64.b64encode(raw_content).decode("utf-8")
    expected_digest = f"sha256:{hashlib.sha256(raw_content).hexdigest()}"

    payload = {
        "title": "Graphene-Enhanced Solid State Lithium-Air Battery Cell",
        "trl": 3,
        "abstract": "Energy density exceeding 650 Wh/kg with 1,500 cycle life.",
        "file_name": "battery_lab_test_report.pdf",
        "file_content": b64_content,
        "content_encoding": "base64",
    }
    response = client.post("/api/register-asset", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["asset"]["sha256_digest"] == expected_digest


def test_asset_registration_invalid_base64_rejected():
    payload = {
        "title": "Graphene Battery Cell",
        "trl": 3,
        "abstract": "Energy density exceeding 650 Wh/kg.",
        "file_name": "report.pdf",
        "file_content": "invalid_base64_content_!!!",
        "content_encoding": "base64",
    }
    response = client.post("/api/register-asset", json=payload)
    assert response.status_code == 422


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


def test_revenue_split_calculator_decimal_fixed_point_format():
    payload = {"amount": "500000.00", "revenue_type": "licensing"}
    response = client.post("/api/calculate-revenue", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_ingested_myr"] == "500000.00"
    assert data["total_ingested_minor_units"] == 50000000
    splits = data["distribution_splits"]
    assert len(splits) == 4
    amounts = [s["amount_myr"] for s in splits]
    assert amounts == ["150000.00", "100000.00", "150000.00", "100000.00"]


def test_revenue_split_calculator_rejects_more_than_two_decimals():
    payload = {"amount": "500000.123", "revenue_type": "licensing"}
    response = client.post("/api/calculate-revenue", json=payload)
    assert response.status_code == 422


def test_revenue_split_calculator_invalid_type_rejected():
    payload = {"amount": "500000.00", "revenue_type": "invalid_stream_type"}
    response = client.post("/api/calculate-revenue", json=payload)
    assert response.status_code == 422


def test_investor_data_room_opaque_and_forged_token_rejection():
    # Unauthenticated request (no auth header) -> 401
    res_unauth = client.get("/api/investor-assets")
    assert res_unauth.status_code == 401

    # Opaque non-JWT token -> 403
    res_opaque = client.get(
        "/api/investor-assets", headers={"Authorization": "Bearer opaque_random_token_12345"}
    )
    assert res_opaque.status_code == 403

    # Forged 3-part token (invalid signature) -> 403
    jwt = create_investor_jwt()
    parts = jwt.split(".")
    forged_jwt = f"{parts[0]}.{parts[1]}.forged_invalid_signature"
    res_forged = client.get(
        "/api/investor-assets", headers={"Authorization": f"Bearer {forged_jwt}"}
    )
    assert res_forged.status_code == 403


def test_investor_data_room_non_object_and_non_finite_exp_payload_rejection():
    # Non-object payload (JSON array) -> 403
    array_payload_jwt = create_investor_jwt(raw_payload=["invalid", "array", "payload"])
    res_array = client.get(
        "/api/investor-assets", headers={"Authorization": f"Bearer {array_payload_jwt}"}
    )
    assert res_array.status_code == 403
    assert "object" in res_array.json()["detail"].lower()

    # Non-numeric string exp claim -> 403
    str_exp_jwt = create_investor_jwt(custom_exp="2026-12-31T23:59:59Z")
    res_str_exp = client.get(
        "/api/investor-assets", headers={"Authorization": f"Bearer {str_exp_jwt}"}
    )
    assert res_str_exp.status_code == 403
    assert "finite numeric" in res_str_exp.json()["detail"].lower()

    # Boolean exp claim -> 403
    bool_exp_jwt = create_investor_jwt(custom_exp=True)
    res_bool_exp = client.get(
        "/api/investor-assets", headers={"Authorization": f"Bearer {bool_exp_jwt}"}
    )
    assert res_bool_exp.status_code == 403
    assert "finite numeric" in res_bool_exp.json()["detail"].lower()


def test_investor_data_room_valid_cryptographic_jwt():
    # Valid signed JWT -> 200
    valid_jwt = create_investor_jwt(sub="accredited_vc_01")
    res_ok = client.get(
        "/api/investor-assets", headers={"Authorization": f"Bearer {valid_jwt}"}
    )
    assert res_ok.status_code == 200
    data = res_ok.json()
    assert "data_room_assets" in data
    assert len(data["data_room_assets"]) >= 2


def test_investor_data_room_untrusted_issuer_and_invalid_audience_rejected():
    # Untrusted issuer -> 403
    untrusted_iss_jwt = create_investor_jwt(iss="https://untrusted.attacker.com")
    res_iss = client.get(
        "/api/investor-assets", headers={"Authorization": f"Bearer {untrusted_iss_jwt}"}
    )
    assert res_iss.status_code == 403
    assert "issuer" in res_iss.json()["detail"].lower()

    # Invalid audience -> 403
    invalid_aud_jwt = create_investor_jwt(aud="wrong-data-room")
    res_aud = client.get(
        "/api/investor-assets", headers={"Authorization": f"Bearer {invalid_aud_jwt}"}
    )
    assert res_aud.status_code == 403
    assert "audience" in res_aud.json()["detail"].lower()


def test_investor_data_room_expired_or_unaccredited_token():
    # Expired token -> 403
    expired_jwt = create_investor_jwt(exp_delta=-3600.0)
    res_exp = client.get("/api/investor-assets", headers={"Authorization": f"Bearer {expired_jwt}"})
    assert res_exp.status_code == 403

    # accredited_investor claim is false -> 403
    unaccredited_jwt = create_investor_jwt(accredited_investor=False)
    res_unacc = client.get(
        "/api/investor-assets", headers={"Authorization": f"Bearer {unaccredited_jwt}"}
    )
    assert res_unacc.status_code == 403


def test_render_yaml_validity():
    render_yaml = ROOT_DIR / "render.yaml"
    assert render_yaml.exists()
    text = render_yaml.read_text(encoding="utf-8")
    assert "runtime: python" in text
    assert 'buildCommand: "uv sync"' in text
    assert "uvicorn src.dca_service.web_app:app" in text
    assert "PYTHON_VERSION" in text
    assert "INVESTOR_JWT_SECRET" in text
    assert "generateValue: true" in text


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
    assert "(>=3.12)" in text
    assert "users must include `uv sync` explicitly" in text


def test_serve_documentation_pages_returns_200_ok():
    doc_links = [
        "/docs/explanation/research-commercialisation-fund-dac-proposal",
        "/docs/explanation/rcf-dac-business-case",
        "/docs/explanation/rcf-dac-technical-data-layer",
        "/docs/explanation/rcf-dac-five-phase-process",
        "/docs/explanation/rcf-dac-governance-budget-risks",
        "/docs/explanation/rcf-dac-ecosystem-precedents",
        "/docs/tutorials/web-application-user-guide",
    ]

    for link in doc_links:
        for ext in [".html", ".md"]:
            url = f"{link}{ext}"
            res = client.get(url)
            assert res.status_code == 200, f"Expected 200 for {url}, got {res.status_code}"
            assert "<!DOCTYPE html>" in res.text

    # Path traversal protection test
    res_traversal = client.get("/docs/../../README.md")
    assert res_traversal.status_code == 404

    # Non-existent doc test
    res_404 = client.get("/docs/explanation/non-existent-doc.html")
    assert res_404.status_code == 404


def test_db_status_api_endpoint():
    response = client.get("/api/db-status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "is_connected" in data
    assert "latency_ms" in data
    assert "environment" not in data
    assert "schema_tables" in data
    assert len(data["schema_tables"]) == 5
    table_names = [t["table_name"] for t in data["schema_tables"]]
    assert "users" in table_names
    assert "assets" in table_names
    assert "cloverleaf_scores" in table_names
    assert "revenue_splits" in table_names
    assert "blockchain_transactions" in table_names

    for table in data["schema_tables"]:
        assert table["status"] in (
            "VERIFIED IN POSTGRESQL DB",
            "MISSING IN DATABASE",
            "UNKNOWN (QUERY FAILED)",
            "VERIFIED DDL SCHEMA FILE",
        )


def test_db_status_html_dashboard_pages():
    for route in ["/db-status", "/db-connection"]:
        response = client.get(route)
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text
        assert "Supabase" in response.text
        assert "Database Status" in response.text
        assert "schema.sql" in response.text
        assert "Environment Secret Variables" not in response.text
        assert "SUPABASE_URL" not in response.text


def test_init_db_endpoint_requires_admin_role():
    # 1. Unauthenticated request -> 401
    res_unauth = client.post("/api/init-db")
    assert res_unauth.status_code == 401

    # 2. Accredited non-admin user token -> 403
    user_jwt = create_investor_jwt(sub="accredited_investor_01")
    res_forbidden = client.post(
        "/api/init-db", headers={"Authorization": f"Bearer {user_jwt}"}
    )
    assert res_forbidden.status_code == 403
    assert "administrator role required" in res_forbidden.json()["detail"].lower()

    # 3. Admin user token -> 200 with mocked initialize_database_schema
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": "admin_01",
        "iss": "https://auth.rcf-dac.univ.edu.my",
        "aud": "rcf-dac-data-room",
        "exp": int(time.time() + 3600),
        "accredited_investor": True,
        "admin": True,
    }
    header_b64 = base64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = base64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(TEST_JWT_SECRET, signing_input, hashlib.sha256).digest()
    sig_b64 = base64url_encode(signature)
    admin_jwt = f"{header_b64}.{payload_b64}.{sig_b64}"

    with patch("dca_service.web_app.initialize_database_schema") as mock_init:
        mock_init.return_value = {"success": True, "message": "Mocked DB initialization successful"}
        res_admin = client.post(
            "/api/init-db", headers={"Authorization": f"Bearer {admin_jwt}"}
        )
        assert res_admin.status_code == 200
        assert res_admin.json()["success"] is True
        mock_init.assert_called_once()
