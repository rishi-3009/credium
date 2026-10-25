"""Tests for sim/gen_bills.py."""

from sim.gen_bills import generate_bills, generate_extras, VENDORS


def test_count_100_bills():
    bills = generate_bills()
    assert len(bills) == 100


def test_label_counts():
    bills = generate_bills()
    counts = {}
    for b in bills:
        counts[b["label"]] = counts.get(b["label"], 0) + 1
    assert counts["GENUINE"] == 70
    assert counts["FORGED_EDITED_AMOUNT"] == 18
    assert counts["FORGED_UNKNOWN_SIGNER"] == 7
    assert counts["AMBER_SOCKPUPPET"] == 5


def test_pin_bills_5_17_18():
    bills = generate_bills()
    bill_map = {b["billId"]: b for b in bills}
    for bid in (5, 17, 18):
        b = bill_map[bid]
        assert b["label"] == "GENUINE"
        assert b["expected"] == "GREEN"
        vendor_tier = next(v["tier"] for v in VENDORS if v["name"] == b["vendorName"])
        assert vendor_tier == "GREEN", f"billId {bid} vendor {b['vendorName']} should be GREEN"


def test_bill_17_amount_and_no():
    bills = generate_bills()
    bill_map = {b["billId"]: b for b in bills}
    b17 = bill_map[17]
    assert b17["billNo"] == 417
    assert b17["bill"]["amountPaise"] == 18000000


def test_bill_17_issuedAt():
    bills = generate_bills()
    bill_map = {b["billId"]: b for b in bills}
    b17 = bill_map[17]
    assert b17["bill"]["issuedAt"] == 1792861200


def test_extras_category_and_billNo():
    extras = generate_extras()
    assert len(extras) == 2
    assert extras[0]["bill"]["category"] == "0x9adecaf25b3c35d4e7a76a0173d42d1ab4288c9a4d5e284038214365835af808"  # CATEGORY_PPE
    assert extras[0]["label"] == "WRONG_CATEGORY"
    assert extras[1]["billNo"] == 599
