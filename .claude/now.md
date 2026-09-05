# Now (as of 2026-09-05)

**State:** main @ 90f8384+, clean, all pushed. Runtime §11 literal after 3 external review
rounds (77 CLI tests + 35 hook assertions). Hooks (M-007) shipped, opt-in via
scripts/install-eaos-hooks.sh. v3 spec FROZEN (docs/specs/2026-09-01-eaos-v3-architecture.md).

## Evidence so far
- Run 1 (investigation): EAOS 6/6 precision + strategy at 1.2x; baseline wider coverage.
- Run 2 (build, Throne): EAOS 7/7 hidden checks vs baseline 3/7 (money-losing holes) —
  at 14.4x input tokens. Cost bar FAILED honestly -> M-010 stakes-proportional lifecycle.
- T-029 (real, synergina): 56 mechanized mutations, 2 review-caught bugs, audit caught drift.

## Next (binding order, spec §14)
1. **Run 3** — pre-registered (evals/results/2026-09-05-run3-hidden-checks.md). USER runs
   both arms (install hooks first). Measures M-010: target checks held, cost <= ~3x.
   MUST happen before shape work (attribution).
2. §14 step 2 SHAPE — packs + compiled prompts + generated config + parity tests.
3. Cognitive runtime (§5–7), memory lifecycle (§10), each behind verbs (budget ≤6 new).

## Operating norms established
- External reviewer loop: every push gets reproduced (bugs AND fixes). Answer reviews with
  reproductions, never assurances. Three rounds converged §11.
- Freeze rule: spec changes need run evidence, not review rounds.
- No launch post until: hooks ✅, M-010 validated by a run, 30s demo clip.
