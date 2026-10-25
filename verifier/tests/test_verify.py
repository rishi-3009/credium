"""verdict() covers the 4 verdicts plus the future-dated held-out case (plan §8d, B2)."""
from sim.signing import CATEGORY_WATER, anvil_account, sign_bill
from verifier.verify import tier_of, verdict

NOW = 1_800_000_000
DAY = 24 * 60 * 60
REGISTRAR = anvil_account(0)["address"]
NGO = anvil_account(1)["address"]


def make_record(vendor_idx: int = 5, signer_idx: int | None = None, issued_at: int = NOW - DAY) -> dict:
    vendor = anvil_account(vendor_idx)
    signer = anvil_account(signer_idx if signer_idx is not None else vendor_idx)
    bill = {
        "vendor": vendor["address"],
        "buyerNGO": NGO,
        "billNo": 417,
        "amountPaise": 18000000,
        "issuedAt": issued_at,
        "category": CATEGORY_WATER,
        "itemsCommitment": "0x" + "11" * 32,
    }
    return {"bill": bill, "vendorSig": sign_bill(bill, signer["key"])}


def enrolled(vendor_idx: int, enrolled_by: str, days_ago: int) -> dict:
    return {anvil_account(vendor_idx)["address"]: {
        "name": f"vendor {vendor_idx}", "enrolledBy": enrolled_by, "enrolledAt": NOW - days_ago * DAY}}


def test_unregistered_vendor_is_unknown():
    result = verdict(make_record(vendor_idx=5), {}, REGISTRAR, NOW)
    assert result["verdict"] == "UNKNOWN"
    assert result["tier"] == 2


def test_signature_from_another_key_is_forged():
    registry = enrolled(5, REGISTRAR, days_ago=8)
    result = verdict(make_record(vendor_idx=5, signer_idx=3), registry, REGISTRAR, NOW)
    assert result["verdict"] == "FORGED"
    assert result["recoveredSigner"] == anvil_account(3)["address"]


def test_vendor_enrolled_by_someone_else_is_amber():
    registry = enrolled(5, anvil_account(2)["address"], days_ago=8)
    result = verdict(make_record(vendor_idx=5), registry, REGISTRAR, NOW)
    assert result["verdict"] == "AMBER"
    assert result["tier"] == 1


def test_registrar_enrolled_under_seven_days_is_amber():
    registry = enrolled(5, REGISTRAR, days_ago=1)
    result = verdict(make_record(vendor_idx=5), registry, REGISTRAR, NOW)
    assert result["verdict"] == "AMBER"


def test_registrar_enrolled_seven_days_is_green():
    registry = enrolled(5, REGISTRAR, days_ago=8)
    result = verdict(make_record(vendor_idx=5), registry, REGISTRAR, NOW)
    assert result["verdict"] == "GREEN"
    assert result["tier"] == 0
    assert result["recoveredSigner"] == anvil_account(5)["address"]


def test_future_dated_bill_is_green():
    # Documented held-out MISS: verdict() has no future-date check (PS honesty, B2).
    registry = enrolled(5, REGISTRAR, days_ago=8)
    result = verdict(make_record(vendor_idx=5, issued_at=NOW + 30 * DAY), registry, REGISTRAR, NOW)
    assert result["verdict"] == "GREEN"


def test_tier_of_matches_the_contract_rule():
    registry = {**enrolled(5, REGISTRAR, days_ago=8), **enrolled(6, anvil_account(2)["address"], days_ago=8)}
    assert tier_of(anvil_account(5)["address"], registry, REGISTRAR, NOW) == 0
    assert tier_of(anvil_account(6)["address"], registry, REGISTRAR, NOW) == 1
    assert tier_of(anvil_account(7)["address"], registry, REGISTRAR, NOW) == 2
