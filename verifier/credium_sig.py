"""EIP-712 hashing and signer recovery for Credium bills and allocations (plan §8b).

Must match contracts/src/PurposeVault.sol byte for byte. Hashes use eth_utils and eth_abi, never hashlib.
"""
from eth_abi import encode
from eth_keys import keys
from eth_utils import keccak, to_bytes, to_checksum_address, to_hex

# No chainId and no verifyingContract on purpose: chain-B evidence must verify on chain A.
DOMAIN_SEPARATOR = keccak(
    encode(
        ["bytes32", "bytes32", "bytes32"],
        [
            keccak(text="EIP712Domain(string name,string version)"),
            keccak(text="Credium"),
            keccak(text="1"),
        ],
    )
)

BILL_TYPEHASH = keccak(
    text="Bill(address vendor,address buyerNGO,uint256 billNo,uint256 amountPaise,"
    "uint256 issuedAt,bytes32 category,bytes32 itemsCommitment)"
)
ALLOCATION_TYPEHASH = keccak(
    text="Allocation(bytes32 billNullifier,address donorVault,uint256 chainId,"
    "uint256 fractionBps,bytes32 reportId)"
)


def bill_digest(bill: dict) -> bytes:
    """Struct hash of a Bill (plan §8b billDigest)."""
    return keccak(
        encode(
            ["bytes32", "address", "address", "uint256", "uint256", "uint256", "bytes32", "bytes32"],
            [
                BILL_TYPEHASH,
                bill["vendor"],
                bill["buyerNGO"],
                bill["billNo"],
                bill["amountPaise"],
                bill["issuedAt"],
                to_bytes(hexstr=bill["category"]),
                to_bytes(hexstr=bill["itemsCommitment"]),
            ],
        )
    )


def bill_nullifier(bill: dict) -> str:
    """Includes the full bill digest, so reusing an invoice number with different content cannot collide."""
    return to_hex(
        keccak(encode(["address", "uint256", "bytes32"], [bill["vendor"], bill["billNo"], bill_digest(bill)]))
    )


def _allocation_struct_hash(alloc: dict) -> bytes:
    return keccak(
        encode(
            ["bytes32", "bytes32", "address", "uint256", "uint256", "bytes32"],
            [
                ALLOCATION_TYPEHASH,
                to_bytes(hexstr=alloc["billNullifier"]),
                alloc["donorVault"],
                alloc["chainId"],
                alloc["fractionBps"],
                to_bytes(hexstr=alloc["reportId"]),
            ],
        )
    )


def _typed_digest(struct_hash: bytes) -> bytes:
    return keccak(b"\x19\x01" + DOMAIN_SEPARATOR + struct_hash)


def _recover(digest: bytes, sig: str) -> str:
    raw = to_bytes(hexstr=sig)
    if len(raw) != 65:
        raise ValueError("signature must be 65 bytes r||s||v")
    r = int.from_bytes(raw[:32], "big")
    s = int.from_bytes(raw[32:64], "big")
    v = raw[64]
    if v not in (27, 28):
        raise ValueError("v must be 27 or 28")
    public_key = keys.Signature(vrs=(v - 27, r, s)).recover_public_key_from_msg_hash(digest)
    return to_checksum_address(public_key.to_checksum_address())


def recover_bill_signer(bill: dict, sig: str) -> str:
    return _recover(_typed_digest(bill_digest(bill)), sig)


def recover_allocation_signer(alloc: dict, sig: str) -> str:
    return _recover(_typed_digest(_allocation_struct_hash(alloc)), sig)
