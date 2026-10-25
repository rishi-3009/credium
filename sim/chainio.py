"""Chain IO helpers for interacting with smart contracts."""

import json
import re
from pathlib import Path
from typing import Any, Optional

from eth_utils import keccak
from eth_abi import decode

from web3 import Web3

__all__ = [
    "load_deployments",
    "load_abi",
    "web3_for",
    "contract",
    "rpc",
    "time_warp",
    "send_tx",
    "call_revert",
    "decode_revert",
    "bill_tuple",
    "alloc_tuple",
]

# Module-level cache for ABIs
_abi_cache: dict[str, list] = {}


def load_deployments(path: str) -> dict:
    """Load deployments from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_abi(name: str) -> list:
    """Load ABI from contracts/out/<name>.sol/<name>.json."""
    base = Path(__file__).resolve().parents[1]
    abi_path = base / "contracts" / "out" / f"{name}.sol" / f"{name}.json"
    if abi_path not in _abi_cache:
        with open(abi_path, "r", encoding="utf-8") as f:
            _abi_cache[abi_path] = json.load(f)["abi"]
    return list(_abi_cache.get(abi_path, []))


def web3_for(deployments: dict, chain_id: int) -> Web3:
    """Get Web3 instance for given chain."""
    rpc_url = deployments["chains"][str(chain_id)]["rpc"]
    return Web3(Web3.HTTPProvider(rpc_url))


def contract(w3: Web3, address: str, abi_name: str) -> Any:
    """Create contract instance at address with ABI."""
    return w3.eth.contract(address=Web3.to_checksum_address(address), abi=load_abi(abi_name))


def rpc(w3: Web3, method: str, params: list) -> list:
    """Make JSON-RPC call and return result or raise RuntimeError."""
    result = w3.provider.make_request(method, params)
    if isinstance(result, list) and len(result) > 0 and "error" in result[0]:
        raise RuntimeError(result[0]["error"]["message"])
    return result if isinstance(result, list) else [result]


def time_warp(w3: Web3, seconds: int) -> None:
    """Jump forward in time."""
    w3.provider.make_request("evm_increaseTime", [seconds])
    w3.provider.make_request("evm_mine", [])


def send_tx(w3: Web3, fn: Any, private_key: str, gas: int = 600000) -> dict:
    """Send transaction and wait for receipt."""
    sender_account = w3.eth.account.from_key(private_key)
    nonce = w3.eth.get_transaction_count(sender_account.address)
    tx = fn.build_transaction({
        "from": sender_account.address,
        "nonce": nonce,
        "gas": gas,
        "gasPrice": w3.eth.gas_price,
        "chainId": w3.eth.chain_id,
    })
    signed = w3.eth.account.sign_transaction(tx, private_key)
    h = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(h, timeout=30)
    return {"txHash": h.hex(), "status": receipt["status"]}


def call_revert(fn: Any, sender: str) -> str | None:
    """Call contract and return decoded revert reason or None."""
    try:
        fn.call({"from": sender})
        return None
    except Exception as e:
        error_match = re.search(r"0x[0-9a-fA-F]{8,}", str(e))
        if error_match:
            return decode_revert(error_match.group(0))
        return f"CALL_FAILED: {str(e)}"


def decode_revert(data_hex: str) -> str:
    """Decode revert reason from error data."""
    try:
        data = bytes.fromhex(data_hex.removeprefix("0x"))
    except ValueError:
        return "Unknown(unknown)"
    
    selector = data[:4].hex()
    
    # Check for Error(string)
    error_string_selector = keccak(text="Error(string)").hex()[:8]
    if selector == error_string_selector:
        try:
            decoded_str = decode(["string"], data[4:])[0]
            return f'Error("{decoded_str}")'
        except Exception:
            return 'Error("unknown")'
    
    # Try each error in ABI
    base = Path(__file__).resolve().parents[1]
    abis = {
        "MockINR": base / "contracts" / "out" / "MockINR.sol" / "MockINR.json",
        "VendorRegistry": base / "contracts" / "out" / "VendorRegistry.sol" / "VendorRegistry.json",
        "PurposeVault": base / "contracts" / "out" / "PurposeVault.sol" / "PurposeVault.json",
    }
    
    for name, abi_path in abis.items():
        if not abi_path.exists():
            continue
        try:
            with open(abi_path, "r", encoding="utf-8") as f:
                abi = json.load(f)["abi"]
        except Exception:
            continue
        
        for entry in abi:
            if entry.get("type") != "error":
                continue
            sig = entry.get("name", "") + "(" + ",".join(inp["type"] for inp in entry.get("inputs", [])) + ")"
            expected_sig = keccak(text=sig).hex()[:8]
            if selector == expected_sig:
                types = [inp["type"] for inp in entry.get("inputs", [])]
                try:
                    decoded = decode(types, data[4:])
                    formatted = format_decode(decoded, entry)
                    return formatted
                except Exception:
                    continue
    
    return f"Unknown(0x{data_hex[:8]})"


def format_decode(decoded, entry):
    """Format decoded values with checksummed addresses."""
    parts = []
    for i, (inp, val) in enumerate(zip(entry.get("inputs", []), decoded)):
        if inp["type"] == "address":
            parts.append(f'"{Web3.to_checksum_address(val)}"')
        elif inp["type"] == "string":
            parts.append(f'"{val}"')
        elif inp["type"].startswith("uint") or inp["type"].startswith("int"):
            parts.append(str(val))
        else:
            parts.append(f'"{val}"')
    return f"{entry['name']}({', '.join(parts)})"


def bill_tuple(b: dict) -> tuple:
    """Parse bill dictionary to tuple."""
    return (
        b["vendor"],
        b["buyerNGO"],
        b["billNo"],
        b["amountPaise"],
        b["issuedAt"],
        b["category"],
        b["itemsCommitment"],
    )


def alloc_tuple(a: dict) -> tuple:
    """Parse allocation dictionary to tuple."""
    bill_nullifier = Web3.to_bytes(hexstr=a["billNullifier"])[:32]
    return (
        bill_nullifier,
        a["donorVault"],
        a["chainId"],
        a["fractionBps"],
        a["reportId"],
    )
