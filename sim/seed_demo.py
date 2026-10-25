"""Seed demo module: enroll vendors, warp time, fund chains, and save snapshot.

Numbered steps:
1. On BOTH chains: for each VENDORS entry with tier GREEN, send `registry.enroll(address, name)` signed with the registrar key.
2. time_warp(w3, 691200) on BOTH chains (so GREEN vendors are older than 7 days).
3. On BOTH chains: for each VENDORS entry with tier AMBER, send `enroll(address, name)` signed with the NGO key.
4. Funding. On 31337: mint EVAL_FUND + DEPOSIT_A to Donor A on the token; approve the vault for DEPOSIT_A, then `vault.deposit(DEPOSIT_A)` from Donor A; approve evalVault for EVAL_FUND, then `evalVault.deposit(EVAL_FUND)` from Donor A. On 31338: mint DEPOSIT_B to Donor B; approve the vault; `vault.deposit(DEPOSIT_B)` from Donor B.
5. Snapshot: `rpc(w3, "evm_snapshot", [])` on each chain. Write JSON `{"simulated": true, "snapshots": {"31337": "0x..", "31338": "0x.."}, "deposits": {"31337": DEPOSIT_A, "31338": DEPOSIT_B}}` to out_snapshot. Make NO releases.
"""

import argparse
import json
import os

from sim.chainio import load_deployments, web3_for, contract, send_tx, rpc, time_warp, call_revert, decode_revert
from sim.signing import anvil_account, synthetic_account
from sim.gen_bills import VENDORS

# Constants
DEPOSIT_A = 1380000000
DEPOSIT_B = 760000000
EVAL_FUND = 1000000000
WARP = 691200

# Registrar and NGO account indices
REGISTRAR_IDX = 0
NGO_IDX = 1

# Donor account indices
DONOR_A_IDX = 6  # funds chain 31337
DONOR_B_IDX = 7  # funds chain 31338


def _send(w3, fn, private_key):
    """Helper to call a contract function with revert check before sending."""
    sender = w3.eth.account.from_key(private_key).address
    revert_reason = call_revert(fn, sender)
    if revert_reason is not None:
        raise RuntimeError(f"Call reverted: {revert_reason}")
    tx_result = send_tx(w3, fn, private_key)
    if tx_result["status"] != 1:
        raise RuntimeError(f"Transaction failed: {tx_result}")
    return tx_result


def seed(deployments_path: str, out_snapshot: str) -> dict:
    """Seed the demo state on both chains."""
    deployments = load_deployments(deployments_path)
    chains = deployments["chains"]
    
    # Get registrar and NGO account keys
    registrar = anvil_account(REGISTRAR_IDX)
    ngo = anvil_account(NGO_IDX)
    
    # Get donor account keys
    donor_a = anvil_account(DONOR_A_IDX)
    donor_b = anvil_account(DONOR_B_IDX)
    
    # Separate vendors by tier
    green_vendors = [v["name"] for v in VENDORS if v["tier"] == "GREEN"]
    amber_vendors = [v["name"] for v in VENDORS if v["tier"] == "AMBER"]
    
    results = {}
    
    for chain_id in [31337, 31338]:
        w3 = web3_for(deployments, chain_id)
        chain_name = str(chain_id)
        
        registry = contract(w3, chains[chain_name]["registry"], "VendorRegistry")
        token = contract(w3, chains[chain_name]["token"], "MockINR")
        vault = contract(w3, chains[chain_name]["vault"], "PurposeVault")
        has_eval_vault = "evalVault" in chains[chain_name]
        
        if has_eval_vault:
            eval_vault = contract(w3, chains[chain_name]["evalVault"], "PurposeVault")
        else:
            eval_vault = None
        
        results[chain_name] = {}
        
        # Step 1: Enroll GREEN vendors on both chains
        for vendor_name in green_vendors:
            vendor_addr = synthetic_account("vendor:" + vendor_name)["address"]
            registry_enroll = registry.functions.enroll(vendor_addr, vendor_name)
            _send(w3, registry_enroll, registrar["key"])
        
        # Step 2: Time warp
        time_warp(w3, WARP)
        
        # Step 3: Enroll AMBER vendors
        for vendor_name in amber_vendors:
            vendor_addr = synthetic_account("vendor:" + vendor_name)["address"]
            registry_enroll = registry.functions.enroll(vendor_addr, vendor_name)
            _send(w3, registry_enroll, ngo["key"])
        
        # Step 4: Funding
        if chain_id == 31337:
            # Mint to Donor A
            mint = token.functions.mint(donor_a["address"], EVAL_FUND + DEPOSIT_A)
            _send(w3, mint, donor_a["key"])
            
            # Approve vault
            approve = token.functions.approve(vault.address, DEPOSIT_A)
            _send(w3, approve, donor_a["key"])
            
            # Deposit to vault
            vault_deposit = vault.functions.deposit(DEPOSIT_A)
            _send(w3, vault_deposit, donor_a["key"])
            
            # Approve evalVault
            approve_eval = token.functions.approve(eval_vault.address, EVAL_FUND)
            _send(w3, approve_eval, donor_a["key"])
            
            # Deposit to evalVault
            eval_deposit = eval_vault.functions.deposit(EVAL_FUND)
            _send(w3, eval_deposit, donor_a["key"])
        
        else:  # chain_id == 31338
            # Mint to Donor B
            mint = token.functions.mint(donor_b["address"], DEPOSIT_B)
            _send(w3, mint, donor_b["key"])
            
            # Approve vault
            approve = token.functions.approve(vault.address, DEPOSIT_B)
            _send(w3, approve, donor_b["key"])
            
            # Deposit to vault
            vault_deposit = vault.functions.deposit(DEPOSIT_B)
            _send(w3, vault_deposit, donor_b["key"])
        
        # Step 5: Snapshot
        snap_result = rpc(w3, "evm_snapshot", [])
        # rpc() wraps non-list responses in a list; extract actual snapshot ID
        if isinstance(snap_result, list) and len(snap_result) > 0:
            inner = snap_result[0]
            snap_id = inner["result"] if isinstance(inner, dict) else inner
        else:
            snap_id = snap_result if isinstance(snap_result, str) else str(snap_result)
        results[chain_name]["snapshot"] = snap_id
        
        results[chain_name]["deposits"] = DEPOSIT_A if chain_id == 31337 else DEPOSIT_B
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_snapshot), exist_ok=True)
    
    # Write snapshot
    # Format: {"simulated": true, "snapshots": {"31337": "0x..", "31338": "0x.."}, "deposits": {...}}
    snapshot_data = {
        "simulated": True,
        "snapshots": {
            "31337": results["31337"]["snapshot"],
            "31338": results["31338"]["snapshot"]
        },
        "deposits": {
            "31337": DEPOSIT_A,
            "31338": DEPOSIT_B
        }
    }
    
    with open(out_snapshot, "w", encoding="utf-8") as f:
        json.dump(snapshot_data, f)
    
    return {"ok": True, "snapshots": snapshot_data}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo chains")
    parser.add_argument("--deployments", required=True, help="Path to deployments JSON")
    parser.add_argument("--out", default="sim/fixtures/snapshot.json", help="Path to write snapshot JSON")
    args = parser.parse_args()
    
    result = seed(args.deployments, args.out)
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
