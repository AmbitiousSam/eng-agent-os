# Session log (append-only)

## 2026-07-13 — Harsh review → fixes → runtime CLI → single front door
- **Harsh critique** (8 review angles + 3 deep readers): core naive assumption identified —
  "same process, same artifacts" ≠ same quality; EAOS value comes from 4 Claude-Code
  mechanics (context isolation, multi-sampling, model tiers, tool scoping) that sequential
  role-play loses while keeping full ceremony cost. Everything enforced was honor-system;
  examples/runs/ empty; validator measured spelling, not function.
- **Fix run** (4 Sonnet workers + verification): doctor false-failure, /triage never
  installed, memory index never seeded, `.eaos/` path schism in 15 personas, un-rostered
  gate owners, 4 acceptance-criteria gates → 2, honest adapter matrix + solo-mode.md,
  golden routing fixture + eval_check + A/B protocol, plain-language final-report template.
  Found during verify: BSD cp trailing-slash bug had merged all 11 skills into ONE SKILL.md
  (live installs never had EAOS skills). Commit 2d1346b.
- **Second harsh review of the fixes** (8 angles): 10 confirmed defects in the fixes
  themselves (validator crashed w/o pyyaml — 58 false errors; skill .bak dirs = phantom
  skills; solo-mode never installed; criteria gap on trivial/small; dangling token-budget
  refs; doctor vacuous pass; stale /incident phases; README still taught role-play; fixture
  punished correct trivial routing; make test missed eval_check). All fixed. Commit 2d1346b
  superseded by the cumulative push.
- **eaos runtime CLI** (ROADMAP #1): scripts/eaos, 10 subcommands, binding exit codes,
  17 unit tests; caught+fixed worker's spawn increment-before-check bug (permanent budget
  lockout). Wired into command/setup/doctor/docs. Commit d06b2f4. Live transcript verified
  every ceiling trips mechanically.
- **Publishing:** pushed all; GitHub wiki created (9 pages, user initialized first page);
  README 219→70 lines (0adc114).
- **Single front door:** /agentic-os only; legacy commands removed on upgrade; triage-shaped
  route added; all docs + wiki swept. Commit 0bbc97f (BREAKING).
- **Open:** zero captured real runs (rung 2), routing dry-run + A/B eval (rung 3).

## 2026-09-01 → 09-05 — Evidence runs, v3 spec, runtime completion, review loop, hooks
- Paired evals: run 1 (audit) complementary at 1.2x; run 2 (Throne build) EAOS 7/7 vs 3/7 at
  14.4x — first public captured run (examples/runs/2026-09-01-T-001).
- v3 architecture spec written through a 3-round adversarial design exchange; frozen rev 2
  (grounding contract, consistency layer, honest enforcement chain, mechanism lifecycle).
- Runtime §11 built (locks, idempotency w/ content-bound keys, parent-tree budgets,
  fingerprints, audit w/ revision journal + tree reconciliation, honest conditional exits).
  Three external review rounds; every finding reproduced fixed before commit.
- M-009 coverage manifest, M-010 stakes lifecycle, models.mode inherit, M-007 hooks shipped.
- T-029 real run on new runtime: audit caught real drift; --stakes gap found + fixed (with
  one honest recommit after a silently-failed patch).
- Decision: run 3 BEFORE shape work, to attribute cost reduction cleanly.

## 2026-09-05 (later) — Review round 4: hooks concurrency/attribution, installer hardening
- Reviewer (read-only, all suites green) found 4 HIGH + 5 medium + a run-3 pre-registration
  contradiction. All reproduced before fixing: audit false-drift under legit concurrent spawns
  (100/100 in our harness), lock-busy exit 1 -> hook blocked, installer 0600->0644, global
  CURRENT misattributed a second session's spawn; empty journal accepted; 1s backup names
  collided; malformed hooks silently replaced; unquoted hook path (126/127).
- Fixes: exit 4 = infrastructure (lock); audit snapshot under project->task lock; session map
  .eaos/sessions/<sid> + `eaos session bind|unbind|resolve` + PostToolUse(Bash) binder hook,
  fail-open on ambiguity, retarget-to-parent on child close; journal_enabled genesis marker;
  installer preserves mode, 0600 O_EXCL ns+pid backups, SchemaError refusal, shlex.quote.
  Discovered on the way: macOS case-insensitive FS — `.eaos/current/` collided with CURRENT.
- Tests: 77->89 CLI, 35->67 hook assertions (injection, lock, two-session, posttool, perms).
- Run 3 pre-registration superseded (rev 2): prompt made honestly non-deploy-bound so
  stakes=toy is the correct classification M-010 measures.
