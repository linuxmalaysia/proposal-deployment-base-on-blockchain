"""
Configurable Policy Engine Module for Digital Custody Asset Platform.

Enforces transaction policy rules, velocity limits, multi-signer quorums,
and destination address allowlists.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Set, List


class PolicyViolationError(Exception):
    """Raised when a proposed transaction violates policy rules."""
    pass


@dataclass
class TransactionProposal:
    proposal_id: str
    client_id: str
    destination_address: str
    amount: Decimal
    asset_symbol: str
    signers: Set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if self.amount <= Decimal("0.0"):
            raise ValueError("Transaction proposal amount must be strictly greater than zero.")


@dataclass
class PolicyRule:
    rule_id: str
    max_amount_per_tx: Decimal
    daily_velocity_limit: Decimal
    required_approvers_count: int
    allowlisted_addresses: Set[str] = field(default_factory=set)
    current_daily_accumulated: Decimal = Decimal("0.0")

    def evaluate(self, proposal: TransactionProposal) -> None:
        """Evaluate a proposal against policy parameters. Raises PolicyViolationError if invalid."""
        # 1. Allowlist Check
        if self.allowlisted_addresses and proposal.destination_address not in self.allowlisted_addresses:
            raise PolicyViolationError(
                f"Destination address {proposal.destination_address} is not on the allowlist."
            )

        # 2. Per-Transaction Amount Limit Check
        if proposal.amount > self.max_amount_per_tx:
            raise PolicyViolationError(
                f"Transaction amount {proposal.amount} exceeds max single limit {self.max_amount_per_tx}."
            )

        # 3. Daily Velocity Limit Check
        if self.current_daily_accumulated + proposal.amount > self.daily_velocity_limit:
            raise PolicyViolationError(
                f"Transaction amount {proposal.amount} causes daily velocity to exceed limit {self.daily_velocity_limit}."
            )

        # 4. Multi-Signer Quorum Check
        if len(proposal.signers) < self.required_approvers_count:
            raise PolicyViolationError(
                f"Signer quorum requirement not met. Provided: {len(proposal.signers)}, Required: {self.required_approvers_count}."
            )

    def record_execution(self, amount: Decimal) -> None:
        if amount <= Decimal("0.0"):
            raise ValueError("Execution amount must be strictly greater than zero.")
        self.current_daily_accumulated += amount
