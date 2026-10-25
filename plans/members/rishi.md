# Rishi — Pod A lead · Credium (`credium`, PS 4.2, Theme 4)

> Built from `plans/credium/MAIN_BUILD_PLAN.md` rev 3 (final, Foundry stack). **Do "Setup now" first, then follow the timeline below. Demo host is Ayaan's laptop; you drive nothing live.**

## ⚠️ Hardware reality: 4 GB RAM
Windows 11 + Claude Code already use most of your RAM, so your laptop is the **dev box only, not the demo host**.

| Rule | Why |
|---|---|
| **No Hardhat / Node.js.** Use **Foundry** (`forge` + `anvil`) | A Hardhat node uses hundreds of MB; anvil is a light Rust binary |
| Prefer `forge test` over keeping a chain running | Contract tests run in-process with no node |
| At most: **1 anvil + FastAPI + 1 browser tab** at a time | Two chains + API + browser ≈ 8 GB, more than you have |
| No Docker. Close Teams, Discord, extra Chrome windows, OneDrive sync | Every 300 MB matters |
| **Ayaan's laptop (24 GB, Linux) hosts** the 17:30 smoke test, the 23:00 mid-eval and the final demo | He unloads Qwen during those runs |
| You view the demo over LAN at most; you drive nothing live (rev 3 §15) | FastAPI binds to `127.0.0.1` locally, to the LAN IP only on the demo host |

## 🔀 Git workflow: `credium` repo (overrides every other git note in the plans)
- **Repo:** https://github.com/rishi-3009/credium. **You own it and you merge.** The repo root IS the project: `contracts/`, `verifier/`, `api/`, `sim/`, `watcher/`, `web/`, `ops/` sit directly in it. Plans live in `plans/`.
- **Branches:** you work on `rishi` and Ayaan on `ayaan`. **Nobody commits to `main`**, except your one bootstrap push.
- **One open PR per branch into `main`.** Every `git push` updates it.
- **When you merge (in the browser):**
  - At each gate: 13:50, 15:30 artifacts, 16:00, 18:00, 22:00, 06:00, 10:45.
  - Whenever Ayaan says "card NN pushed" and you need his code.
  - Use **Merge pull request → Confirm merge**. **Do NOT delete the branch.** Then run `git pull --no-edit origin main` locally.
- **Every `git pull` in this plan** means `git pull --no-edit origin main`.
- **Opening a PR:**
  - The first time, and again after each merge (a merged PR closes): push, open the repo page, click **Compare & pull request**, check `main ← rishi`, then **Create**.
- **15:30 artifacts:** Ayaan needs `contracts/out/*.json`, so **merge your PR right after that push** and tell him "artifacts merged".

## ✅ Setup now (on a phone hotspot; venue Wi-Fi is unreliable)
- [ ] **Clone the repo outside OneDrive, then bootstrap `main` with the plans** (OneDrive sync breaks build folders and eats RAM):
  ```bash
  mkdir -p /c/dev && cd /c/dev
  git clone https://github.com/rishi-3009/credium.git      # empty repo: "cloned an empty repository" is normal
  cd credium
  # copy the CONTENTS of the credium-handoff folder (plans/, CREDITS.md, README.md) into C:\dev\credium, then:
  git add plans CREDITS.md README.md
  git commit -m "Bootstrap: plans and credits"
  git push -u origin main                                  # the ONLY direct push to main
  git config pull.rebase false
  git config push.autoSetupRemote true
  git switch -c rishi                                      # your branch from now on
  ```
  Then on GitHub, go to **Settings → Collaborators → Add people** and add Ayaan. Message him: **"main is up, accept the invite"**.
- [ ] **Open Claude Code in `C:\dev\credium`.** Every prompt below reads plans from `C:\dev\credium\plans\...`.
- [ ] **Install Foundry** in Git Bash (⚠️ not yet verified on Windows; if it fails, tell the orchestrator immediately):
  ```bash
  curl -L https://foundry.paradigm.xyz | bash
  # open a NEW Git Bash window, then:
  foundryup
  forge --version && anvil --version
  ```
  Fallback if `foundryup` fails: download the prebuilt Windows zip from the Foundry GitHub releases, unzip `forge.exe`/`anvil.exe`/`cast.exe` into `C:\dev\foundry\` and add that to PATH. **Last resort:** anvil runs only on Ayaan's laptop and you connect to it over LAN (`http://<ayaan-ip>:8545`).
- [ ] **Check Python 3.11+:**
  ```bash
  py -3.11 --version
  ```
- [ ] **Pre-cache the compiler** while you have internet: once the contracts folder exists, run `forge build` once so solc gets downloaded and cached.
- [ ] Copy pip wheels and the Foundry binaries to USB as an offline backup.

## Stack changes vs. the first plan
| Was | Now |
|---|---|
| Hardhat compile/test | `forge build` / `forge test` |
| Hardhat node ×2 | `anvil --chain-id 31337 --port 8545` and `anvil --chain-id 31338 --port 8546` |
| `deploy.ts` | `forge script` or a Python (web3.py) deploy that reads `out/*.json` |
| Hardhat artifacts for Ayaan | Commit `out/*.json` (ABI + bytecode only) at **15:30** |
| 14:30 Solidity go/no-go via Hardhat | `forge test`: positive (chain-B allocation recovers the NGO) + negative (release on chain A reverts `WrongChain`) |
| Demo on your laptop | Demo on **Ayaan's** laptop |

---

# Your plan: Credium, Pod A lead (rev 3)

**You own:** `C:\dev\credium\contracts\` (src, test, foundry.toml, deploy.py, out/ artifacts), `C:\dev\credium\verifier\` (credium_sig.py, verify.py, tests/), `C:\dev\credium\api\` (main.py).
**Your AI:** Claude Code (Windows).
**Your machine:** Windows 11 · Intel i3 · integrated GPU (no CUDA) · **4 GB RAM**. Dev box only, never the demo host.
**Your one job in one sentence:** Make the Solidity contracts and the Python verifier agree byte-for-byte on the signed invoice format, so a fake or re-used bill is rejected on chain and a double-signed bill freezes every donor vault.

**Who depends on you, and when:**
- **Ayaan:** 13:50 (you confirm his chain-B sample recovers); 15:30 `out/*.json` artifacts; 16:00 `deploy.py`; 18:00 the `/api/*` routes and JSON shapes (his `web/` and `watcher` code target them); 20:00 `verify.py` (his `eval_run` calls `verdict`).
- **The orchestrator:** 14:30 GO/NO-GO result. A hash mismatch there triggers §15a.
- **The 23:00 mid-eval:** you explain the contracts, the chain-free signature domain, and the freeze.

**You depend on:**
- **Ayaan, 13:50:** `sim/fixtures/vector.json`, the chain-B sample file, and `sim/signing.py` frozen (his card **A1**). Until then, use your own reference signer: `verifier/tests/reference_sign.py` (you write it 13:35–13:50 with `eth_account`).
- **Ayaan, by 14:30:** `sim/fixtures/bills.json` with pins for billId 5, 17, 18 (card **A2**). Until then, use the 3 hand-made bills inside `verifier/tests/reference_sign.py`.
- **Ayaan's demo host, 16:00–18:00:** anvil ×2, `run_demo.sh` (A3), `seed_demo` (A5), attack CLIs (A6a, A6b), `scan_once` (A7), `compute_meter` (A9), `eval_run` (A10). Until then: `forge test` runs in-process and needs no node.

⚠️ ASK Ayaan: exact filename of the chain-B sample he sends at 13:50 (rev 3 does not name it).

## Must-have card (if nothing else works, these work)
| Item | Pass test |
|---|---|
| **GO/NO-GO (14:30)** | `forge test --match-contract GateTest` passes: positive (vector allocation recovers to NGO) and negative (chain-B allocation released on chain A reverts `WrongChain`) |
| **Release** | `release()` pays GREEN bill #405 on chain A |
| **Freeze** | `submitEquivocation` freezes both vaults on #417. Release after that reverts `VaultFrozen("equivocation")` |
| **`GET /api/state`** | returns the §8f shape with both chains, meter, `stale` |
| **`GET /api/bills`** | public fields only, never `items` or `salt` |
| **`POST /api/release`** | `eth_call` first; revert decoded to a readable string; success returns `txHash` |

Everything else is Ayaan's or cut (§13 cut list).

## Timeline (hour by hour, gates in bold)
| Time block | Task | Done when | Push to |
|---|---|---|---|
| 13:05–13:35 | Setup (see Setup now above) | `forge build` ok on hotspot; venv ok; `pytest` runs | nothing yet |
| 13:35–13:50 | MockINR, VendorRegistry, `credium_sig.py`, `reference_sign.py` | `pytest verifier/tests -q` green on your reference | `contracts/src`, `verifier/` |
| **13:50** | **Python check**: Ayaan's chain-B sample recovers to the NGO | `test_vector.py` passes | `verifier/` |
| 13:50–14:30 | PurposeVault skeleton, `release()` up to the `chainId` check, GateTest | GateTest compiles | `contracts/` |
| **14:30** | **GO/NO-GO**: `forge test --match-contract GateTest` | positive and negative pass, or §15a | nothing to push |
| 14:30–15:30 | Full `release()` and `Release.t.sol` (1 happy + 8 negative) | `forge test --match-contract ReleaseTest` green | `contracts/` |
| **15:00** | **Check on your partner**: pull; run `pytest sim/tests` on your laptop (Windows cross-check); confirm `vector.json` and chain-B sample arrived | Ayaan's A1 and A2 status known | nothing |
| **15:30** | **Artifacts**: 3 ABI + bytecode JSONs | files on remote; Ayaan confirms he pulled | `contracts/out` (forced add) |
| 15:30–16:00 | `Vault.t.sol`, `deploy.py` (one anvil, chain 31337 only) | forge green; deploy writes `deployments.json` for 31337 | `contracts/` |
| **16:00** | **Contracts green** | release, registry and negative tests green; `deploy.py` written | `contracts/` |
| 16:00–17:30 | `submitEquivocation` and `Equivocation.t.sol` | `forge test` green | `contracts/` |
| **17:00** | **Check on your partner**: pull; confirm A3 `run_demo.sh` and A4 watcher pure part exist and `pytest watcher/tests` ran | 17:30 smoke is go | nothing |
| **17:30** | **Smoke test on Ayaan's laptop**. You stand by and run the Windows-only check | Windows check passes | `api/tests` |
| 17:30–18:00 | Fix list from smoke (your files only) | fixes pushed | `contracts/`, `api/` |
| **18:00** | **Integration gate**: #417 frozen on both chains via API; `VaultFrozen` decoded | gate check in Section 11 | `api/` |
| 18:00–19:00 | `api/main.py` routes (§8f) | `pytest api/tests -q` green | `api/` |
| **19:00** | **Check on your partner**: pull; confirm A5, A6a, A6b print one JSON each on Linux; A8 reads only §8f routes | | nothing |
| 19:00–20:00 | `verify.py`; tierOf 50-case check against chain | `pytest verifier -q` green | `verifier/` |
| **20:00** | `verify.py` done; API binds to LAN IP on demo host | Ayaan's `eval_run` runs | nothing |
| **21:00** | **No-new-work check** with Ayaan (m12). **Check on your partner** | both cut lists frozen; sleep rotation agreed | nothing |
| **22:00** | **Mid-eval prep**: E2E ×3 on demo host, restart → run_demo → reset → step 1 | E2E green 3 times | nothing |
| 22:45 | Rehearse the 3-min flow; tick §16 rows you own | rehearsal done | `docs/credium/` (if video) |
| **23:00** | **MID-EVAL**: steps 1–7 live from demo host. You explain contracts, domain, freeze | feedback noted | `outputs/03-mid-eval-feedback.md` (append only) |
| **23:00** | **Check on your partner** (before mid-eval) | steps 1–7 status known | nothing |
| 23:15–00:00 | Act on feedback (block 15) | smallest change agreed | as needed |
| **00:00** | Side quest decision, 15 min, with Ayaan | decided | nothing |
| **01:00** | **Check on your partner** | sprint 3 status | nothing |
| 00:00–03:00 | Sprint 3 (block 16) | eval numbers in place | `contracts/`, `api/`, `verifier/` |
| **03:00** | **Check on your partner** (last before sleep). Then sleep 03:00–04:30 | Ayaan awake | nothing |
| **05:00** | **Check on your partner** (you awake, Ayaan asleep 04:30–06:00): read his last commits | list of his needs for 06:00 | nothing |
| **06:00** | **Feature freeze**: no new features, bugs and polish only | freeze commit tagged | `contracts/`, `api/`, `verifier/` |
| 06:00–08:30 | Polish, slide text, backup video copies on your laptop | copies on disk | `docs/credium/` |
| **07:00** | **Check on your partner** | backup video copies present | nothing |
| 08:30–10:30 | Rehearse ×3, Q&A drill (block 18) | you answer the 5 questions | nothing |
| **09:00** | **Check on your partner** | rehearsal issues list | nothing |
| **10:45** | **Final push**. Do not push at 10:59 | `git status` clean | remote |
| 11:00 | Hack ends | | |

**Gate note:** rev 3 puts GO/NO-GO at **14:30**. `plans/PORTFOLIO.md` still says 14:00. Rev 3 wins; the portfolio line is stale.

## Build blocks: brief and Claude Code prompt per block
Every prompt below assumes you work only in `C:\dev\credium`. Do not edit `sim/`, `watcher/`, `ops/` or `web/` (Ayaan's). Do not install Node, Hardhat or Docker. Before any `forge test` or `anvil` run, close Chrome, Teams and OneDrive, then check free RAM:
```powershell
Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory
```
This prints free RAM in KB. Below about 1,500,000 KB (1.5 GB), stop and reboot (§12).

### Block 1 · 13:05–13:35 · Setup
**Brief:** Do "Setup now" top to bottom on the hotspot. Then make the folders and the Python environment.
- Create `C:\dev\credium\contracts`, `verifier\tests`, `api\tests`. Ayaan's folders (`sim`, `watcher`, `ops`, `web`) arrive by `git pull --no-edit origin main`. Do not create them.
- Shared repo URL: ⚠️ ASK orchestrator. It is not in the context files. Until it is known, Setup uses the §12 commands only.
- Python environment:
```powershell
cd C:\dev\credium
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install "web3>=7" eth-account eth-abi eth-utils pytest httpx fastapi uvicorn
```
*What this does:* creates a private Python 3.11 environment in `.venv` so the project's libraries don't mix with other installs. If `Activate.ps1` is blocked, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- Foundry: `forge --version` must print a version. Then `cd contracts` and `forge build` once, so solc 0.8.24 is cached.

**Prompt (paste into Claude Code):**
```
Read C:\dev\credium\plans\credium\MAIN_BUILD_PLAN.md sections 6 and 12 only.
In C:\dev\credium\contracts create foundry.toml exactly as section 12 says: src, out, lib, the OpenZeppelin remapping, and fs_permissions read on ../sim/fixtures.
Run forge install for OpenZeppelin/openzeppelin-contracts@v5.0.2 and foundry-rs/forge-std. If a tag does not exist, stop and tell me which one.
Run forge build once. Write no product code. Do not install Node, Hardhat or Docker.
Report: forge version, whether solc 0.8.24 cached, and the output of: python -c "import web3, eth_account; print('ok')" run from C:\dev\credium with the venv active.
```
**Done when:** `forge build` succeeds and the Python import prints `ok`.

### Block 2 · 13:35–13:50 · Tokens, registry, signatures, reference signer
**Brief:** Four files, in this order. Each has a test.
1. `contracts/src/MockINR.sol`: ERC20, `decimals()` returns 0 (units = paise), open `mint` (it is a mock).
2. `contracts/src/VendorRegistry.sol`: constructor `(address registrar)`. `enroll(address vendor, string name)` is open and records `enrolledBy = msg.sender` and `enrolledAt = block.timestamp`. `tierOf` per §8a: **GREEN** iff `enrolledBy == registrar` AND age ≥ 7 days; **AMBER** iff enrolled by anyone else, or registrar with age < 7 days; **UNREGISTERED** otherwise (tier 2). This is M1, the registrar rule.
3. `verifier/credium_sig.py`: `recover_bill_signer`, `recover_allocation_signer`, `bill_nullifier` with the exact signatures in Section 8d. Use `eth_utils.keccak` and `eth_abi.encode`. Never `hashlib.sha3_256`.
4. `verifier/tests/reference_sign.py`: an **independent** signer built on `eth_account.messages.encode_typed_data`. It must not import `credium_sig.py`. The NGO key comes from environment variable `NGO_KEY`. Never commit a key. This file is also your mock for Ayaan's `signing.py`.

**Prompt (paste into Claude Code):**
```
Read C:\dev\credium\plans\credium\MAIN_BUILD_PLAN.md sections 8a, 8b, 8d and PLAN_REVIEW.md M1, M3, M4.
Create these four files in C:\dev\credium, exactly as specified:
(1) contracts/src/MockINR.sol: ERC20, decimals 0, open mint.
(2) contracts/src/VendorRegistry.sol: constructor(address registrar); enroll(address vendor, string name) records enrolledBy=msg.sender, enrolledAt=block.timestamp; isRegistered; tierOf per section 8a (0 GREEN iff enrolledBy==registrar AND block.timestamp >= enrolledAt + 7 days; 1 AMBER iff enrolled by anyone else, or registrar younger than 7 days; 2 UNREGISTERED).
(3) verifier/credium_sig.py: recover_bill_signer(bill:dict, sig:str)->str, recover_allocation_signer(alloc:dict, sig:str)->str, bill_nullifier(bill:dict)->str, exactly per section 8d and 8b. Use eth_utils.keccak and eth_abi.encode. Never hashlib.
(4) verifier/tests/reference_sign.py: independent signer using eth_account.messages.encode_typed_data with domain {name:"Credium", version:"1"}. It must NOT import credium_sig. NGO key from env NGO_KEY. Never hard-code a key.
Then write verifier/tests/test_credium_sig.py: sign 3 bills and 3 allocations with reference_sign; assert recover_* returns the reference address (compare lowercase).
Run: pytest verifier/tests -q. Do not touch sim/, api/ or watcher/.
```
**Done when:** `pytest verifier/tests -q` is green. The 13:50 check depends on it.

### Block 3 · 13:50 · Python check (GATE 1)
**Brief:** Ayaan hands over `sim/fixtures/vector.json`, the chain-B sample, and frozen `signing.py` at 13:50. Your check uses your own code and your own reference. Do not import his `signing.py`. That independence is the point of the check.
- Pass: the chain-B allocation recovers to the NGO, and the recomputed nullifier and digests match the vector.
- Fail: fix within 30 minutes. A mismatch still standing at 14:30 is the §15a trigger.

**Prompt (paste into Claude Code):**
```
Read C:\dev\credium\plans\credium\MAIN_BUILD_PLAN.md sections 8b and 8d, and C:\dev\credium\plans\credium\PLAN_REVIEW.md B1(b).
Create C:\dev\credium\verifier\tests\test_vector.py.
It loads C:\dev\credium\sim\fixtures\vector.json (keys: DOMAIN_SEPARATOR, billDigest, billNullifier, allocDigest, sigs, signers, negatives) and the chain-B allocation sample at the path given in the message from Ayaan.
Assert: recover_allocation_signer(sample) equals the NGO entry inside signers (lowercase compare); recomputed nullifier and allocDigest equal the vector values; DOMAIN_SEPARATOR matches section 8b's formula.
Negative: change fractionBps by 1 in a copy; recovered signer must NOT equal the NGO.
Imports allowed: credium_sig, eth_account, json, pathlib. Do NOT import sim.signing.
Run: pytest verifier/tests/test_vector.py -q
```
**Done when:** the test passes. Then message Ayaan "13:50 check green" with the commit id.

### Block 4 · 13:50–14:30 · PurposeVault top half and GateTest
**Brief:** Write `contracts/src/PurposeVault.sol` with the 8a constructor, the events and errors, `deposit`, `billSigner`, `allocationSigner`, and `DOMAIN_SEPARATOR` as a **hard-coded constant** (not OZ EIP712, M4). Write `release()` up to and including the `chainId` check, in the exact order from §8a. A valid vendor signature must pass before the chainId check is reached, otherwise the negative test proves nothing.
Write `contracts/test/Gate.t.sol` with contract **`GateTest`** (the name the 14:30 command uses):
- Positive: `DOMAIN_SEPARATOR` equals the vector; `allocationSigner(chain-B allocation, sig)` equals the NGO.
- Negative: a chain-B allocation released on chain 31337 reverts `WrongChain(31338)`.
- Read the vector with `vm.readFile("../sim/fixtures/vector.json")` and `vm.parseJson`.

**Prompt (paste into Claude Code):**
```
Read C:\dev\credium\plans\credium\MAIN_BUILD_PLAN.md sections 8a, 8b, 8c and PLAN_REVIEW.md B1(c), M4.
In C:\dev\credium\contracts create src/PurposeVault.sol per section 8a: constructor(address token, address ngo, address registry, bytes32 category, uint256 capPaise); deposit; billSigner; allocationSigner; DOMAIN_SEPARATOR as a hard-coded constant from section 8b, NOT an OZ EIP712 inheritance; ECDSA.tryRecover for signatures.
Write release() up to and including the chainId check, in this exact order: frozen, category, NGO, tier, vendor sig, chainId. Leave the rest for later.
Create test/Gate.t.sol with contract GateTest. Positive: DOMAIN_SEPARATOR equals sim/fixtures/vector.json; allocationSigner of the chain-B allocation equals the NGO. Negative: release on chain 31337 of a chain-B allocation (with a valid vendor sig) reverts WrongChain(31338). Use vm.readFile("../sim/fixtures/vector.json") and vm.parseJson.
Do not touch sim/, watcher/, web/. Run: forge build.
```
**Done when:** `forge build` compiles and GateTest exists.

### Block 5 · 14:30 · GO/NO-GO (GATE 2)
Run in PowerShell:
```powershell
cd C:\dev\credium\contracts
forge test --match-contract GateTest -vv
```
*What this does:* runs only the gate tests, with verbose output. Expected: all GateTest tests pass, 0 failed.
- **PASS:** continue to block 6.
- **FAIL, hash mismatch** (recovered signer ≠ NGO, or DOMAIN_SEPARATOR ≠ vector) while `test_vector.py` passed at 13:50: this is the **§15a trigger**. Tell the orchestrator within 5 minutes. Do not start block 6 on the old design.
- **FAIL, forge does not run** (solc, lib or path errors): **setup slip, not a fallback**. Fix it. If forge still does not run at 14:45, tell the orchestrator. Ayaan runs `forge test` on Linux (§15, "Setup slip" row).

**Prompt (paste into Claude Code, only if it fails):**
```
Run: forge test --match-contract GateTest -vv from C:\dev\credium\contracts. Read the full output.
Tell me which assertion failed and whether the failure is (a) a setup/solc/path error or (b) a hash or signature mismatch.
For (b), print the DOMAIN_SEPARATOR and the recovered signer from forge, and the same values from test_vector.py. Do not change any code yet.
```

### Block 6 · 14:30–15:30 · Full release() and Release.t.sol
**Brief:** Finish `release()` in §8a order. Split checks into internal helper functions if you get "stack too deep". Payee = `bill.vendor`. Pay `amountPaise * fractionBps / 10000` (floor), and track `usedBps` cumulatively.
- ⚠️ ASK orchestrator: rev 3 has a `cap` check but no definition. **Working assumption:** total released from the vault may not exceed `capPaise` (₹2 cr in the demo, `CapExceeded()`). Confirm before you write the check.
- **Happy path:** GREEN bill #405 at a full fraction emits `Released` with every field.
- **Eight negatives** (my proposed set, covering the demo rows): `WrongCategory`, `WrongNGO`, `UnknownVendor`, `TierNotGreen(1)`, `BadVendorSig`, `WrongVault`, `OverAllocated`, `VaultFrozen`. `WrongChain` is already in GateTest.

**Prompt (paste into Claude Code):**
```
Read C:\dev\credium\plans\credium\MAIN_BUILD_PLAN.md section 8a (release order and errors) and PLAN_REVIEW.md B1(c), M2, M4, m4.
In C:\dev\credium\contracts finish PurposeVault.release() after the chainId check, in this order: donorVault == this (WrongVault), nullifier (NullifierMismatch), NGO sig (BadNgoSig), fraction in (0,10000] (BadFraction), cumulative usedBps <= 10000 (OverAllocated), cap (CapExceeded: ASSUMPTION released + amount <= capPaise, flag it in a comment), balance (InsufficientBalance). Pay floor(amountPaise*fractionBps/10000) to bill.vendor. Emit Released with every field from section 8a.
Split into internal helpers if you get stack too deep.
Write test/Release.t.sol: 1 happy path plus 8 negatives: WrongCategory, WrongNGO, UnknownVendor, TierNotGreen(1), BadVendorSig, WrongVault, OverAllocated, VaultFrozen. Use vm.warp for the 7-day GREEN age.
Run: forge test --match-contract ReleaseTest. Do not touch sim/, watcher/, web/.
```
**Done when:** `forge test --match-contract ReleaseTest` is green.

### Block 7 · 15:30 · Artifacts push (ARTIFACTS GATE)
**Brief:** Ayaan's laptop needs only the ABI and bytecode of the three contracts, not your whole `out/` folder. Forge's default `.gitignore` hides `out/`, so the three files must be force-added.
```powershell
cd C:\dev\credium
forge build --root contracts
git status
git add contracts/src contracts/test contracts/foundry.toml verifier api
git commit -m "contracts: release, registry, gate tests"
git pull --no-edit origin main
git push
git add -f contracts/out/MockINR.sol/MockINR.json contracts/out/VendorRegistry.sol/VendorRegistry.json contracts/out/PurposeVault.sol/PurposeVault.json
git commit -m "artifacts: ABI and bytecode for demo host"
git push
```
*What each git step does:* `git status` lists what changed. `git add` picks files for the next commit. `git commit` saves them locally with a message. `git pull --no-edit origin main` fetches Ayaan's changes and replays yours on top. `git push` uploads your commits. `-f` forces the add past `.gitignore`. **Never run `git add .`**, because it would also add `lib\` and `cache\`.

**Prompt (paste into Claude Code, if you want help):**
```
From C:\dev\credium, run git status and show me exactly which files would be committed. Do not stage anything yet.
Then confirm that these three files exist and are non-empty: contracts/out/MockINR.sol/MockINR.json, contracts/out/VendorRegistry.sol/VendorRegistry.json, contracts/out/PurposeVault.sol/PurposeVault.json. Each must contain an "abi" and a "bytecode" key.
```
**Done when:** Ayaan replies that he pulled and can see the three files.

### Block 8 · 15:30–16:00 · Vault tests and deploy.py
**Brief:**
- `contracts/test/Vault.t.sol`: deposit (approve, then deposit, then `Deposited` event), cap behaviour.
- `contracts/deploy.py` (web3.py v7) per §8c and §8e. It reads `out/<Name>.sol/<Name>.json`. Deploys `MockINR`, `VendorRegistry(registrar)`, and `PurposeVault` per chain with category `keccak("WATER")`. Deploys `evalVault` on 31337 with the same registry (B4). Reads chainId from `eth_chainId` (m7). Writes the `--deployments` JSON with `"simulated": true`.
- Deployer key from env `DEPLOYER_KEY`, never committed. Registrar = anvil account #0.
- **`deploy.py` does not enrol vendors.** Ayaan's `seed_demo` (A5) does that, so the boundary is clear.
- Your laptop has only one anvil, so the full two-chain deploy is Ayaan's run at 16:00. On your laptop test 31337 only. If the script needs a flag for that, add `--only-chain 31337`. It is your file, so that change is yours to make.
```powershell
anvil --chain-id 31337 --port 8545 --host 127.0.0.1
```
*What this does:* starts a local test chain on your laptop (light Rust binary). Keep it running only for this test, then press Ctrl+C.

**Prompt (paste into Claude Code):**
```
Read C:\dev\credium\plans\credium\MAIN_BUILD_PLAN.md sections 8a, 8c, 8e and PLAN_REVIEW.md B4, m7.
In C:\dev\credium\contracts write deploy.py (web3.py v7). CLI: python contracts\deploy.py --deployments <path>. It reads out\<Name>.sol\<Name>.json for MockINR, VendorRegistry, PurposeVault. Chain RPCs: 31337 at http://127.0.0.1:8545 and 31338 at http://127.0.0.1:8546; read the chainId from eth_chainId, not from a constant. Deployer key from env DEPLOYER_KEY (never hard-coded). Registrar = the account whose key is DEPLOYER_KEY.
Per chain: MockINR (decimals 0), VendorRegistry(registrar), PurposeVault(token, ngo, registry, keccak("WATER"), capPaise). Deploy evalVault only on 31337 with the same registry.
Write deployments.json exactly as section 8c, including "simulated": true. Print the JSON result to stdout with json.dumps(ensure_ascii=True). Logs go to stderr. Build all file paths from __file__, never from the current directory.
Do not enrol vendors. Add --only-chain 31337 if needed so it can run against one anvil.
Also write contracts/test/Vault.t.sol: deposit approve-then-transfer, Deposited event, cap.
Run: forge test --match-contract VaultTest. Do not touch sim/, watcher/, web/.
```
**Done when:** `forge test --match-contract VaultTest` is green, and `deploy.py --only-chain 31337` writes a JSON file (or you have confirmed the flag is unneeded).

### Block 9 · 16:00 · Contracts green (GATE 3)
```powershell
cd C:\dev\credium\contracts
forge test
```
*What this does:* runs every Solidity test (Gate, Release, Vault). Expected: 0 failed.
Then Ayaan runs `deploy.py` on both anvils. You check the `deployments.json` he pastes has `31337` and `31338` entries and `"simulated": true`.
**Done when:** `forge test` is fully green and the deploy output is pasted in chat.

### Block 10 · 16:00–17:30 · submitEquivocation and Equivocation.t.sol
**Brief:** Implement `submitEquivocation(Allocation a, bytes sigA, Allocation b, bytes sigB)` in the §8a rules: if already frozen, return. Recover both signatures with `tryRecover`, both must equal `ngo`, nullifiers equal, allocation hashes differ, each fraction ≤ 10000, and the sum > 10000. Then freeze with reason `"equivocation"` and emit `Frozen`.
**Test:** deploy two vaults in one forge test. Two NGO allocations with the same nullifier, fractions 10000 and 10000 (#417). Submit to both. Both frozen. A release after that reverts `VaultFrozen("equivocation")`. Also cover the 6000 + 6000 encore (#418) and the no-op when already frozen.

**Prompt (paste into Claude Code):**
```
Read C:\dev\credium\plans\credium\MAIN_BUILD_PLAN.md sections 4 (A3, A4), 8a (submitEquivocation rules) and PLAN_REVIEW.md M12.
In C:\dev\credium\contracts implement PurposeVault.submitEquivocation exactly as the section 8a rules say: no-op if frozen; recover both sigs with ECDSA.tryRecover and require each == ngo; nullifiers equal; allocation hashes differ; fractions <= 10000; sum > 10000; then freeze with reason "equivocation" and emit Frozen(reason, billNullifier, submitter).
Write test/Equivocation.t.sol: two NGO-signed allocations with the same billNullifier and fractions 10000 + 10000 (bill 417); submit to two vaults; both frozen; release reverts VaultFrozen("equivocation"). Add a 6000 + 6000 case (bill 418). Add a no-op test when already frozen.
Run: forge test --match-contract EquivocationTest. Do not touch sim/, watcher/, web/.
```
**Done when:** `forge test --match-contract EquivocationTest` is green.

### Block 11 · 17:30 · Smoke test on Ayaan's laptop (you: standby + Windows check)
**Brief:** Ayaan runs `run_demo.sh`, `forge30`, `double_claim`, and manual #417 on Linux. You stand by. Triage his errors: contract or API bug goes to you; `sim/` bug goes to him; anything that does not fit goes on the cut list (§13, M15).
Your job here is the **Windows-only check** (review M10): subprocess and encoding on your machine, without a chain.
```powershell
cd C:\dev\credium
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\Activate.ps1
pytest api\tests -q
```
*What this does:* sets UTF-8 for Python on this shell, then runs the API tests on Windows.

**Prompt (paste into Claude Code):**
```
Read C:\dev\credium\plans\credium\MAIN_BUILD_PLAN.md sections 8e and PLAN_REVIEW.md M10.
In C:\dev\credium create api\tests\test_win_subprocess.py. It calls subprocess.run([sys.executable, "-c", 'import json; print(json.dumps({"ok": True}))'], capture_output=True, text=True) and asserts returncode 0 and json.loads(stdout) == {"ok": True}.
Add a second test that spawns sys.executable -m sim.gen_bills --help from the project root (cwd set to the folder of __file__'s parent parent). Assert returncode 0. Skip with pytest.skip if sim/ is not pulled yet.
Run: pytest api\tests -q. Report failures verbatim. Do not change any file outside api\tests.
```
**Done when:** `pytest api\tests -q` is green or skipped, not failed.

### Block 12 · 17:30–18:00 · Smoke fix list
Fix only the contract and API problems Ayaan reported. Anything else goes on the cut list. Push by 18:00.

### Block 13 · 18:00–19:00 · api/main.py (INTEGRATION GATE)
**Brief:** FastAPI app in `api/main.py`, all routes per Section 8f. Bind 127.0.0.1 by default; accept `--host <LAN IP>` only on the demo host.
- `GET /api/state`, `GET /api/bills`, `POST /api/release` are the must-haves.
- `POST /api/release` algorithm (§8f, 3 steps): (1) build the Bill and Allocation from the fixture, sign the allocation with the NGO key through `sim.signing.sign_allocation`, with `donorVault` from `deployments.json`. (2) `eth_call` `release` from any address. On revert, decode the 4-byte selector and args with the ABI from `out/PurposeVault.sol/PurposeVault.json` and `eth_abi`. (3) On success, send the tx, wait for the receipt, return `txHash`.
- `GET /api/bills` returns only `billId, billNo, vendorName, amountPaise, verdict, tier, recoveredSigner, reason`. A test asserts no `items` or `salt` key ever appears (M8).
- Thin wrappers for Ayaan's CLIs: `/api/attack/forge30`, `/api/attack/double-claim` (subprocess via `sys.executable`), `/api/watcher/scan` (in-process `scan_once`, §15), `/api/eval` (serves `sim/fixtures/eval.json`), `/api/reset` (`evm_revert` to `snapshot.json`).

**Prompt (paste into Claude Code):**
```
Read C:\dev\credium\plans\credium\MAIN_BUILD_PLAN.md sections 8c, 8e, 8f, and PLAN_REVIEW.md M7, M8, M10, B3.
In C:\dev\credium\api create main.py: FastAPI app implementing the 8f routes exactly (method, route, body, returns). Default bind 127.0.0.1; accept --host and --port on the CLI for the demo host.
Implement /api/release with the 3-step algorithm in 8f. Decode reverts by the 4-byte selector using the ABI in contracts/out/PurposeVault.sol/PurposeVault.json and eth_abi. Return {"ok":false,"chainId":...,"revert":"VaultFrozen(\"equivocation\")"} on revert.
Implement /api/state from web3 (block number, vault fields, meter from sim.meter.compute_meter with a read-only import).
/api/bills returns public fields only. Never return items or salt.
Subprocess calls use sys.executable and cwd set to the project root. Logs to stderr. json.dumps(ensure_ascii=True).
Write api/tests/test_api.py with FastAPI TestClient. Include a test that decodes a VaultFrozen("equivocation") revert payload and one that decodes BadVendorSig(address).
Run: pytest api -q. Do not edit sim/, watcher/, web/.
```
**Done when:** `pytest api -q` is green, and at 18:00 Ayaan's run on the demo host shows #417 frozen on both chains through the API.

**18:00 gate check (Ayaan runs on demo host, you read the output):**
```bash
curl -X POST http://127.0.0.1:8000/api/attack/double-claim -H "Content-Type: application/json" -d '{"billNo":417,"fractionBps":10000}'
curl -X POST http://127.0.0.1:8000/api/watcher/scan
curl -X POST http://127.0.0.1:8000/api/release -H "Content-Type: application/json" -d '{"chainId":31337,"billNo":417,"fractionBps":10000}'
```
*What these do:* run the double claim, run the watcher scan, then try a release on the frozen bill. Expected: the scan reports `FROZEN` on both chains, and the release returns `"ok": false` with `VaultFrozen("equivocation")` decoded.

### Block 14 · 19:00–20:00 · verify.py and tierOf check
**Brief:** `verifier/verify.py`: `verdict(record, registry, registrar, now)` per §8d, order: unregistered → UNKNOWN; recovered ≠ claimed vendor → FORGED; tier 1 → AMBER; tier 0 → GREEN. `now` is the latest chain block timestamp, never the wall clock (B2). **Do not add a future-dated check.** The held-out bill must stay a MISS (PS honesty).
Also: the Python `tierOf` matches the chain on 50 vendor cases via `eth_call` (m5). Run on your laptop with one anvil (31337), or Ayaan runs it on the demo host.

**Prompt (paste into Claude Code):**
```
Read C:\dev\credium\plans\credium\MAIN_BUILD_PLAN.md sections 8d (verdict order), 9 (vendors), 10 and PLAN_REVIEW.md B2, m5.
Write C:\dev\credium\verifier\verify.py: verdict(record:dict, registry:dict, registrar:str, now:int)->dict returning {"verdict":"GREEN|AMBER|FORGED|UNKNOWN","tier":0|1|2,"recoveredSigner":str,"reason":str}. Order: unregistered -> UNKNOWN; recovered != claimed vendor -> FORGED; tier 1 -> AMBER; tier 0 -> GREEN. Use registry shape {address: {"name","enrolledBy","enrolledAt"}}. Use credium_sig.recover_bill_signer. Do NOT add any future-dated check.
Write verifier/tests/test_verify.py covering the 4 verdicts plus one test that a future-dated bill is GREEN (documents the held-out MISS).
Write verifier/tests/test_tier_vs_chain.py that reads the tierOf rule in Python and compares against eth_call on http://127.0.0.1:8545 for 50 vendor cases. Skip if the RPC is down.
Run: pytest verifier -q. Do not touch sim/, watcher/, web/.
```
**Done when:** `pytest verifier -q` is green (chain test may skip if no anvil).

### Block 15 · 23:15–00:00 · Act on mid-eval feedback
**Prompt (paste into Claude Code):**
```
Read C:\dev\credium\outputs\03-mid-eval-feedback.md (if it exists).
List every mentor point that touches contracts, verifier or api. For each, propose the smallest change, the file it touches, and the time it costs. Do not implement anything until I say go.
```

### Block 16 · 00:00–03:00 · Sprint 3
**Brief:** Only the work that raises the evaluation numbers or the red-team demo. In this order: (1) the 50 random cross-chain signature checks (§10) if not already done at 18:00; (2) any gap in the 8 negatives; (3) `/api/release` error text for the demo. Wow-upgrades (§14) only if you are ahead at 02:00. Stop at 03:00.
**Prompt (paste into Claude Code):**
```
Read C:\dev\credium\plans\credium\MAIN_BUILD_PLAN.md sections 10 and 13 and 14.
In C:\dev\credium, check these in order and report the status of each: (1) is there a test that recovers 50 random Python-signed chain-B allocations on chain A? If not, write it in verifier/tests/test_crosschain_50.py; (2) list which of the 8 Release negatives are green; (3) list every API route in api/main.py that is not yet covered by a test.
Make no changes until you have reported. Then wait for me.
```

### Block 17 · 03:00–04:30 · Sleep
You sleep 03:00–04:30. Ayaan is awake for the pod. See the sleep slot below.

### Block 18 · 04:30–06:00 · Awake: freeze preparation
**Prompt (paste into Claude Code):**
```
In C:\dev\credium run: forge test (from contracts), pytest verifier -q, pytest api -q. Print every failure verbatim. Do not change code.
```
**Done when:** the three commands are green, or failures are listed for the freeze.

### Block 19 · 06:00 · Feature freeze
No new features. Bugs and polish only. Tag the commit `freeze-06` so you can always return to it. (`git tag freeze-06`, then `git push --tags`.)

### Block 20 · 06:00–10:30 · Polish, slides, rehearsal, Q&A
**Prompt for slide text (paste into Claude Code):**
```
Read C:\dev\credium\plans\credium\MAIN_BUILD_PLAN.md sections 1, 3, 4 and 16.
Write slide text for the contracts and API slide (max 8 lines). It must state: payment plus signed invoice, not the well; chain-free signature domain and why; the freeze is permanent in v1; SIMULATED label. Plain English. Do not write code.
```

**Q&A drill: 5 questions you must answer in 30 seconds each:**
| # | Judge question | Your answer |
|---|---|---|
| 1 | Why no chainId in the signature domain? Isn't that a replay risk? | Release checks `chainId == block.chainid` and `donorVault == this`, so a replay is bounded by the struct fields. The chain-free domain lets chain-B evidence verify on chain A. |
| 2 | Who can freeze a vault, and can it be undone? | Anyone with gas can run `submitEquivocation`. No unfreeze in v1. v2 would refund donors pro rata after a dispute window. |
| 3 | What does the chain actually prove? | Payment from the vault and a vendor-signed invoice. Not that the well was built. Delivery is future work. |
| 4 | Why does a GREEN vendor need the registrar? | M1: an NGO cannot make its own vendor GREEN. `enrolledBy` must be the registrar and the vendor must be 7 days old. The registrar is the v1 trust anchor. |
| 5 | What does your verifier miss? | The future-dated bill class (MISS 1/1, by design), and vendor collusion. |

### Block 21 · 10:45 · Final push
```powershell
cd C:\dev\credium
git status
git add contracts/src contracts/test contracts/deploy.py contracts/foundry.toml verifier api
git commit -m "final: credium pod A"
git pull --no-edit origin main
git push
```
Check `git status` first and list every file you are about to add. If anything under `lib\`, `cache\` or `out\` appears, leave it out. Do not push at 10:59.

## Contracts you must follow (copied from main plan rev 3, §8)
### 8a Solidity (exact)
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

### 8c deployments.json (written by your `deploy.py`)
```
{"simulated": true, "ngo": "0x…", "registrar": "0x…", "chains": {"31337": {"rpc": "http://127.0.0.1:8545", "token": "0x…", "registry": "0x…", "vault": "0x…", "evalVault": "0x…"}, "31338": {"rpc": "http://127.0.0.1:8546", "token": "0x…", "registry": "0x…", "vault": "0x…"}}}
```

### 8d Your Python signatures
```
verifier/credium_sig.py  (Rishi) recover_bill_signer(bill:dict, sig:str)->str · recover_allocation_signer(alloc:dict, sig:str)->str · bill_nullifier(bill:dict)->str
verifier/verify.py      (Rishi) verdict(record:dict, registry:dict, registrar:str, now:int)->dict   # now = latest chain block timestamp
                                -> {"verdict":"GREEN|AMBER|FORGED|UNKNOWN","tier":0|1|2,"recoveredSigner":str,"reason":str}
```
Ayaan's side (you call it, you do not write it): `sim/signing.py` (`sign_allocation` used by `/api/release`), `sim/meter.py` (`compute_meter`), `watcher/watcher.py` (`scan_once`).

### 8f API (your routes; bind 127.0.0.1 unless `--host` on the demo host)
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

**`/api/release` algorithm (§8f):** (1) build Bill and Allocation from the fixture; sign the allocation with the NGO key via `sim.signing`, `donorVault` from deployments. (2) `eth_call` release from any address. On revert, decode the 4-byte selector and args with the `out/` ABI and `eth_abi`. (3) On success, send the tx, wait for the receipt, return `txHash`.

### Decisions still open (not in rev 3)
- `cap` semantics (block 6): ⚠️ ASK orchestrator. Working assumption flagged in code.
- Shared repo URL (block 1): ⚠️ ASK orchestrator.
- Chain-B sample filename (block 3): ⚠️ ASK Ayaan.
- 22:00 E2E: rev 3 has E2E in your column, but §15 says you drive nothing live. This plan reads it as Ayaan types and you check the output. ⚠️ ASK orchestrator to confirm.

## Handoffs to and from Ayaan (cards A1–A10)
| Card | Direction | What it is | Your contract with it | Time |
|---|---|---|---|---|
| A1 `sim/signing.py` | Ayaan → you | §8d functions, frozen | You never import it in the verifier (independence). The API imports it read-only. | 13:50 frozen |
| A2 `sim/gen_bills.py` | Ayaan → you | 100 bills, pins 5/17/18 | Bills JSON shape per §8c. `/api/bills` reads it. | 14:30 |
| A3 `ops/run_demo.sh` | Ayaan | start anvils, deploy, seed, API | You review deploy and API start order at 16:00 | 16:00 |
| A4 `watcher/watcher.py` pure part | Ayaan → you | `find_equivocations` | `/api/watcher/scan` calls `scan_once` | 18:00 |
| A5 `sim/seed_demo.py` | Ayaan | enrols GREEN by #0, time travel, deposits | Seed does enrolment, `deploy.py` does not | 16:00 |
| A6a `sim/attacks/forge30.py` | Ayaan | 30 bills + WRONG_CATEGORY row | `/api/attack/forge30` wraps the CLI | 18:00 |
| A6b `sim/attacks/double_claim.py` | Ayaan | #417 / #418 allocations | `/api/attack/double-claim` wraps the CLI | 18:00 |
| A7 `watcher.scan_once` + CLI | Ayaan → you | freezes #417 | `/api/watcher/scan` calls it in-process | 18:00 |
| A8 `web/index.html` | Ayaan | reads only §8f routes | You deliver the JSON shapes by 18:00. Any change: tell Ayaan in writing. | 18:00 |
| A9 `sim/meter.py` | Ayaan → you | `compute_meter` | `/api/state` meter field comes from it | 18:00 |
| A10 `sim/eval_run.py` | Ayaan → you | writes `eval.json` | Uses your `verdict()` from 20:00 | 20:00 |

**Your handoffs to Ayaan:** 13:50 "check green" message. 15:30 artifacts commit. 16:00 `deploy.py`. 18:00 API routes. 20:00 `verify.py`.

## §15a fallback trigger (single-chain demo)
- **Trigger (only this):** a hash or signature mismatch at **14:30** that is still unfixed. Python passed at 13:50 but `GateTest` positive fails, or `DOMAIN_SEPARATOR` differs from the vector.
- **Not a trigger:** forge will not run, solc is missing, a path is wrong, or Python fails at 13:50 (fix those first). These are setup slips. The gate moves; no fallback.
- **If triggered:** tell the orchestrator at once. Keep the contracts. Drop chain B from the demo. On chain A show: the forge-30 table, `WrongCategory`, `TierNotGreen`, the same-chain 60+60 → `OverAllocated`, and the meter. The cross-chain freeze becomes future work and is said so on stage. Your must-have changes: `/api/state` lists one chain; `/api/release` on 31337 only. Ready by 18:00 on the demo host.

## Your part of the red-team demo and the evaluation chain
| Demo step | Your code | Chain link | What the judge sees |
|---|---|---|---|
| 2 Inbound donation | `PurposeVault.deposit` (balance in `/api/state`) | Inbound donation | Two vault panels, meter |
| 3 Release #405 | `release()` happy path, `/api/release` | Escrow + invoice proof | Green release, vendor sig VALID, items hidden |
| 4 Forge 30% | Verifier verdicts + `release()` reverts (`BadVendorSig`, `UnknownVendor`, `TierNotGreen(1)`) | Invoice proof, escrow | Per-row table, P/R |
| 4 WRONG_CATEGORY | `WrongCategory` revert | Escrow | Revert line |
| 5 Double-claim #417 | Each chain's `release()` passes alone | Escrow per chain | Both panels "per-chain check: PASS" |
| 6 Watcher scan | `submitEquivocation` on both vaults | Impact verification | Red, "FROZEN" |
| 7 Release after freeze | `VaultFrozen("equivocation")` decoded | Impact verification | Revert line |
| 8 Meter invariant | Verifier-verified amounts feed `compute_meter` (Ayaan) | Impact verification | Invariant FALSE on a rogue release |
| Held-out MISS | Nothing added. The future-dated bill passes (by design) | Honest limit | MISS 1/1 |

**Evaluation numbers you own:** chain vs verifier agreement (100/100 target, via `verdict()` and chain outcome); cross-chain sig verify (1 sample by 14:30, 50 random by 18:00 or sprint 3).

## Sleep slot
- **03:00–04:30: you sleep.** Ayaan is awake for the pod and the demo host.
- **04:30–06:00: Ayaan sleeps.** You are awake for the 06:00 freeze.
- Before you sleep, the 03:00 check: Ayaan confirms he is awake and his last commit is pushed. Put your phone on loud.

## If you're blocked
- **More than 20 minutes stuck:** write the blocker in one line in chat with the exact error. You are the pod lead, so the orchestrator is your escalation point. Tell Ayaan too, if it touches his files.
- **Quick fixes:**
  | Symptom | Do this |
  |---|---|
  | forge install or solc download fails | Switch to the hotspot. Ask Ayaan to run `forge test` on Linux (§15). |
  | "stack too deep" | Move checks into internal helper functions. |
  | Windows encoding error in Python | `$env:PYTHONUTF8 = "1"` in the same shell, then re-run. |
  | RAM below 1.5 GB | Stop anvil, close Chrome, then reboot if still low (§12). |
  | Ayaan's laptop unreachable | Demo runs on his machine anyway. You work on tests locally. |

## How I know I'm done
| Gate | Check (exact) | Pass means |
|---|---|---|
| 13:50 | `pytest verifier\tests\test_vector.py -q` | passed, and "13:50 check green" sent |
| 14:30 | `forge test --match-contract GateTest -vv` | 0 failed |
| 15:30 | `git log --oneline -1` shows the artifacts commit; Ayaan confirms pull | three JSONs on remote |
| 16:00 | `forge test` (whole project) green; deploy output shows 31337 and 31338 | contracts green |
| 17:30 | `pytest api\tests -q` green or skipped, not failed | Windows check passes |
| 18:00 | Ayaan's gate check: #417 FROZEN on both chains; release returns VaultFrozen decoded | integration gate |
| 20:00 | `pytest verifier -q` and `pytest api -q` green | verify and API done |
| 22:00 | E2E green 3 times in a row (restart → run_demo → reset → step 1) | mid-eval ready |
| 06:00 | `git tag freeze-06` made; `forge test` and pytest green on that commit | freeze |
| 10:45 | `git status` clean; final push done | done |

## Mid-eval: what I show and say (23:00)
- **Show:** the release revert list on the forge-30 table, then the #417 freeze appearing on both panels after one watcher scan.
- **Say:** "The signature domain has no chainId on purpose, so a chain-B NGO signature verifies on chain A, and each vault releases only what its own bill and its own NGO's signature allow. We prove payment and a signed invoice, not that the well works."
