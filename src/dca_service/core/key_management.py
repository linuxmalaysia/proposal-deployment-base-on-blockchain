"""
Key Management Module for Digital Custody Asset (DCA) Platform.

Implements MPC (Multi-Party Computation) threshold quorums and HSM-backed
vault tiering (Hot, Warm, Cold) using pure Python domain constructs.
"""

from dataclasses import dataclass, field
from enum import Enum, auto


class VaultTier(Enum):
    HOT = auto()
    WARM = auto()
    COLD = auto()


@dataclass(frozen=True)
class KeyShare:
    share_id: str
    holder_id: str
    encrypted_payload: str
    tier: VaultTier


@dataclass
class ThresholdPolicy:
    required_signatures: int
    total_shares: int

    def __post_init__(self) -> None:
        if self.required_signatures <= 0:
            raise ValueError("Required signatures must be greater than zero.")
        if self.required_signatures > self.total_shares:
            raise ValueError("Required signatures cannot exceed total shares.")


class KeyVault:
    def __init__(
        self,
        vault_id: str,
        tier: VaultTier,
        policy: ThresholdPolicy,
        initial_shares: list[KeyShare] | None = None
    ) -> None:
        self.vault_id = vault_id
        self.tier = tier
        self.policy = policy
        self._key_shares: list[KeyShare] = []

        if initial_shares:
            for share in initial_shares:
                self.add_key_share(share)

    @property
    def key_shares(self) -> list[KeyShare]:
        return list(self._key_shares)

    def add_key_share(self, share: KeyShare) -> None:
        if share.tier != self.tier:
            raise ValueError(f"Share tier {share.tier} does not match vault tier {self.tier}.")
        if len(self._key_shares) >= self.policy.total_shares:
            raise ValueError(
                f"Vault cannot exceed policy total shares capacity of {self.policy.total_shares}."
            )
        if any(existing.share_id == share.share_id for existing in self._key_shares):
            raise ValueError(f"Key share with ID '{share.share_id}' already exists in vault.")
        self._key_shares.append(share)

    def validate_quorum(self, provided_share_ids: set[str]) -> bool:
        unique_provided = set(provided_share_ids)
        valid_count = sum(1 for share in self._key_shares if share.share_id in unique_provided)
        return valid_count >= self.policy.required_signatures
