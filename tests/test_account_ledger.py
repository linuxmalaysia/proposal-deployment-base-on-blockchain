"""Tests for segregated account ledger and non-commingling rules."""

from decimal import Decimal
import pytest
from dca_service.core.account_ledger import (
    SubAccount,
    SegregatedLedger,
    ComminglingError,
    InsufficientBalanceError,
)


def test_sub_account_deposit_withdrawal():
    sub_acc = SubAccount(sub_account_id="sub-1", client_id="client-a", asset_symbol="BTC")
    sub_acc.deposit(Decimal("2.5"))
    assert sub_acc.balance == Decimal("2.5")

    sub_acc.withdraw(Decimal("1.0"))
    assert sub_acc.balance == Decimal("1.5")

    with pytest.raises(InsufficientBalanceError):
        sub_acc.withdraw(Decimal("10.0"))


def test_segregated_ledger_commingling_prevention():
    ledger_a = SegregatedLedger(ledger_id="led-a", client_id="client-a")
    ledger_a.get_or_create_sub_account("sub-a1", "ETH")

    # Accessing existing sub-account with wrong client ID raises ComminglingError
    ledger_b = SegregatedLedger(ledger_id="led-b", client_id="client-b")
    ledger_b.sub_accounts["sub-a1"] = ledger_a.sub_accounts["sub-a1"]

    with pytest.raises(ComminglingError, match="belongs to client client-a, not client-b"):
        ledger_b.get_or_create_sub_account("sub-a1", "ETH")


def test_sub_account_asset_mismatch_prevention():
    ledger = SegregatedLedger(ledger_id="led-1", client_id="client-a")
    ledger.get_or_create_sub_account("sub-1", "BTC")

    with pytest.raises(ValueError, match="does not match requested 'ETH'"):
        ledger.get_or_create_sub_account("sub-1", "ETH")


def test_internal_transfer_same_client():
    ledger = SegregatedLedger(ledger_id="led-1", client_id="client-x")
    acc1 = ledger.get_or_create_sub_account("acc-1", "USDC")
    acc2 = ledger.get_or_create_sub_account("acc-2", "USDC")

    acc1.deposit(Decimal("1000.00"))
    ledger.transfer_internal("acc-1", "acc-2", Decimal("400.00"))

    assert acc1.balance == Decimal("600.00")
    assert acc2.balance == Decimal("400.00")


def test_deposit_rejects_zero_and_negative_amounts():
    sub_acc = SubAccount(sub_account_id="sub-2", client_id="client-a", asset_symbol="ETH")

    with pytest.raises(ValueError, match="Deposit amount must be positive."):
        sub_acc.deposit(Decimal("0.0"))

    with pytest.raises(ValueError, match="Deposit amount must be positive."):
        sub_acc.deposit(Decimal("-5.0"))

    assert sub_acc.balance == Decimal("0.0")


def test_withdraw_rejects_zero_and_negative_amounts():
    sub_acc = SubAccount(sub_account_id="sub-3", client_id="client-a", asset_symbol="ETH")
    sub_acc.deposit(Decimal("10.0"))

    with pytest.raises(ValueError, match="Withdrawal amount must be positive."):
        sub_acc.withdraw(Decimal("0.0"))

    with pytest.raises(ValueError, match="Withdrawal amount must be positive."):
        sub_acc.withdraw(Decimal("-1.0"))

    assert sub_acc.balance == Decimal("10.0")


def test_withdraw_exact_balance_to_zero():
    sub_acc = SubAccount(sub_account_id="sub-4", client_id="client-a", asset_symbol="BTC")
    sub_acc.deposit(Decimal("5.0"))
    sub_acc.withdraw(Decimal("5.0"))
    assert sub_acc.balance == Decimal("0.0")


def test_get_or_create_sub_account_is_idempotent_for_same_client():
    ledger = SegregatedLedger(ledger_id="led-2", client_id="client-y")
    first = ledger.get_or_create_sub_account("acc-1", "USDC")
    first.deposit(Decimal("50.0"))

    second = ledger.get_or_create_sub_account("acc-1", "USDC")

    assert second is first
    assert second.balance == Decimal("50.0")
    assert len(ledger.sub_accounts) == 1


def test_transfer_internal_missing_sub_account_raises_key_error():
    ledger = SegregatedLedger(ledger_id="led-3", client_id="client-z")
    ledger.get_or_create_sub_account("acc-1", "USDC")

    with pytest.raises(KeyError, match="Both sub-accounts must exist within the client ledger."):
        ledger.transfer_internal("acc-1", "acc-missing", Decimal("10.0"))

    with pytest.raises(KeyError, match="Both sub-accounts must exist within the client ledger."):
        ledger.transfer_internal("acc-missing", "acc-1", Decimal("10.0"))


def test_transfer_internal_rejects_mismatched_asset_symbols():
    ledger = SegregatedLedger(ledger_id="led-4", client_id="client-w")
    acc1 = ledger.get_or_create_sub_account("acc-1", "BTC")
    ledger.get_or_create_sub_account("acc-2", "ETH")
    acc1.deposit(Decimal("1.0"))

    with pytest.raises(ValueError, match="Cannot transfer directly between different asset symbols."):
        ledger.transfer_internal("acc-1", "acc-2", Decimal("0.5"))


def test_transfer_internal_insufficient_balance_leaves_accounts_unchanged():
    ledger = SegregatedLedger(ledger_id="led-5", client_id="client-v")
    acc1 = ledger.get_or_create_sub_account("acc-1", "USDC")
    acc2 = ledger.get_or_create_sub_account("acc-2", "USDC")
    acc1.deposit(Decimal("10.0"))

    with pytest.raises(InsufficientBalanceError):
        ledger.transfer_internal("acc-1", "acc-2", Decimal("100.0"))

    assert acc1.balance == Decimal("10.0")
    assert acc2.balance == Decimal("0.0")
