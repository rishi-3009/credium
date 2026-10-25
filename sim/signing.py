"""SIMULATED. Public test keys only."""

from eth_account import Account
from eth_abi import encode
from eth_utils import keccak
import json
import secrets

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MNEMONIC: str = "test test test test test test test test test test test junk"

BILL_TYPE: str = (
    "Bill(address vendor,address buyerNGO,uint256 billNo,uint256 amountPaise,"
    "uint256 issuedAt,bytes32 category,bytes32 itemsCommitment)"
)

ALLOC_TYPE: str = (
    "Allocation(bytes32 billNullifier,address donorVault,uint256 chainId,"
    "uint256 fractionBps,bytes32 reportId)"
)

# Domain separator: keccak(encode([bytes32,bytes32,bytes32], [TYPE_HASH, NAME_HASH, VERSION_HASH]))
_TYPE_HASH: bytes = keccak(b"EIP712Domain(string name,string version)")
NAME_HASH: bytes = keccak(b"Credium")
VERSION_HASH: bytes = keccak(b"1")
DOMAIN_SEPARATOR: str = "0x" + keccak(encode(["bytes32", "bytes32", "bytes32"], [_TYPE_HASH, NAME_HASH, VERSION_HASH])).hex()

BILL_TYPEHASH: str = "0x" + keccak(BILL_TYPE.encode()).hex()
ALLOC_TYPEHASH: str = "0x" + keccak(ALLOC_TYPE.encode()).hex()

# Category constants
CATEGORY_WATER: str = "0x" + keccak(b"WATER").hex()
CATEGORY_PPE: str = "0x" + keccak(b"PPE").hex()

# Type descriptor lists in field order
BILL_TYPES: list[dict] = [
    {"name": "vendor", "type": "address"},
    {"name": "buyerNGO", "type": "address"},
    {"name": "billNo", "type": "uint256"},
    {"name": "amountPaise", "type": "uint256"},
    {"name": "issuedAt", "type": "uint256"},
    {"name": "category", "type": "bytes32"},
    {"name": "itemsCommitment", "type": "bytes32"},
]

ALLOC_TYPES: list[dict] = [
    {"name": "billNullifier", "type": "bytes32"},
    {"name": "donorVault", "type": "address"},
    {"name": "chainId", "type": "uint256"},
    {"name": "fractionBps", "type": "uint256"},
    {"name": "reportId", "type": "bytes32"},
]

# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _b(h: str) -> bytes:
    """Convert a hex string (with or without 0x prefix) to bytes."""
    return bytes.fromhex(h[2:])


def _h(raw: bytes) -> str:
    """Convert bytes to a 0x-prefixed hex string."""
    return "0x" + raw.hex()


def _sign_struct(struct_hash: str, private_key: str) -> str:
    """Sign a struct hash per EIP-712 and return 0x-prefixed r||s||v."""
    h = keccak(b"\x19\x01" + _b(DOMAIN_SEPARATOR) + _b(struct_hash))
    sig = Account.unsafe_sign_hash(h, private_key).signature
    assert sig[64] in (27, 28)
    return _h(bytes(sig))

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def bill_digest(bill: dict) -> str:
    """Return the struct hash of a Bill (NOT the signing hash)."""
    types = [
        "bytes32", "address", "address", "uint256", "uint256",
        "uint256", "bytes32", "bytes32",
    ]
    values = [
        _b(BILL_TYPEHASH),
        bill["vendor"],
        bill["buyerNGO"],
        bill["billNo"],
        bill["amountPaise"],
        bill["issuedAt"],
        _b(bill["category"]),
        _b(bill["itemsCommitment"]),
    ]
    raw = keccak(encode(types, values))
    return _h(raw)


def bill_nullifier(bill: dict) -> str:
    """Return billNullifier = keccak(vendor || billNo || billDigest)."""
    types = ["address", "uint256", "bytes32"]
    values = [
        bill["vendor"],
        bill["billNo"],
        _b(bill_digest(bill)),
    ]
    raw = keccak(encode(types, values))
    return _h(raw)


def allocation_digest(alloc: dict) -> str:
    """Return the struct hash of an Allocation."""
    types = [
        "bytes32", "bytes32", "address", "uint256", "uint256", "bytes32",
    ]
    values = [
        _b(ALLOC_TYPEHASH),
        _b(alloc["billNullifier"]),
        alloc["donorVault"],
        alloc["chainId"],
        alloc["fractionBps"],
        _b(alloc["reportId"]),
    ]
    raw = keccak(encode(types, values))
    return _h(raw)


def items_commitment(items: list, salt: bytes) -> str:
    """Return keccak(salt + canonical JSON of items)."""
    canonical = json.dumps(items, sort_keys=True, separators=(",", ":")).encode()
    raw = keccak(salt + canonical)
    return _h(raw)


def sign_bill(bill: dict, vendor_key: str) -> str:
    """Sign a Bill struct and return 0x-prefixed r||s||v."""
    return _sign_struct(bill_digest(bill), vendor_key)


def sign_allocation(alloc: dict, ngo_key: str) -> str:
    """Sign an Allocation struct and return 0x-prefixed r||s||v."""
    return _sign_struct(allocation_digest(alloc), ngo_key)


def anvil_account(index: int) -> dict:
    """Derive an account from the public test mnemonic."""
    Account.enable_unaudited_hdwallet_features()
    acct = Account.from_mnemonic(
        MNEMONIC, account_path=f"m/44'/60'/0'/0/{index}"
    )
    return {"address": acct.address, "key": _h(bytes(acct.key))}


def synthetic_account(label: str) -> dict:
    """Derive a SIMULATED account from a label string (never funded)."""
    key_bytes = keccak(label.encode())
    acct = Account.from_key(key_bytes)
    return {"address": acct.address, "key": _h(bytes(acct.key))}
