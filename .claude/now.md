# Now (as of 2026-09-05)

**State:** main clean, all pushed. Runtime §11 literal after 5 external review rounds
(99 CLI tests + 72 hook assertions). Hooks (M-007) opt-in via scripts/install-eaos-hooks.sh.
Round 4: session-scoped hooks, exit 4 for lock contention, coherent audit snapshot,
installer hardening. Round 5: unmapped sessions never adopt a task; PostToolUse binder only
via `session bind --fresh` (command-position regex, exit_code 0, last stdout line, recent +
unclaimed task); journal_start_revision + project-level heads.jsonl anchor (head truncation
and coordinated in-dir rollback detected; heads.jsonl rewrite out of scope, documented);
session in task-new idempotency; lock steals audited until `lock-steal-ack`. v3 spec FROZEN
(docs/specs/2026-09-01-eaos-v3-architecture.md).

**Position:** Round 5 fixes landed; the 09-09 real run's seven blunder-fixes landed (2026-09-11)
-> awaiting round 6 reproduction/review -> then Run 3.

**09-11 changes (from the 09-09 run review):** verify refuses `verified` on deferral-shaped
evidence; high RISK opens `R-<msg>` that --require/report demand a verdict for; cap 15 = 12
planning + 2 loop-back + 1 verifier, `eaos spawn` refuses to plan into reserves; audit (p)
flags checker roles folded into the orchestrator; setup.sh strips persona `model:` under
inherit (doctor checks); intake: deliverable-class words are blocking questions, attribution
constraints are ACs, deploy-shaped work carries an executed-rehearsal AC and a rehearsal gate
before launch review; protocol body cap 400 chars (orchestrator wrote 87% of output tokens).

**Real run 2026-09-09 (private repo, 3 tasks, production stakes, ~5h, ~262k output tokens):**
hooks fired but every fire failed open — the binder demanded a literal `eaos` and the
orchestrator writes `$E task new` (fixed: variable in command position now binds; --fresh
guard is the real protection). 3/3 tasks reached DONE without `episode close` (new audit check
done_without_episode_close). At 12/12 the orchestrator applied AND re-graded its own fix
(new `reserved_verifier_spawns: 1`). Model-switch observed: 68/165 main turns on opus-5 under
`inherit` — cause unknown (fast mode? /model?), ask user.

**Other machine / after pull:** `./setup.sh && ./scripts/install-eaos-hooks.sh` (re-run the
installer: it adds the PostToolUse entry idempotently).

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
