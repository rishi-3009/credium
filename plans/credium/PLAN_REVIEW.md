# PLAN REVIEW — credium (Pod A) · critic Mode B · 25 Oct

Reviewed `plans/credium/MAIN_BUILD_PLAN.md` (rev 1) against PORTFOLIO.md, 04-team.md, 03-timeline.md, 02-judging-criteria.md, PS 4.2. No web search.

## Summary
1. The core idea holds and the EIP-712 design is defensible with conditions (see verdict). The plan as written has **5 blockers**.
2. B1–B5 stop the 14:00 go/no-go, 18:00 integration or the 23:00 slice. B2 and B5 would fail live on stage.
3. Free only before 13:35: bill-digest nullifier (M3), registrar-based tierOf (M1), pins for #405/#417/#418 (B2), AMBER policy (M2).
4. Worst failure mode: a setup slip (OneDrive, solc download) at 14:00 auto-triggers Effect Lock, which has no plan (M11).
5. Rishi and Ayaan are both over-allocated. M5 and M6 give reallocations.

## EIP-712 verdict
Defensible, with conditions. Release is bounded by struct checks: `chainId == block.chainid`, `donorVault == this`, recovered signer == the vault's NGO, nullifier match. Cross-vault/cross-chain replay of a release is blocked there. The chain-free domain is **required**: chain-B equivocation evidence must verify on chain A, which a standard domain (chainId + verifyingContract) makes impossible. That is the answer for judges.
Holes to close: no negative test (M4); nullifier collides on invoice-number reuse (M3); dev stacks share chainId 31337 (m1); OZ EIP712 must not be inherited (M4).

## BLOCKERS
| # | Problem | Fix |
|---|---|---|
| B1 | 14:00 go/no-go not runnable; fails by default. Needs Hardhat on an untested Windows/OneDrive path, solc 0.8.24 download (internet), Ayaan's `signing.py` + `vector.json` by 13:50, positive check only. A setup slip reads as crypto fail → Effect Lock. | (a) Now: move contracts/ + .venv out of OneDrive (e.g. `C:\dev\credium`), run `npx hardhat compile` once on hotspot to cache solc. (b) 13:50 Python-only check: Rishi's `recover_allocation_signer` on Ayaan's chain-B sample returns NGO and matches an `eth_account` `encode_typed_data` reference (not Ayaan's code). (c) 14:30 Solidity check: `allocationSigner` returns NGO (positive) AND release on chain A reverts `WrongChain` for the chain-B allocation (negative). (d) Setup slip moves gate to 14:30; only a hash mismatch after 14:30 triggers fallback. |
| B2 | #405 not pinned (30% chance not GENUINE → step 3 "release OK" fails at 23:00); no vendors pinned. If verifier uses wall clock, after `evm_increaseTime(691200)` GREEN vendors look <7d old → AMBER. | `gen_bills` pins billId 5 (#405), 17 (#417 Ramesh Hardware), 18 (#418) as GENUINE with GREEN vendors + pytest. API uses latest block timestamp as `now`. Test: after time travel, GREEN vendor verdict is GREEN. |
| B3 | Ayaan's chains/artifacts have no owner. `deploy_py.py` needs Hardhat artifacts he never builds; A5–A7 need a chain and Anvil is cut first; 4 of 8 files unrunnable 16:00–18:00; his Python only ran on Linux. | Rishi commits `contracts/artifacts` (ABI + bytecode JSON only) at 15:30; Ayaan pulls. Anvil stays as Ayaan's test chain (cut only from demo path). 17:30 Windows smoke test: seed, forge30, double_claim on Rishi's laptop. |
| B4 | 23:00 eval table can't be produced. `evalVault` absent from Solidity/deploy spec; `/api/eval` needs eth_call release on 100 bills but no file creates NGO allocation sigs. | `gen_bills` also emits allocation + ngoSig per bill (via signing.py). `deploy.ts` deploys evalVault with same registry. Eval script runs once → `sim/fixtures/eval.json` with `"simulated": true`; `/api/eval` serves the file. |
| B5 | Meter invariant is tautological (unexplained = residual, so sum = 0 by construction). Showing it as a check is misrepresentation. | unexplained = pledged − deposited (deposited from chain: Deposited logs or balance + released). Real invariant: Σ `vault.released()` across both chains == verified + amber from verifier. Test: release a bill the verifier never saw → `invariantOk` false. Show once on screen. |

## MAJOR
| # | Problem | Fix |
|---|---|---|
| M1 | NGO can fake GREEN: open enroll + age ≥7d = GREEN. | `VendorRegistry(registrar)`. GREEN iff enrolledBy == registrar AND age ≥ 7d. AMBER iff not registrar or registrar <7d. Else UNREGISTERED. |
| M2 | AMBER vendors get paid; forge table still says "caught". | Preferred: release reverts `TierNotGreen(tier)` for tier ≠ 0. Or label "FLAGGED, PAID" + "v1 flags AMBER, does not block" on slide + amberPaise on meter. Decide before 13:35. |
| M3 | `billNullifier = keccak(vendor, billNo)` collides on invoice-number reuse (FY resets) → false permanent freeze. | `keccak256(abi.encode(vendor, billNo, billDigest))`. `bill_nullifier` takes the bill dict. Land before vector.json at 13:50. Watcher pairs only within one NGO address. |
| M4 | Domain needs: (a) negative tests (WrongChain, WrongVault, WrongNGO); (b) don't inherit OZ EIP712 — hard-code DOMAIN_SEPARATOR, assert = vector; Python uses `eth_utils` keccak, not `hashlib.sha3_256`; (c) use `ECDSA.tryRecover` so BadNgoSig fires. reportId never checked. | Add tests; bind reportId in release or document as informational before vector freeze. |
| M5 | Rishi over-allocated; RAM unknown. | /api/eval becomes a file (B4); `verifier/meter.py` → Ayaan as A9 with pytest; run_demo.ps1 as 10-line script at 21:00; one must-have card (go/no-go, release + freeze, /api/state + /api/bills + /api/release); confirm RAM (~8 GB needed). |
| M6 | Ayaan's queue too big for copy-paste on 35B (each file 150–400 lines, model unload per run). | Split A6 → A6a forge30, A6b double_claim. Numbered step list for A5. Code on 9B coder (check `nvidia-smi`); 35B for review only. |
| M7 | POST /api/release unspecified (NGO signing path unassigned; custom-error decoding). | 5-line algorithm in §8f: eth_call first, decode revert with artifacts ABI + eth_abi. Test VaultFrozen + BadVendorSig decoding at 18:00. |
| M8 | Deterministic salt + plaintext bills.json → itemsCommitment brute-forceable; "items hidden" is UI only. | `secrets.token_bytes(32)` per bill in NGO-side fixture only; /api/bills never returns items/salt (test). Optional: selective opening to an auditor. |
| M9 | Setup needs internet at worst time. | Setup now on hotspot; cache pip wheels, npm tarballs, solc, Foundry on USB. Check `py -3.11 --version`. |
| M10 | Windows/Linux friction. | `sys.executable` + cwd for subprocess; `json.dumps(ensure_ascii=True)`, `PYTHONUTF8=1`; bind FastAPI to 127.0.0.1; paths relative to `__file__`. |
| M11 | Fallback is not a plan; single-chain freeze needs a 2h feature. | Decide now: (a) 10-line Effect Lock plan with owner, or (b) single-chain demo showing forge table + OverAllocated revert, cross-chain freeze as future work. |
| M12 | Freeze permanent; watcher is a dependency. | Limits slide: "v1 no owner → no unfreeze; v2 donor pro-rata refund after dispute window." "Anyone can run scan_once; needs gas, not permission." |
| M13 | Cut list drops PS-named "spending outside declared categories". | Keep one forge row: WATER bill vs other-category vault → REVERT WrongCategory. Remove cut #6. |
| M14 | Snapshot id dies on node restart. | run_demo = start nodes, deploy, seed, snapshot every time. Test restart → run_demo → reset → step 1. |
| M15 | 18:00 gate has no slack. | 17:30 manual #417 path via CLI on Hardhat; failures go to cut list. |
| M16 | Eval is 100% by construction. | Add one attack class the verifier wasn't written for (buyerNGO = another NGO, or future issuedAt). Report result incl. misses in `notCovered`. |

## MINOR
- m1 Anvil hedge uses chainIds 31339/31340; "dev-only" on slide.
- m2 Label "unexplained (simulated swap/bridge loss)"; limits: no hop tracing/off-ramp monitoring; signed fiat-vendor bill = off-ramp evidence.
- m3 "Beneficiaries never appear on chain or in API; delivery proof is future work."
- m4 Specify cap semantics, release amount rounding (amountPaise × fractionBps / 10000), payee in §8a.
- m5 One Python tierOf, tested vs chain on 50 vendor cases via eth_call.
- m6 seed approves before deposit; MockINR decimals = 0 (units = paise).
- m7 deploy.ts reads chainId from `eth_chainId`.
- m8 CREDITS: chai, httpx, @nomicfoundation/hardhat-ethers, eth-utils.
- m9 Show protected balance (₹1.38 cr A, ₹76 lakh B) on freeze screen; loss bound ~₹1.8 lakh per claim.
- m10 Name mechanism "two-signature equivocation freeze"; first users (CSR teams, small donors); per-bill cost (one signature).
- m11 Delete cut items not in any milestone (#2 bridge relayer, #8 separate watcher process) or schedule them.
- m12 21:00 "no new work" check; cut Merkle and Stars first.

**BLOCKERS: 5** — B1 14:00 gate · B2 pins + verifier clock · B3 Ayaan chain/artifacts · B4 eval table · B5 tautological invariant.
