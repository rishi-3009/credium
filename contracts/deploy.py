"""SIMULATED deploy for the two local anvil chains (plan §8c, §8e).

Deploys MockINR, VendorRegistry(registrar) and PurposeVault per chain. Deploys evalVault on 31337 only.
Does NOT enrol vendors: that is sim/seed_demo.py's job.

Usage (cwd anywhere; paths come from __file__):
    DEPLOYER_KEY=0x... python contracts/deploy.py --deployments contracts/deployments.json [--only-chain 31337]

Logs go to stderr. The deployments JSON is written to --deployments. The same JSON goes to stdout.
"""
import argparse
import json
import os
import sys
from pathlib import Path

from eth_utils import keccak, to_checksum_address
from web3 import Web3

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"

# Anvil account #1 (public test mnemonic). Plan §9: NGO = #1, registrar = #0.
NGO_ADDRESS = to_checksum_address("0x70997970C51812dc3A010C7d01b50e0d17dc79C8")
CAP_PAISE = 2_000_000_000  # ₹2 cr
CATEGORY_WATER = keccak(text="WATER")

CHAINS = {
    31337: "http://127.0.0.1:8545",
    31338: "http://127.0.0.1:8546",
}


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def load_artifact(name: str) -> dict:
    path = OUT_DIR / f"{name}.sol" / f"{name}.json"
    with path.open(encoding="utf-8") as f:
        artifact = json.load(f)
    return {"abi": artifact["abi"], "bytecode": artifact["bytecode"]["object"]}


def deploy(w3: Web3, account, artifact: dict, *args) -> str:
    contract_factory = w3.eth.contract(abi=artifact["abi"], bytecode=artifact["bytecode"])
    tx = contract_factory.constructor(*args).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
        }
    )
    signed = account.sign_transaction(tx)
    receipt = w3.eth.wait_for_transaction_receipt(w3.eth.send_raw_transaction(signed.raw_transaction))
    if receipt["status"] != 1:
        raise RuntimeError(f"deploy failed in tx {receipt['transactionHash'].hex()}")
    return to_checksum_address(receipt["contractAddress"])


def deploy_chain(chain_id: int, rpc: str, account, artifacts: dict, with_eval_vault: bool) -> dict:
    w3 = Web3(Web3.HTTPProvider(rpc))
    actual = w3.eth.chain_id
    if actual != chain_id:
        raise RuntimeError(f"{rpc} reports chainId {actual}, expected {chain_id}")
    log(f"chain {chain_id} at {rpc}: deploying")

    token = deploy(w3, account, artifacts["MockINR"])
    registry = deploy(w3, account, artifacts["VendorRegistry"], account.address)
    vault = deploy(
        w3, account, artifacts["PurposeVault"], token, NGO_ADDRESS, registry, CATEGORY_WATER, CAP_PAISE
    )
    entry = {"rpc": rpc, "token": token, "registry": registry, "vault": vault}
    if with_eval_vault:
        entry["evalVault"] = deploy(
            w3, account, artifacts["PurposeVault"], token, NGO_ADDRESS, registry, CATEGORY_WATER, CAP_PAISE
        )
    log(f"chain {chain_id}: token={token} registry={registry} vault={vault}")
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy Credium contracts to local anvil chains (SIMULATED).")
    parser.add_argument("--deployments", required=True, help="Path to write deployments.json")
    parser.add_argument("--only-chain", type=int, choices=sorted(CHAINS), help="Deploy to one chain only")
    args = parser.parse_args()

    key = os.environ.get("DEPLOYER_KEY")
    if not key:
        log("DEPLOYER_KEY is not set")
        return 1

    w3_probe = Web3()
    account = w3_probe.eth.account.from_key(key)
    log(f"registrar / deployer: {account.address}")

    artifacts = {name: load_artifact(name) for name in ("MockINR", "VendorRegistry", "PurposeVault")}

    chain_ids = [args.only_chain] if args.only_chain else sorted(CHAINS)
    chains = {}
    for chain_id in chain_ids:
        chains[str(chain_id)] = deploy_chain(
            chain_id, CHAINS[chain_id], account, artifacts, with_eval_vault=(chain_id == 31337)
        )

    deployments = {
        "simulated": True,
        "ngo": NGO_ADDRESS,
        "registrar": account.address,
        "chains": chains,
    }
    dest = Path(args.deployments)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(deployments, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    log(f"wrote {dest}")
    print(json.dumps(deployments, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
