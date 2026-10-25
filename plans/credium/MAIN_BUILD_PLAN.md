# MAIN BUILD PLAN — Credium  (Pod A: Rishi (lead, Claude Code) + Ayaan (support, Qwen))
Slug `credium` · rev 3 (PLAN_REVIEW B1–B5, M1–M16 and the 4 GB / Foundry / demo-host change) · **all data SIMULATED · local chains only**
**Demo host = Ayaan's laptop** (Linux, 24 GB). **Rishi's laptop = dev box** (4 GB, Windows): `forge` only, at most one anvil.
## 1. One-liner + themes
- **One-liner:** An NGO that cites one bill twice signs its own fraud proof, and every donor's escrow, on every chain, freezes on it. **Primary:** PS 4.2 · T4 Information Asymmetry. **Stack theme:** none.
- **Honest scope (say it on stage):** local multi-chain simulation (two anvil chains, 31337 + 31338). Proves a vendor-signed invoice was paid and one bill was claimed twice. Does **not** prove the well was built. Freeze stops future disbursement only, no claw-back, permanent in v1. Fallback (b), single-chain: §15a.
## 2. Demo flow (north star, 3 min, SIMULATED banner, runs on Ayaan's laptop)
| # | What judges see | Chain link |
|---|---|---|
| 1 | Hook: "A ₹1.5 cr water pledge is swapped, bridged and spent through local vendors. Donors can't check." | Inbound Donation |
| 2 | Two panels: Donor A → Chain A vault (WATER, cap ₹2 cr); Donor B → Chain B. Meter: pledged ₹2.30 cr, deposited ₹2.14 cr (chain logs), "unexplained ₹16 lakh (simulated swap/bridge loss)". | Inbound Donation |
| 3 | Release pinned bill #0405 (GREEN vendor) → OK. Card: vendor sig VALID, recovered signer = vendor, `itemsCommitment` shown, items hidden. | Escrow + Invoice Proof |
| 4 | **Forge 30%**: 30 bills submitted, all reverted. 18 "amount edited: recovered signer ≠ Ramesh Hardware", 7 "unregistered signer", 5 "enrolled by NGO, not registrar → TierNotGreen(1)". Plus one PPE bill to the WATER vault → `WrongCategory`. | Invoice Proof, Escrow |
| 5 | **Double-claim** #0417 (₹1,80,000 pipes): 100% on chain A and 100% on chain B. Both panels: "per-chain check: PASS". | Escrow (per chain) |
| 6 | Watcher (not admin) clicks **Scan**. Both panels flip red: "Equivocation: NGO key signed 200% of bill #0417. FROZEN." | Impact Verification |
| 7 | NGO release on chain A → revert `VaultFrozen("equivocation")`. Encore: #0418 split 60% + 60% → same freeze. | Escrow / Impact |
| 8 | Meter invariant: Σ on-chain released = verifier-verified. Show once a rogue release the verifier never saw → invariant FALSE. "Proves payment and a signed invoice, not that the well works." | Impact Verification |
## 3. Evaluation chain → component mapping
| Chain link | Component / function | Screen | Test | 23:00 | 11:00 |
|---|---|---|---|---|---|
| Inbound Donation | `PurposeVault.deposit`; mock swap+bridge in `sim/seed_demo.py` | Panels, meter | `test/Vault.t.sol` | REAL (mock hop) | REAL (relayer cut-first) |
| Escrow Condition | `PurposeVault.release`: category, tier GREEN, vendor sig, NGO alloc sig, cumulative ≤100%/chain, not frozen, cap | Release, revert text | `test/Release.t.sol` (1 happy + 8 negative) | REAL | REAL |
| Off-Chain Invoice Proof | EIP-712 `Bill` + salted `itemsCommitment`; `verifier/verify.py` | Bill card, forge table | `test/Gate.t.sol`, `verifier/tests` | REAL | REAL |
| Crypto Impact Verification | `submitEquivocation` cross-chain freeze; `sim/meter.py`; `watcher/` | Scan, meter | `test/Equivocation.t.sol`, `watcher/tests` | PARTIAL (no Merkle) | REAL (+Merkle ack, cut-first) |
## 4. Red-team scenario
| Attack | Injected by | Caught by | UI shows |
|---|---|---|---|
| A1 Forge 30% | `sim/attacks/forge30.py`: 18 edited-amount, 7 unregistered-signer, 5 NGO-enrolled | `BadVendorSig` / `UnknownVendor` / `TierNotGreen(1)` (release pays GREEN only) | Per-row table, P/R |
| A2 Wrong category | forge30 also sends one vendor-signed PPE bill to the WATER vault (outside the 30) | `WrongCategory` | Revert line |
| A3 Double-claim #0417 | `sim/attacks/double_claim.py --billNo 417 --fractionBps 10000` | Each chain alone passes. **Watcher** pairs the two NGO-signed allocations (same nullifier, same NGO, sum > 10000 bps) and submits both sigs to both vaults | Green → Scan → red |
| A4 Split 60+60 #0418 | same CLI, `--billNo 418 --fractionBps 6000` | same rule | same |
| A5 Release after freeze | `POST /api/release` | `VaultFrozen` | Revert line |
| Held-out class (not designed for) | one future-dated bill (`issuedAt` > chain time) | nothing: passes verifier and chain | Listed as MISS in eval |

Why a chain-B proof can be checked on chain A: the chain-free EIP-712 domain (§8b). Each allocation carries its own `chainId` and `donorVault`.
**Limits said aloud:** (1) only executed or published allocations can be paired; (2) vendor collusion is not caught; (3) freeze is permanent, no claw-back; (4) the future-dated class is missed by design.
## 5. Architecture
```
 DEMO HOST = Ayaan's laptop (Linux, 24 GB)
 [3] sim/ actors + attacks ──signed txs──► [1] anvil :8545 (chain 31337) ◄──┐ logs, eth_call
                           ──signed txs──► [1] anvil :8546 (chain 31338) ◄──┤
 [4] watcher/ bot (no admin key) ──Released logs → submitEquivocation──► A+B ┤
 [5] api/ FastAPI :8000 (LAN IP for demo) + verifier/ + sim/meter.py ────────┘
          │ JSON ──► [6] web/index.html (browser on demo host; Rishi may view over LAN)
 [2] contracts/ (Solidity, built and tested with forge) deployed to both chains by contracts/deploy.py
```
## 6. Tech stack
| Layer | Choice | Why | Runs on | Fallback |
|---|---|---|---|---|
| Chains | Foundry `anvil` ×2: `--chain-id 31337 --port 8545`, `--chain-id 31338 --port 8546` | Light Rust binary; no Node | Ayaan's laptop (demo); Rishi: one anvil max | Single-chain demo §15a |
| Contracts | Solidity 0.8.24; `forge build`, `forge test`; OZ 5.x (`ECDSA.tryRecover`, `ERC20`); forge-std | Audited primitives; Solidity tests with `vm.warp`, `vm.chainId`, `vm.readFile` | Rishi's dev box (`forge test` only) | Ayaan runs `forge test` on Linux |
| Deploy | `contracts/deploy.py` (web3.py) reads `contracts/out/<Name>.sol/<Name>.json` | No Node; same script on both laptops | Demo host | — |
| Python | web3.py v7, eth-account, eth-abi, eth-utils, FastAPI, uvicorn, pytest, httpx | RPC, typed-data hashing, JSON API | Both | — |
| UI | one `web/index.html`, vanilla JS + fetch, no CDN | Offline, no build | Browser on demo host | cached `eval.json` + last state |
| ML / LLM | **none in product**; Qwen is coding help only | Demo RAM stays free | — | — |
Test accounts: Anvil default mnemonic accounts (public, test-only). Keys are read from the anvil output, never committed.
## 7. Folder ownership inside the `credium` repo (repo root = project)
| Folder | Owner | Purpose | Talks to |
|---|---|---|---|
| `contracts/` | Rishi | `src/` (`MockINR`, `VendorRegistry`, `PurposeVault`); `test/*.t.sol`; `foundry.toml`; `deploy.py`; `out/` (3 artifact JSONs committed 15:30) | anvil RPC; ABIs to `sim`, `watcher`, `api` |
| `verifier/` | Rishi | `credium_sig.py` (recover, nullifier), `verify.py` (verdicts) | `api` |
| `api/` | Rishi | FastAPI `main.py`; CLIs via `sys.executable`; decodes reverts; serves `eval.json` | verifier, sim, watcher, anvil |
| `ops/` | **Ayaan** (demo host is Linux) | `run_demo.sh`: start both anvils, deploy, seed, snapshot, start API | all |
| `sim/` | Ayaan | `signing.py`, `gen_bills.py`, `seed_demo.py`, `attacks/`, `meter.py`, `eval_run.py`, `fixtures/`, `tests/` | anvil, `deployments.json`, ABIs |
| `watcher/` | Ayaan | `watcher.py` (`find_equivocations`, `scan_once`, CLI) | anvil, `deployments.json` |
| `web/` | Ayaan | `index.html` single file (from 18:00) | `api` JSON only |

Only the owner edits a folder. Code moves between laptops at gates by USB or shared repo copy (set up 13:05). `api/` imports `sim.signing` and `sim.meter` read-only. Ayaan freezes `signing.py` at 13:50.
## 8. Interface contracts (exact)
### 8a Solidity
```
struct Bill { address vendor; address buyerNGO; uint256 billNo; uint256 amountPaise; uint256 issuedAt; bytes32 category; bytes32 itemsCommitment; }
struct Allocation { bytes32 billNullifier; address donorVault; uint256 chainId; uint256 fractionBps; bytes32 reportId; }
VendorRegistry(address registrar): enroll(address vendor, string name)   // open; records enrolledBy=msg.sender, enrolledAt=block.timestamp
  isRegistered(address) → bool
  tierOf(address vendor) → uint8  // 0 GREEN: enrolledBy==registrar AND age≥7d | 1 AMBER: enrolled by anyone else, or registrar <7d | 2 UNREGISTERED
PurposeVault(address token, address ngo, address registry, bytes32 category, uint256 capPaise)  // no owner, no pause; MockINR decimals 0 (units = paise)
  deposit(uint256 amountPaise)
  release(Bill b, bytes vendorSig, Allocation a, bytes ngoSig)            // permissionless; sigs authorise; payee = bill.vendor; pays amountPaise*fractionBps/10000 (floor)
  submitEquivocation(Allocation a, bytes sigA, Allocation b, bytes sigB)  // permissionless; no-op if already frozen
  billSigner(Bill, bytes) → address · allocationSigner(Allocation, bytes) → address
  usedBps(bytes32) · released() · cap() · frozen() · frozenReason()
  event Deposited(address indexed donor, uint256 amountPaise)
  event Released(bytes32 indexed billNullifier, address indexed vendor, uint256 billNo, uint256 amountPaise,
                 address donorVault, uint256 chainId, uint256 fractionBps, bytes32 reportId, bytes ngoSig, uint8 tier)
  event Frozen(string reason, bytes32 indexed billNullifier, address submitter)
  errors: VaultFrozen(string) WrongCategory() WrongNGO() UnknownVendor(address) TierNotGreen(uint8) BadVendorSig(address) WrongChain(uint256)
          WrongVault() NullifierMismatch() BadNgoSig(address) BadFraction(uint256) OverAllocated(uint256) CapExceeded() InsufficientBalance()
```
`release` order: frozen → category → NGO → tier (2 → `UnknownVendor`; 1 → `TierNotGreen`) → vendor sig (`tryRecover`, else `BadVendorSig`) → `chainId == block.chainid` → `donorVault == this` → nullifier → NGO sig → fraction in (0,10000] → cumulative ≤10000 → cap → balance.
`submitEquivocation`: if frozen, return. Recover both with `tryRecover`, require `== ngo`; nullifiers equal; allocation hashes differ; fractions ≤10000; sum > 10000 → freeze `"equivocation"`.
`DOMAIN_SEPARATOR` is a hard-coded constant, asserted equal to the vector. No OZ `EIP712` inheritance. `reportId` is informational (documented, not checked).
### 8b EIP-712 (Python and Solidity must match)
```
Domain        {name:"Credium", version:"1"}   // NO chainId, NO verifyingContract (on purpose)
Bill          Bill(address vendor,address buyerNGO,uint256 billNo,uint256 amountPaise,uint256 issuedAt,bytes32 category,bytes32 itemsCommitment)
Allocation    Allocation(bytes32 billNullifier,address donorVault,uint256 chainId,uint256 fractionBps,bytes32 reportId)
DOMAIN_SEPARATOR = keccak256(abi.encode(keccak256("EIP712Domain(string name,string version)"), keccak256("Credium"), keccak256("1")))
billDigest    = keccak256(abi.encode(BILL_TYPEHASH, vendor, buyerNGO, billNo, amountPaise, issuedAt, category, itemsCommitment))
billNullifier = keccak256(abi.encode(vendor, billNo, billDigest))   // includes bill content: invoice-number reuse cannot collide
digest = keccak256(0x1901 ‖ DOMAIN_SEPARATOR ‖ structHash)           // abi.encode = 32-byte words, not packed
category = keccak256("WATER")
itemsCommitment = keccak256(salt32 ‖ canonicalItems)   // off-chain only; salt = secrets.token_bytes(32), private fixture
canonicalItems = json.dumps(items, sort_keys=True, separators=(",",":")).encode()
sig = 65 bytes r‖s‖v, v ∈ {27,28}. Python uses eth_utils.keccak, never hashlib sha3.
```
Why no chainId: OZ `EIP712` binds the current chainId, so chain-B evidence could never verify on chain A. Replay is bounded by the struct fields checked on release.
**Vector (13:50):** `sim/fixtures/vector.json` holds DOMAIN_SEPARATOR, billDigest, billNullifier, allocDigest, sigs, signers, plus negatives (wrong chainId, tampered fraction). `test/Gate.t.sol` reads it with `vm.readFile` and `vm.parseJson`.
### 8c Files
`contracts/deployments.json` (written by `deploy.py` on the demo host): `{"simulated": true, "ngo": "0x…", "registrar": "0x…", "chains": {"31337": {"rpc": "http://127.0.0.1:8545", "token": "0x…", "registry": "0x…", "vault": "0x…", "evalVault": "0x…"}, "31338": {"rpc": "http://127.0.0.1:8546", "token": "0x…", "registry": "0x…", "vault": "0x…"}}}`
`sim/fixtures/bills.json` (gen_bills, public): `{"simulated": true, "bills": [{"billId": 17, "billNo": 417, "label": "GENUINE", "expected": "GREEN", "vendorName": "Ramesh Hardware", "bill": {"vendor": "0x…", "buyerNGO": "0x…", "billNo": 417, "amountPaise": 18000000, "issuedAt": 1792806000, "category": "0x…", "itemsCommitment": "0x…"}, "vendorSig": "0x…", "nullifier": "0x…", "reportId": "0x…"}]}` Private: `sim/fixtures/private/bills_private.json` (items, salt), **never served** (test).
`donorVault` is known only after deploy, so `ngoSig` is signed at run time through `sim.signing.sign_allocation` by `eval_run` and the attacks.
### 8d Python signatures
```
sim/signing.py          (Ayaan) bill_digest(bill:dict)->str · bill_nullifier(bill:dict)->str · items_commitment(items:list[dict], salt:bytes)->str
                                sign_bill(bill:dict, vendor_key:str)->str · sign_allocation(alloc:dict, ngo_key:str)->str
verifier/credium_sig.py  (Rishi) recover_bill_signer(bill:dict, sig:str)->str · recover_allocation_signer(alloc:dict, sig:str)->str · bill_nullifier(bill:dict)->str
verifier/verify.py      (Rishi) verdict(record:dict, registry:dict, registrar:str, now:int)->dict   # now = latest chain block timestamp
                                -> {"verdict":"GREEN|AMBER|FORGED|UNKNOWN","tier":0|1|2,"recoveredSigner":str,"reason":str}
sim/meter.py            (Ayaan) compute_meter(pledged:int, deposited:int, released_onchain:int, verified:int, amber:int)->dict
                                -> unexplainedPaise = pledged-deposited; invariantOk = released_onchain == verified   # AMBER is blocked (TierNotGreen), so it is never released
sim/eval_run.py         (Ayaan) run(deployments_path:str, bills_path:str, out:str="sim/fixtures/eval.json")->dict
watcher/watcher.py      (Ayaan) find_equivocations(released:list[dict])->list[dict]   # pure; pairs only allocations with the same ngo
                                scan_once(deployments_path:str)->dict
```
`verdict` order: unregistered → UNKNOWN; recovered ≠ claimed vendor → FORGED; tier 1 → AMBER; tier 0 → GREEN. `registry` = `{address: {"name","enrolledBy","enrolledAt"}}`.
### 8e CLIs (cwd `/credium`; one JSON object on stdout; logs to stderr; `ensure_ascii=True`; `PYTHONUTF8=1`; paths from `__file__`)
```
python contracts/deploy.py --deployments contracts/deployments.json        # Rishi's script, run by Ayaan; deploys both chains
python -m sim.gen_bills --write sim/fixtures/bills.json
python -m sim.seed_demo --deployments contracts/deployments.json           # writes snapshot.json
python -m sim.attacks.forge30 --deployments contracts/deployments.json --bills sim/fixtures/bills.json   # 30 + 1 WRONG_CATEGORY row
python -m sim.attacks.double_claim --billNo 417 --fractionBps 10000 --deployments contracts/deployments.json
python -m sim.eval_run --deployments contracts/deployments.json --bills sim/fixtures/bills.json --out sim/fixtures/eval.json
python -m watcher.watcher --once --deployments contracts/deployments.json  # key: env WATCHER_KEY (default anvil account #8)
```
### 8f API (FastAPI; default bind 127.0.0.1:8000; demo: `--host <LAN IP of Ayaan's laptop>`; `"simulated": true` everywhere)
| Method | Route | Body | Returns |
|---|---|---|---|
| GET | `/`, `/api/health` | — | `web/index.html`; `{"ok":true,"chains":{"31337":true,"31338":true}}` |
| GET | `/api/state` | — | `{"chains":[{"chainId":31337,"label":"Chain A · Donor A","up":true,"block":212,"vault":{"address":"0x…","capPaise":2000000000,"balancePaise":1380000000,"releasedPaise":0,"frozen":false,"frozenReason":""}}],"meter":{"pledgedPaise":2300000000,"depositedPaise":2140000000,"verifiedPaise":0,"amberPaise":0,"unexplainedPaise":160000000,"invariantOk":true},"stale":false}` |
| GET | `/api/bills` | — | public fields only: `billId, billNo, vendorName, amountPaise, verdict, tier, recoveredSigner, reason` |
| GET | `/api/eval` | — | serves `sim/fixtures/eval.json` (static, regenerated by `eval_run`) |
| POST | `/api/release` | `{"chainId":31337,"billNo":405,"fractionBps":10000}` | `{"ok":true,"txHash":"0x…"}` or `{"ok":false,"chainId":31337,"revert":"VaultFrozen(\"equivocation\")"}` |
| POST | `/api/attack/forge30` | — | `{"rows":[…],"summary":{"reverted":30,"tierBlocked":5,"missed":0}}` |
| POST | `/api/attack/double-claim` | `{"billNo":417,"fractionBps":10000}` (encore `418`, `6000`) | `{"steps":[{"chainId":31337,"result":"OK","perChainCheck":"PASS"},{"chainId":31338,"result":"OK","perChainCheck":"PASS"}]}` |
| POST | `/api/watcher/scan` | — | `{"equivocations":[{"billNo":417,"signedTotalBps":20000,"submitted":[{"chainId":31337,"status":"FROZEN"},{"chainId":31338,"status":"FROZEN"}]}],"error":null}` |
| POST | `/api/reset` | — | `evm_revert` to `snapshot.json`, re-snapshot, `{"ok":true}` |

**`/api/release` algorithm:** (1) build Bill and Allocation from the fixture; sign the allocation with the NGO key via `sim.signing`, `donorVault` from deployments. (2) `eth_call` release from any address. On revert, decode the 4-byte selector and args with the `out/` ABI and `eth_abi`. (3) On success, send the tx, wait for the receipt, return `txHash`. Test VaultFrozen and BadVendorSig decoding at 18:00.
## 9. Synthetic data / scenario spec (all labelled SIMULATED)
- **Accounts:** anvil default accounts. Registrar = #0 (stands in for an independent registrar; v1 trust anchor, said on slide). NGO #1. Donor A #6, Donor B #7, watcher #8.
- **Vendors:** GREEN ×6 incl. "Ramesh Hardware" (enrolled by #0, then +8 days). AMBER ×2 "Shree Supplies", "Om Enterprises" (enrolled by NGO #1). UNREGISTERED ×1 "Sharma Traders".
- **Bills:** 100, `billId` 0–99, `billNo = 400 + billId`, `issuedAt = 1792800000 + 3600·billId`. **Pinned GENUINE with GREEN vendors:** billId 5 (#405), 17 (#417, Ramesh), 18 (#418). Pytest asserts. Plus one held-out future-dated bill (billNo 499, outside the 100).
- **Labels (`random.Random(417)` shuffle):** GENUINE 70 · FORGED_EDITED_AMOUNT 18 · FORGED_UNKNOWN_SIGNER 7 · AMBER_SOCKPUPPET 5. Plus one WRONG_CATEGORY row in forge30 (outside the 30).
- **Items:** 1–4 lines (`desc`, `qty`, `unitPaise`); salt via `secrets.token_bytes(32)` into the private fixture.
- **Pledges:** Donor A ₹1.5 cr, deposit ₹1.38 cr (8% mock swap+bridge loss). Donor B ₹80 lakh, deposit ₹76 lakh (5%). Caps ₹2 cr. evalVault funded for eth_call.
- **Seed (`sim/seed_demo.py`):** GREEN enrol by #0 on both chains → `evm_increaseTime(691200)` + `evm_mine` → NGO enrols AMBER vendors → mint and deposit (approve before deposit) → **no releases** (happy path is the live click) → `evm_snapshot`. `run_demo.sh` repeats this every run. Honest note: sock-puppets are AMBER because the NGO enrolled them, not because of age (age rule: `vm.warp` test).
## 10. Evaluation numbers we will show
| Metric | How computed | Scenario |
|---|---|---|
| Flag precision / recall; false positives | flagged = chain revert (any); positives = 30; FP over the 70 genuine; run once → `eval.json` | 100 bills via evalVault eth_call |
| Chain vs verifier agreement | verdict ↔ chain outcome (target 100/100) | same 100 |
| Cross-chain sig verify | Python-signed chain-B allocation verified on chain A | 1 sample at 14:30 (`forge test`); 50 random by 18:00 |
| Double-claim freeze | pairs found; both vaults FROZEN; blocks-to-freeze | #417, #418 |
| Meter invariant | Σ `released()` both chains == verified (AMBER blocked, so the amber term is 0) | positive, plus negative (rogue release → FALSE) |
| Not covered (stated row) | vendor collusion; off-chain spend; delivery; **held-out future-dated bill: MISS 1/1** | printed as `notCovered` |
## 11. Milestones
| By | Rishi (lead, dev box) | Ayaan (support, demo host) | Gate check |
|---|---|---|---|
| 13:05–13:35 | Foundry on Windows (verify at setup, §12); `forge build` on hotspot caches solc; RAM rules §12 | Foundry on Linux; two anvils up; `signing.py`; `gen_bills.py` + pins | `pytest sim/tests` green (70/18/7/5; pins 5/17/18) |
| **13:50** | `recover_allocation_signer` on Ayaan's chain-B sample == `eth_account.encode_typed_data` reference | Sends chain-B sample + `vector.json`; freezes `signing.py` | Python-only sig check passes |
| **14:30 GO/NO-GO** | `forge test --match-contract GateTest`: positive (vector sig → NGO on chain 31337) and negative (chain-B allocation release → `WrongChain`) | — | Pass → continue. Hash mismatch → fallback (b), §15a. Setup slip moves this gate, no fallback. |
| 15:30 | Commits `contracts/out/*.json` (3 artifacts) and `src/` | Pulls code and artifacts | Artifacts on demo host |
| 16:00 | `release()` + registry + negative tests green; `deploy.py` written | `deploy.py` run on both anvils; `seed_demo`, `find_equivocations` | Deploy writes `deployments.json` |
| **17:30** | Standby: runs `forge test` only | Smoke on demo host: `run_demo.sh`, forge30, double_claim CLI, manual #417 | Failures go to cut list (M15) |
| **18:00 integration** | `submitEquivocation` + freeze; `/api/state`, `/api/bills`, `/api/release` decode | `scan_once`, `meter.py`, `forge30.py`, `double_claim.py` | **#417 frozen on both chains via API; VaultFrozen decoded** |
| 20:00 | `verify.py`; API binds to LAN IP | `eval_run`; web v1 | UI ↔ API loop; `eval.json` generated |
| **22:00 E2E + RT** | E2E ×3 on demo host; restart → run_demo → reset → step 1 | UI: panels, meter, eval table | **E2E + red-team green** |
| 22:45 | Backup video → `docs/credium/` | Rehearse 3-min flow | §16 checklist |
| **23:00 mid-eval** | Steps 1–7 live from demo host | Same | **MID-EVAL** |
| 06:00 / 10:45 | Freeze at 06:00 (bugs, polish); final push at 10:45 | Same | Feature freeze, then push |

**Rishi's must-have card:** go/no-go, release + freeze, `/api/state` + `/api/bills` + `/api/release`. Everything else is Ayaan's or cut. **Ayaan's queue (one file each; each has a check he runs himself; code on the 9B coder after `nvidia-smi`, 35B for review only; unload Qwen for every demo run):**
| # | File | Exact signature / I-O | Check |
|---|---|---|---|
| A1 | `sim/signing.py` | §8d functions; `CATEGORY_WATER` = keccak("WATER") | `pytest sim/tests/test_signing.py` |
| A2 | `sim/gen_bills.py` | `generate_bills(seed:int=417, n:int=100)->list[dict]`; CLI §8e | counts; pins 5/17/18 GENUINE + GREEN |
| A3 | `ops/run_demo.sh` | numbered steps: start two anvils (31337/8545, 31338/8546), `deploy.py`, `seed_demo`, start API (`--host $LAN_IP` if set) | Restart → run → reset → step 1 works |
| A4 | `watcher/watcher.py` pure part | `find_equivocations(released:list[dict])->list[dict]` | `pytest watcher/tests` |
| A5 | `sim/seed_demo.py` | `seed(deployments_path:str, out_snapshot:str)->dict`; numbered steps 1–5 in header | Writes snapshot |
| A6a | `sim/attacks/forge30.py` | CLI §8e (30 + WRONG_CATEGORY row) | summary reverted 30 / tierBlocked 5 |
| A6b | `sim/attacks/double_claim.py` | CLI §8e | Prints both steps |
| A7 | `watcher/watcher.py` `scan_once` + CLI | `scan_once(deployments_path:str)->dict` | Freezes #417 on the demo host |
| A8 | `web/index.html` | Reads only §8f routes; panels, console, meter, eval table, SIMULATED banner, cached fallback | Opens in browser against live API |
| A9 | `sim/meter.py` | `compute_meter` (§8d) | `pytest`: invariant true and rogue-release false |
| A10 | `sim/eval_run.py` | `run(...)` (§8d) | Writes `eval.json` with `"simulated": true` |

**Rishi's critical path:** contracts 13:35–16:00 (forge) → artifacts 15:30 → integration 18:00 on demo host → API + verifier 20:00 → E2E 22:00.
## 12. Setup commands
> **Repo (updated 13:45):** https://github.com/rishi-3009/credium. The repo root is the project, with no `credium/` subfolder. Clone to `C:\dev\credium` or `~/dev/credium`. Rishi works on branch `rishi` and Ayaan on `ayaan`. Both merge into `main` by pull request, and only Rishi merges. The exact steps are in the "Git workflow" box of `plans/members/rishi.md` and the "Git" section of `plans/members/ayaan.md`, and those win over the commands below.
**Rishi (Windows dev box, 4 GB):**
```powershell
# verify at setup: Foundry on Windows = prebuilt win32 zip (github.com/foundry-rs/foundry/releases) or foundryup in Git Bash; then `forge --version`
git clone https://github.com/rishi-3009/credium.git C:\dev\credium   # work outside OneDrive; repo root = project
cd C:\dev\credium\contracts; forge install OpenZeppelin/openzeppelin-contracts@v5.0.2 foundry-rs/forge-std   # verify tags at setup
forge build      # run once on hotspot: caches solc 0.8.24 under %USERPROFILE%\.svm
forge test
py -3.11 -m venv ..\.venv; ..\.venv\Scripts\Activate.ps1; pip install "web3>=7" eth-account eth-abi eth-utils pytest httpx
```
`foundry.toml`: `src="src"`, `out="out"`, `libs=["lib"]`, `remappings=["@openzeppelin/=lib/openzeppelin-contracts/"]`, `fs_permissions=[{access="read", path="../sim/fixtures"}]`.
**Rishi RAM rules (4 GB):** close every other app first (Claude Code included where possible); one browser tab; no Docker; `forge test` instead of a running node; at most one anvil + API + one tab for local checks; stop and reboot if free RAM < 1.5 GB.
**Ayaan (demo host, Linux):**
```bash
curl -L https://foundry.paradigm.xyz | bash && source ~/.bashrc && foundryup
anvil --chain-id 31337 --port 8545 --host 127.0.0.1 &
anvil --chain-id 31338 --port 8546 --host 127.0.0.1 &
cast chain-id --rpc-url http://127.0.0.1:8546          # expect 31338
```
Ayaan unloads Qwen before every demo run.
## 13. Cut list (in order)
1. Bridge relayer (mock hop stays) · 2. Beneficiary Merkle + delivery ack (narrate; 11:00 link PARTIAL) · 3. 60+60 encore (keep #417) · 4. Stars "Beat the Escrow" · 5. Separate watcher process → API button (only if CLI breaks) · 6. Web polish.
**Never cut:** cross-chain freeze (#417); forge-30 table with real reverts; `WrongCategory` row; `VaultFrozen` revert; meter invariant with the negative test; the held-out MISS row.
## 14. Wow-upgrades (only if ahead at 02:00): pHash near-duplicate check on a re-photographed #0417 · second watcher on a second laptop over LAN · beneficiary Merkle + signed delivery-ack proof, no PII · catch same-chain 60+60 by scanning reverted-tx calldata.
## 15. Risks + fallbacks
| Risk | Fallback / mitigation |
|---|---|
| Hash mismatch at 14:30 | Fallback (b), §15a. Orchestrator updates PORTFOLIO. |
| Setup slip (Foundry on Windows, solc, hotspot) | Gate moves to 14:30; no fallback triggered. Rishi pushes code; Ayaan runs `forge test` on Linux. |
| Rishi's 4 GB RAM | Rishi runs `forge` and Python checks only. All demo runs, anvil and API are on Ayaan's laptop. |
| LAN to Ayaan's laptop flaky | Rishi drives nothing live; the projector runs on Ayaan's laptop. Rishi's laptop is backup only. |
| Qwen output buggy; 35B eats RAM | pytest check per file; blocked >20 min → tell Rishi; unload the model before any demo run |
| `release` "stack too deep"; watcher subprocess >5 s | Split checks into helpers; call `scan_once` in-process from the API |
| Judges read "on-chain" as "impact proven"; eval looks too perfect | Slide 1: "payment + signed invoice, not the well." Show the unexplained term, held-out MISS row, `notCovered`, "designed attacks, synthetic" |
| Frozen = permanent | Limits slide: "v1 no owner → no unfreeze; v2 donor pro-rata refund after a dispute window." Anyone can run `scan_once`; it needs gas, not permission. |
## 15a Fallback (b): single-chain demo (decided, M11)
Trigger: hash mismatch at 14:30. Action: keep the contracts, drop chain B from the demo. Show on chain A: forge-30 table, `WrongCategory`, `TierNotGreen`, same-chain 60+60 → `OverAllocated`, meter. Watcher runs off-chain only (`find_equivocations` on fixtures). Cross-chain freeze is future work and is said so on stage. Ready by 18:00, runs on the demo host.
## 16. Mid-eval checklist (23:00)
- [ ] `run_demo.sh` runs steps 1–7 live from Ayaan's laptop with no manual edits; backup video in `docs/credium/`
- [ ] Architecture diagram (§5) on slide 1 with SIMULATED label
- [ ] Eval table (§10) with "designed attacks, synthetic", the held-out MISS row and `notCovered`
- [ ] Rishi explains contracts, chain-free signature domain, freeze. Ayaan explains bill generator, attacks, watcher, meter. Mentor feedback → `outputs/03-mid-eval-feedback.md`
- [ ] Problem slide cites CBI (~31 lakh NGOs, ~2.9 lakh filed statements) and the Srijan scam (₹800–1,500 cr)
## 17. CREDITS entries (rows appended to root `CREDITS.md`)
- Toolchain (MIT / Apache-2.0): Foundry (forge, anvil), forge-std; Solidity solc (GPL-3.0, compiler only); OpenZeppelin Contracts 5.x (MIT)
- Libraries (MIT): web3.py v7, eth-account, eth-abi, eth-utils, FastAPI, pytest, httpx · uvicorn (BSD-3) · standard EIP-712 (CC0) · concept only, no code: double-sign equivocation (consensus-specs, CC0)
- Cited facts: LatestLaws, Deccan Herald (pitch slide only). Data: original synthetic bills, vendors, keys and pledges (labelled SIMULATED).
## Open items (PLAN_REVIEW, not fixed in rev 3)
- m2 label "unexplained" simulated; m3 beneficiaries never on chain or in API (delivery = future work); m5 one Python `tierOf`, tested vs chain on 50 cases; m7 deploy reads chainId from `eth_chainId`; m9 show protected balance on freeze screen; m10 name the mechanism "two-signature equivocation freeze"; m12 21:00 "no new work" check. M10 Windows subprocess and encoding: verify at 17:30.
