"""Independent EIP-712 signer for tests. Built only on eth_account. Must NOT import credium_sig.

This also stands in for Ayaan's sim/signing.py until his card A1 is frozen at 13:50.
"""
import os

from eth_account import Account
from eth_account.messages import encode_typed_data
from eth_utils import to_hex

DOMAIN = {"name": "Credium", "version": "1"}

TYPES = {
    "Bill": [
        {"name": "vendor", "type": "address"},
        {"name": "buyerNGO", "type": "address"},
        {"name": "billNo", "type": "uint256"},
        {"name": "amountPaise", "type": "uint256"},
        {"name": "issuedAt", "type": "uint256"},
        {"name": "category", "type": "bytes32"},
        {"name": "itemsCommitment", "type": "bytes32"},
    ],
    "Allocation": [
        {"name": "billNullifier", "type": "bytes32"},
        {"name": "donorVault", "type": "address"},
        {"name": "chainId", "type": "uint256"},
        {"name": "fractionBps", "type": "uint256"},
        {"name": "reportId", "type": "bytes32"},
    ],
}


def _sign(primary_type: str, message: dict, private_key: str) -> str:
    # Three-argument form: domain, custom types (without EIP712Domain), message.
    signable = encode_typed_data(
        domain_data=DOMAIN,
        message_types={primary_type: TYPES[primary_type]},
        message_data=message,
    )
    signed = Account.sign_message(signable, private_key=private_key)
    return to_hex(signed.signature)


def sign_bill(bill: dict, vendor_key: str) -> str:
    return _sign("Bill", bill, vendor_key)


def sign_allocation(alloc: dict, ngo_key: str | None = None) -> str:
    # NGO key comes from the environment and is never committed.
    key = ngo_key or os.environ["NGO_KEY"]
    return _sign("Allocation", alloc, key)
