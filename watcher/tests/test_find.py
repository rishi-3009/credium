"""Tests for find_equivocations."""

from watcher.watcher import find_equivocations

# Shared constants for test records
NULLIFIER = "0x" + "ab" * 32
REPORT_ID = "0x" + "11" * 32
NGO = "0x" + "22" * 20


def make_record(chain_id, bill_no, donor_vault, fraction_bps):
    """Helper to create a Released record."""
    return {
        "chainId": chain_id,
        "billNo": bill_no,
        "billNullifier": NULLIFIER,
        "ngo": NGO,
        "donorVault": donor_vault,
        "fractionBps": fraction_bps,
        "reportId": REPORT_ID,
        "ngoSig": "0x" + "ff" * 32,
    }


def test_equivocation_same_nullifier_same_ngo():
    """Two records, same nullifier and ngo: chain 31337 fraction 10000 vault 0xAAA,
    chain 31338 fraction 10000 vault 0xBBB → 1 item, signedTotalBps 20000."""
    records = [
        make_record(31337, 1, "0xAAA", 10000),
        make_record(31338, 1, "0xBBB", 10000),
    ]
    result = find_equivocations(records)
    assert len(result) == 1
    assert result[0]["signedTotalBps"] == 20000


def test_no_equivocation_equal_fractions():
    """Fractions 5000 and 5000 → [] (sum is not above 10000)."""
    records = [
        make_record(31337, 1, "0xAAA", 5000),
        make_record(31338, 1, "0xBBB", 5000),
    ]
    result = find_equivocations(records)
    assert len(result) == 0


def test_equivocation_high_fractions():
    """Fractions 6000 and 6000 on two chains → 1 item, signedTotalBps 12000."""
    records = [
        make_record(31337, 1, "0xAAA", 6000),
        make_record(31338, 1, "0xBBB", 6000),
    ]
    result = find_equivocations(records)
    assert len(result) == 1
    assert result[0]["signedTotalBps"] == 12000


def test_different_ngo():
    """Same nullifier, different ngo → []"""
    records = [
        make_record(31337, 1, "0xAAA", 10000),
        make_record(31338, 1, "0xBBB", 10000),
    ]
    # Override ngo on second record
    records[1]["ngo"] = "0x" + "33" * 20
    result = find_equivocations(records)
    assert len(result) == 0


def test_identical_allocation():
    """Identical allocation twice (same vault, chain, fraction, reportId) → []"""
    records = [
        make_record(31337, 1, "0xAAA", 10000),
        make_record(31337, 1, "0xAAA", 10000),
    ]
    result = find_equivocations(records)
    assert len(result) == 0
