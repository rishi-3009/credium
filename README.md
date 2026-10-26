# Credium

**Team Obsidian · CASCADE '26** · PS 4.2 *The Black Hole Ledger* · Theme 4 *Information Asymmetry*

Purpose-bound NGO escrow. Vendors sign their own bills. If an NGO claims the same bill twice, across two donors or two chains, its own two signatures prove it, and anyone can freeze the vault. No auditor and no admin key.

Mechanism: **two-signature equivocation freeze**.

> **Everything here is SIMULATED.** Bills, vendors, donors, keys and pledges are synthetic. Chains are local Anvil instances. No real money moves.

---

## The idea

A vendor signs a bill. The NGO signs an *allocation*: how much of that bill to pay, from which vault, on which chain. Each chain checks its own allocation, so an NGO that claims 60% on chain A and 60% on chain B passes each chain on its own.

Both allocations carry **the same bill nullifier** and the **same NGO key**. Hand the pair to any vault and it freezes permanently. The fraud proof comes from the fraud itself.

```
NGO signs alloc(chain A, 6000 bps) ─┐
                                    ├──> sum 12000 bps > 10000 → FREEZE
NGO signs alloc(chain B, 6000 bps) ─┘
```

Anyone can submit the pair. The `watcher/` bot has no privileges that a stranger could not also use.

### Why the signing domain omits `chainId`

Normal EIP-712 binds signatures to one chain. Credium leaves `chainId` out of the domain for allocations and puts `chainId` and `donorVault` inside the signed struct, where release checks them. That lets both signatures be verified in one place. Replay is limited by the per-chain `usedBps` cap.

## What it proves, and what it does not

> **It proves a vendor-signed invoice was paid, and that one bill was claimed twice. It does not prove the well was built.**

Delivery is off-chain and unverified. We have not verified a GST API and do not claim one.

---

## Quick start

Requires Python 3.11+ and [Foundry](https://getfoundry.sh).

```bash
git submodule update --init --recursive
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cd contracts && forge build && cd ..
bash ops/run_demo.sh
```

Then open **http://127.0.0.1:8000/**.

`ops/run_demo.sh` stops old processes, starts Anvil on ports 8545 (chain 31337) and 8546 (chain 31338), waits for both RPCs, deploys, seeds the bills, and starts the API. The script expects its Python at `~/credium-venv/bin/python`. Change `PY` at the top of the script if your venv is somewhere else.

## Demo steps

| # | Step | What it shows |
|---|---|---|
| 1 | Health | Both chains up, contracts deployed |
| 2 | Bills | 100 bills: 70 GREEN, 5 AMBER, 18 FORGED, 7 UNKNOWN |
| 3 | Release a GREEN bill | Both signatures verify, money moves |
| 4 | Forged bill | Reverts `BadVendorSig`. An edited amount breaks the signature |
| 5 | AMBER bill | Reverts `TierNotGreen(1)`. NGO-enrolled is not registrar-enrolled |
| 6 | Double claim | Same bill on both chains, watcher submits the pair, both vaults freeze |
| 7 | Reset | `evm_revert` restores both chains |

Reset works only on Anvil. `evm_revert` does not exist on a real network.

## Vendor tiers

| Tier | Meaning | Releasable |
|---|---|---|
| `GREEN` (0) | Enrolled by the registrar, 7+ days old | Yes |
| `AMBER` (1) | Enrolled by the NGO | No: `TierNotGreen(1)` |
| `UNREGISTERED` (2) | Not enrolled | No: `UnknownVendor` |

## Layout

| Path | Purpose |
|---|---|
| `contracts/src/PurposeVault.sol` | Escrow, release checks, equivocation freeze |
| `contracts/src/VendorRegistry.sol` | Vendor enrolment and tiers |
| `contracts/src/MockINR.sol` | Mock rupee token (test only). Units are paise, so `decimals` is 0 |
| `api/main.py` | FastAPI app and demo routes |
| `sim/` | Bill generation, seeding, attacks, EIP-712 signing, evaluation |
| `verifier/` | Signature recovery and verdict logic |
| `watcher/` | Permissionless equivocation submitter |
| `web/index.html` | Desktop demo ledger |
| `web/app/index.html` | Mobile view, served at `/app/` |
| `web/experimental-addons/` | Role-split prototype UIs |
| `android/` | WebView wrapper around the mobile view |
| `ops/run_demo.sh` | Full cold start |
| `plans/` | Build plan and member cards |

## API

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/` | Desktop demo ledger |
| `GET` | `/app/` | Mobile view |
| `GET` | `/experimental/index.html` | Role-split prototype UIs |
| `GET` | `/api/health` | Chain status |
| `GET` | `/api/state` | Vault balances, caps, frozen flags, pledge meter |
| `GET` | `/api/bills` | Flat list, public fields only |
| `GET` | `/api/eval` | Detector precision and recall (from `sim/fixtures/eval.json`) |
| `POST` | `/api/release` | Body: `{chainId, billNo, fractionBps}` |
| `POST` | `/api/attack/forge30` | Submit the 30 forged bills |
| `POST` | `/api/attack/double-claim` | Claim one bill on both chains |
| `POST` | `/api/watcher/scan` | Run the watcher once |
| `POST` | `/api/reset` | Revert both chains to the snapshot |

## Mobile app

`android/app/src/main/java/org/credium/app/Config.kt` holds `DEMO_URL` and `LAN_URL`. They are compiled in, so changing them needs a rebuild.

```bash
cd android && ./gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

## Testing

```bash
cd contracts && forge test                          # 40 Solidity tests
python -m pytest api sim verifier watcher -q        # Python tests
```

The Python tests that need a running chain (the tier comparison and the chain-dependent API checks) skip when Anvil is not up.

## Security notes

- **All keys are public Anvil test keys.** Anyone can forge anything with them.
- **Chains are local** (`127.0.0.1`). Not a testnet, not mainnet.
- **The API has no authentication.** Anyone who can reach it can press any button, including the watcher scan, which freezes vaults.
- **The watcher is honest by circumstance, not by permission.**
- Signature recovery uses OpenZeppelin `tryRecover`, which rejects high-`s` malleable signatures. Without that check one valid signature could be turned into a second one and break the equivocation proof.

## Credits

See [`CREDITS.md`](CREDITS.md). Contracts are original. OpenZeppelin supplies `ECDSA` and `ERC20`, and forge-std supplies the test cheatcodes.
