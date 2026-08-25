"""
Key Management Module for Digital Custody Asset (DCA) Platform.

Implements MPC (Multi-Party Computation) threshold quorums and HSM-backed
vault tiering (Hot, Warm, Cold) using pure Python domain constructs.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Set


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


@dataclass
class KeyVault:
    vault_id: str
    tier: VaultTier
    policy: ThresholdPolicy
    key_shares: List[KeyShare] = field(default_factory=list)

    def add_key_share(self, share: KeyShare) -> None:
        if share.tier != self.tier:
            raise ValueError(f"Share tier {share.tier} does not match vault tier {self.tier}.")
        self.key_shares.append(share)

    def validate_quorum(self, provided_share_ids: Set[str]) -> bool:
        valid_count = sum(1 for share in self.key_shares if share.share_id in provided_share_ids)
        return valid_count >= self.policy.required_signatures
