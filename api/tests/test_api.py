"""API tests with FastAPI TestClient (plan §8f, M7, M8). Chain-free: no anvil needed.

Live release and double-claim checks run at the 18:00 gate on the demo host.
"""
import json
import sys
from pathlib import Path

import pytest
from eth_abi import encode
from eth_utils import keccak
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from api.main import create_app  # noqa: E402
from sim.chainio import decode_revert  # noqa: E402
from sim.signing import anvil_account  # noqa: E402

BILLS = ROOT / "sim" / "fixtures" / "bills.json"
PUBLIC_KEYS = {"billId", "billNo", "vendorName", "amountPaise", "verdict", "tier", "recoveredSigner", "reason"}


@pytest.fixture
def client(tmp_path):
    # No deployments.json in tmp_path: chain routes must answer 503, not crash.
    app = create_app(deployments=tmp_path / "deployments.json", bills=BILLS, snapshot=tmp_path / "snap.json",
                     evaluation=tmp_path / "eval.json")
    return TestClient(app)


def test_bills_returns_public_fields_only(client):
    rows = client.get("/api/bills").json()
    assert len(rows) == 100
    for row in rows:
        assert set(row) == PUBLIC_KEYS


def test_bills_is_a_bare_list_for_the_frontend(client):
    # web/index.html calls list.forEach on the response body directly.
    assert isinstance(client.get("/api/bills").json(), list)


def test_down_chain_has_numeric_vault_fields(client, tmp_path):
    # Without numbers the page renders NaN for a chain that is down.
    dep = tmp_path / "deployments.json"
    dep.write_text(json.dumps({"simulated": True, "chains": {}}), encoding="utf-8")
    app_client = TestClient(create_app(deployments=dep, bills=BILLS))
    chain = app_client.get("/api/state").json()["chains"][0]
    assert chain["up"] is False
    assert chain["vault"]["balancePaise"] == 0
    assert chain["vault"]["releasedPaise"] == 0


def test_bills_never_contain_items_or_salt(client):
    text = client.get("/api/bills").text
    assert '"items"' not in text
    assert '"salt"' not in text


def test_state_without_deployments_is_503(client):
    assert client.get("/api/state").status_code == 503


def test_eval_serves_the_static_file(tmp_path):
    evaluation = tmp_path / "eval.json"
    evaluation.write_text(json.dumps({"simulated": True, "flag": 30}), encoding="utf-8")
    client = TestClient(create_app(evaluation=evaluation))
    assert client.get("/api/eval").json() == {"simulated": True, "flag": 30}


def test_eval_missing_is_503(tmp_path):
    client = TestClient(create_app(evaluation=tmp_path / "missing.json"))
    assert client.get("/api/eval").status_code == 503


def test_decodes_vault_frozen_equivocation():
    data = keccak(text="VaultFrozen(string)")[:4] + encode(["string"], ["equivocation"])
    assert decode_revert("0x" + data.hex()) == 'VaultFrozen("equivocation")'


def test_decodes_bad_vendor_sig_address():
    signer = anvil_account(6)["address"]
    data = keccak(text="BadVendorSig(address)")[:4] + encode(["address"], [signer])
    assert decode_revert("0x" + data.hex()) == f'BadVendorSig("{signer}")'
