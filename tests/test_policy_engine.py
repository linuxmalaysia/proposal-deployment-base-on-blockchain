"""Tests for transaction policy engine enforcement."""

from decimal import Decimal
import pytest
from dca_service.core.policy_engine import (
    TransactionProposal,
    PolicyRule,
    PolicyViolationError,
)


def test_transaction_proposal_positive_amount():
    with pytest.raises(ValueError, match="strictly greater than zero"):
        TransactionProposal(
            proposal_id="p0",
            client_id="c1",
            destination_address="0xANY",
            amount=Decimal("0.0"),
            asset_symbol="USDT"
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
    rule.evaluate(prop_valid)
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


def test_policy_record_execution_positive_amount():
    rule = PolicyRule(
        rule_id="rule-x",
        max_amount_per_tx=Decimal("100.0"),
        daily_velocity_limit=Decimal("500.0"),
        required_approvers_count=1
    )
    with pytest.raises(ValueError, match="strictly greater than zero"):
        rule.record_execution(Decimal("-10.0"))
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


def test_policy_max_amount_per_tx_boundary_is_allowed():
    rule = PolicyRule(
        rule_id="rule-4",
        max_amount_per_tx=Decimal("100.0"),
        daily_velocity_limit=Decimal("100.0"),
        required_approvers_count=1,
    )

    prop = TransactionProposal(
        proposal_id="p1",
        client_id="c1",
        destination_address="0xANY",
        amount=Decimal("100.0"),
        asset_symbol="BTC",
        signers={"user1"},
    )
    rule.evaluate(prop)  # Exactly at the limit should be allowed, not raise.


def test_policy_max_amount_per_tx_exceeded_raises():
    rule = PolicyRule(
        rule_id="rule-5",
        max_amount_per_tx=Decimal("100.0"),
        daily_velocity_limit=Decimal("1000.0"),
        required_approvers_count=1,
    )

    prop = TransactionProposal(
        proposal_id="p1",
        client_id="c1",
        destination_address="0xANY",
        amount=Decimal("100.01"),
        asset_symbol="BTC",
        signers={"user1"},
    )
    with pytest.raises(PolicyViolationError, match="exceeds max single limit"):
        rule.evaluate(prop)


def test_policy_empty_allowlist_permits_any_destination():
    rule = PolicyRule(
        rule_id="rule-6",
        max_amount_per_tx=Decimal("100.0"),
        daily_velocity_limit=Decimal("100.0"),
        required_approvers_count=1,
        allowlisted_addresses=set(),
    )

    prop = TransactionProposal(
        proposal_id="p1",
        client_id="c1",
        destination_address="0xANYTHING",
        amount=Decimal("10.0"),
        asset_symbol="ETH",
        signers={"user1"},
    )
    rule.evaluate(prop)  # No allowlist configured means any destination is valid.


def test_record_execution_accumulates_across_multiple_calls():
    rule = PolicyRule(
        rule_id="rule-7",
        max_amount_per_tx=Decimal("1000.0"),
        daily_velocity_limit=Decimal("150.0"),
        required_approvers_count=1,
    )

    rule.record_execution(Decimal("50.0"))
    rule.record_execution(Decimal("50.0"))
    assert rule.current_daily_accumulated == Decimal("100.0")

    prop = TransactionProposal(
        proposal_id="p1",
        client_id="c1",
        destination_address="0xANY",
        amount=Decimal("50.0"),
        asset_symbol="USDT",
        signers={"user1"},
    )
    rule.evaluate(prop)  # 100 + 50 == 150, exactly at the daily limit, should pass.

    rule.record_execution(Decimal("50.0"))
    assert rule.current_daily_accumulated == Decimal("150.0")

    with pytest.raises(PolicyViolationError, match="causes daily velocity to exceed limit"):
        rule.evaluate(prop)


def test_policy_checks_are_evaluated_in_priority_order():
    """Allowlist violations should be reported even when other limits are also breached."""
    rule = PolicyRule(
        rule_id="rule-8",
        max_amount_per_tx=Decimal("10.0"),
        daily_velocity_limit=Decimal("10.0"),
        required_approvers_count=5,
        allowlisted_addresses={"0xAPPROVED"},
    )

    prop = TransactionProposal(
        proposal_id="p1",
        client_id="c1",
        destination_address="0xNOTLISTED",
        amount=Decimal("9999.0"),
        asset_symbol="BTC",
        signers=set(),
    )
    with pytest.raises(PolicyViolationError, match="not on the allowlist"):
        rule.evaluate(prop)
