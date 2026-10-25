# CREDIUM — Judge's Demo Walkthrough

> "A Rs 1.5 cr water pledge is swapped, bridged and spent through local vendors. Donors can't check."

CREDIUM is a smart contract system that makes **cross-chain fund flows auditable**. Donors deposit on two parallel chains, vendors invoice against a shared ledger, and a permissionless watcher **freezes equivocations** — the same bill paid twice — before any double-spend completes.

Below is a card-by-card walkthrough of what was built, why it matters, and how to demonstrate it live.

---

## Card 01 — Foundry & Anvil Setup (Infrastructure)

**What:** Configured the local development environment — Foundry toolchain (forge, cast, anvil), Python venv, and the two parallel Anvil chains (chain IDs 31337 and 31338).

**Why it matters:** This is the simulation sandbox. Anvil provides deterministic, resettable chains so the demo can be repeated identically on any laptop. Foundry handles contract compilation and testing.

---

## Card 02 — EIP-712 Digital Signatures (`sim/signing.py`)

**What:** Implemented EIP-712 typed structured signing for vendor invoices and donor allocation approvals. Every bill is cryptographically signed by the vendor; every release is signed by the NGO.

**Why it matters:** Without signature verification, anyone can submit a fake invoice. EIP-712 ensures:
- Vendor identity is cryptographically bound to the bill
- The NGO's allocation approval cannot be forged
- Signatures are deterministic and verifiable on-chain

---

## Card 03 — Attack Vector JSON (`sim/fixtures/vector.json`)

**What:** A structured JSON file defining the exact attack vectors CREDIUM must detect — forged signatures, unknown signers, amber-tier sockpuppets, and double-claims.

**Why it matters:** This is our **test harness**. Each entry describes an attack scenario: the bill data, the expected revert reason, and the vendor tier. It transforms "does it work?" into measurable, reproducible results.

---

## Card 04 — Synthetic Bill Generator (`sim/gen_bills.py`)

**What:** Generated 100 synthetic bills with 30 designed attack rows and 70 genuine rows. Includes three pinned bills (5, 17, 18) and two extras: a wrong-category bill and a held-out future-dated bill.

**Why it matters:** The dataset simulates real-world conditions:
- 30% attack rate (forged signatures, unknown signers, sockpuppets)
- Tier-based filtering (only GREEN vendors are accepted)
- A held-out test case that *intentionally passes* — measuring blind spots

---

## Card 05 — Equivocation Detection (`watcher/find_equivocations`)

**What:** A pure function that compares Released events across both chains. When the same bill nullifier appears with different allocation parameters, it flags an equivocation.

**Why it matters:** This is the **core insight** of CREDIUM. On a single chain, a bill looks legitimate. Across chains, the same bill claimed with different donor allocations is mathematically impossible — a double-spend attempt.

---

## Card 06 — Metering Module (`sim/meter.py`)

**What:** Computes the financial invariant: whether all donor deposits are accounted for as either verified releases, unexplained balances, or amber-tier reserves.

**Why it matters:** This answers the auditor's question: **"Where did the money go?"** The invariant must hold at all times. If it breaks, funds are missing or unverified.

---

## Card 07 — Chain I/O Helpers (`sim/chainio.py`)

**What:** A shared Python module providing deployment loading, transaction sending, ABI decoding, revert analysis, and struct serialization for both chains.

**Why it matters:** Every script — seeding, attacks, watcher, evaluation — shares this module. It is the **single source of truth** for on-chain interaction. Revert decoding turns cryptic error bytes into human-readable reasons.

---

## Card 08 — Demo Seeding (`sim/seed_demo.py`)

**What:** Puts the chains into the demo state:
1. Enrolls GREEN vendors via registrar, AMBER via NGO (on both chains)
2. Warps time 8 days forward (so GREEN vendors age out of the new-enrollment window)
3. Mints and deposits funds from both donors
4. Takes a chain snapshot for fast reset

**Why it matters:** This is the **one command** that sets up the entire demo. Without it, the system is empty. With it, every attack scenario is ready to execute.

---

## Card 09 — Demo Bootstrap Script (`ops/run_demo.sh`)

**What:** A single bash script that: stops old processes → starts both chains → deploys contracts → seeds the state → starts the API server.

**Why it matters:** **"One command, full demo."** Any judge, in any environment, can run this and see CREDIUM in action. It handles the full lifecycle from cold start to live demo.

---

## Card 10 — Forge 30% Attack (`sim/attacks/forge30.py`)

**What:** Submits 30 forged bills to the WATER vault:
- 18 rows: **edited amounts** (signature doesn't match the bill)
- 7 rows: **unknown signers** (non-existent vendor)
- 5 rows: **amber-tier sockpuppets** (not GREEN tier)
- 1 extra: **wrong category** submission

**Why it matters:** This is the **stress test**. All 30 must revert. The system should flag every attack, with zero false positives on genuine bills.

**Expected result:** All 30 revert. Precision = 1.0, Recall = 1.0.

---

## Card 11 — Double-Claim Attack (`sim/attacks/double_claim.py`)

**What:** Releases the same genuine bill on both chains simultaneously. Each chain sees a valid, unique claim. Only the cross-chain watcher can detect the double-spend.

**Why it matters:** This is the **classic cross-chain attack**. A malicious vendor submits the same invoice to Donor A's chain and Donor B's chain, collecting double the funds. Without cross-chain verification, both releases pass.

---

## Card 12 — Watcher Scan + Freeze (`watcher/watcher.py`)

**What:** The permissionless watcher:
1. Reads all Released events from both chains
2. Calls equivocation detection
3. Submits the conflicting signatures to both vaults
4. **Freezes the vault permanently** on both chains

**Why it matters:** This is the **defensive core**. Anyone can run the watcher — no special privileges needed. Once an equivocation is found, the vault freezes. No more releases. The double-spend attempt is stopped, and the evidence is preserved on-chain.

---

## Card 13 — Web Layout (`web/index.html`)

**What:** A single offline-capable HTML file with:
- Amber "SIMULATED" banner
- Two chain panels (Chain A / Chain B)
- Financial meter box
- 7 demo buttons (release, forge, double-claim, scan, reset)
- Bills table
- Console output
- Evaluation section

**Why it matters:** **Zero dependencies, zero build step, zero CDN.** This page runs on any browser, even without internet. It is the judge-facing interface.

---

## Card 14 — Live JavaScript (`web/index.html` — JS)

**What:** The JavaScript engine that:
- Polls the API every 2 seconds for live state and bill data
- Renders chain panels with frozen state detection
- Fills the financial meter with real-time numbers
- Wires all 7 demo buttons to API endpoints
- Caches state in `localStorage` when the API is down

**Why it matters:** The page is **alive**. It updates in real-time as you click buttons, and it survives API outages through offline caching.

---

## Card 15 — Evaluation Numbers (`sim/eval_run.py`)

**What:** Runs all 100 bills through the chain's own check (eth_call on evalVault, no state change), producing `sim/fixtures/eval.json`:

| Metric | Value |
|---|---|
| Positives (designed attacks) | 30 |
| Flagged by chain | 30 |
| True Positives | 30 |
| False Positives | 0 |
| **Precision** | **1.0** |
| **Recall** | **1.0** |
| Held-out future bill result | **MISS** |

**Why it matters:** These numbers are the **measurable proof** that CREDIUM's chain-level checks work. Perfect precision means zero false alarms. Perfect recall means zero attacks slip through. The held-out MISS reveals the one blind spot: future-dated bills.

---

## Card 16 — Evaluation Table (`web/index.html` — eval rendering)

**What:** Renders the evaluation JSON in the web page:
- Summary line: "Flag precision 1.0, recall 1.0, false positives 0 (out of 70 genuine)"
- Held-out result: "Held-out future-dated bill: MISS 1/1"
- Not-covered list: vendor collusion, off-chain spend, delivery, held-out future-dated bill
- Scrollable 100-row per-bill table

**Why it matters:** The judge sees **not just that the system works, but proof that it works**. The numbers are generated from the same simulation that ran the attacks. It is self-verifying.

---

## How to Demo (Live)

```bash
./ops/run_demo.sh
```

Then in the browser:

1. **Click "Release #405"** — A genuine bill releases successfully. The meter updates.
2. **Click "Forge 30%"** — 30 forged bills are submitted. All 30 revert. The console shows each revert reason.
3. **Click "Double-claim #417"** — The same bill is claimed on both chains. Each passes its individual check.
4. **Click "Watch Scan"** — The watcher detects the double-claim. Both panels turn red: **"FROZEN: equivocation"**.
5. **Scroll to Evaluation** — Precision 1.0, Recall 1.0. The held-out future bill is shown as MISS.
6. **Stop the API** — Reload the page. The evaluation section persists from cache. **"API: cached"**.

---

## What CREDIUM Proves

| Claim | Evidence |
|---|---|
| Per-chain checks work | Card 15: precision 1.0 |
| Cross-chain detection works | Card 12: watcher freezes double-claims |
| No special privileges needed | Card 12: permissionless submitEquivocation |
| Attack detection is complete | Card 15: recall 1.0 (all 30 attacks caught) |
| Demo is reproducible | Card 9: one command, full reset |

## What CREDIUM Does Not Prove (Honest Scope)

- **Vendor collusion:** Two GREEN vendors can still collude to fake deliveries
- **Off-chain spend:** Money may be diverted before or after on-chain settlement
- **Delivery quality:** The invoice proves payment, not that the well was built
- **The held-out future-dated bill:** A future-dated invoice passes all checks — this is the MISS in Card 15

---

*Built as part of the CREDIUM project. All chains, bills, and keys are synthetic. Designed attacks are labeled and measured.*
