"""FastAPI app for the Credium demo (plan §8f). SIMULATED.

Run from anywhere (paths come from __file__):
    python api/main.py                      # binds 127.0.0.1:8000
    python api/main.py --host <LAN IP>      # demo host only

Logs go to stderr. Responses are JSON with ensure_ascii=True.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sim.chainio import (  # noqa: E402
    alloc_tuple,
    bill_tuple,
    call_revert,
    contract,
    send_tx,
    web3_for,
)
from sim.meter import compute_meter  # noqa: E402
from sim.signing import anvil_account, sign_allocation  # noqa: E402
from verifier.credium_sig import recover_bill_signer  # noqa: E402
from watcher.watcher import scan_once  # noqa: E402

CHAIN_LABELS = {"31337": "Chain A · Donor A", "31338": "Chain B · Donor B"}
PLEDGED_PAISE = 2_300_000_000  # §2 synthetic pledge figure (₹2.30 cr)
NGO_IDX = 1  # §9: NGO = anvil #1 (signs allocations)
RELAYER_IDX = 9  # any funded account can submit release; #9 is the attacker account in forge30
PUBLIC_BILL_FIELDS = ("billId", "billNo", "vendorName", "amountPaise", "verdict", "tier", "recoveredSigner", "reason")

DEFAULT_DEPLOYMENTS = ROOT / "contracts" / "deployments.json"
DEFAULT_BILLS = ROOT / "sim" / "fixtures" / "bills.json"
DEFAULT_SNAPSHOT = ROOT / "sim" / "fixtures" / "snapshot.json"
DEFAULT_EVAL = ROOT / "sim" / "fixtures" / "eval.json"
WEB_INDEX = ROOT / "web" / "index.html"
WEB_EXPERIMENTAL_DIR = ROOT / "web" / "experimental-addons" / "ui"


class AsciiJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json.dumps(content, ensure_ascii=True).encode("utf-8")


class ReleaseBody(BaseModel):
    chainId: int
    billNo: int
    fractionBps: int


class DoubleClaimBody(BaseModel):
    billNo: int
    fractionBps: int


def _read_json(path: Path) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(503, detail=f"missing {path.name}: run the demo setup first")


def _run_cli(args: list[str]) -> dict:
    """Run one of Ayaan's CLIs with sys.executable and cwd at the project root (M10)."""
    env = {**os.environ, "PYTHONUTF8": "1"}
    proc = subprocess.run(
        [sys.executable, *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", env=env, timeout=600
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise HTTPException(500, detail=proc.stderr[-2000:])
    return json.loads(proc.stdout.strip().splitlines()[-1])


def create_app(
    deployments: Path = DEFAULT_DEPLOYMENTS,
    bills: Path = DEFAULT_BILLS,
    snapshot: Path = DEFAULT_SNAPSHOT,
    evaluation: Path = DEFAULT_EVAL,
) -> FastAPI:
    app = FastAPI(title="Credium API (SIMULATED)", default_response_class=AsciiJSONResponse)

    def load_dep() -> dict:
        return _read_json(deployments)

    def bill_entries() -> list[dict]:
        return _read_json(bills)["bills"]

    def verdicts(dep: dict | None, entries: list[dict]) -> dict[str, dict]:
        """Verdict per billNo from verifier/verify.py (Block 14). Empty until that module exists."""
        try:
            from verifier.verify import verdict as verify_bill
        except ImportError:
            return {}
        if dep is None or "31337" not in dep["chains"]:
            return {}
        w3 = web3_for(dep, 31337)
        registry = contract(w3, dep["chains"]["31337"]["registry"], "VendorRegistry")
        vendors = {}
        for e in entries:
            addr = e["bill"]["vendor"]
            if addr in vendors:
                continue
            name, enrolled_by, enrolled_at = registry.functions.vendors(addr).call()
            if enrolled_at:
                vendors[addr] = {"name": name, "enrolledBy": enrolled_by, "enrolledAt": enrolled_at}
        now = w3.eth.get_block("latest")["timestamp"]
        return {str(e["billNo"]): verify_bill(e, vendors, dep["registrar"], now) for e in entries}

    def chain_state(dep: dict, chain_id: str) -> dict:
        chain = dep["chains"].get(chain_id, {})
        try:
            if not chain:
                raise KeyError(f"chain {chain_id} not in deployments.json")
            w3 = web3_for(dep, int(chain_id))
            vault = contract(w3, chain["vault"], "PurposeVault")
            token = contract(w3, chain["token"], "MockINR")
            deposited = sum(ev["args"]["amountPaise"] for ev in vault.events.Deposited.get_logs(from_block=0))
            frozen = vault.functions.frozen().call()
            return {
                "chainId": int(chain_id),
                "label": CHAIN_LABELS[chain_id],
                "up": True,
                "block": w3.eth.block_number,
                "frozen": frozen,
                "vault": {
                    "address": chain["vault"],
                    "capPaise": vault.functions.cap().call(),
                    "balancePaise": token.functions.balanceOf(chain["vault"]).call(),
                    "releasedPaise": vault.functions.released().call(),
                    "frozen": frozen,
                    "frozenReason": vault.functions.frozenReason().call(),
                },
                "_deposited": deposited,
                "_released": [ev["args"] for ev in vault.events.Released.get_logs(from_block=0)],
            }
        except Exception as e:  # chain down: report it, do not fail the whole state call
            sys.stderr.write(f"chain {chain_id} unreachable: {e}\n")
            return {"chainId": int(chain_id), "label": CHAIN_LABELS[chain_id], "up": False, "block": None,
                    "frozen": False,
                    "vault": {"address": chain.get("vault"), "capPaise": 0, "balancePaise": 0, "releasedPaise": 0,
                              "frozen": False, "frozenReason": ""},
                    "_deposited": 0, "_released": []}

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(WEB_INDEX)

    # Mount experimental UI static files
    app.mount("/experimental", StaticFiles(directory=str(WEB_EXPERIMENTAL_DIR)), name="experimental")

    @app.get("/api/health")
    def health() -> dict:
        dep = load_dep()
        up = {c: chain_state(dep, c)["up"] for c in CHAIN_LABELS}
        return {"ok": all(up.values()), "chains": up, "simulated": True}

    @app.get("/api/state")
    def state() -> dict:
        dep = load_dep()
        chains = [chain_state(dep, c) for c in CHAIN_LABELS]
        entries = bill_entries()
        by_bill_no = verdicts(dep, entries)
        released_rows = [r for ch in chains for r in ch["_released"]]
        verified = sum(r["amountPaise"] for r in released_rows
                       if by_bill_no.get(str(r["billNo"]), {}).get("verdict") == "GREEN")
        amber = sum(r["amountPaise"] for r in released_rows
                    if by_bill_no.get(str(r["billNo"]), {}).get("verdict") == "AMBER")
        meter = compute_meter(
            PLEDGED_PAISE,
            sum(ch["_deposited"] for ch in chains),
            sum(r["amountPaise"] for r in released_rows),
            verified,
            amber,
        )
        for ch in chains:
            del ch["_deposited"], ch["_released"]
        return {
            "simulated": True,
            "chains": chains,
            "meter": meter,
            "stale": not all(ch["up"] for ch in chains),
        }

    @app.get("/api/bills")
    def bills_view() -> list[dict]:
        entries = bill_entries()
        try:
            dep = load_dep()
        except HTTPException:
            dep = None
        by_bill_no = verdicts(dep, entries)
        rows = []
        for e in entries:
            v = by_bill_no.get(str(e["billNo"]), {})
            row = {
                "billId": e["billId"],
                "billNo": e["billNo"],
                "vendorName": e["vendorName"],
                "amountPaise": e["bill"]["amountPaise"],
                "verdict": v.get("verdict"),
                "tier": v.get("tier"),
                "recoveredSigner": recover_bill_signer(e["bill"], e["vendorSig"]),
                "reason": v.get("reason"),
            }
            rows.append({k: row[k] for k in PUBLIC_BILL_FIELDS})
        return rows  # web/index.html iterates this list directly

    @app.get("/api/eval")
    def eval_table() -> dict:
        return _read_json(evaluation)

    @app.post("/api/release")
    def release(body: ReleaseBody) -> dict:
        dep = load_dep()
        chain_key = str(body.chainId)
        if chain_key not in dep["chains"]:
            raise HTTPException(404, detail=f"no chain {body.chainId} in deployments")
        entry = next((e for e in bill_entries() if e["billNo"] == body.billNo), None)
        if entry is None:
            raise HTTPException(404, detail=f"no bill {body.billNo} in fixtures")

        # Step 1: build the Allocation and sign it as the NGO.
        alloc = {
            "billNullifier": entry["nullifier"],
            "donorVault": dep["chains"][chain_key]["vault"],
            "chainId": body.chainId,
            "fractionBps": body.fractionBps,
            "reportId": entry["reportId"],
        }
        ngo_sig = sign_allocation(alloc, anvil_account(NGO_IDX)["key"])

        # Step 2: eth_call first; a revert comes back decoded, not as a raw error.
        w3 = web3_for(dep, body.chainId)
        vault = contract(w3, dep["chains"][chain_key]["vault"], "PurposeVault")
        fn = vault.functions.release(
            bill_tuple(entry["bill"]),
            bytes.fromhex(entry["vendorSig"][2:]),
            alloc_tuple(alloc),
            bytes.fromhex(ngo_sig[2:]),
        )
        relayer = anvil_account(RELAYER_IDX)
        revert = call_revert(fn, relayer["address"])
        if revert is not None:
            return {"ok": False, "chainId": body.chainId, "revert": revert}

        # Step 3: send, wait for the receipt, return the hash.
        sent = send_tx(w3, fn, relayer["key"])
        if sent["status"] != 1:
            return {"ok": False, "chainId": body.chainId, "revert": "transaction reverted on-chain"}
        return {"ok": True, "chainId": body.chainId, "txHash": sent["txHash"]}

    @app.post("/api/attack/forge30")
    def attack_forge30() -> dict:
        return _run_cli(["-m", "sim.attacks.forge30", "--deployments", str(deployments), "--bills", str(bills)])

    @app.post("/api/attack/double-claim")
    def attack_double_claim(body: DoubleClaimBody) -> dict:
        return _run_cli([
            "-m", "sim.attacks.double_claim",
            "--billNo", str(body.billNo),
            "--fractionBps", str(body.fractionBps),
            "--deployments", str(deployments),
        ])

    @app.post("/api/watcher/scan")
    def watcher_scan() -> dict:
        return scan_once(str(deployments))

    @app.post("/api/reset")
    def reset() -> dict:
        """evm_revert each chain to its snapshot, then take a fresh snapshot (§8f).

        anvil snapshots are single-use: a successful evm_revert consumes the id.
        So every chain must be re-snapshotted and persisted even when a later
        chain fails, otherwise snapshot.json keeps an id that can never be
        reverted again and every future reset returns 500.
        """
        dep = load_dep()
        snap = _read_json(snapshot)
        reverted: list[str] = []
        stale: list[str] = []

        for chain_id, snap_id in list(snap["snapshots"].items()):
            w3 = web3_for(dep, int(chain_id))
            result = w3.provider.make_request("evm_revert", [snap_id])["result"]
            if result:
                reverted.append(chain_id)
            else:
                stale.append(chain_id)
            # Always take a fresh snapshot and persist it, whether or not the
            # revert succeeded: the old id is spent either way.
            snap["snapshots"][chain_id] = w3.provider.make_request(
                "evm_snapshot", []
            )["result"]
            with open(snapshot, "w", encoding="utf-8") as f:
                json.dump(snap, f)

        if stale:
            # A stale id means the chain moved past the snapshot (old anvil run,
            # or the id was consumed by hand). Chain state is now arbitrary, so
            # say so plainly instead of pretending the demo is at its baseline.
            raise HTTPException(
                409,
                detail=(
                    f"snapshot expired on chain(s) {', '.join(stale)}; "
                    "run ops/run_demo.sh to redeploy and re-seed"
                ),
            )

        return {"ok": True, "reverted": reverted, "snapshots": snap["snapshots"]}

    return app


# ops/run_demo.sh starts this with `uvicorn api.main:app --host <LAN IP> --port 8000`.
app = create_app()


def main() -> None:
    import uvicorn

    parser = argparse.ArgumentParser(description="Credium API (SIMULATED)")
    parser.add_argument("--host", default="127.0.0.1", help="bind address; LAN IP only on the demo host")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--deployments", default=str(DEFAULT_DEPLOYMENTS))
    parser.add_argument("--bills", default=str(DEFAULT_BILLS))
    parser.add_argument("--snapshot", default=str(DEFAULT_SNAPSHOT))
    parser.add_argument("--eval", default=str(DEFAULT_EVAL))
    args = parser.parse_args()
    app = create_app(Path(args.deployments), Path(args.bills), Path(args.snapshot), Path(args.eval))
    uvicorn.run(app, host=args.host, port=args.port, log_config=None)


if __name__ == "__main__":
    main()
