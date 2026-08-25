"""Tests for segregated account ledger and non-commingling rules."""

import re
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

    ledger_b = SegregatedLedger(ledger_id="led-b", client_id="client-b")
    ledger_b.sub_accounts["sub-a1"] = ledger_a.sub_accounts["sub-a1"]

    with pytest.raises(ComminglingError, match=re.escape("belongs to client client-a, not client-b.")):
        ledger_b.get_or_create_sub_account("sub-a1", "ETH")


def test_sub_account_asset_mismatch_prevention():
    ledger = SegregatedLedger(ledger_id="led-1", client_id="client-a")
    ledger.get_or_create_sub_account("sub-1", "BTC")

    with pytest.raises(ValueError, match=re.escape("Sub-account sub-1 asset 'BTC' does not match requested 'ETH'.")):
        ledger.get_or_create_sub_account("sub-1", "ETH")


def test_internal_transfer_same_client():
    ledger = SegregatedLedger(ledger_id="led-1", client_id="client-x")
    acc1 = ledger.get_or_create_sub_account("acc-1", "USDC")
    acc2 = ledger.get_or_create_sub_account("acc-2", "USDC")

    acc1.deposit(Decimal("1000.00"))
    ledger.transfer_internal("acc-1", "acc-2", Decimal("400.00"))

    assert acc1.balance == Decimal("600.00")
    assert acc2.balance == Decimal("400.00")
