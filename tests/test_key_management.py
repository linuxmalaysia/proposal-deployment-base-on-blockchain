"""Tests for MPC and HSM key management vault tiering."""

import re
import dataclasses

import pytest
from dca_service.core.key_management import (
    VaultTier,
    KeyShare,
    ThresholdPolicy,
    KeyVault,
)


def test_threshold_policy_validation():
    policy = ThresholdPolicy(required_signatures=2, total_shares=3)
    assert policy.required_signatures == 2

    with pytest.raises(ValueError, match=re.escape("Required signatures must be greater than zero.")):
        ThresholdPolicy(required_signatures=0, total_shares=3)

    with pytest.raises(ValueError, match=re.escape("Required signatures cannot exceed total shares.")):
    with pytest.raises(ValueError, match="Required signatures must be greater than zero."):
        ThresholdPolicy(required_signatures=0, total_shares=3)

    with pytest.raises(ValueError, match="Required signatures cannot exceed total shares."):
        ThresholdPolicy(required_signatures=4, total_shares=3)


def test_vault_quorum_evaluation():
    policy = ThresholdPolicy(required_signatures=2, total_shares=3)
    vault = KeyVault(vault_id="vault-warm-1", tier=VaultTier.WARM, policy=policy)

    share1 = KeyShare(share_id="s1", holder_id="h1", encrypted_payload="p1", tier=VaultTier.WARM)
    share2 = KeyShare(share_id="s2", holder_id="h2", encrypted_payload="p2", tier=VaultTier.WARM)
    share3 = KeyShare(share_id="s3", holder_id="h3", encrypted_payload="p3", tier=VaultTier.WARM)

    vault.add_key_share(share1)
    vault.add_key_share(share2)
    vault.add_key_share(share3)

    # Insufficient signatures
    assert not vault.validate_quorum({"s1"})

    # Valid quorum
    assert vault.validate_quorum({"s1", "s2"})
    assert vault.validate_quorum({"s1", "s2", "s3"})


def test_vault_duplicate_share_and_capacity_rejection():
    policy = ThresholdPolicy(required_signatures=1, total_shares=2)
    vault = KeyVault(vault_id="v1", tier=VaultTier.HOT, policy=policy)

    share1 = KeyShare(share_id="s1", holder_id="h1", encrypted_payload="p1", tier=VaultTier.HOT)
    share2 = KeyShare(share_id="s2", holder_id="h2", encrypted_payload="p2", tier=VaultTier.HOT)
    share3 = KeyShare(share_id="s3", holder_id="h3", encrypted_payload="p3", tier=VaultTier.HOT)

    vault.add_key_share(share1)

    with pytest.raises(ValueError, match=re.escape("Key share with ID 's1' already exists in vault.")):
        vault.add_key_share(share1)

    vault.add_key_share(share2)

    with pytest.raises(ValueError, match=re.escape("Vault cannot exceed policy total shares capacity of 2.")):
        vault.add_key_share(share3)


def test_vault_tier_mismatch_rejection():
    policy = ThresholdPolicy(required_signatures=1, total_shares=1)
    vault = KeyVault(vault_id="vault-cold-1", tier=VaultTier.COLD, policy=policy)
    hot_share = KeyShare(share_id="s-hot", holder_id="h1", encrypted_payload="p", tier=VaultTier.HOT)

    with pytest.raises(ValueError, match=re.escape("Share tier VaultTier.HOT does not match vault tier VaultTier.COLD.")):
        vault.add_key_share(hot_share)
def test_vault_tier_mismatch_rejection():
    policy = ThresholdPolicy(required_signatures=1, total_shares=1)
    vault = KeyVault(vault_id="vault-cold-1", tier=VaultTier.COLD, policy=policy)
    hot_share = KeyShare(share_id="s-hot", holder_id="h1", encrypted_payload="p", tier=VaultTier.HOT)

    with pytest.raises(ValueError, match="Share tier VaultTier.HOT does not match vault tier VaultTier.COLD."):
        vault.add_key_share(hot_share)


def test_threshold_policy_allows_required_equal_to_total_shares():
    policy = ThresholdPolicy(required_signatures=3, total_shares=3)
    assert policy.required_signatures == 3
    assert policy.total_shares == 3


def test_validate_quorum_with_empty_provided_shares_is_false():
    policy = ThresholdPolicy(required_signatures=1, total_shares=1)
    vault = KeyVault(vault_id="vault-hot-1", tier=VaultTier.HOT, policy=policy)
    vault.add_key_share(
        KeyShare(share_id="s1", holder_id="h1", encrypted_payload="p1", tier=VaultTier.HOT)
    )

    assert not vault.validate_quorum(set())


def test_validate_quorum_ignores_unknown_share_ids():
    policy = ThresholdPolicy(required_signatures=2, total_shares=2)
    vault = KeyVault(vault_id="vault-warm-2", tier=VaultTier.WARM, policy=policy)
    vault.add_key_share(
        KeyShare(share_id="s1", holder_id="h1", encrypted_payload="p1", tier=VaultTier.WARM)
    )
    vault.add_key_share(
        KeyShare(share_id="s2", holder_id="h2", encrypted_payload="p2", tier=VaultTier.WARM)
    )

    # "s-unknown" does not belong to the vault so only s1/s2 should count.
    assert vault.validate_quorum({"s1", "s2", "s-unknown"})
    assert not vault.validate_quorum({"s1", "s-unknown"})


def test_key_share_is_immutable():
    share = KeyShare(share_id="s1", holder_id="h1", encrypted_payload="p1", tier=VaultTier.HOT)

    with pytest.raises(dataclasses.FrozenInstanceError):
        share.holder_id = "h2"


def test_key_vault_starts_with_no_key_shares():
    policy = ThresholdPolicy(required_signatures=1, total_shares=2)
    vault = KeyVault(vault_id="vault-empty", tier=VaultTier.COLD, policy=policy)

    assert vault.key_shares == []
    assert not vault.validate_quorum({"anything"})
