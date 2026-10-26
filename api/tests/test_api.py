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


def test_root_serves_the_demo_page_not_the_experimental_ui(client):
    # Plan 8f: GET / is web/index.html. The role-selection UI lives under /experimental.
    page = client.get("/").text
    assert "<title>CREDIUM Demo</title>" in page
    assert client.get("/experimental/index.html").status_code == 200


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


class _FakeProvider:
    """Mimics anvil: evm_revert consumes the id, evm_snapshot mints a new one."""

    def __init__(self, spent: set):
        self.spent = set(spent)
        self.counter = 100

    def make_request(self, method, params):
        if method == "evm_revert":
            snapshot_id = params[0]
            if snapshot_id in self.spent:
                return {"result": False}
            self.spent.add(snapshot_id)
            return {"result": True}
        if method == "evm_snapshot":
            self.counter += 1
            return {"result": hex(self.counter)}
        raise AssertionError(f"unexpected {method}")


def test_reset_succeeds_and_rotates_snapshot_ids(tmp_path, monkeypatch):
    import api.main as api_main
    deployments = tmp_path / "deployments.json"
    deployments.write_text(json.dumps({"chains": {"31337": {}, "31338": {}}}), encoding="utf-8")
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(json.dumps({"simulated": True, "snapshots": {"31337": "0x1", "31338": "0x2"}}),
                        encoding="utf-8")
    provider = _FakeProvider(spent=set())
    monkeypatch.setattr(api_main, "web3_for",
                        lambda dep, chain_id: type("W3", (), {"provider": provider})())
    client = TestClient(create_app(deployments=deployments, bills=BILLS, snapshot=snapshot,
                                   evaluation=tmp_path / "eval.json"))

    first = client.post("/api/reset")
    assert first.status_code == 200, first.text
    ids_after_first = json.loads(snapshot.read_text())["snapshots"]
    assert ids_after_first != {"31337": "0x1", "31338": "0x2"}, "ids must rotate after a revert"

    # The regression: a second reset must work, because the file now holds
    # ids that were never spent. Previously evm_revert returned false here.
    second = client.post("/api/reset")
    assert second.status_code == 200, second.text
    assert json.loads(snapshot.read_text())["snapshots"] != ids_after_first


def test_reset_with_expired_snapshot_reports_and_self_heals(tmp_path, monkeypatch):
    import api.main as api_main
    deployments = tmp_path / "deployments.json"
    deployments.write_text(json.dumps({"chains": {"31337": {}, "31338": {}}}), encoding="utf-8")
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(json.dumps({"simulated": True, "snapshots": {"31337": "0x1", "31338": "0x2"}}),
                        encoding="utf-8")
    provider = _FakeProvider(spent={"0x1", "0x2"})  # both ids already consumed
    monkeypatch.setattr(api_main, "web3_for",
                        lambda dep, chain_id: type("W3", (), {"provider": provider})())
    client = TestClient(create_app(deployments=deployments, bills=BILLS, snapshot=snapshot,
                                   evaluation=tmp_path / "eval.json"))

    response = client.post("/api/reset")
    assert response.status_code == 409
    assert "run ops/run_demo.sh" in response.json()["detail"]

    # Self-heal: the stale ids are replaced, so the file is not poisoned forever.
    # The old code raised before writing, leaving the spent ids on disk and every
    # later reset failing the same way.
    ids = json.loads(snapshot.read_text())["snapshots"]
    assert "0x1" not in ids.values() and "0x2" not in ids.values()

    # And the next reset works again.
    assert client.post("/api/reset").status_code == 200
