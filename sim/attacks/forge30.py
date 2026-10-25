"""Forge 30% attack: submit 30 forged bills + 1 wrong-category bill to the WATER vault.

Every forged bill must revert with the right error. Output a row per bill and a summary.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from sim.chainio import (
    load_deployments,
    web3_for,
    contract,
    call_revert,
    send_tx,
    bill_tuple,
    alloc_tuple,
)
from sim.signing import bill_nullifier, sign_allocation, anvil_account, CATEGORY_WATER

# Constants
ATTACKER_KEY_IDX = 9
TARGET_CHAIN = 31337


def run(deployments_path: str, bills_path: str) -> dict:
    """Submit 30 forged bills + 1 wrong-category bill and record reverts.

    Returns {"simulated": true, "rows": [...], "summary": {...}}
    """
    deployments = load_deployments(deployments_path)
    with open(bills_path, "r", encoding="utf-8") as f:
        bills_data = json.load(f)

    w3 = web3_for(deployments, TARGET_CHAIN)
    vault = contract(w3, deployments["chains"][str(TARGET_CHAIN)]["vault"], "PurposeVault")

    attacker = anvil_account(ATTACKER_KEY_IDX)
    attacker_address = w3.eth.account.from_key(attacker["key"]).address
    ngo_key = anvil_account(1)["key"]

    # Step 2: Collect forged entries (label starts with FORGED_ or equals AMBER_SOCKPUPPET)
    forged = [b for b in bills_data["bills"]
              if b["label"].startswith("FORGED_") or b["label"] == "AMBER_SOCKPUPPET"]
    assert len(forged) == 30, f"Expected 30 forged entries, got {len(forged)}"

    # Find the WRONG_CATEGORY extra
    wrong_category_extra = None
    for b in bills_data.get("extras", []):
        if b["label"] == "WRONG_CATEGORY":
            wrong_category_extra = b
            break

    rows = []

    # Step 3-6: Process each row
    for entry in forged + ([wrong_category_extra] if wrong_category_extra else []):
        bill = entry["bill"]

        # Build allocation
        alloc = {
            "billNullifier": entry["nullifier"],
            "donorVault": deployments["chains"][str(TARGET_CHAIN)]["vault"],
            "chainId": TARGET_CHAIN,
            "fractionBps": 10000,
            "reportId": entry["reportId"],
        }
        ngo_sig = sign_allocation(alloc, ngo_key["key"])

        # Build release function call
        release_fn = vault.functions.release(
            bill_tuple(bill),
            bytes.fromhex(entry["vendorSig"][2:]),
            alloc_tuple(alloc),
            bytes.fromhex(ngo_sig[2:]),
        )

        # Step 4: Check revert first
        revert = call_revert(release_fn, attacker_address)

        if revert is None:
            # Step 5: Send the real transaction
            receipt = send_tx(w3, release_fn, attacker["key"], gas=600000)
            status_str = "reverted" if receipt["status"] == 0 else "PASSED"
            row = {
                "billId": entry["billId"],
                "billNo": entry["billNo"],
                "label": entry["label"],
                "kind": "WRONG_CATEGORY" if entry["label"] == "WRONG_CATEGORY" else "FORGED",
                "expected": entry["expected"],
                "revert": "NONE",
                "txHash": receipt["txHash"],
                "status": status_str,
            }
        else:
            # Reverted as expected
            receipt = send_tx(w3, release_fn, attacker["key"], gas=600000)
            row = {
                "billId": entry["billId"],
                "billNo": entry["billNo"],
                "label": entry["label"],
                "kind": "WRONG_CATEGORY" if entry["label"] == "WRONG_CATEGORY" else "FORGED",
                "expected": entry["expected"],
                "revert": revert,
                "txHash": receipt["txHash"],
                "status": "reverted",
            }

        rows.append(row)

    # Step 7: Summary
    forged_rows = [r for r in rows if r["kind"] == "FORGED"]
    wrong_category_rows = [r for r in rows if r["kind"] == "WRONG_CATEGORY"]

    reverted = sum(1 for r in forged_rows if r["status"] == "reverted")
    tier_blocked = sum(1 for r in forged_rows if r["revert"].startswith("TierNotGreen"))
    missed = sum(1 for r in forged_rows if r["status"] == "PASSED")
    wrong_cat_ok = any(r["revert"].startswith("WrongCategory") for r in wrong_category_rows) if wrong_category_rows else False

    summary = {
        "reverted": reverted,
        "tierBlocked": tier_blocked,
        "missed": missed,
        "wrongCategory": 1 if wrong_cat_ok else 0,
    }

    # Step 8: Print result
    result = {"simulated": True, "rows": rows, "summary": summary}
    print(json.dumps(result, ensure_ascii=True))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Forge 30% attack")
    parser.add_argument("--deployments", required=True, help="Path to deployments JSON")
    parser.add_argument("--bills", required=True, help="Path to bills JSON")
    args = parser.parse_args()

    run(args.deployments, args.bills)


if __name__ == "__main__":
    main()
