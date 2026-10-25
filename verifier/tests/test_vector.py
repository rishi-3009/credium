"""13:50 check: my verifier against Ayaan's sim/fixtures/vector.json.

Imports only credium_sig, eth_account, json and pathlib. Does NOT import sim.signing, so the check
stays independent of his code.
"""
import json
from pathlib import Path

from eth_account import Account
from eth_utils import keccak, to_hex

import credium_sig

VECTOR = Path(__file__).resolve().parents[2] / "sim" / "fixtures" / "vector.json"


def _load():
    return json.loads(VECTOR.read_text(encoding="utf-8"))


def test_domain_separator_matches_vector():
    assert to_hex(credium_sig.DOMAIN_SEPARATOR) == _load()["domainSeparator"].lower()


def test_bill_digest_nullifier_and_vendor_sig():
    v = _load()
    bill = v["bill"]
    assert credium_sig.bill_digest(bill).hex() == v["billDigest"][2:]
    assert credium_sig.bill_nullifier(bill).lower() == v["billNullifier"].lower()
    assert credium_sig.recover_bill_signer(bill, v["vendorSig"]).lower() == v["vendor"].lower()


def test_chain_a_allocation_recovers_ngo():
    v = _load()
    alloc = v["allocation"]
    assert to_hex(credium_sig.allocation_digest(alloc)).lower() == v["allocDigest"].lower()
    assert credium_sig.recover_allocation_signer(alloc, v["ngoSig"]).lower() == v["ngo"].lower()


def test_chain_b_allocation_recovers_ngo():
    """The sample the 13:50 check is about: chain B, verified in Python."""
    v = _load()
    alloc = v["chainB"]["allocation"]
    assert to_hex(credium_sig.allocation_digest(alloc)).lower() == v["chainB"]["allocDigest"].lower()
    assert credium_sig.recover_allocation_signer(alloc, v["chainB"]["ngoSig"]).lower() == v["ngo"].lower()


def test_tampered_fraction_does_not_recover_ngo():
    v = _load()
    tampered = v["tampered"]["allocation"]
    recovered = credium_sig.recover_allocation_signer(tampered, v["tampered"]["ngoSig"])
    assert recovered.lower() != v["ngo"].lower()
