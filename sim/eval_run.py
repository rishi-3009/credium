import argparse
import json
import os
from datetime import datetime, timezone
from typing import Optional

from sim.chainio import load_deployments, web3_for, contract, call_revert, bill_tuple, alloc_tuple
from sim.signing import sign_allocation, anvil_account


try:
    from verifier.verify import verdict_for_entry
except ImportError:
    verdict_for_entry = None


def is_positive(label: str) -> bool:
    """Check if label is a positive (attack) case."""
    return label.startswith("FORGED_") or label == "AMBER_SOCKPUPPET"


def run(deployments_path: str, bills_path: str, out: str = "sim/fixtures/eval.json") -> dict:
    """Run evaluation on bills and write results to JSON file."""
    dep = load_deployments(deployments_path)
    bills = json.load(open(bills_path, "r", encoding="utf-8"))
    w3 = web3_for(dep, 31337)
    evalVault = dep["chains"]["31337"]["evalVault"]
    vault = contract(w3, evalVault, "PurposeVault")

    rows = []
    for entry in bills["bills"]:
        alloc = {
            "billNullifier": entry["nullifier"],
            "donorVault": evalVault,
            "chainId": 31337,
            "fractionBps": 10000,
            "reportId": entry["reportId"],
        }
        ngoSig = sign_allocation(alloc, anvil_account(1)["key"])
        
        chain_result = call_revert(
            vault.functions.release,
            bill_tuple(entry["bill"]),
            bytes.fromhex(entry["vendorSig"][2:]),
            alloc_tuple(alloc),
            bytes.fromhex(ngoSig[2:]),
            anvil_account(9)["address"],
        )
        
        flagged = chain_result is not None
        row = {
            "billId": entry["billId"],
            "billNo": entry["billNo"],
            "label": entry["label"],
            "expected": "PASS" if entry["label"] == "GENUINE" else "FLAG",
            "chainResult": chain_result if chain_result else "OK",
            "flagged": flagged,
            "verdict": verdict_for_entry(entry, deployments_path) if verdict_for_entry else None,
        }
        rows.append(row)

    positives = sum(1 for r in rows if is_positive(r["label"]))
    flagged_count = sum(1 for r in rows if r["flagged"])
    truePositives = sum(1 for r in rows if r["flagged"] and is_positive(r["label"]))
    falsePositives = sum(1 for r in rows if r["flagged"] and r["label"] == "GENUINE")
    precision = round(truePositives / flagged_count, 3) if flagged_count > 0 else 0
    recall = round(truePositives / positives, 3) if positives > 0 else 0

    flag_block = {
        "positives": positives,
        "flagged": flagged_count,
        "truePositives": truePositives,
        "falsePositives": falsePositives,
        "precision": precision,
        "recall": recall,
    }

    if verdict_for_entry:
        match_count = sum(
            1 for r in rows
            if ((r["verdict"] == "GREEN") == (not r["flagged"]))
        )
        agreement = {"total": 100, "match": match_count}
    else:
        agreement = None

    held_out_entry = next((e for e in bills["extras"] if e["billNo"] == 599), None)
    if held_out_entry:
        alloc_ho = {
            "billNullifier": held_out_entry["nullifier"],
            "donorVault": evalVault,
            "chainId": 31337,
            "fractionBps": 10000,
            "reportId": held_out_entry["reportId"],
        }
        ngoSig_ho = sign_allocation(alloc_ho, anvil_account(1)["key"])
        chain_result_ho = call_revert(
            vault.functions.release,
            bill_tuple(held_out_entry["bill"]),
            bytes.fromhex(held_out_entry["vendorSig"][2:]),
            alloc_tuple(alloc_ho),
            bytes.fromhex(ngoSig_ho[2:]),
            anvil_account(9)["address"],
        )
        flagged_ho = chain_result_ho is not None
        held_out = {
            "billNo": 599,
            "label": held_out_entry["label"],
            "chainResult": chain_result_ho if chain_result_ho else "OK",
            "flagged": flagged_ho,
            "result": "MISS" if not flagged_ho else "CAUGHT",
        }
    else:
        held_out = {}

    not_covered = [
        "vendor collusion",
        "off-chain spend",
        "delivery",
        "held-out future-dated bill: MISS 1/1",
    ]

    out_dir = os.path.dirname(out)
    os.makedirs(out_dir, exist_ok=True)

    output = {
        "simulated": True,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "flag": flag_block,
        "agreement": agreement,
        "rows": rows,
        "heldOut": held_out,
        "notCovered": not_covered,
    }

    json.dump(output, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=True)

    print(json.dumps({"ok": True, "flag": flag_block, "agreement": agreement, "heldOut": held_out}))
    print("Misses:")
    for r in rows:
        if r["expected"] == "FLAG" and not r["flagged"]:
            print(f"  {r['billId']}: expected FLAG, not flagged")
    if held_out.get("result") == "MISS":
        print(f"  held-out billNo 599: MISS")

    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deployments", required=True)
    parser.add_argument("--bills", required=True)
    parser.add_argument("--out", default="sim/fixtures/eval.json")
    args = parser.parse_args()
    run(args.deployments, args.bills, args.out)


if __name__ == "__main__":
    main()
