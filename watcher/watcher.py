"""Pure logic: no network, no files."""

from itertools import combinations


def find_equivocations(released: list) -> list:
    """Find two NGO-signed allocations of the same bill that add up to more than 100%.

    Args:
        released: list of Released records, each a dict with keys:
            chainId, billNo, billNullifier, ngo, donorVault, fractionBps,
            reportId, ngoSig.

    Returns:
        list of dicts, each with keys:
            billNo, billNullifier, ngo, signedTotalBps, a, b.
    """
    # Step 1: Build groups keyed by (billNullifier.lower(), ngo.lower())
    groups: dict[tuple, list] = {}
    for record in released:
        key = (record["billNullifier"].lower(), record["ngo"].lower())
        groups.setdefault(key, []).append(record)

    # Step 2-4: Check each group for equivocations
    equivocations: list[dict] = []
    for group in groups.values():
        if len(group) < 2:
            continue
        for i, j in combinations(range(len(group)), 2):
            a = group[i]
            b = group[j]

            # Step 3: Skip if they represent the same allocation
            identity_a = (
                a["donorVault"].lower(),
                a["chainId"],
                a["fractionBps"],
                a["reportId"].lower(),
            )
            identity_b = (
                b["donorVault"].lower(),
                b["chainId"],
                b["fractionBps"],
                b["reportId"].lower(),
            )
            if identity_a == identity_b:
                continue

            # Step 4: Check for equivocation
            total = a["fractionBps"] + b["fractionBps"]
            if total > 10000:
                equivocations.append({
                    "billNo": a["billNo"],
                    "billNullifier": a["billNullifier"],
                    "ngo": a["ngo"],
                    "signedTotalBps": total,
                    "a": a,
                    "b": b,
                })

    # Step 5: Sort results
    equivocations.sort(key=lambda x: (x["billNo"], x["a"]["chainId"], x["b"]["chainId"]))

    return equivocations


"""Append to watcher.py: scan_once + CLI."""

import argparse
import json
import os
import sys

from sim.chainio import (
    load_deployments,
    web3_for,
    contract,
    send_tx,
    call_revert,
    alloc_tuple,
    alloc_struct_tuple,
    decode_revert,
)
from sim.signing import anvil_account


WATCHER_KEY = os.environ.get("WATCHER_KEY") or anvil_account(8)["key"]


def scan_once(deployments_path: str) -> dict:
    """Read every Released event, find equivocations, submit to both vaults."""
    try:
        dep = load_deployments(deployments_path)

        # Step 2: Collect Released events from both chains
        records = []
        for c in ["31337", "31338"]:
            w3 = web3_for(dep, c)
            vault = contract(w3, dep["chains"][c]["vault"], "PurposeVault")
            logs = vault.events.Released.get_logs(from_block=0)
            for log in logs:
                args = log["args"]
                billNullifier_hex = "0x" + args.billNullifier.hex()
                reportId_hex = "0x" + args.reportId.hex()
                alloc = {
                    "billNullifier": billNullifier_hex,
                    "donorVault": args.donorVault,
                    "chainId": args.chainId,
                    "fractionBps": args.fractionBps,
                    "reportId": reportId_hex,
                }
                ngo_addr = vault.functions.allocationSigner(
                    alloc_tuple(alloc), bytes.fromhex(args.ngoSig.hex())
                ).call()
                records.append({
                    "chainId": int(c),
                    "billNo": args.billNo,
                    "billNullifier": billNullifier_hex,
                    "ngo": ngo_addr,
                    "donorVault": args.donorVault,
                    "fractionBps": args.fractionBps,
                    "reportId": reportId_hex,
                    "ngoSig": "0x" + args.ngoSig.hex(),
                })

        # Step 4: Find equivocations
        equivocations = find_equivocations(records)

        # Step 5: Submit each equivocation to both vaults
        for eq in equivocations:
            for c in [31337, 31338]:
                w3 = web3_for(dep, c)
                vault = contract(w3, dep["chains"][str(c)]["vault"], "PurposeVault")

                alloc_a = {
                    "billNullifier": eq["a"]["billNullifier"],
                    "donorVault": eq["a"]["donorVault"],
                    "chainId": eq["a"]["chainId"],
                    "fractionBps": eq["a"]["fractionBps"],
                    "reportId": eq["a"]["reportId"],
                }
                alloc_b = {
                    "billNullifier": eq["b"]["billNullifier"],
                    "donorVault": eq["b"]["donorVault"],
                    "chainId": eq["b"]["chainId"],
                    "fractionBps": eq["b"]["fractionBps"],
                    "reportId": eq["b"]["reportId"],
                }

                fn = vault.functions.submitEquivocation(
                    alloc_struct_tuple(alloc_a),
                    bytes.fromhex(eq["a"]["ngoSig"][2:]),
                    alloc_struct_tuple(alloc_b),
                    bytes.fromhex(eq["b"]["ngoSig"][2:]),
                )

                result = {"chainId": c, "status": "FROZEN"}

                if vault.functions.frozen().call():
                    result["status"] = "FROZEN"
                else:
                    send_tx(w3, fn, WATCHER_KEY, gas=600000)
                    if vault.functions.frozen().call():
                        result["status"] = "FROZEN"
                    else:
                        revert_text = call_revert(fn, w3.eth.accounts[0])
                        if revert_text:
                            result["status"] = f"FAILED: {decode_revert(revert_text)}"
                        else:
                            result["status"] = "FAILED: unknown"

                eq.setdefault("submitted", []).append(result)

        # Step 6: Build result
        equivs_out = []
        for eq in equivocations:
            equivs_out.append({
                "billNo": eq["billNo"],
                "billNullifier": eq["billNullifier"],
                "ngo": eq["ngo"],
                "signedTotalBps": eq["signedTotalBps"],
                "submitted": eq.get("submitted", []),
            })

        return {"simulated": True, "equivocations": equivs_out, "error": None}

    except Exception as e:
        return {"simulated": True, "equivocations": [], "error": str(e)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Watcher")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--deployments", type=str, help="Path to deployments JSON")
    args = parser.parse_args()

    if args.once:
        if not args.deployments:
            print("Error: --deployments is required with --once", file=sys.stderr)
            sys.exit(1)
        result = scan_once(args.deployments)
        print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
