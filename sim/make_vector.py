"""Generate sim/fixtures/vector.json for Rishi's Gate.t.sol tests."""

import argparse
import json
from eth_keys import keys
from eth_utils import keccak

from sim.signing import (
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


def recover(struct_hash: str, sig_hex: str) -> str:
    s = bytes.fromhex(sig_hex[2:])
    h = keccak(
        b"\x19\x01"
        + bytes.fromhex(DOMAIN_SEPARATOR[2:])
        + bytes.fromhex(struct_hash[2:])
    )
    sig = keys.Signature(
        vrs=(
            s[64] - 27,
            int.from_bytes(s[:32], "big"),
            int.from_bytes(s[32:64], "big"),
        )
    )
    return sig.recover_public_key_from_msg_hash(h).to_checksum_address()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate vector.json")
    parser.add_argument("--out", required=True, help="Output path for vector.json")
    args = parser.parse_args()

    # Fixed inputs
    salt = bytes(range(32))
    items = [{"desc": "PVC pipe 1 inch", "qty": 2, "unitPaise": 9000000}]
    donorVault = anvil_account(6)["address"]
    reportId = "0x" + keccak(b"report-417").hex()

    # Step 1: accounts
    ngo = anvil_account(1)
    vendor = synthetic_account("vendor:vector")

    # Step 2: items_commitment + bill
    commitment = items_commitment(items, salt)
    bill = {
        "vendor": vendor["address"],
        "buyerNGO": ngo["address"],
        "billNo": 417,
        "amountPaise": 18000000,
        "issuedAt": 1792861200,
        "category": CATEGORY_WATER,
        "itemsCommitment": commitment,
    }

    # Step 3: bill digest + nullifier + vendor sig
    bill_digest_val = bill_digest(bill)
    bill_nullifier_val = bill_nullifier(bill)
    vendor_sig = sign_bill(bill, vendor["key"])

    # Step 4: allocation + ngo sig
    alloc = {
        "billNullifier": bill_nullifier_val,
        "donorVault": donorVault,
        "chainId": 31337,
        "fractionBps": 10000,
        "reportId": reportId,
    }
    alloc_digest_val = allocation_digest(alloc)
    ngo_sig = sign_allocation(alloc, ngo["key"])

    # Step 5: chainB (wrong chainId)
    alloc_chain_b = dict(alloc, chainId=31338)
    chain_b_digest = allocation_digest(alloc_chain_b)
    chain_b_sig = sign_allocation(alloc_chain_b, ngo["key"])

    # Step 6: tampered (wrong fractionBps, same ngoSig)
    alloc_tampered = dict(alloc, fractionBps=6000)
    tampered_digest = allocation_digest(alloc_tampered)

    # Step 7: self-check
    assert recover(alloc_digest_val, ngo_sig) == ngo["address"]
    assert recover(chain_b_digest, chain_b_sig) == ngo["address"]
    assert recover(tampered_digest, ngo_sig) != ngo["address"]

    # Step 8: write JSON
    obj = {
        "simulated": True,
        "domain": {"name": "Credium", "version": "1"},
        "domainSeparator": DOMAIN_SEPARATOR,
        "ngo": ngo["address"],
        "vendor": vendor["address"],
        "bill": bill,
        "billDigest": bill_digest_val,
        "billNullifier": bill_nullifier_val,
        "vendorSig": vendor_sig,
        "allocation": alloc,
        "allocDigest": alloc_digest_val,
        "ngoSig": ngo_sig,
        "chainB": {
            "allocation": alloc_chain_b,
            "allocDigest": chain_b_digest,
            "ngoSig": chain_b_sig,
        },
        "tampered": {
            "allocation": alloc_tampered,
            "allocDigest": tampered_digest,
            "ngoSig": ngo_sig,
        },
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=True)

    # Print confirmation
    print(
        json.dumps(
            {"ok": True, "out": args.out, "billNullifier": bill_nullifier_val}
        )
    )


if __name__ == "__main__":
    main()
