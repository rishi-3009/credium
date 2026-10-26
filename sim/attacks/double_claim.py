"""Double claim attack: release the same bill on both chains 31337 and 31338.

Each chain alone says PASS. The watcher catches the pair.
"""

import argparse
import json
import os
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
from sim.signing import sign_allocation, anvil_account


def run(billNo: int, fractionBps: int, deployments_path: str,
        bills_path: str = "sim/fixtures/bills.json") -> dict:
    """Release the same bill on both chains and record results.

    Returns {"simulated": true, "billNo": N, "fractionBps": F, "steps": [...]}
    """
    deployments = load_deployments(deployments_path)

    # Resolve bills_path relative to project root if not absolute
    if not os.path.isabs(bills_path):
        project_root = Path(__file__).resolve().parents[2]
        bills_path = str(project_root / bills_path)

    with open(bills_path, "r", encoding="utf-8") as f:
        bills_data = json.load(f)

    # Step 2: Find entry by billNo
    entry = None
    for b in bills_data["bills"]:
        if b["billNo"] == billNo:
            entry = b
            break

    if entry is None:
        raise ValueError(f"No bill with billNo={billNo} found in {bills_path}")
    if entry["label"] != "GENUINE":
        raise ValueError("bill is not GENUINE")

    sender = anvil_account(6)
    sender_address = web3_for(deployments, 31337).eth.account.from_key(sender["key"]).address
    ngo_key = anvil_account(1)["key"]

    steps = []

    # Step 3: For each chain, build alloc and ngoSig
    for c in [31337, 31338]:
        w3 = web3_for(deployments, c)
        vault = contract(w3, deployments["chains"][str(c)]["vault"], "PurposeVault")

        chain_vault = deployments["chains"][str(c)]["vault"]

        alloc = {
            "billNullifier": entry["nullifier"],
            "donorVault": chain_vault,
            "chainId": c,
            "fractionBps": fractionBps,
            "reportId": entry["reportId"],
        }
        ngo_sig = sign_allocation(alloc, ngo_key)

        bill = entry["bill"]

        # Step 4: Check revert first
        release_fn = vault.functions.release(
            bill_tuple(bill),
            bytes.fromhex(entry["vendorSig"][2:]),
            alloc_tuple(alloc),
            bytes.fromhex(ngo_sig[2:]),
        )

        revert = call_revert(release_fn, sender_address)

        if revert is not None:
            # Step 4b: Reverted
            step = {
                "chainId": c,
                "result": revert,
                "perChainCheck": "FAIL",
                "txHash": None,
            }
        else:
            # Step 5: Send the real transaction
            receipt = send_tx(w3, release_fn, sender["key"], gas=600000)
            if receipt["status"] == 1:
                step = {
                    "chainId": c,
                    "result": "OK",
                    "perChainCheck": "PASS",
                    "txHash": receipt["txHash"],
                }
            else:
                step = {
                    "chainId": c,
                    "result": "REVERTED",
                    "perChainCheck": "FAIL",
                    "txHash": receipt["txHash"],
                }

        steps.append(step)

    # Step 6: Print result
    result = {
        "simulated": True,
        "billNo": billNo,
        "fractionBps": fractionBps,
        "steps": steps,
    }
    print(json.dumps(result, ensure_ascii=True))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Double claim attack")
    parser.add_argument("--billNo", type=int, required=True, help="Bill number to double-claim")
    parser.add_argument("--fractionBps", type=int, required=True, help="Fraction in basis points")
    parser.add_argument("--deployments", type=str, required=True, help="Path to deployments JSON")
    parser.add_argument("--bills", type=str, default="sim/fixtures/bills.json",
                        help="Path to bills JSON (default: sim/fixtures/bills.json)")
    args = parser.parse_args()

    run(args.billNo, args.fractionBps, args.deployments, args.bills)


if __name__ == "__main__":
    main()
