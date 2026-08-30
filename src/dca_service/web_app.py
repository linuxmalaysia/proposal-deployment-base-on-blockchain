"""
Digital Research Asset Custodian (DAC) & Research Commercialisation Fund (RCF)
FastAPI Web Application Adapter & Service Entry Point.

Governed by DSOM Protocol // OKF v0.2 Standard // Concentric Clean Architecture.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
import os
import time
import uuid
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field, field_validator

# Initialise FastAPI web application instance
app = FastAPI(
    title="RCF & DAC Interactive Web Portal",
    description="Research Commercialisation Fund & Digital Asset Custodian Service API",
    version="0.1.0",
)

# Root directory pathing
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = BASE_DIR / "assets"
DOCS_DIR = BASE_DIR / "docs"

if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

# Mandatory JWT secret lookup (fails closed if environment variable is missing)
_jwt_secret_env = os.environ.get("INVESTOR_JWT_SECRET")
if not _jwt_secret_env:
    raise RuntimeError("FATAL: Missing required environment variable 'INVESTOR_JWT_SECRET'")
INVESTOR_JWT_SECRET = _jwt_secret_env.encode()

# Module-level expected claims constants
EXPECTED_ISSUER = "https://auth.rcf-dac.univ.edu.my"
EXPECTED_AUDIENCE = "rcf-dac-data-room"

# In-memory storage for demonstration / web service operation
USER_REGISTRY: Dict[str, Dict[str, Any]] = {}
ASSET_REGISTRY: Dict[str, Dict[str, Any]] = {}

RevenueType = Literal["royalties", "licensing", "equity", "dividend"]
ContentEncoding = Literal["base64", "raw", "text"]


# --- Helper Cryptographic Utilities ---

def base64url_encode(data: bytes) -> str:
    """Encode bytes to URL-safe Base64 without trailing '=' padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def base64url_decode(encoded_str: str) -> bytes:
    """Decode URL-safe Base64 string with optional missing padding restored."""
    padded = encoded_str + "=" * (-len(encoded_str) % 4)
    return base64.urlsafe_b64decode(padded.encode())


# --- Pydantic Request Models ---

class UserRegistrationRequest(BaseModel):
    name: str = Field(..., description="Full Name and Title")
    role: str = Field(..., description="Institutional Role")
    dept: str = Field(..., description="Faculty or Centre of Excellence")
    email: EmailStr = Field(..., description="Institutional Email Address")


class AssetRegistrationRequest(BaseModel):
    title: str = Field(..., description="Research Project or Prototype Title")
    trl: int = Field(..., ge=1, le=9, description="Technology Readiness Level (1-9)")
    abstract: str = Field(..., description="Scientific Abstract & Innovation Summary")
    file_name: str = Field(..., description="Evidentiary File Reference Name")
    file_content: Optional[str] = Field(None, description="Raw file payload or base64 representation")
    content_encoding: Optional[ContentEncoding] = Field(
        None, description="Explicit content encoding: base64, raw, or text"
    )


class CloverleafScoreRequest(BaseModel):
    tech: int = Field(48, ge=0, le=60, description="Technology Strengths Score (Max 60)")
    market: int = Field(65, ge=0, le=80, description="Market Attractiveness Score (Max 80)")
    comm: int = Field(46, ge=0, le=60, description="Commercialisation Avenues Score (Max 60)")
    mgmt: int = Field(44, ge=0, le=60, description="Management & Execution Score (Max 60)")


class RevenueSplitRequest(BaseModel):
    amount: Decimal = Field(
        Decimal("500000.00"),
        ge=Decimal("0.00"),
        description="Total Ingested Revenue (MYR)",
    )
    revenue_type: RevenueType = Field(
        "licensing",
        description="Type of revenue stream: royalties, licensing, equity, or dividend",
    )

    @field_validator("amount")
    @classmethod
    def validate_max_two_decimal_places(cls, v: Decimal) -> Decimal:
        if v.as_tuple().exponent < -2:
            raise ValueError("Monetary amount cannot have more than two decimal places.")
        return v


# --- API Endpoints ---

@app.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint for Render service monitoring."""
    return {"status": "ok", "service": "rcf-dac-web-app", "version": "0.1.0"}


@app.post("/api/register-user", status_code=status.HTTP_201_CREATED)
def register_user(req: UserRegistrationRequest) -> Dict[str, Any]:
    """Mint W3C Decentralised Identifier (DID) and register institutional user."""
    unique_nonce = uuid.uuid4()
    seed_str = f"{req.name}-{req.role}-{req.dept}-{time.time()}-{unique_nonce}"
    did_hash = hashlib.sha256(seed_str.encode()).hexdigest()[:16]
    did = f"did:univ:{did_hash}"

    record = {
        "name": req.name,
        "role": req.role,
        "dept": req.dept,
        "email": req.email,
        "did": did,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    USER_REGISTRY[did] = record
    return {
        "message": "User identity registered & W3C DID minted",
        "user": record,
        "simulated_db_table": "percona_postgresql_16.users",
    }


@app.post("/api/register-asset", status_code=status.HTTP_201_CREATED)
def register_asset(req: AssetRegistrationRequest) -> Dict[str, Any]:
    """Register research asset and generate SHA-256 evidence vault hash."""
    if req.file_content is not None:
        if req.content_encoding == "base64":
            try:
                file_bytes = base64.b64decode(req.file_content, validate=True)
            except Exception as err:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid Base64 file_content payload: {err}",
                )
        else:
            file_bytes = req.file_content.encode()
    else:
        fallback_str = req.file_name if req.file_name else req.title
        file_bytes = fallback_str.encode()

    sha256_digest = f"sha256:{hashlib.sha256(file_bytes).hexdigest()}"

    asset_seed = f"{req.title}-{req.abstract}-{req.trl}-{time.time()}-{uuid.uuid4()}"
    asset_id_hash = hashlib.sha256(asset_seed.encode()).hexdigest()[:12]
    asset_id = f"did:univ:asset-{asset_id_hash}"
    tx_outbox_id = f"outbox_tx_{int(time.time() * 1000) % 1000000}"

    asset_record = {
        "asset_id": asset_id,
        "title": req.title,
        "trl": req.trl,
        "abstract": req.abstract,
        "file_name": req.file_name,
        "sha256_digest": sha256_digest,
        "tx_outbox_id": tx_outbox_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    ASSET_REGISTRY[asset_id] = asset_record
    return {
        "message": "Digital Research Asset registered in evidence vault",
        "asset": asset_record,
        "outbox_status": "QUEUED_PERCONA_TIMESCALEDB_OUTBOX",
    }


@app.post("/api/calculate-cloverleaf")
def calculate_cloverleaf(req: CloverleafScoreRequest) -> Dict[str, Any]:
    """Calculate Cloverleaf Market Readiness Score (MRS) (>180 qualification target)."""
    total_score = req.tech + req.market + req.comm + req.mgmt
    max_score = 260
    is_qualified = total_score > 180

    if is_qualified:
        funding_tier = "Tier 1 PoC Kickstarter Grant (RM 50,000 - RM 250,000)"
        status_label = "INVESTMENT-READY (Score > 180)"
    else:
        funding_tier = "Requires laboratory TRL escalation & market sizing refinement"
        status_label = f"DEVELOPMENT REQUIRED (Score {total_score} <= 180 Target)"

    return {
        "breakdown": {
            "tech_strengths": {"score": req.tech, "max": 60, "min_target": 42},
            "market_attractiveness": {"score": req.market, "max": 80, "min_target": 55},
            "commercialisation_avenues": {"score": req.comm, "max": 60, "min_target": 42},
            "management_execution": {"score": req.mgmt, "max": 60, "min_target": 41},
        },
        "total_score": total_score,
        "max_score": max_score,
        "is_investment_grade": is_qualified,
        "status_label": status_label,
        "rcf_funding_tier": funding_tier,
    }


@app.post("/api/calculate-revenue")
def calculate_revenue(req: RevenueSplitRequest) -> Dict[str, Any]:
    """Calculate IP policy revenue-split matrix across institutional stakeholders."""
    amount = max(Decimal("0.00"), req.amount)
    rev_type = req.revenue_type.lower()

    if rev_type == "royalties":
        percentages = [Decimal("0.333"), Decimal("0.333"), Decimal("0.334"), Decimal("0.000")]
    elif rev_type == "equity":
        percentages = [Decimal("0.35"), Decimal("0.10"), Decimal("0.25"), Decimal("0.30")]
    elif rev_type == "dividend":
        percentages = [Decimal("0.25"), Decimal("0.15"), Decimal("0.30"), Decimal("0.30")]
    elif rev_type == "licensing":
        percentages = [Decimal("0.30"), Decimal("0.20"), Decimal("0.30"), Decimal("0.20")]
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported revenue type: {req.revenue_type}",
        )

    stakeholders = [
        ("🏛️ Central University Treasury", percentages[0]),
        ("🔬 Originating Dept / Lab", percentages[1]),
        ("👩‍🔬 Lead Inventors & Team", percentages[2]),
        ("🚀 RCF Re-investment Fund", percentages[3]),
    ]

    allocations = []
    total_allocated = Decimal("0.00")

    for name, pct in stakeholders:
        alloc = (amount * pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        allocations.append(alloc)
        total_allocated += alloc

    remainder = amount - total_allocated
    if remainder != Decimal("0.00"):
        target_idx = 3 if percentages[3] > Decimal("0") else 0
        allocations[target_idx] += remainder

    splits = [
        {
            "stakeholder": name,
            "percentage": str((pct * Decimal("100")).quantize(Decimal("0.1"))),
            "amount_myr": str(alloc.quantize(Decimal("0.01"))),
            "amount_minor_units": int(alloc * 100),
        }
        for (name, pct), alloc in zip(stakeholders, allocations)
    ]

    return {
        "revenue_type": rev_type,
        "total_ingested_myr": str(amount.quantize(Decimal("0.01"))),
        "total_ingested_minor_units": int(amount * 100),
        "distribution_splits": splits,
    }


def verify_investor_bearer_token(
    token: str, secret: bytes = INVESTOR_JWT_SECRET
) -> Dict[str, Any]:
    """
    Perform cryptographic HMAC-SHA256 verification and claims check on investor Bearer tokens.
    Rejects opaque, malformed, unsigned, forged, expired, non-dict, or missing claim tokens.
    """
    if not token or not isinstance(token, str):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Invalid or missing token string.",
        )

    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Token is opaque or malformed non-JWT structure.",
        )

    header_b64, payload_b64, sig_b64 = parts

    # Verify HMAC-SHA256 signature
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected_sig = base64url_encode(hmac.new(secret, signing_input, hashlib.sha256).digest())

    if not hmac.compare_digest(sig_b64, expected_sig):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Invalid or forged token signature.",
        )

    # Decode and parse payload claims
    try:
        payload_bytes = base64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode())
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Unparseable or malformed JWT payload.",
        ) from None

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. JWT payload must be a JSON object.",
        )

    # Validate required claims
    if "exp" not in payload:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Missing required 'exp' expiration claim.",
        )

    exp_val = payload["exp"]
    if not isinstance(exp_val, (int, float)) or isinstance(exp_val, bool) or not math.isfinite(exp_val):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. 'exp' claim must be a finite numeric value.",
        )

    if exp_val < time.time():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Token has expired.",
        )

    if payload.get("iss") != EXPECTED_ISSUER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Missing or untrusted token issuer ('iss').",
        )

    if payload.get("aud") != EXPECTED_AUDIENCE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Missing or invalid token audience ('aud').",
        )

    if not payload.get("accredited_investor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Missing required 'accredited_investor' claim.",
        )

    return payload


@app.get("/api/investor-assets")
def get_investor_assets(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> Dict[str, Any]:
    """Retrieve NDA-gated data room listings for accredited investors."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing or invalid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split("Bearer ", 1)[1].strip()
    verify_investor_bearer_token(token)

    default_listings = [
        {
            "asset_id": "did:univ:asset-9f82a1",
            "title": "Graphene Solid State Battery Cell",
            "trl": 3,
            "cloverleaf_score": 203,
            "max_score": 260,
            "funding_tier": "Tier 1 PoC Grant (RM 150,000)",
            "status": "Cleared for Fund",
        },
        {
            "asset_id": "did:univ:asset-4b12c8",
            "title": "AI Diagnostic Bio-Chip Array",
            "trl": 5,
            "cloverleaf_score": 218,
            "max_score": 260,
            "funding_tier": "Tier 2 Co-Investment VC (RM 2.5M)",
            "status": "Cleared for Fund",
        },
    ]
    registered = list(ASSET_REGISTRY.values())
    return {
        "data_room_assets": default_listings,
        "user_registered_assets": registered,
        "access_level": "Accredited VC / Corporate Partner NDA Gated",
    }


def render_markdown_to_html(md_text: str) -> str:
    """Simple parser to convert index.md markdown elements to clean HTML."""
    import re

    # Strip Liquid tags like {::options ... /}
    md_text = re.sub(r"\{::options.*?\/\}", "", md_text)

    # Convert horizontal rules
    md_text = re.sub(r"^---$", "<hr>", md_text, flags=re.MULTILINE)

    # Convert headers (###, ##, #)
    md_text = re.sub(r"^### (.*)$", r"<h3>\1</h3>", md_text, flags=re.MULTILINE)
    md_text = re.sub(r"^## (.*)$", r"<h2>\1</h2>", md_text, flags=re.MULTILINE)
    md_text = re.sub(r"^# (.*)$", r"<h1>\1</h1>", md_text, flags=re.MULTILINE)

    # Convert bold text **text**
    md_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", md_text)

    # Convert markdown links [text](url)
    md_text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', md_text)

    # Convert bullet lists - text
    lines = md_text.splitlines()
    html_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            item_text = stripped[2:]
            html_lines.append(f"  <li>{item_text}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(line)

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


@app.get("/docs/{file_path:path}", response_class=HTMLResponse)
def serve_docs(file_path: str) -> HTMLResponse:
    """Serve documentation Markdown files rendered as HTML."""
    target_path = file_path
    if target_path.endswith(".html"):
        target_path = target_path[:-5] + ".md"
    elif not target_path.endswith(".md"):
        target_path = target_path + ".md"

    doc_file = (DOCS_DIR / target_path).resolve()

    # Prevent path traversal outside of DOCS_DIR
    try:
        doc_file.relative_to(DOCS_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documentation page not found")

    if not doc_file.exists() or not doc_file.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documentation page not found")

    content = doc_file.read_text(encoding="utf-8")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2]

    rendered_html = render_markdown_to_html(content)

    html_wrapper = f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="UTF-8">
  <title>RCF & DAC Documentation</title>
  <link rel="stylesheet" href="/assets/css/style.css">
  <script src="/assets/js/rcf-dac-app.js" defer></script>
</head>
<body>
  <div class="container">
    <p style="margin-bottom: 1.5rem;"><a href="/">&larr; Return to RCF & DAC Interactive Portal Homepage</a></p>
    {rendered_html}
  </div>
</body>
</html>"""
    return HTMLResponse(content=html_wrapper)


@app.get("/", response_class=HTMLResponse)
def serve_index() -> HTMLResponse:
    """Serve interactive web application HTML homepage."""
    index_file = BASE_DIR / "index.md"
    if index_file.exists():
        content = index_file.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2]

        rendered_html = render_markdown_to_html(content)

        html_wrapper = f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="UTF-8">
  <title>RCF & DAC Interactive Web Portal</title>
  <link rel="stylesheet" href="/assets/css/style.css">
  <script src="/assets/js/rcf-dac-app.js" defer></script>
</head>
<body>
  <div class="container">
    {rendered_html}
  </div>
</body>
</html>"""
        return HTMLResponse(content=html_wrapper)
    return HTMLResponse("<h1>RCF & DAC Web Application Service Online</h1>")
