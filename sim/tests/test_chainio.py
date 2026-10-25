import pytest
from pathlib import Path

from eth_utils import keccak
from eth_abi import encode

from sim.chainio import decode_revert, bill_tuple, alloc_tuple

# Check if ABI files exist (written by Rishi's forge build from 15:30)
_base = Path(__file__).resolve().parents[2]
_abi_available = (
    (_base / "contracts" / "out" / "MockINR.sol" / "MockINR.json").exists()
    and (_base / "contracts" / "out" / "VendorRegistry.sol" / "VendorRegistry.json").exists()
    and (_base / "contracts" / "out" / "PurposeVault.sol" / "PurposeVault.json").exists()
)


def test_decode_revert_error_string():
    """Test decode_revert with Error(string) example."""
    # Error(string) selector
    selector = keccak(text="Error(string)").hex()[:8]
    # Pad to 32 bytes
    data = bytes.fromhex(selector) + b"\x00" * 28 + b"hello world"
    data_hex = data.hex()
    result = decode_revert(data_hex)
    assert "Error" in result


@pytest.mark.skipif(not _abi_available, reason="ABI files not yet written by forge build")
def test_decode_revert_tier_not_green():
    """Test decode_revert with TierNotGreen(uint8) example."""
    # Simulate TierNotGreen(1) error
    selector = keccak(text="TierNotGreen(uint8)").hex()[:8]
    data = bytes.fromhex(selector) + encode(["uint8"], [1])
    data_hex = data.hex()
    result = decode_revert(data_hex)
    assert "TierNotGreen" in result


@pytest.mark.skipif(not _abi_available, reason="ABI files not yet written by forge build")
def test_decode_revert_vault_frozen():
    """Test decode_revert with VaultFrozen(string) example."""
    # Simulate VaultFrozen("equivocation") error
    selector = keccak(text="VaultFrozen(string)").hex()[:8]
    data = bytes.fromhex(selector) + encode(["string"], ["equivocation"])
    data_hex = data.hex()
    result = decode_revert(data_hex)
    assert "VaultFrozen" in result


def test_decode_revert_unknown():
    """Test decode_revert with unknown selector."""
    result = decode_revert("0x1234567800000000000000000000000000000000000000000000000000000000")
    assert "Unknown" in result


def test_bill_tuple():
    """Test bill_tuple on sample dict."""
    b = {
        "vendor": "0x0000000000000000000000000000000000000001",
        "buyerNGO": "0x0000000000000000000000000000000000000002",
        "billNo": 12345,
        "amountPaise": 100000,
        "issuedAt": "2024-01-01T00:00:00Z",
        "category": b"food",
        "itemsCommitment": b"rice, wheat",
    }
    result = bill_tuple(b)
    assert len(result) == 7
    assert result[0] == b["vendor"]
    assert result[1] == b["buyerNGO"]
    assert result[2] == b["billNo"]
    assert result[3] == b["amountPaise"]
    assert result[4] == b["issuedAt"]
    assert result[5] == b["category"]
    assert result[6] == b["itemsCommitment"]


def test_alloc_tuple():
    """Test alloc_tuple on sample dict."""
    a = {
        "billNullifier": "0x" + "00" * 64,
        "donorVault": "0x0000000000000000000000000000000000000003",
        "chainId": 31337,
        "fractionBps": 100,
        "reportId": b"report123",
    }
    result = alloc_tuple(a)
    assert len(result) == 5
    # billNullifier should be 32-byte bytes from hex string
    assert len(result[0]) == 32
    assert result[1] == a["donorVault"]
    assert result[2] == a["chainId"]
    assert result[3] == a["fractionBps"]
    assert result[4] == a["reportId"]
