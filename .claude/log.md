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

## 2026-09-05 (later still) — Review round 5: session adoption, binder trust, history anchors
- Reviewer's 6 open items all reproduced: unmapped session adopted the sole active task and got
  blocked on its budget; `echo "eaos task new"; echo T-001` bound a session; journal head
  removal read "started at revision 2" = clean; coordinated state+journal rollback clean; same
  task-new key from another session replayed silently; stale-lock steal warned, audit clean.
- Fixes: resolve never binds implicitly (no-sid CURRENT fallback only while zero sessions
  tracked); posttool: command-position regex + exit_code 0 + last stdout line + `session bind
  --fresh` (<=300s old, unclaimed); journal_start_revision + .eaos/heads.jsonl project anchor
  + audit (n) project_head_anchor; session in task-new fingerprint, replay re-binds;
  .eaos/lock-events.jsonl + warroom LOCK STOLEN line + audit (m) lock_steals until ack.
- Run 3 pre-registration rev 3: bar is the protocol's < 2x, not "~3x"; outcomes enumerated.
- Honest scope line: a rollback that also rewrites heads.jsonl is not detectable in-checkout.

## 2026-09-09 — First real run on the round-5 runtime (glideparcs-pdc, private)
- 3 tasks (recover lost CDK deploy branch, CI/CD pipeline, local rehearsal); 19+35 ACs verified
  by independent verifier; 2 real loop-backs (env-pinning defect, IAM escalation); T-003 ran at
  internal stakes with ONE agent — proportional ceremony worked unprompted.
- App export failed (session 1 process died mid-T-002 at 15:55Z; session 2 is a resume that
  replays history). Rendered exports from disk: <project>/.eaos/exports/ (gitignored).
- EAOS findings -> fixes: binder regex blind to `$E task new` (every hook fire failed open;
  spawns were recorded cooperatively, 25/25 matched the transcript's Agent launches);
  episode close skipped 3/3 (audit (o)); orchestrator self-fix + self-regrade at 12/12
  (reserved verifier slot). Tests 99->103 CLI, 72->73 hook.
- Cost profile: main 227k out / 50.5M cache-read; subagents 35k out / 48.9M cache-read.

## 2026-09-11 — Seven fixes from the 09-09 run review ("the blunders")
- Headline: first real deploy of the reviewed role stack failed (em-dash in IAM description) after
  35 ACs, review, security, verifier APPROVE, launch GO, rehearsal — static checks never saw it.
- Blunders: deliverable word "workflows" assumed away (12 agents on wrong scope); five never-run
  criteria stored `verified` ("HUMAN-RUN pending", "SUPERSEDED") so --require exited 0; high RISK
  filed as follow-up until the human asked for a rehearsal; checker roles folded into the
  orchestrator to stay at 12/12; GROUND grepped for an expected role name instead of listing;
  Co-Authored-By added against instruction -> filter-branch + force push; `inherit` a lie
  (persona model: frontmatter overrode the session model).
- Fixes: DEFERRAL_EVIDENCE_RE in verify; open_risks -> R-<msg> verdicts; cap 15 with two
  reserves; audit (p) checker_role_folded; setup.sh strips model: under inherit + doctor;
  intake/verifier/playbook/command/routing/loop text for rehearsal, always-ask words,
  attribution ACs, no-fold; protocol body cap 400. Tests 103->111 CLI, 73 hook.
- Token observation (09-09 run, deduped): main 227k out / 50.5M cache-read; 25 subagents 35k
  out / 48.9M cache-read. Orchestrator prose = 87% of output.
