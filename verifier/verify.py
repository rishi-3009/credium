"""Bill verdicts (plan §8d, §8a tierOf). SIMULATED.

verdict order: unregistered -> UNKNOWN; recovered != claimed vendor -> FORGED; tier 1 -> AMBER; tier 0 -> GREEN.
`now` is the latest chain block timestamp, never the wall clock (B2).
There is NO future-dated check: a bill dated after `now` is still GREEN. That is the documented held-out MISS.
"""
from eth_utils import to_checksum_address

from verifier.credium_sig import recover_bill_signer

GREEN_AGE = 7 * 24 * 60 * 60  # VendorRegistry.GREEN_AGE = 7 days


def _same(a: str, b: str) -> bool:
    return to_checksum_address(a) == to_checksum_address(b)


def tier_of(vendor: str, registry: dict, registrar: str, now: int) -> int:
    """Python mirror of VendorRegistry.tierOf. 0 GREEN, 1 AMBER, 2 UNREGISTERED."""
    entry = registry.get(to_checksum_address(vendor))
    if entry is None:
        return 2
    if _same(entry["enrolledBy"], registrar) and now >= entry["enrolledAt"] + GREEN_AGE:
        return 0
    return 1


def verdict(record: dict, registry: dict, registrar: str, now: int) -> dict:
    """record = {"bill": {...}, "vendorSig": "0x...", ...}; registry = {address: {name, enrolledBy, enrolledAt}}."""
    bill = record["bill"]
    vendor = to_checksum_address(bill["vendor"])
    registry = {to_checksum_address(k): v for k, v in registry.items()}
    try:
        recovered = recover_bill_signer(bill, record["vendorSig"])
    except ValueError as e:
        return {"verdict": "FORGED", "tier": 2, "recoveredSigner": "", "reason": f"unreadable vendor signature: {e}"}

    if vendor not in registry:
        return {"verdict": "UNKNOWN", "tier": 2, "recoveredSigner": recovered, "reason": "vendor not registered"}

    tier = tier_of(vendor, registry, registrar, now)
    if recovered != vendor:
        return {"verdict": "FORGED", "tier": tier, "recoveredSigner": recovered,
                "reason": "vendor signature does not match the claimed vendor"}
    if tier == 1:
        return {"verdict": "AMBER", "tier": 1, "recoveredSigner": recovered,
                "reason": "vendor not enrolled by the registrar, or enrolled under 7 days"}
    return {"verdict": "GREEN", "tier": 0, "recoveredSigner": recovered,
            "reason": "registrar-enrolled vendor, enrolled 7+ days"}
