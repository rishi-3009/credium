"""Generate 100 synthetic bills for testing Gate.t.sol."""

import argparse
import json
import os
import random
import secrets
import sys
from pathlib import Path

from eth_utils import keccak

from sim.signing import (
    CATEGORY_PPE,
    CATEGORY_WATER,
    bill_digest,
    bill_nullifier,
    items_commitment,
    sign_bill,
    synthetic_account,
)

# ---------------------------------------------------------------------------
# VENDORS (exact names and tiers)
# ---------------------------------------------------------------------------

VENDORS: list[dict] = [
    {"name": "Ramesh Hardware", "tier": "GREEN"},
    {"name": "Lakshmi Pipes", "tier": "GREEN"},
    {"name": "Bharat Electricals", "tier": "GREEN"},
    {"name": "Gupta Cement", "tier": "GREEN"},
    {"name": "Nagpur Tools", "tier": "GREEN"},
    {"name": "Vidarbha Plumbing", "tier": "GREEN"},
    {"name": "Sai Water Works", "tier": "GREEN"},
    {"name": "Mahalaxmi Agro Supplies", "tier": "GREEN"},
    {"name": "Deccan Pump House", "tier": "GREEN"},
    {"name": "Kisan Borewell Services", "tier": "GREEN"},
    {"name": "Shivaji Sanitation Co.", "tier": "GREEN"},
    {"name": "Shree Supplies", "tier": "AMBER"},
    {"name": "Om Enterprises", "tier": "AMBER"},
    {"name": "Jai Bhavani Traders", "tier": "AMBER"},
    {"name": "Sharma Traders", "tier": "UNREGISTERED"},
]

# Realistic line items for water and sanitation works: (description, min paise, max paise).
ITEM_CATALOGUE: list[tuple[str, int, int]] = [
    ("PVC pipe 1 inch, 3 m", 18000, 42000),
    ("GI pipe 0.5 inch, 6 m", 32000, 58000),
    ("Gate valve 1 inch", 35000, 90000),
    ("Hand pump washer set", 2500, 6000),
    ("Hand pump cylinder assembly", 120000, 240000),
    ("Cement bag 50 kg, OPC 53", 38000, 45000),
    ("Submersible pump 0.5 HP", 680000, 950000),
    ("Borewell casing pipe 4 inch, 3 m", 150000, 310000),
    ("HDPE water tank 500 L", 420000, 610000),
    ("Chlorine tablets, pack of 100", 15000, 30000),
    ("Electric motor 1 HP", 540000, 780000),
    ("Solar panel 150 W", 620000, 880000),
    ("Copper cable 2.5 sq mm, 90 m", 310000, 420000),
    ("Brass tap and faucet set", 9000, 28000),
    ("Teflon tape, roll", 1500, 4000),
    ("Sanitary pan with flush", 180000, 320000),
    ("Water meter, 15 mm", 45000, 95000),
    ("Pressure gauge 0-10 bar", 22000, 48000),
    ("Masonry sand, tractor load", 240000, 360000),
    ("Labour, skilled mason, day", 85000, 120000),
]

GREEN_VENDOR_NAMES = [v["name"] for v in VENDORS if v["tier"] == "GREEN"]
AMBER_VENDOR_NAMES = [v["name"] for v in VENDORS if v["tier"] == "AMBER"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ITEMS: dict[int, dict] = {}  # billId → {"items": [...], "salt": "0x..."}


def _vendor_key(name: str) -> str:
    return synthetic_account("vendor:" + name)["key"]


def _make_bill(billId: int, vendor_name: str, buyerNGO: str,
               default_amount: int = -1, category: str = CATEGORY_WATER) -> dict:
    billNo = 400 + billId
    issuedAt = 1792800000 + 3600 * billId
    salt = secrets.token_bytes(32)
    items = []
    for _ in range(random.randrange(1, 5)):
        desc, low, high = random.choice(ITEM_CATALOGUE)
        items.append({
            "desc": desc,
            "qty": random.randrange(1, 11),
            "unitPaise": random.randrange(low, high + 1, 100),
        })
    itemsCommitment = items_commitment(items, salt)
    reportId = "0x" + keccak(f"report-{billNo}".encode()).hex()

    bill = {
        "vendor": synthetic_account("vendor:" + vendor_name)["address"],
        "buyerNGO": buyerNGO,
        "billNo": billNo,
        "amountPaise": 18000000,
        "issuedAt": issuedAt,
        "category": category,
        "itemsCommitment": itemsCommitment,
    }
    vendor_sig = sign_bill(bill, _vendor_key(vendor_name))
    nullifier = bill_nullifier(bill)

    _ITEMS[billId] = {"items": items, "salt": "0x" + salt.hex()}

    return {
        "billId": billId,
        "billNo": billNo,
        "label": "",  # filled in later
        "expected": "",  # filled in later
        "vendorName": vendor_name,
        "bill": bill,
        "vendorSig": vendor_sig,
        "nullifier": nullifier,
        "reportId": reportId,
        "_private": {"items": items, "salt": "0x" + salt.hex()},
    }


def generate_bills(seed: int = 417, n: int = 100) -> list[dict]:
    """Generate *n* synthetic bills with deterministic labels."""
    rng = random.Random(seed)

    # Step 1: build label pool
    pool = (
        ["GENUINE"] * 67
        + ["FORGED_EDITED_AMOUNT"] * 18
        + ["FORGED_UNKNOWN_SIGNER"] * 7
        + ["AMBER_SOCKPUPPET"] * 5
    )
    rng.shuffle(pool)

    buyerNGO = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    bills = []
    labels_to_expected = {
        "GENUINE": "GREEN",
        "FORGED_EDITED_AMOUNT": "FORGED",
        "FORGED_UNKNOWN_SIGNER": "UNKNOWN",
        "AMBER_SOCKPUPPET": "AMBER",
    }

    choice_rng = random.Random(seed + 4000)  # one stream for all bills, so vendors vary
    for billId in range(n):
        # Step 2: assign label
        if billId in (5, 17, 18):
            label = "GENUINE"
        else:
            label = pool.pop(0)

        # Step 3: assign vendor
        if label in ("GENUINE", "FORGED_EDITED_AMOUNT"):
            vendor_name = choice_rng.choice(GREEN_VENDOR_NAMES)
        elif label == "FORGED_UNKNOWN_SIGNER":
            vendor_name = "Sharma Traders"
        elif label == "AMBER_SOCKPUPPET":
            vendor_name = choice_rng.choice(AMBER_VENDOR_NAMES)
        else:
            vendor_name = choice_rng.choice(GREEN_VENDOR_NAMES)

        # Step 4: create bill
        bill = _make_bill(billId, vendor_name, buyerNGO, category=CATEGORY_WATER)
        bill["label"] = label
        bill["expected"] = labels_to_expected[label]

        # FORGED_EDITED_AMOUNT: store original bill, sign original, then tamper stored bill
        if label == "FORGED_EDITED_AMOUNT":
            # bill was already created and signed above (original)
            # now modify the stored bill to have a different amountPaise
            original_amount = bill["bill"]["amountPaise"]
            edited_bill = dict(bill["bill"])
            edited_bill["amountPaise"] = original_amount + 1000000
            bill["bill"] = edited_bill
            # vendorSig remains the signature of the original (now invalid)

        bills.append(bill)

    return bills


def generate_extras() -> list[dict]:
    """Generate the 2 extra bills (WRONG_CATEGORY and HELD_OUT_FUTURE)."""
    buyerNGO = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"

    # extras[0]: WRONG_CATEGORY
    bill100 = _make_bill(
        100, "Ramesh Hardware", buyerNGO,
        5000000, CATEGORY_PPE,
    )
    bill100["billId"] = 100
    bill100["billNo"] = 598
    bill100["label"] = "WRONG_CATEGORY"
    bill100["expected"] = "WRONG_CATEGORY"

    # extras[1]: HELD_OUT_FUTURE (future-dated)
    # Spec card 04: billNo 599, amountPaise 4000000, issuedAt = 1792800000 + 3600*400.
    # Build the FINAL bill first, then sign it: signing before mutating issuedAt
    # produces a signature that does not match the stored bill.
    bill101 = _make_bill(
        101, "Ramesh Hardware", buyerNGO,
        4000000, CATEGORY_WATER,
    )
    bill101["billId"] = 101
    bill101["billNo"] = 599
    bill101["label"] = "HELD_OUT_FUTURE"
    bill101["expected"] = "FLAG"
    bill101["bill"]["billNo"] = 599
    bill101["bill"]["amountPaise"] = 4000000
    bill101["bill"]["issuedAt"] = 1792800000 + 3600 * 400
    # Re-sign the final bill, then recompute the nullifier over it.
    bill101["vendorSig"] = sign_bill(bill101["bill"], _vendor_key("Ramesh Hardware"))
    bill101["nullifier"] = bill_nullifier(bill101["bill"])

    return [bill100, bill101]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic bills")
    parser.add_argument(
        "--write", required=True, help="Path to write bills.json"
    )
    args = parser.parse_args()

    bills = generate_bills()
    extras = generate_extras()

    # Count labels
    counts: dict[str, int] = {
        "GENUINE": 0,
        "FORGED_EDITED_AMOUNT": 0,
        "FORGED_UNKNOWN_SIGNER": 0,
        "AMBER_SOCKPUPPET": 0,
    }
    for b in bills:
        counts[b["label"]] = counts.get(b["label"], 0) + 1

    # Write public JSON (strip _private)
    public_bills = []
    for b in bills:
        entry = {k: v for k, v in b.items() if k != "_private"}
        public_bills.append(entry)

    public_extras = []
    for b in extras:
        entry = {k: v for k, v in b.items() if k != "_private"}
        public_extras.append(entry)

    public_obj = {
        "simulated": True,
        "vendors": [
            {"name": v["name"], "address": synthetic_account("vendor:" + v["name"])["address"],
             "tier": v["tier"]}
            for v in VENDORS
        ],
        "bills": public_bills,
        "extras": public_extras,
    }

    out_path = args.write
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(public_obj, f, indent=2, ensure_ascii=True)

    # Write private JSON
    root = Path(__file__).resolve().parents[1]
    private_path = root / "sim" / "fixtures" / "private" / "bills_private.json"
    private_path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(private_path), "w", encoding="utf-8") as f:
        json.dump({"simulated": True, "items": _ITEMS}, f, indent=2, ensure_ascii=True)

    # Print summary
    summary = {"ok": True, "counts": counts}
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
