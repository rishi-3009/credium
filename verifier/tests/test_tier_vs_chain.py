"""Python tier_of matches VendorRegistry.tierOf via eth_call on 50 vendor cases (plan m5).

Needs anvil on 31337 and contracts/deployments.json. Skips if either is missing.
"""
import json
from pathlib import Path

import pytest

from sim.chainio import contract, web3_for
from sim.signing import anvil_account, synthetic_account
from verifier.verify import tier_of

ROOT = Path(__file__).resolve().parents[2]
DEPLOYMENTS = ROOT / "contracts" / "deployments.json"
BILLS = ROOT / "sim" / "fixtures" / "bills.json"
CASES = 50


def _deployments():
    if not DEPLOYMENTS.exists():
        pytest.skip("contracts/deployments.json not written yet")
    with open(DEPLOYMENTS, encoding="utf-8") as f:
        dep = json.load(f)
    try:
        web3_for(dep, 31337).eth.chain_id
    except Exception:
        pytest.skip("anvil on 127.0.0.1:8545 is not running")
    return dep


def _cases() -> list[str]:
    with open(BILLS, encoding="utf-8") as f:
        vendors = list(dict.fromkeys(b["bill"]["vendor"] for b in json.load(f)["bills"]))
    addresses = vendors + [anvil_account(i)["address"] for i in range(10)]
    i = 0
    while len(addresses) < CASES:
        addresses.append(synthetic_account(f"tier-case-{i}")["address"])
        i += 1
    return addresses[:CASES]


def test_python_tier_matches_chain_for_50_cases():
    dep = _deployments()
    w3 = web3_for(dep, 31337)
    registry_contract = contract(w3, dep["chains"]["31337"]["registry"], "VendorRegistry")
    registrar = dep["registrar"]
    now = w3.eth.get_block("latest")["timestamp"]

    registry = {}
    mismatches = []
    cases = _cases()
    for addr in cases:
        name, enrolled_by, enrolled_at = registry_contract.functions.vendors(addr).call()
        if enrolled_at:
            registry[addr] = {"name": name, "enrolledBy": enrolled_by, "enrolledAt": enrolled_at}

    for addr in cases:
        chain_tier = registry_contract.functions.tierOf(addr).call()
        py_tier = tier_of(addr, registry, registrar, now)
        if chain_tier != py_tier:
            mismatches.append((addr, chain_tier, py_tier))
    assert len(cases) == CASES
    assert mismatches == []
