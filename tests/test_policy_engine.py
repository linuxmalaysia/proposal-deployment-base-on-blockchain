"""Tests for transaction policy engine enforcement."""

from decimal import Decimal
import pytest
from dca_service.core.policy_engine import (
    TransactionProposal,
    PolicyRule,
    PolicyViolationError,
)


def test_transaction_proposal_positive_amount():
    """Verify transaction proposal rejects zero or negative amounts."""
    with pytest.raises(ValueError, match="strictly greater than zero"):
        TransactionProposal(
            proposal_id="p0",
            client_id="c1",
            destination_address="0xANY",
            amount=Decimal("0.0"),
            asset_symbol="USDT"
        )


def test_transaction_proposal_non_list_signers_rejected():
    """Verify transaction proposal requires signers as list type not set."""
    with pytest.raises(ValueError, match="Signers must be provided as a list"):
        TransactionProposal(
            proposal_id="p_non_list",
            client_id="c1",
            destination_address="0xANY",
            amount=Decimal("10.0"),
            asset_symbol="ETH",
            signers={"signer1"}  # set passed instead of list
        )


def test_transaction_proposal_duplicate_signers_rejected():
    """Verify transaction proposal rejects duplicate signer identities."""
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
    """Verify transaction proposal rejects empty or whitespace-only signer identities."""
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
    """Verify policy rule enforces destination address allowlist restrictions."""
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
    rule.evaluate(prop_valid, verified_authenticated_signers={"user1"})

    prop_blocked = TransactionProposal(
        proposal_id="p2",
        client_id="c1",
        destination_address="0xUNAPPROVED",
        amount=Decimal("10.0"),
        asset_symbol="ETH",
        signers=["user1"]
    )
    with pytest.raises(PolicyViolationError, match="not on the allowlist"):
        rule.evaluate(prop_blocked, verified_authenticated_signers={"user1"})


def test_policy_velocity_limit_enforcement():
    """Verify policy rule enforces daily velocity limit across multiple transactions."""
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
    rule.evaluate(prop, verified_authenticated_signers={"user1"})
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
        rule.evaluate(prop2, verified_authenticated_signers={"user1"})


def test_policy_unauthenticated_signer_rejected():
    """Verify policy rule rejects transactions from unauthenticated signers."""
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
    # Evaluated without verifier attestation for user_fake
    with pytest.raises(PolicyViolationError, match="unauthenticated"):
        rule.evaluate(prop_unauth, verified_authenticated_signers=set())


def test_policy_unauthorized_signer_rejected():
    """Verify policy rule rejects transactions from unauthorised signers."""
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
        rule.evaluate(prop_unauthz, verified_authenticated_signers={"user3"})


def test_policy_record_execution_positive_amount():
    """Verify policy rule execution recording rejects negative amounts."""
    rule = PolicyRule(
        rule_id="rule-x",
        max_amount_per_tx=Decimal("100.0"),
        daily_velocity_limit=Decimal("500.0"),
        required_approvers_count=1
    )
    with pytest.raises(ValueError, match="strictly greater than zero"):
        rule.record_execution(Decimal("-10.0"))
