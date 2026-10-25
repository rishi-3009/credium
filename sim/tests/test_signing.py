"""Tests for sim/signing.py — EIP-712 helpers and anvil account derivation."""

from eth_account import Account
from eth_account.messages import encode_typed_data
from eth_keys import keys
from eth_utils import keccak
import pytest

from sim.signing import (
    ALLOC_TYPES,
    ALLOC_TYPEHASH,
    BILL_TYPES,
    BILL_TYPEHASH,
    CATEGORY_PPE,
    CATEGORY_WATER,
    DOMAIN_SEPARATOR,
    allocation_digest,
    anvil_account,
    bill_digest,
    bill_nullifier,
    items_commitment,
    sign_allocation,
    sign_bill,
    synthetic_account,
)


def _b(h: str) -> bytes:
    """Convert a 0x-hex string to bytes."""
    return bytes.fromhex(h[2:])


def _h(raw: bytes) -> str:
    """Convert bytes to a 0x-prefixed hex string."""
    return "0x" + raw.hex()


# ---------------------------------------------------------------------------
# Test 1: anvil account addresses
# ---------------------------------------------------------------------------

def test_anvil_addresses():
    """Derived addresses must match the well-known anvil test mnemonic."""
    acct0 = anvil_account(0)
    acct1 = anvil_account(1)
    assert acct0["address"].lower() == "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266"
    assert acct1["address"].lower() == "0x70997970c51812dc3a010c7d01b50e0d17dc79c8"


# ---------------------------------------------------------------------------
# Test 2: parity with eth_account.encode_typed_data
# ---------------------------------------------------------------------------

def test_parity_with_eth_account():
    """Our signing must produce the same digest as eth_account's encode_typed_data."""
    # --- Bill test --------------------------------------------------------
    salt = bytes(32)
    bill = {
        "vendor": synthetic_account("vendor:test")["address"],
        "buyerNGO": anvil_account(1)["address"],
        "billNo": 417,
        "amountPaise": 18_000_000,
        "issuedAt": 1792861200,
        "category": CATEGORY_WATER,
        "itemsCommitment": items_commitment(
            [{"desc": "Gate valve", "qty": 1, "unitPaise": 500_000}],
            salt,
        ),
    }

    domain_data = {"name": "Credium", "version": "1"}
    signable = encode_typed_data(
        domain_data=domain_data,
        message_types={"Bill": BILL_TYPES},
        message_data=bill,
    )
    assert signable.header == _b(DOMAIN_SEPARATOR)
    assert signable.body == _b(bill_digest(bill))

    vendor_key = synthetic_account("vendor:test")["key"]
    signable_sig = _h(
        Account.sign_message(signable, vendor_key).signature
    )
    our_sig = sign_bill(bill, vendor_key)
    assert signable_sig == our_sig

    # --- Allocation test --------------------------------------------------
    bill_null = bill_nullifier(bill)
    alloc = {
        "billNullifier": bill_null,
        "donorVault": anvil_account(0)["address"],
        "chainId": 31337,
        "fractionBps": 10000,
        "reportId": "0x" + keccak(b"report:1").hex(),
    }

    signable_a = encode_typed_data(
        domain_data=domain_data,
        message_types={"Allocation": ALLOC_TYPES},
        message_data=alloc,
    )
    assert signable_a.header == _b(DOMAIN_SEPARATOR)
    assert signable_a.body == _b(allocation_digest(alloc))

    ngo_key = synthetic_account("ngo:alice")["key"]
    signable_a_sig = _h(
        Account.sign_message(signable_a, ngo_key).signature
    )
    our_a_sig = sign_allocation(alloc, ngo_key)
    assert signable_a_sig == our_a_sig


# ---------------------------------------------------------------------------
# Test 3: recover signer from signature
# ---------------------------------------------------------------------------

def test_recover_signer():
    """Recovering the signer from the signature must yield the vendor address."""
    bill = {
        "vendor": synthetic_account("vendor:test")["address"],
        "buyerNGO": anvil_account(1)["address"],
        "billNo": 417,
        "amountPaise": 18_000_000,
        "issuedAt": 1792861200,
        "category": CATEGORY_WATER,
        "itemsCommitment": items_commitment(
            [{"desc": "Gate valve", "qty": 1, "unitPaise": 500_000}],
            bytes(32),
        ),
    }
    vendor_key = synthetic_account("vendor:test")["key"]
    sig = sign_bill(bill, vendor_key)
    sig_bytes = _b(sig)

    # Recover the signer
    h = keccak(b"\x19\x01" + _b(DOMAIN_SEPARATOR) + _b(bill_digest(bill)))
    signer = keys.Signature(
        vrs=(sig_bytes[64] - 27,
             int.from_bytes(sig_bytes[:32], "big"),
             int.from_bytes(sig_bytes[32:64], "big"))
    ).recover_public_key_from_msg_hash(h)
    signer_addr = signer.to_checksum_address()

    assert signer_addr == bill["vendor"]


# ---------------------------------------------------------------------------
# Test 4: salt and amount change hashes
# ---------------------------------------------------------------------------

def test_salt_and_amount_change_hashes():
    """Changing salt or amount must produce different hashes."""
    salt_a = bytes(32)
    salt_b = bytes([1]) + bytes(31)
    items = [{"desc": "Gate valve", "qty": 1, "unitPaise": 500_000}]

    hc_a = items_commitment(items, salt_a)
    hc_b = items_commitment(items, salt_b)
    assert hc_a != hc_b, "Different salts must produce different items_commitment"

    base_bill = {
        "vendor": anvil_account(0)["address"],
        "buyerNGO": anvil_account(1)["address"],
        "billNo": 417,
        "amountPaise": 18_000_000,
        "issuedAt": 1792861200,
        "category": CATEGORY_WATER,
        "itemsCommitment": items_commitment(items, salt_a),
    }
    bill_low = dict(base_bill, amountPaise=9_000_000)
    assert bill_nullifier(base_bill) != bill_nullifier(bill_low), (
        "Different amountPaise must produce different bill_nullifier"
    )
