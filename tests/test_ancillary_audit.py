"""Tests for ancillary rails and immutable audit logger."""

from decimal import Decimal
from dca_service.core.ancillary_audit import (
    AuditLogger,
import dataclasses
from decimal import Decimal

import pytest

from dca_service.core.ancillary_audit import (
    AuditEvent,
    AuditLogger,
    StakingDelegation,
    TokenizedCollateralAsset,
)


def test_audit_logger_event_immutability():
    logger = AuditLogger()
    details = {"amount": "100.0", "asset": "USDC"}

    event = logger.log(
        event_id="e1",
        action="DEPOSIT",
        actor_id="client-1",
        details=details
    )

    # Mutate source details dict
    details["amount"] = "999999.0"

    events = logger.get_events()
    assert len(events) == 1
    assert events[0].details["amount"] == "100.0"

    # Mutate retrieved event details
    events[0].details["amount"] = "888888.0"

    events_second_fetch = logger.get_events()
    assert events_second_fetch[0].details["amount"] == "100.0"
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


def test_tokenized_collateral_valuation_exact_boundary():
    exactly_matched = TokenizedCollateralAsset(
        asset_id="rwa-3",
        client_id="client-corp",
        token_symbol="USD-TBILL",
        total_supply=Decimal("500000.00"),
        underlying_rwa_valuation=Decimal("500000.00")
    )
    assert exactly_matched.is_fully_collateralised()


def test_audit_logger_preserves_multiple_events_in_order():
    logger = AuditLogger()
    logger.log(event_id="e1", action="DEPOSIT", actor_id="client-1", details={})
    logger.log(event_id="e2", action="WITHDRAWAL", actor_id="client-1", details={})

    events = logger.get_events()
    assert [e.event_id for e in events] == ["e1", "e2"]
    assert [e.action for e in events] == ["DEPOSIT", "WITHDRAWAL"]


def test_audit_logger_get_events_returns_independent_copy():
    logger = AuditLogger()
    logger.log(event_id="e1", action="DEPOSIT", actor_id="client-1", details={})

    events = logger.get_events()
    events.append("tampered")

    assert len(logger.get_events()) == 1
    assert logger.get_events()[0].event_id == "e1"


def test_audit_event_is_immutable():
    logger = AuditLogger()
    event = logger.log(event_id="e1", action="DEPOSIT", actor_id="client-1", details={"a": 1})

    with pytest.raises(dataclasses.FrozenInstanceError):
        event.action = "TAMPERED"


def test_audit_logger_log_returns_the_created_event():
    logger = AuditLogger()
    details = {"amount": "50.0"}
    event = logger.log(event_id="e1", action="STAKE", actor_id="client-1", details=details)

    assert isinstance(event, AuditEvent)
    assert event.actor_id == "client-1"
    assert event.details == details
    assert event in logger.get_events()


def test_staking_delegation_defaults_to_active():
    delegation = StakingDelegation(
        delegation_id="del-1",
        client_id="client-1",
        validator_address="validator-abc",
        amount=Decimal("100.0"),
        asset_symbol="ETH",
    )
    assert delegation.is_active is True


def test_staking_delegation_can_be_created_inactive():
    delegation = StakingDelegation(
        delegation_id="del-2",
        client_id="client-1",
        validator_address="validator-abc",
        amount=Decimal("100.0"),
        asset_symbol="ETH",
        is_active=False,
    )
    assert delegation.is_active is False
