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


def test_transaction_proposal_duplicate_signers_rejected():
    with pytest.raises(ValueError, match="Duplicate signers detected"):
        TransactionProposal(
            proposal_id="p_dup",
            client_id="c1",
            destination_address="0xANY",
            amount=Decimal("10.0"),
            asset_symbol="ETH",
            signers=["signer1", "signer1"]
        )


def test_transaction_proposal_empty_signer_identity_rejected():
    with pytest.raises(ValueError, match="non-empty string"):
        TransactionProposal(
            proposal_id="p_empty",
            client_id="c1",
            destination_address="0xANY",
            amount=Decimal("10.0"),
            asset_symbol="ETH",
            signers=["   "]
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
        signers=["user1"]
    )
    rule.evaluate(prop_valid)

    prop_blocked = TransactionProposal(
        proposal_id="p2",
        client_id="c1",
        destination_address="0xUNAPPROVED",
        amount=Decimal("10.0"),
        asset_symbol="ETH",
        signers=["user1"]
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
        signers=["user1"]
    )
    rule.evaluate(prop)
    rule.record_execution(Decimal("90.0"))

    prop2 = TransactionProposal(
        proposal_id="p2",
        client_id="c1",
        destination_address="0xANY",
        amount=Decimal("70.0"),
        asset_symbol="USDT",
        signers=["user1"]
    )
    with pytest.raises(PolicyViolationError, match="causes daily velocity to exceed limit"):
        rule.evaluate(prop2)


def test_policy_unauthenticated_signer_rejected():
    rule = PolicyRule(
        rule_id="rule-auth",
        max_amount_per_tx=Decimal("100.0"),
        daily_velocity_limit=Decimal("500.0"),
        required_approvers_count=1,
        authenticated_signers={"user1"}
    )

    prop_unauth = TransactionProposal(
        proposal_id="p_unauth",
        client_id="c1",
        destination_address="0xANY",
        amount=Decimal("10.0"),
        asset_symbol="ETH",
        signers=["user_fake"]
    )
    with pytest.raises(PolicyViolationError, match="unauthenticated"):
        rule.evaluate(prop_unauth)


def test_policy_unauthorized_signer_rejected():
    rule = PolicyRule(
        rule_id="rule-authz",
        max_amount_per_tx=Decimal("100.0"),
        daily_velocity_limit=Decimal("500.0"),
        required_approvers_count=1,
        authorized_signers={"user1", "user2"}
    )

    prop_unauthz = TransactionProposal(
        proposal_id="p_unauthz",
        client_id="c1",
        destination_address="0xANY",
        amount=Decimal("10.0"),
        asset_symbol="ETH",
        signers=["user3"]
    )
    with pytest.raises(PolicyViolationError, match="unauthorized"):
        rule.evaluate(prop_unauthz)


def test_policy_record_execution_positive_amount():
    rule = PolicyRule(
        rule_id="rule-x",
        max_amount_per_tx=Decimal("100.0"),
        daily_velocity_limit=Decimal("500.0"),
        required_approvers_count=1
    )
    with pytest.raises(ValueError, match="strictly greater than zero"):
        rule.record_execution(Decimal("-10.0"))
