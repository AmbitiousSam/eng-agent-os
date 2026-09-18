# Now (as of 2026-09-05)

**State:** v4 BUILT (2026-09-18), pending commit: model-led front door (~1.2k tokens, loaded
once), three boundary agents (builder/reader/checker, tool-scoped, no personas), 11 on-demand
checklists (parity-extracted from the 17 personas + playbooks), runtime verbs snapshot / check /
unit / board / writer / ctx / status --packet, Stop hook records context size (advisory),
setup.sh cleans up v1-v3 installs (280 agency-agents, 17 personas, skills, playbooks), validator
rewritten for the v4 layout. v3 preserved at tag `e0-baseline` for E0. Spec DRAFT rev 2 with an
implementation note; freeze needs E0/E1 outcomes + tests per contract.

**Position (2026-09-18, after first runs):** 7 real runs on v4.0.0 done — see
evals/results/2026-09-18-v4-first-runs.md (scorecard + 5 findings). Fixes from them in progress:
front door (human gate for history rewrites, checker unconditional above toy, fixed criterion
ids, task/verify/close unconditional), audit check (b) removed. OPEN: hooks bound 1/6 sessions.
Earlier position: v4.0.0 released; v3 backed up on branch `v3` + release v3.0.0;
scenarios (K-3) built. NEXT: real runs under v4, then review rounds on the runs. Runtime surface
is FROZEN: no new verb without a run showing the need.
Earlier: v4 review round 1 (871d3d0) answered: 6 findings reproduced + fixed (unavailable != ready,
latest check decides, completion consumes units + void evidence, non-git tree hash, workspace
writer lease, manifest-based installer cleanup with quarantine + --dry-run), E0 isolated env
script. Round 2 (0af3a85): waiver reporting structured, lock order project->task before any
mutation, E0 env rewrites literal paths + hashes, dry-run creates nothing. Next: reviewer
re-probe -> real runs under v4 -> review rounds.
E0 (pre-registered, evals/results/2026-09-17-E0-preregistration.md) runs against the tag.
Hidden checks for E0 live OUTSIDE the repo: ~/.eaos-holdouts/E0/hidden-checks.md (sha256 in the
pre-registration). Grading harness not yet written.

**Other machine / after pull:** `./setup.sh` (cleans up + installs v4) and
`./scripts/install-eaos-hooks.sh`; restart Claude Code.

## Evidence so far
- Run 1 (investigation): EAOS 6/6 precision + strategy at 1.2x; baseline wider coverage.
- Run 2 (build, Throne): EAOS 7/7 hidden checks vs baseline 3/7 (money-losing holes) —
  at 14.4x input tokens. Cost bar FAILED honestly -> M-010 stakes-proportional lifecycle.
- T-029 (real, synergina): 56 mechanized mutations, 2 review-caught bugs, audit caught drift.

## Next (binding order, spec §14)
1. **Run 3** — pre-registered rev 3 (evals/results/2026-09-05-run3-hidden-checks.md;
   rev 1 superseded: "put it live today" contradicted stakes=toy; rev 2 superseded: "~3x"
   was softer than the protocol's fixed < 2x bar). USER runs both arms after round-6 review
   (install hooks first). Measures M-010 against < 2x. MUST happen before shape work.
2. §14 step 2 SHAPE — packs + compiled prompts + generated config + parity tests.
3. Cognitive runtime (§5–7), memory lifecycle (§10), each behind verbs (budget ≤6 new).

## Operating norms established
- External reviewer loop: every push gets reproduced (bugs AND fixes). Answer reviews with
  reproductions, never assurances. Three rounds converged §11.
- Freeze rule: spec changes need run evidence, not review rounds.
- No launch post until: hooks ✅, M-010 validated by a run, 30s demo clip.

- 2026-09-18 late: runs 8-9 reviewed; hooks 1-of-6 resolved (artifact + resume-bind fix); see evals/results/2026-09-18-v4-first-runs.md
