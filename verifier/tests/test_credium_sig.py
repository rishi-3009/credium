import pytest
from eth_account import Account
from eth_utils import keccak, to_hex

import credium_sig
import reference_sign


@pytest.fixture
def ngo(monkeypatch):
    # Fresh throwaway key per test. Nothing is hard-coded or committed.
    account = Account.create()
    monkeypatch.setenv("NGO_KEY", account.key.hex())
    return account


def _bill(vendor: str, ngo_address: str, bill_no: int) -> dict:
    return {
        "vendor": vendor,
        "buyerNGO": ngo_address,
        "billNo": bill_no,
        "amountPaise": 18_000_000,
        "issuedAt": 1_792_800_000 + 3600 * bill_no,
        "category": to_hex(keccak(text="WATER")),
        "itemsCommitment": to_hex(keccak(text=f"items-{bill_no}")),
    }


def _allocation(bill_no: int, fraction_bps: int, donor_vault: str) -> dict:
    return {
        "billNullifier": to_hex(keccak(text=f"nullifier-{bill_no}")),
        "donorVault": donor_vault,
        "chainId": 31337,
        "fractionBps": fraction_bps,
        "reportId": to_hex(keccak(text=f"report-{bill_no}")),
    }


@pytest.mark.parametrize("bill_no", [405, 417, 418])
def test_bill_signer_recovers_to_vendor(ngo, bill_no):
    vendor = Account.create()
    bill = _bill(vendor.address, ngo.address, bill_no)
    sig = reference_sign.sign_bill(bill, vendor.key.hex())
    assert credium_sig.recover_bill_signer(bill, sig).lower() == vendor.address.lower()


@pytest.mark.parametrize("fraction_bps", [10_000, 6_000, 4_000])
def test_allocation_signer_recovers_to_ngo(ngo, fraction_bps):
    alloc = _allocation(417, fraction_bps, Account.create().address)
    sig = reference_sign.sign_allocation(alloc)
    assert credium_sig.recover_allocation_signer(alloc, sig).lower() == ngo.address.lower()


def test_nullifier_is_bytes32_and_changes_with_bill_content(ngo):
    vendor = Account.create().address
    base = _bill(vendor, ngo.address, 417)
    edited = dict(base, amountPaise=base["amountPaise"] + 1)
    n = credium_sig.bill_nullifier(base)
    assert len(n) == 66 and n.startswith("0x")
    assert n != credium_sig.bill_nullifier(edited)
