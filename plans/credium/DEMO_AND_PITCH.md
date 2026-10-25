# DEMO & PITCH — Credium  (Pod A)
Slug `credium` · PS 4.2 Black Hole Ledger · Theme 4 Information Asymmetry · **no stack theme** · built from MAIN_BUILD_PLAN rev 3 + PLAN_REVIEW

**Everything shown is SIMULATED.** Two local Anvil chains (31337, 31338), synthetic bills, vendors and pledges. Say it in the first minute and keep the SIMULATED banner on screen.
**Slot budget (~8 min):** 3-min pitch, then ~5 min where judges press the red-team console, then Q&A.
**Roles:** Rishi narrates (contracts, freeze, limits). Ayaan drives the demo host (his Linux laptop, 24 GB) and owns the attack, watcher and meter scripts. Harshavi and Aditya (Pod B) field Q&A and run the Stars table.

## 0. Stage rules
- Open and close with the same line: **"It proves a vendor-signed invoice was paid and one bill was claimed twice. It does not prove the well was built."**
- Only claim what is REAL at the moment you show it (§5). At 23:00 the swap/bridge hop is a mock and there is no Merkle beneficiary ack.
- Button labels below are what we ask Ayaan to set in `web/index.html` (A8). The API route in brackets is the truth if a label differs.

## 1. The 3-minute pitch (script with timestamps)
| Time | Say / show | Chain link |
|---|---|---|
| 0:00–0:20 | **Hook (sourced):** "The CBI told the Supreme Court there are about 31 lakh NGOs in India. Only about 2.9 lakh had filed financial statements." (LatestLaws) | — |
| 0:20–0:40 | **User + pain:** *Anita* (fictional persona), a CSR programme officer. Her company funds a ₹1.5 cr water project (simulated). She gets a PDF and cannot check whether the water arrived. Srijan (Bihar): ~₹800–1,500 cr of govt funds through one NGO, 2007–13, estimates vary; first conviction Nov 2025, ~8 years after the FIR (Deccan Herald, ETV Bharat). | Inbound Donation (setup) |
| 0:40–0:55 | **LIVE.** Two chain panels, WATER vaults, cap ₹2 cr each. Meter: pledged ₹2.30 cr, deposited ₹2.14 cr, "unexplained ₹16 lakh (simulated swap/bridge loss)". | Inbound Donation |
| 0:55–1:10 | **LIVE.** Release bill #0405 (GREEN vendor): **OK**. Bill card: vendor signature VALID, recovered signer = vendor, `itemsCommitment` shown, items hidden. | Escrow + Invoice Proof |
| 1:10–1:25 | **LIVE RED TEAM.** Forge 30%: all 30 forged bills revert. Read the three reasons: BadVendorSig (18), UnknownVendor (7), TierNotGreen(1) (5). | Invoice Proof, Escrow |
| 1:25–2:10 | **LIVE RED TEAM, the demo moment.** Double-claim #0417 (₹1,80,000 pipes) at 100% on both chains. Both panels: "per-chain check: PASS". (10-second moment: two green panels.) Click Scan as the watcher. Both panels turn red: "NGO key signed 200% of bill #0417. FROZEN." Point at the protected balance. Release on chain A is refused: `VaultFrozen("equivocation")`. | Impact Verification (+ Escrow) |
| 2:10–2:35 | **How it works.** One sentence: "Two local chains each hold a donor's vault. The NGO can release only by signing allocations. Anyone can submit two of the NGO's own signatures for one bill to any vault, and that vault freezes." **Mechanism: two-signature equivocation freeze.** The vendor signs the bill, so the NGO cannot re-salt it. The signing domain has no chainId on purpose, so chain-B evidence is checkable on chain A. No owner, no admin key. | — |
| 2:35–3:00 | **Numbers, impact, close.** On designed attacks with synthetic data: 30 of 30 forged bills reverted. Held-out bill: MISS 1 of 1, and we say so. Close: the line from §0. | Meter / eval |

Judge-driven red-team block (~5 min) is in §3.

## 2. Synthetic-data labelling (say it and show it)
- Say in the first minute: "All data is simulated. The chain is a local test chain. No money moves."
- SIMULATED banner on every screen; `"simulated": true` in `/api/state`, `/api/bills`, `/api/eval`.
- **Real and cited:** the CBI and Srijan figures, and the CBI 2022 FCRA case (fake invoices, Business Standard).
- **Synthetic:** 100 bills (70 GENUINE, 18 edited-amount, 7 unknown-signer, 5 sock-puppet); 9 vendors (6 GREEN, 2 AMBER, 1 UNREGISTERED); pledges ₹1.5 cr and ₹80 lakh; mock 8% and 5% loss; Anvil default test accounts.
- **Real code:** the Solidity release checks, signature recovery and reverts run on a real EVM. Only the money, the bills, the hop and the attacker are scripted.

## 3. Live red team, exact clicks (judges drive, ~5 min)
Start with **Reset**. After the pitch the vaults are frozen, so the encore would show `VaultFrozen`, not the equivocation.

| # | Ayaan clicks (label) | Route | What the screen must show |
|---|---|---|---|
| R0 | **Reset** | POST /api/reset | Vaults back to pre-release state; no FROZEN flags |
| R1 | **Forge 30%** | POST /api/attack/forge30 | Table of 31 rows. Summary reads `reverted 30`. Reasons: BadVendorSig (18), UnknownVendor (7), TierNotGreen(1) (5) |
| R2 | Point at the row 31 WRONG_CATEGORY line (vendor-signed PPE bill sent to the WATER vault) | (same response) | Revert `WrongCategory()`. The signature is valid; the category is refused |
| R3 | **Double-claim**: billNo `418`, % `60` (fractionBps 6000) | POST /api/attack/double-claim | Chain A: OK, per-chain PASS. Chain B: OK, per-chain PASS. Each chain alone is 60% |
| R4 | **Scan** (watcher panel, label "watcher, no admin key") | POST /api/watcher/scan | Both panels FROZEN. "NGO signed 120% of bill #0418" |
| R5 | **Release**: chainId `31337`, billNo = a fresh GENUINE GREEN bill (not 405), % `100` | POST /api/release | `ok:false`, revert `VaultFrozen("equivocation")` |
| R6 | **Eval** tab, row "Held-out: future-dated bill" | GET /api/eval | `MISS 1/1`. Say: "It passes the verifier and the chain. We did not design for it." |
| R7 | **Eval** tab, meter row "rogue release" | GET /api/eval | Positive row invariantOk true; rogue-release row false |

- R5 note: the release order checks `frozen` first, so the reason is `VaultFrozen` even for a bill already paid. Still use a fresh bill so nobody can ask about `OverAllocated`.
- 10-second moment, shown at R4: "Both vaults green for the same bill. One click. Both red. The NGO signed its own fraud proof."

## 4. Limits (say all four aloud; they are on slide 7)
1. **Freeze is permanent in v1.** No owner, no unfreeze, no claw-back. The ₹1.8 lakh already paid out for #0417 is not recovered. v2: donor pro-rata refund after a dispute window.
2. **The watcher needs gas, not permission.** Anyone can run `scan_once`. It acts only on two NGO-signed allocations for one bill.
3. **No hop tracing.** We do not follow funds through swaps, bridges or off-ramps. The signed fiat-vendor bill is the only off-ramp evidence. The loss is simulated.
4. **Beneficiaries are never on chain or in the API.** Delivery proof is future work. No PII is stored.
- Also true, say if asked: vendor collusion is not caught; only executed or published allocations can be paired; the future-dated class is missed by design; the registrar is a v1 trust anchor for vendor tiers.
- **Protected balance on the freeze screen:** show the live `balancePaise` per chain. The ₹1.38 cr and ₹76 lakh figures are the pre-release deposits only. After #0405 and the #0417 claim the live numbers are lower. Never say ₹1.38 cr at the freeze screen.

## 5. Mid-eval talk track (23:00, 2 min)
**What works now (REAL unless marked):**
- Inbound donation: vaults, meter. Swap/bridge hop **MOCKED**.
- Escrow release: category, tier, vendor signature, per-chain cap, frozen check. Forge table and WrongCategory row.
- Invoice proof: EIP-712 vendor bill, hidden `itemsCommitment`.
- Impact: cross-chain freeze, **only if the 22:00 E2E + red-team gate is green**. Meter REAL. **No Merkle ack (PARTIAL).**

**Script:**
1. "This is a slice. It is local, simulated and a bit rough." Run steps 1–7 live (plan §16).
2. Say what is mocked: "The hop between donor and vault is a mock. The meter's unexplained line is simulated."
3. Next: real lock-and-mint relayer; Merkle delivery ack with no PII; v2 refund after a dispute window.
4. Ask mentors: "Is 'a vendor-signed invoice was paid' the right claim to stop at? Would a funder accept a vendor signature as evidence?"
5. If the gate is red: say so, play the backup video, show the test output. Do not run the live path.

## 6. Stars hook (30 seconds, at the table)
- **Option A (only if built by 21:00):** `replay.html` on a USB stick. Plays the recorded R1–R5 run from a JSON file. No chain, no LAN. Banner: "REPLAY · SIMULATED". Visitor picks a bill number and two percentages, presses Pay twice, then Scan. Same red and green as the live run. Counter: attempts / caught.
- **Option B (default, no build):** printed card. "Can you get bill #0417 paid twice without a freeze? Pick a split across two chains." Back of card: any total over 100% across chains is frozen by the NGO's own two signatures.
- **Script:** "You play the NGO. Pay this bill 100% here and 100% there. Press Scan. Your own two signatures just froze your own vaults. Now try 60 and 60."
- Do not say the replay is live. The plan's Stars item is cut-first (plan §13 #4).

## 7. Theme angles
- **Primary PS 4.2 (Theme 4 Information Asymmetry):** "The NGO cannot hide a second use of the same bill, because its own two signatures are the proof."
- **Stack theme:** none. Do not claim a second theme.

## 8. Who says what
| Time | Speaker | Owns |
|---|---|---|
| 0:00–0:40 | Rishi | Hook, persona, problem with sources |
| 0:40–2:10 | Ayaan drives; Rishi narrates the chain links | Live steps (clicks in §3 order) |
| 2:10–2:35 | Rishi | Mechanism, architecture in one sentence, chain-free domain |
| 2:35–3:00 | Ayaan | Eval numbers, MISS row, what is simulated |
| Red-team block | Ayaan runs the console; Rishi answers | §3 table |
| Q&A | Rishi: contracts, domain, replay, oracle. Ayaan: bills, attacks, watcher, meter. Harshavi and Aditya (Pod B): India, first users, who pays | §9 |
| Stars table | Harshavi | §6 |
Every member must be able to answer all 12 Q&A items. Aditya holds the timer and the backup video.

## 9. Judge Q&A drill (12 items)
1. **Is your data real?** No, and the screen says so. Bills, vendors, keys and pledges are synthetic on a local test chain with public test accounts. The only real facts are the cited CBI, Srijan and FCRA figures. The Solidity checks and reverts are real EVM code.
2. **What's simulated?** Donor money (₹1.5 cr and ₹80 lakh), the swap/bridge loss (8% and 5%, labelled "unexplained (simulated)"), the 100 bills and 9 vendors, the attacker scripts. Not simulated: the release checks, the signature checks, the freeze transaction.
3. **How does it handle the adversary?** Forged receipts fail the vendor signature check (edited amount → BadVendorSig), an unknown signer fails (UnknownVendor), an NGO-enrolled sock-puppet fails the tier rule (TierNotGreen). Double-count across chains and 60+60 splits: the NGO's own two allocations form a fraud proof, and any watcher can submit them. Wrong category: WrongCategory. The CBI's 2022 FCRA case says NGOs generated fake invoices (Business Standard). Not caught: vendor collusion.
4. **How do you know it's right / calibrated?** The verdicts are checks, not probabilities. The eval (100 synthetic bills) reports flags, false positives over the 70 genuine, and chain-verifier agreement. We designed those attacks, so a high score is by construction. The informative number is the held-out row: a future-dated bill passes both the verifier and the chain. MISS 1/1. We show it.
5. **How would this deploy in India?** Not built; this is the path. (a) A vendor registrar. In the demo, account #0 stands in; a real body would need to exist. (b) Bills: a vendor-signed bill, possibly from a GST invoice. We have not verified a GST API and claim none. (c) An EVM chain, choice open. (d) Users: FCRA-registered NGOs and CSR funders. Scale: ₹55,741.51 cr to 13,520 NGOs, FY2019-20 to FY2021-22 (Parliament disclosure).
6. **Why a chain-free EIP-712 domain?** The standard domain binds chainId, so a signature made for chain B fails on chain A. The double-claim evidence exists on both chains, so the freeze must check chain-B signatures on chain A. We leave chainId and verifyingContract out of the domain and put chainId and donorVault inside the signed struct. Release requires chainId == block.chainid and donorVault == this vault.
7. **Replay safety?** One signed allocation pays at most its fraction, once per chain (cumulative usedBps ≤ 10000). It cannot pay on another chain (chainId check) or from another vault (donorVault check). The nullifier binds vendor, billNo and the full bill digest, so a reused invoice number with different content does not collide. Signatures use OZ `tryRecover`, which rejects malleable high-s signatures. Known gap: reportId is informational, not checked.
8. **The oracle problem: does the chain prove the well was built?** No. It proves a vendor-signed invoice was paid from the vault and that one bill was claimed twice. Delivery is future work. The meter shows the unexplained gap instead of hiding it.
9. **Sock-puppet vendors?** The NGO can enrol vendors, but GREEN needs registrar enrolment and at least 7 days of age. NGO-enrolled or young vendors are AMBER, and release reverts TierNotGreen(1). Not caught: a registrar-approved vendor that colludes with the NGO. We say so. The registrar is a v1 trust anchor, and we name it as a central point.
10. **Who pays?** Donors pay gas for deposits. The NGO pays gas for its own releases. Vendors sign off-chain and pay nothing. Anyone can run the watcher and pay its gas, without permission. Who funds the watcher at scale is open; we have not priced it, so we give no per-bill figure.
11. **Who are the first 100 users?** Our plan, not validated: CSR programme teams that must report utilisation, plus partner NGOs that want a verifiable report. Start with one funder and one NGO pilot, then vendors who sign bills. Small donors give through NGO websites and are the second group. No user conversations yet. Say so.
12. **A legit NGO reuses a bill number. Does it freeze forever?** Reuse with different content does not collide, because the nullifier includes the digest. A true double-claim does freeze, and v1 has no unfreeze. That is permanent. Freeze stops future disbursement only. v2 would refund donors pro-rata after a dispute window.

## 10. Slide outline (max 7)
1. **Problem.** Hook (31 lakh / 2.9 lakh, LatestLaws), Srijan line, SIMULATED banner, the one-line scope.
2. **Persona and chain.** Anita's day in one line; the four chain links we will show.
3. **Architecture.** Six boxes from MAIN_BUILD_PLAN §5, two local chains, the watcher, "no admin key".
4. **Mechanism.** Two-signature equivocation freeze: two signatures, one bill, freeze. Chain-free domain in one line.
5. **Demo proof.** Screenshot of the freeze screen with live protected balance, plus the forge table with the WRONG_CATEGORY row.
6. **Eval.** Designed attacks, synthetic. 30/30, the held-out MISS row, notCovered list, meter negative row.
7. **Limits and path.** The four limits from §4, India path (§9 Q5), first 100 users, v2 refund.

## 11. Pre-demo checklist
- [ ] Ayaan checks `nvidia-smi`, then unloads Qwen before the run
- [ ] `run_demo.sh` restart → steps → Reset → step 1 works (test on Ayaan's laptop twice)
- [ ] API bound to 127.0.0.1 on stage (PLAN_REVIEW M10). LAN bind only for Rishi's backup view
- [ ] SIMULATED banner visible; `simulated: true` in /api/state, /api/bills, /api/eval
- [ ] Pinned bills #0405, #0417, #0418 verified GENUINE + GREEN in `sim/fixtures/bills.json`
- [ ] Fresh GENUINE GREEN bill for R5 chosen and checked (not 405)
- [ ] Freeze screen reads live `balancePaise`, not ₹1.38 cr
- [ ] Forge table shows 31 rows including the WRONG_CATEGORY row
- [ ] `sim/fixtures/eval.json` generated with `"simulated": true`, MISS row and notCovered present
- [ ] Demo inputs saved (§12) and each run tested once from the file
- [ ] Backup video in `docs/credium/`; screenshots taken; copy on USB
- [ ] Laptop plugged in, notifications off, one browser tab, zoom and projector resolution tested
- [ ] Each member has spoken the lines aloud once; each can answer Q1–Q12
- [ ] 3-minute rehearsal twice with a timer (Aditya)
- [ ] 21:00 "no new work" check (PLAN_REVIEW m12). Stars and Merkle cut first

## 12. Demo inputs (`docs/credium/demo-inputs/`, to create and test at 22:00)
| File | Contents |
|---|---|
| `pinned-bills.txt` | #0405 (billId 5), #0417 (billId 17, Ramesh Hardware), #0418 (billId 18). All GENUINE + GREEN |
| `fresh-bill-R5.txt` | One other GENUINE GREEN billNo for step R5 |
| `pitch-steps.json` | release 405 @10000 on chain 31337; double-claim 417 @10000; scan |
| `encore.json` | After reset: double-claim 418 @6000; scan |
| `held-out.json` | billNo 499, issuedAt beyond chain time. **Eval only, never a live click** |
| `expected.txt` | The exact screen strings from §1 and §3, for the rehearsal check |

## 13. Backup plan
| Failure | Fallback |
|---|---|
| Anvil or API dies | `ops/run_demo.sh` restart (starts both chains, deploys, seeds, snapshots, starts API), then Reset, then step 1 |
| Web page broken | Terminal on the projector: `python -m sim.attacks.forge30 --deployments contracts/deployments.json --bills sim/fixtures/bills.json`; `python -m sim.attacks.double_claim --billNo 417 --fractionBps 10000 --deployments contracts/deployments.json`; `python -m watcher.watcher --once --deployments contracts/deployments.json` |
| Page works, data stale | UI shows cached `eval.json` and last state (plan §6). Say "cached" |
| Everything fails | Play `docs/credium/backup-demo.mp4` (recorded at 22:45 from the 22:00 E2E run; first frame says SIMULATED). Screenshots in `docs/credium/screenshots/` (forge table, freeze screen, eval table) |
| Venue Wi-Fi down | No network needed. Everything runs on 127.0.0.1 on the demo host |

## 14. Open issues for the build team (fix before 22:00)
1. **Encore needs Reset first.** After #0417 the vaults are frozen, so 60+60 shows VaultFrozen instead of the equivocation. The script in §3 resets first.
2. ✅ **DECIDED (orchestrator, 13:10): option (a).** AMBER is blocked, and the invariant is `released == verified` (main plan lines updated). Original note: **AMBER policy and the meter disagree.** Plan §4 says release pays GREEN only (AMBER reverts). The invariant `released == verified + amber` then fails whenever amber > 0, because nothing AMBER is ever released. Pick one: (a) AMBER blocked, so the amber term is 0 and the invariant is `released == verified`; or (b) AMBER paid and flagged, and the forge table must not say TierNotGreen. Recommend (a) (PLAN_REVIEW M2).
3. **Summary count.** Plan summary says `reverted: 30`, but the screen shows 31 rows. Read the row, not the summary, until the API returns the WRONG_CATEGORY row in the summary.
4. **Button labels** are not specified in plan A8. This doc sets them. Ayaan confirms at 18:00.
5. **Stars has no host or build owner** in the plan. Option B is the default.
6. **Freeze-screen figures:** plan m9's ₹1.38 cr / ₹76 lakh are pre-release values. Live values differ after #0405.
