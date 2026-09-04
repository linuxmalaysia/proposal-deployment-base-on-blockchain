"""Unit tests for static-asset integrity and HTTP response hardening."""

from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("INVESTOR_JWT_SECRET", "test_rcf_dac_jwt_secret_key_2026")

import dca_service.web_app as web_app


client = TestClient(web_app.app)


@pytest.fixture(autouse=True)
def clear_asset_sri_cache() -> None:
    """Keep integrity-cache assertions independent of test execution order."""
    web_app.ASSET_SRI_CACHE.clear()


def _expected_sri(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).digest()
    return f"sha256-{base64.b64encode(digest).decode('utf-8')}"


@pytest.mark.parametrize("asset_path", ["css/style.css", "/assets/css/style.css"])
def test_get_asset_sri_returns_sha256_digest_for_supported_path_styles(asset_path: str) -> None:
    expected = _expected_sri(web_app.ASSETS_DIR / "css" / "style.css")

    integrity = web_app.get_asset_sri(asset_path)

    assert integrity == expected
    algorithm, encoded_digest = integrity.split("-", maxsplit=1)
    assert algorithm == "sha256"
    assert len(base64.b64decode(encoded_digest, validate=True)) == hashlib.sha256().digest_size
    assert web_app.ASSET_SRI_CACHE[asset_path] == expected


@pytest.mark.parametrize("asset_path", ["missing.js", "/assets/missing.js", "css"])
def test_get_asset_sri_returns_empty_string_without_caching_unavailable_assets(asset_path: str) -> None:
    assert web_app.get_asset_sri(asset_path) == ""
    assert asset_path not in web_app.ASSET_SRI_CACHE


def test_get_asset_sri_reuses_cached_digest_after_the_file_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    asset = assets_dir / "bundle.js"
    asset.write_bytes(b"original bundle")
    monkeypatch.setattr(web_app, "BASE_DIR", tmp_path)
    monkeypatch.setattr(web_app, "ASSETS_DIR", assets_dir)

    original_integrity = web_app.get_asset_sri("/assets/bundle.js")
    asset.write_bytes(b"changed bundle")

    assert web_app.get_asset_sri("/assets/bundle.js") == original_integrity
    assert original_integrity == _expected_sri_for_bytes(b"original bundle")


def _expected_sri_for_bytes(content: bytes) -> str:
    digest = hashlib.sha256(content).digest()
    return f"sha256-{base64.b64encode(digest).decode('utf-8')}"


@pytest.mark.parametrize("path", ["/health", "/does-not-exist"])
def test_security_headers_apply_to_successful_and_error_responses(path: str) -> None:
    response = client.get(path, headers={"Accept-Encoding": "identity"})

    assert response.headers["content-security-policy"] == (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"


def test_preload_link_header_is_added_only_to_html_responses() -> None:
    css_sri = _expected_sri(web_app.ASSETS_DIR / "css" / "style.css")
    js_sri = _expected_sri(web_app.ASSETS_DIR / "js" / "rcf-dac-app.js")

    html_login_response = client.get("/login", headers={"Accept-Encoding": "identity"})
    html_root_response = client.get("/", headers={"Accept-Encoding": "identity"})
    json_response = client.get("/health", headers={"Accept-Encoding": "identity"})
    static_response = client.get("/assets/css/style.css", headers={"Accept-Encoding": "identity"})

    assert html_login_response.headers["link"] == (
        f'</assets/css/style.css>; rel=preload; as=style; integrity="{css_sri}"; crossorigin=anonymous'
    )
    assert html_root_response.headers["link"] == (
        f'</assets/css/style.css>; rel=preload; as=style; integrity="{css_sri}"; crossorigin=anonymous, '
        f'</assets/js/rcf-dac-app.js>; rel=preload; as=script; integrity="{js_sri}"; crossorigin=anonymous'
    )
    assert "link" not in json_response.headers
    assert "link" not in static_response.headers


@pytest.mark.parametrize(
    ("path", "includes_javascript"),
    [
        ("/", True),
        ("/docs/explanation/architecture-overview.html", True),
        ("/login", False),
        ("/user-management", False),
    ],
)
def test_rendered_pages_include_preloads_and_matching_integrity_attributes(
    path: str, includes_javascript: bool
) -> None:
    response = client.get(path, headers={"Accept-Encoding": "identity"})
    css_integrity = _expected_sri(web_app.ASSETS_DIR / "css" / "style.css")
    js_integrity = _expected_sri(web_app.ASSETS_DIR / "js" / "rcf-dac-app.js")

    assert response.status_code == 200
    assert '<link rel="preload" href="/assets/css/style.css" as="style" crossorigin="anonymous">' in response.text
    assert (
        f'<link rel="stylesheet" href="/assets/css/style.css" '
        f'integrity="{css_integrity}" crossorigin="anonymous">'
    ) in response.text
    if includes_javascript:
        assert '<link rel="preload" href="/assets/js/rcf-dac-app.js" as="script" crossorigin="anonymous">' in response.text
        assert (
            f'<script src="/assets/js/rcf-dac-app.js" integrity="{js_integrity}" '
            'crossorigin="anonymous" defer></script>'
        ) in response.text
    else:
        assert 'src="/assets/js/rcf-dac-app.js"' not in response.text


@pytest.mark.parametrize(("accepted_encoding", "expected_encoding"), [("gzip", "gzip"), ("br", "br")])
def test_large_html_responses_support_configured_compression(
    accepted_encoding: str, expected_encoding: str
) -> None:
    response = client.get("/", headers={"Accept-Encoding": accepted_encoding})

    assert response.status_code == 200
    assert response.headers["content-encoding"] == expected_encoding
    assert "vary" in response.headers
    assert "Accept-Encoding" in response.headers.get_list("vary")
    assert response.text.startswith("<!DOCTYPE html>")


@pytest.mark.parametrize("asset_path", ["/assets/css/style.css", "/assets/js/rcf-dac-app.js"])
@pytest.mark.parametrize(("accepted_encoding", "expected_encoding"), [("gzip", "gzip"), ("br", "br")])
def test_static_web_assets_support_gzip_and_brotli_compression(
    asset_path: str, accepted_encoding: str, expected_encoding: str
) -> None:
    response = client.get(asset_path, headers={"Accept-Encoding": accepted_encoding})

    assert response.status_code == 200
    assert response.headers["content-encoding"] == expected_encoding
    assert "vary" in response.headers
    assert "Accept-Encoding" in response.headers.get_list("vary")


def test_small_responses_remain_uncompressed_at_minimum_size_boundary() -> None:
    response = client.get("/health", headers={"Accept-Encoding": "gzip, br"})

    assert response.status_code == 200
    assert "content-encoding" not in response.headers
    assert int(response.headers["content-length"]) < 500
