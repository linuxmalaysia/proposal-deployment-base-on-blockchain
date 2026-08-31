"""
Segregated Account Ledger Module for Digital Custody Asset Platform.

Enforces zero-commingling of client digital assets via isolated sub-accounts
and strict balance tracking.
"""

from dataclasses import dataclass, field
from decimal import Decimal


class ComminglingError(Exception):
    """Raised when an action violates client asset segregation policies."""


class InsufficientBalanceError(Exception):
    """Raised when an account withdrawal exceeds available balance."""


@dataclass
class SubAccount:
    sub_account_id: str
    client_id: str
    asset_symbol: str
    balance: Decimal = Decimal("0.0")

    def deposit(self, amount: Decimal) -> None:
        if amount <= Decimal("0.0"):
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount

    def withdraw(self, amount: Decimal) -> None:
        if amount <= Decimal("0.0"):
            raise ValueError("Withdrawal amount must be positive.")
        if amount > self.balance:
            raise InsufficientBalanceError(
                f"Account {self.sub_account_id} balance {self.balance} is insufficient for {amount}."
            )
        self.balance -= amount


@dataclass
class SegregatedLedger:
    ledger_id: str
    client_id: str
    sub_accounts: dict[str, SubAccount] = field(default_factory=dict)

    def get_or_create_sub_account(self, sub_account_id: str, asset_symbol: str) -> SubAccount:
        """
        Retrieve a matching sub-account or create one for this ledger's client.
        
        Parameters:
            sub_account_id (str): Identifier of the sub-account.
            asset_symbol (str): Asset held by the sub-account.
        
        Returns:
            SubAccount: The existing or newly created sub-account.
        
        Raises:
            ComminglingError: If the sub-account belongs to another client.
            ValueError: If an existing sub-account uses a different asset.
        """
        if sub_account_id in self.sub_accounts:
            existing = self.sub_accounts[sub_account_id]
            if existing.client_id != self.client_id:
                raise ComminglingError(
                    f"Sub-account {sub_account_id} belongs to client {existing.client_id}, not {self.client_id}."
                )
            if existing.asset_symbol != asset_symbol:
                raise ValueError(
                    f"Sub-account {sub_account_id} asset '{existing.asset_symbol}' does not match requested '{asset_symbol}'."
                )
            return existing

        sub_acc = SubAccount(
            sub_account_id=sub_account_id,
            client_id=self.client_id,
            asset_symbol=asset_symbol
        )
        self.sub_accounts[sub_account_id] = sub_acc
        return sub_acc

    def transfer_internal(
        self,
        from_sub_acc_id: str,
        to_sub_acc_id: str,
        amount: Decimal
    ) -> None:
        """Transfer assets strictly between sub-accounts of the SAME client."""
        if from_sub_acc_id not in self.sub_accounts or to_sub_acc_id not in self.sub_accounts:
            raise KeyError("Both sub-accounts must exist within the client ledger.")

        source = self.sub_accounts[from_sub_acc_id]
        destination = self.sub_accounts[to_sub_acc_id]

        if source.client_id != self.client_id or destination.client_id != self.client_id:
            raise ComminglingError("Cannot transfer funds between accounts belonging to different clients.")

        if source.asset_symbol != destination.asset_symbol:
            raise ValueError("Cannot transfer directly between different asset symbols.")

        source.withdraw(amount)
        destination.deposit(amount)
