"""Tests for transaction policy engine enforcement."""

from decimal import Decimal
import pytest
from dca_service.core.policy_engine import (
    TransactionProposal,
    PolicyRule,
    PolicyViolationError,
)


def test_policy_allowlist_enforcement():
    rule = PolicyRule(
        rule_id="rule-1",
        max_amount_per_tx=Decimal("100.0"),
        daily_velocity_limit=Decimal("500.0"),
        required_approvers_count=1,
        allowlisted_addresses={"0xAPPROVED"}
    )

    prop_valid = TransactionProposal(
        proposal_id="p1",
        client_id="c1",
        destination_address="0xAPPROVED",
        amount=Decimal("10.0"),
        asset_symbol="ETH",
        signers={"user1"}
    )
    rule.evaluate(prop_valid)  # Should pass without error

    prop_blocked = TransactionProposal(
        proposal_id="p2",
        client_id="c1",
        destination_address="0xUNAPPROVED",
        amount=Decimal("10.0"),
        asset_symbol="ETH",
        signers={"user1"}
    )
    with pytest.raises(PolicyViolationError, match="not on the allowlist"):
        rule.evaluate(prop_blocked)


def test_policy_velocity_limit_enforcement():
    rule = PolicyRule(
        rule_id="rule-2",
        max_amount_per_tx=Decimal("100.0"),
        daily_velocity_limit=Decimal("150.0"),
        required_approvers_count=1
    )

    prop = TransactionProposal(
        proposal_id="p1",
        client_id="c1",
        destination_address="0xANY",
        amount=Decimal("90.0"),
        asset_symbol="USDT",
        signers={"user1"}
    )
    rule.evaluate(prop)
    rule.record_execution(Decimal("90.0"))

    # Second tx exceeding daily accum limit
    prop2 = TransactionProposal(
        proposal_id="p2",
        client_id="c1",
        destination_address="0xANY",
        amount=Decimal("70.0"),
        asset_symbol="USDT",
        signers={"user1"}
    )
    with pytest.raises(PolicyViolationError, match="causes daily velocity to exceed limit"):
        rule.evaluate(prop2)


def test_policy_quorum_enforcement():
    rule = PolicyRule(
        rule_id="rule-3",
        max_amount_per_tx=Decimal("1000.0"),
        daily_velocity_limit=Decimal("5000.0"),
        required_approvers_count=2
    )

    prop_insufficient = TransactionProposal(
        proposal_id="p1",
        client_id="c1",
        destination_address="0xANY",
        amount=Decimal("50.0"),
        asset_symbol="BTC",
        signers={"user1"}
    )
    with pytest.raises(PolicyViolationError, match="Signer quorum requirement not met"):
        rule.evaluate(prop_insufficient)
