"""
Digital Research Asset Custodian (DAC) & Research Commercialisation Fund (RCF)
FastAPI Web Application Adapter & Service Entry Point.

Governed by DSOM Protocol // OKF v0.2 Standard // Concentric Clean Architecture.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

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

# In-memory storage for demonstration / web service operation
USER_REGISTRY: Dict[str, Dict[str, Any]] = {}
ASSET_REGISTRY: Dict[str, Dict[str, Any]] = {}


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


class CloverleafScoreRequest(BaseModel):
    tech: int = Field(48, ge=0, le=60, description="Technology Strengths Score (Max 60)")
    market: int = Field(65, ge=0, le=80, description="Market Attractiveness Score (Max 80)")
    comm: int = Field(46, ge=0, le=60, description="Commercialisation Avenues Score (Max 60)")
    mgmt: int = Field(44, ge=0, le=60, description="Management & Execution Score (Max 60)")


class RevenueSplitRequest(BaseModel):
    amount: float = Field(500000.0, ge=0.0, description="Total Ingested Revenue (MYR)")
    revenue_type: str = Field(
        "licensing",
        description="Type of revenue stream: royalties, licensing, equity, or dividend",
    )


# --- API Endpoints ---

@app.get("/health")
def health_check() -> Dict[str, str]:
    """Health check endpoint for Render service monitoring."""
    return {"status": "ok", "service": "rcf-dac-web-app", "version": "0.1.0"}


@app.post("/api/register-user", status_code=status.HTTP_201_CREATED)
def register_user(req: UserRegistrationRequest) -> Dict[str, Any]:
    """Mint W3C Decentralised Identifier (DID) and register institutional user."""
    seed_str = f"{req.name}-{req.role}-{req.dept}-{time.time()}"
    did_hash = hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:16]
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
    file_bytes = (req.file_content or req.file_name or req.title).encode("utf-8")
    sha256_digest = f"sha256:{hashlib.sha256(file_bytes).hexdigest()}"

    asset_seed = f"{req.title}-{req.abstract}-{req.trl}-{time.time()}"
    asset_id_hash = hashlib.sha256(asset_seed.encode("utf-8")).hexdigest()[:12]
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
    amount = max(0.0, req.amount)
    rev_type = req.revenue_type.lower()

    if rev_type == "royalties":
        treasury_pct, dept_pct, inventor_pct, rcf_pct = 0.333, 0.333, 0.334, 0.0
    elif rev_type == "equity":
        treasury_pct, dept_pct, inventor_pct, rcf_pct = 0.35, 0.10, 0.25, 0.30
    elif rev_type == "dividend":
        treasury_pct, dept_pct, inventor_pct, rcf_pct = 0.25, 0.15, 0.30, 0.30
    else:  # default 'licensing'
        rev_type = "licensing"
        treasury_pct, dept_pct, inventor_pct, rcf_pct = 0.30, 0.20, 0.30, 0.20

    splits = [
        {
            "stakeholder": "🏛️ Central University Treasury",
            "percentage": round(treasury_pct * 100, 1),
            "amount_myr": round(amount * treasury_pct, 2),
        },
        {
            "stakeholder": "🔬 Originating Dept / Lab",
            "percentage": round(dept_pct * 100, 1),
            "amount_myr": round(amount * dept_pct, 2),
        },
        {
            "stakeholder": "👩‍🔬 Lead Inventors & Team",
            "percentage": round(inventor_pct * 100, 1),
            "amount_myr": round(amount * inventor_pct, 2),
        },
        {
            "stakeholder": "🚀 RCF Re-investment Fund",
            "percentage": round(rcf_pct * 100, 1),
            "amount_myr": round(amount * rcf_pct, 2),
        },
    ]

    return {
        "revenue_type": rev_type,
        "total_ingested_myr": amount,
        "distribution_splits": splits,
    }


@app.get("/api/investor-assets")
def get_investor_assets() -> Dict[str, Any]:
    """Retrieve NDA-gated data room listings for accredited investors."""
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


@app.get("/", response_class=HTMLResponse)
def serve_index() -> HTMLResponse:
    """Serve interactive web application HTML homepage."""
    index_file = BASE_DIR / "index.md"
    if index_file.exists():
        content = index_file.read_text(encoding="utf-8")
        # Strip frontmatter if present for basic HTML rendering wrapper
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2]

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
    {content}
  </div>
</body>
</html>"""
        return HTMLResponse(content=html_wrapper)
    return HTMLResponse("<h1>RCF & DAC Web Application Service Online</h1>")
