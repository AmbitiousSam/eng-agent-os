# EAOS v3 architecture — binding specification (2026-09-01, rev 2 — FROZEN)

Consolidates: the T-017 run analysis, the 6-project disk scan, the memory review, and a
three-round adversarial design exchange. Supersedes the architecture portion of
`2026-07-13-eaos-product-design.md` (its product strategy stands). Every mechanism cites
evidence or carries EVAL-PENDING.

**Freeze rule:** this is the final review-driven revision. Further changes must cite run
evidence (kernel law 6 applies to the spec itself).

## 1. Problem statement

EAOS improves *process reliability* more than *solution reliability*. Proven value:
defect-catching via genuine maker/checker isolation. Measured weaknesses: bookkeeping
bypass, context waste, monolithic shape, write-only memory — and under-investment in the
original problem: grounding in unfamiliar codebases and business logic.

## 2. Evidence baseline (raw: session export T-017; `.eaos/` dirs across 6 projects)

Strengths: 5 real defects caught in T-017's billing path (incl. pre-existing double-credit
race; verifier refused a skipped test as passing) · convergence rule worked (CHALLENGE ×4
→ amended ADR) · codebase map is the most-reused artifact system-wide (9/10 tasks, sre) ·
conditional business-pack activation earned its spawn · mechanization adoption trending up
(robot: 6/6 state.json vs 0 pre-CLI).

Failures: honor-system decay (verbs bypassed mid-run: messages:0, criteria≈0, loopbacks:0;
index.md dead in 4/6 projects) · epic fragmentation (23 spawns vs cap 12, invisible;
duplicate children T-022≡T-024, T-023≡T-027) · context waste (8.6M in/1.4M out, one worker
1.03M-in/82k-out, ~36% output = coordination) · write-only memory (7/23 files never read
elsewhere; lessons chain 1–2 tasks; zero cross-project transfer) · cold-start abandonment
(3 projects: 1–4 shallow tasks, never returned) · dishonest verdict enum (T17-09 AC2 was
honestly deferred — inexpressible in pass/fail).

## 3. Evidence disposition matrix

| Measured failure | Disposition |
|---|---|
| Bookkeeping bypass | Addressed: wrapper-as-authoritative-path, hooks as accelerators, audit reconciliation (§11) |
| Epic budget fragmentation | Addressed: atomic parent-tree budgets (§11) |
| Duplicate tasks | Addressed: deterministic task fingerprint (§11) |
| Context waste | Addressed: scoped packs (§8) + diagnostic context metrics (§11) |
| Write-only memory | Addressed: runtime retrieval + lifecycle (§10) |
| Verdict dishonesty | Addressed: expanded criterion states (§11) |
| Cold-start abandonment | **Deferred to product plan** — not solvable by the cognitive runtime. Tracked: first-run completion, second-task return rate, doctor success, time-to-first-verified-task. |

## 4. Kernel laws

1. Prompt rules are wishes; exit codes are rules.
2. No artifact without a producer AND a consumer.
3. No store without verbs and a lifecycle (owner, write/read verbs, audit rule,
   supersession/deletion path).
4. Pipelines for predictable work; cognitive loops for uncertainty — selected, never
   universal.
5. Maker and checker require genuine context isolation; simulated teams are banned.
6. Every mechanism carries a lifecycle contract (§12); mechanisms are falsifiable.
7. No unconditional completion claim while required criteria remain unverified;
   honest partial states are first-class (§11 criterion states).

## 5. Execution-mode selection

Default by kind: `feature|chore|refactor|release` → pipeline; `bug|incident|question` →
cognitive. **Cognitive detour** from a pipeline fires only on observable triggers:
- an impact-map unknown remains unresolved
- multiple candidate authoritative paths remain
- identified write sites not all classified
- a dynamic dispatch/event consumer cannot be traced
- current behavior cannot be reproduced
- code, tests and documentation disagree
- an implementation assumption is disproven mid-IMPLEMENT
- a downstream failure contradicts the current change model

Detour entry/exit recorded by the runtime; audit flags unclosed detours. No
self-assessed "confidence" triggers of any kind.

## 6. Cognitive state model (runtime-owned; state.json extension; cognitive mode/detours)

- **Claims**: {text, type: observed|inferred|assumed, status: active|supported|disproven|
  superseded, evidence_for[], evidence_against[], exceptions[], validated_at_commit}.
  Categorical only; no decimals.
- **Unknowns**: named list; resolved by probes.
- **Probes**: {question, action, result ref, claims updated}.
- **Retry law**: a retry must vary the hypothesis, action, or execution condition.
  Exception: failures classified *transient* may repeat under a bounded retry policy with
  recorded reason, backoff, max attempts. `hard_blocker` never loops — it transitions to
  BLOCKED or a human gate. Failure reasons preserved in state (transient | environment |
  implementation | hypothesis | verification) even where CLI flags stay coarse.

## 7. Grounding contract (GROUND produces a task world model, not a directory summary)

Grounding record may contain (varies by task): entry points · candidate authoritative
paths · callers/consumers · DB read/write sites · events produced/consumed · tests
covering current behavior · config/flag dependencies · business entities and state
transitions · explicit business invariants · contradictions between code/tests/docs/
runtime · unresolved localization unknowns · candidate edit surface + blast radius.

**Evidence precedence** (conflicts become named unknowns or two-sided claims — a lower
rank never silently overrides a higher observation):
1. reproducible runtime behavior → 2. tests exercising the behavior → 3. executable
source paths → 4. API/schema/DB contracts → 5. docs and ADRs → 6. git history →
7. model inference.

**Exit condition:** change surface localized with cited evidence, OR remaining
uncertainty explicitly represented and routed (cognitive detour or human gate).
The impact map is consumed by PLAN, IMPLEMENT and VERIFY; audit flags an impact map no
downstream phase referenced (law 2).
EVAL-PENDING: does this contract improve localization accuracy and hidden-acceptance
performance vs plain Claude Code? (Evidence for priority: map reuse 9/10 tasks.)

## 8. Harness & pack architecture

- **Packs** = unit of modularity: `packs/<name>/pack.yaml` with {name, version, requires,
  conflicts, contributes: personas/playbooks/skills/templates/routing-fragment/gates}.
  Core: engineering (default), ops, business. Enable/disable per install and project.
- **Compiled prompts:** the `/eaos` command, adapters, and CLI config are build artifacts
  (`make build`): deterministic output, rule precedence + conflict detection, generated
  manifest (enabled packs, versions, input hashes, compiler version). **Golden parity
  tests against current behavior pass before the god file is deleted.**
- **Scoped context:** workers receive role-scoped packs (spec + artifact refs + relevant
  decisions), never transcript dumps (evidence: 1.03M/82k worker).
- Model policy: `models.mode: inherit` (default) | `tiered` (opt-in, harness-permitting).

## 9. Multi-agent mechanics (kept throughout — proven)

Preserved: fresh-context implementer/reviewer/verifier; fan-out where lenses are distinct
(each member must be able to produce a finding class the others can't); security veto;
convergence rule. Removed as ceremony: role-play on non-isolating runtimes (solo-mode
instead); table-driven spawns with no expected distinct finding. Verifier contract:
fresh spawn, spec+diff+commands only, per-criterion evidence.

## 10. Memory architecture (four stores + lifecycle; law 3 applies to each)

- **Working** — §6 model. CLI-owned; dies with the task; feeds the episode.
- **Episodic** — `runs.jsonl`: one structured line per task (kind, playbook, roster,
  spawns, loopbacks, criteria results, tokens where available, verdict); war room stays
  the raw record. Retrieved only on similarity to the current task.
- **Semantic** — facts/ADRs with provenance {source, evidence, commit, validated_at,
  exceptions, status}; supersession mandatory; generated index (never hand-maintained).
- **Procedural** — repo-specific procedures with triggers + failure conditions; promoted
  from episodes only after demonstrated success or independent validation.
- **Retrieval is runtime-performed, not prompt-declared:** the runtime queries stores
  (by kind/paths/symbols/signals), injects selected entries into the phase pack, and
  records {query, injected, skipped, reasons}. Audit verifies: retrieval ran, injected
  entries were active (not superseded), memory budget respected. No "the model should
  consult memory" prose anywhere.
- **Global (`~/.claude/eaos/memory/`)** — EVAL-PENDING. Promotion requires: demonstrated
  success · ≥2 distinct projects · project/customer identifiers stripped · no secrets,
  source, or proprietary business facts · explicit applicability predicate
  (applies_when / does_not_apply_when) · documented failure conditions · human approval
  while EVAL-PENDING. Generalized procedures/patterns only — never copied project facts.
- Extraction produces candidates, never trusted memory.

## 11. Runtime consistency & CLI contract

**Consistency (binding):** every runtime state file carries schema_version + revision ·
updates use a task/project lock + atomic temp-file rename · mutating verbs accept or
generate an idempotency key (hook retries cannot duplicate spawns/messages/episodes/
evidence) · parent-tree spawn budget is reserved atomically BEFORE the child spawn
persists · runs.jsonl appends locked, deduped by (task id, close revision) · a crashed
write leaves previous-valid or next-valid state, never partial · audit detects stale
locks, duplicate closes, revision regressions, parent-child budget disagreement.

**Verbs:** existing set stands — init, task new (`--parent`; duplicate detection by
deterministic fingerprint {parent, kind, target paths/symbols, criteria ids, outcome}:
exact match under same parent → block, overlap → warn, `--allow-duplicate --reason` →
permit+record), append (`--file -`), phase, spawn (check-before-persist), loopback
(`--class`), gate, verify (`--bulk`), status, report, audit.
**Criterion states:** verified | failed | blocked | not_reproducible |
manual_confirmation_required. Report may state conditional completion ("implementation
complete; release blocked pending AC-007") — never unconditional success over
unverified required criteria (law 7; evidence: T17-09 AC2 honest deferral).
**New-verb budget: ≤6** for cognitive+memory layers (claim, probe, unknown, episode,
memory, learn — final naming at implementation; no new verb without retiring one).

**Enforcement chain (honest version):** the runtime/adapter wrapper is the authoritative
mutation path → hooks auto-invoke it where the host reliably intercepts (accelerators,
not source of truth) → `eaos audit` is the final reconciliation backstop. A host adapter
may claim fail-closed only after adapter-specific tests prove direct spawn/retry/
completion paths cannot bypass the runtime.

**Context metrics are diagnostic, never completion gates:** audit reports absolute tokens
by worker/role, repeated-context estimate, coordination-output share, findings/criteria
influenced, model+cache info where the host exposes it; reports "unavailable" rather
than inferring. Mechanism evaluations — not ratio thresholds — decide whether scoped
packs earn their keep.

## 12. Mechanism lifecycle (`mechanisms.yaml`, validator-checked for shape)

Entry (≤10 lines): {id, status: proposed|instrumented|active|validated|rejected|retired,
motivating_evidence (run artifact links), expected_effect, primary_metric, guardrails,
owner, evaluation_due_after_runs, removal_condition}. Validator asserts structural
completeness; the EVALUATOR (eval runs) determines effect; the maintainer retains,
revises, or removes. Removal conditions are executed, not admired.

## 13. Evaluation contract

Controls: same repo commit, task statement, base model + version, effort, tool
permissions, environment; fixed baseline CLAUDE.md; hidden acceptance criteria; grader
blinded to harness. **Tiered rigor:** minimum = paired single runs with variance recorded
as a limitation; multi-trial where cost permits — an honest eval that runs beats a
perfect one that doesn't. Metrics: defects caught, criteria pass rate, false completions,
normalized tokens AND estimated cost (caching/tier-aware), coordination share, wall
clock. **Report by task class** (bug / incident / feature / refactor / business-rule /
cross-service) — no single aggregate that lets easy tasks hide hard failures. EAOS
winning only on complex bugs + business-rule changes is an acceptable outcome that
sharpens the wedge. Bar unchanged: better defects/criteria at <2× cost, else simplify.

## 14. Migration plan (order binding)

1. **Eval & capture** — runs.jsonl + episode close, capture-run script, baseline runs.
   Nothing ships ahead of this except its own instrumentation.
2. **Shape** — pack manifests, compiled prompts + parity tests, generated config;
   duplicated prose deleted only after its mechanized replacement lands.
3. **Bookkeeping in the new shape** — consistency layer (§11), parent budgets,
   fingerprints, audit, ergonomics, models.mode, hooks-as-accelerators.
4. **Grounding contract + conditional cognitive runtime** (§5–7).
5. **Memory lifecycle** (§10), store by store, each behind its verbs.
6. **Measured optimization** — remove what numbers don't defend; only then tool-neutral
   extraction.

Backward compatibility: existing `.eaos/` layouts remain readable; old tasks valid.

## 15. Non-goals

No universal-autonomy claims · no confidence decimals · no automatic promotion of model
conclusions into memory · no simulated multi-agent on non-isolating runtimes · no
vector/embedding infrastructure at current scale · no portability expansion before
measured improvement · no new verbs beyond budget without retiring one · no token-ratio
completion gates · no hand-maintained indexes · no eval postponed in pursuit of eval
perfection.
