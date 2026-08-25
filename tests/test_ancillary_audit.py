"""Tests for ancillary rails and immutable audit logger."""

from decimal import Decimal
from dca_service.core.ancillary_audit import (
    AuditLogger,
    StakingDelegation,
    TokenizedCollateralAsset,
)


def test_audit_logger_event_immutability():
    logger = AuditLogger()
    logger.log(
        event_id="e1",
        action="DEPOSIT",
        actor_id="client-1",
        details={"amount": "100.0", "asset": "USDC"}
    )

    events = logger.get_events()
    assert len(events) == 1
    assert events[0].event_id == "e1"
    assert events[0].action == "DEPOSIT"


def test_tokenized_collateral_valuation():
    asset = TokenizedCollateralAsset(
        asset_id="rwa-1",
        client_id="client-corp",
        token_symbol="USD-TBILL",
        total_supply=Decimal("1000000.00"),
        underlying_rwa_valuation=Decimal("1050000.00")
    )
    assert asset.is_fully_collateralised()

    under_collateralised = TokenizedCollateralAsset(
        asset_id="rwa-2",
        client_id="client-corp",
        token_symbol="USD-TBILL",
        total_supply=Decimal("1000000.00"),
        underlying_rwa_valuation=Decimal("950000.00")
    )
    assert not under_collateralised.is_fully_collateralised()
