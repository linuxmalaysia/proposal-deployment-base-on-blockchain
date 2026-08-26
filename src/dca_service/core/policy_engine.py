"""
Configurable Policy Engine Module for Digital Custody Asset Platform.

Enforces transaction policy rules, velocity limits, multi-signer quorums,
and destination address allowlists.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Set, List, Collection


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
    signers: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.amount <= Decimal("0.0"):
            raise ValueError("Transaction proposal amount must be strictly greater than zero.")

        # Require signers to be a list before checking entries or duplicates
        if not isinstance(self.signers, list):
            raise ValueError("Signers must be provided as a list.")

        # Runtime validation: check for non-empty string values and duplicate signers
        for signer in self.signers:
            if not isinstance(signer, str) or not signer.strip():
                raise ValueError("Signer identity must be a non-empty string.")

        if len(self.signers) != len(set(self.signers)):
            raise ValueError("Duplicate signers detected in transaction proposal.")


@dataclass
class PolicyRule:
    rule_id: str
    max_amount_per_tx: Decimal
    daily_velocity_limit: Decimal
    required_approvers_count: int
    allowlisted_addresses: Set[str] = field(default_factory=set)
    authorized_signers: Set[str] = field(default_factory=set)
    authenticated_signers: Set[str] = field(default_factory=set)
    current_daily_accumulated: Decimal = Decimal("0.0")

    def evaluate(self, proposal: TransactionProposal, verified_authenticated_signers: Set[str] | None = None) -> None:
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

        # 4. Multi-Signer Quorum & Signer Validation Check
        # Membership in TransactionProposal.signers alone is not treated as authentication evidence.
        # Active session/signature verifier attestation must be supplied via verified_authenticated_signers.
        auth_evidence = verified_authenticated_signers if verified_authenticated_signers is not None else set()

        valid_signers: set[str] = set()
        for signer in proposal.signers:
            # Check authentication evidence if authenticated_signers set or verifier attestation is enforced
            if self.authenticated_signers and (signer not in self.authenticated_signers or signer not in auth_evidence):
                raise PolicyViolationError(f"Signer '{signer}' is unauthenticated.")

            # Check authorisation if authorized_signers set is defined
            if self.authorized_signers and signer not in self.authorized_signers:
                raise PolicyViolationError(f"Signer '{signer}' is unauthorized.")

            valid_signers.add(signer)

        if len(valid_signers) < self.required_approvers_count:
            raise PolicyViolationError(
                f"Signer quorum requirement not met. Provided: {len(valid_signers)}, Required: {self.required_approvers_count}."
            )

    def record_execution(self, amount: Decimal) -> None:
        if amount <= Decimal("0.0"):
            raise ValueError("Execution amount must be strictly greater than zero.")
        self.current_daily_accumulated += amount
