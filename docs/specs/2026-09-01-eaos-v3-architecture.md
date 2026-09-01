# EAOS v3 architecture — binding specification (2026-09-01)

Consolidates: the T-017 run analysis, the 6-project disk scan, the memory-architecture
review, and the two-round adversarial design exchange. Supersedes the architecture portions
of `2026-07-13-eaos-product-design.md` (its product strategy — prove-then-publish, wedge,
phases — stands unchanged). Every mechanism here cites evidence or is marked EVAL-PENDING.

## 1. Problem statement

EAOS currently improves *process reliability* more than *solution reliability*. Its proven
value is defect-catching via genuine maker/checker isolation; its measured weaknesses are
bookkeeping bypass, context waste, monolithic shape, and memory that writes but doesn't
compound.

## 2. Evidence baseline (raw artifacts: session export T-017 + `.eaos/` dirs on disk)

Confirmed strengths:
- Maker≠checker catches real defects: 5 in T-017's billing path alone, incl. a pre-existing
  double-credit race and a verifier refusing a skipped test as passing.
- Convergence rule works: developer CHALLENGE ×4 → architect resolution → amended ADR.
- Codebase map is the most-reused artifact in the system (9/10 tasks, sre project).
- Conditional business-pack activation earned its cost (finance-analyst → margin ADR).
- Adoption of mechanization is trending up (robot project: 6/6 state.json, 4 tasks to
  STABILIZE; pre-CLI projects: 0).

Confirmed failures:
- Honor-system decay: CLI verbs bypassed mid-run (messages:0, criteria≈0, loopbacks:0
  despite re-review); index.md absent in 4/6 projects; consolidation never ran.
- Epic fragmentation: 23 spawns vs cap 12, invisible because children reset counters;
  duplicate child tasks (T-022≡T-024, T-023≡T-027).
- Context waste: 8.6M in / 1.4M out for part of one epic, all top-tier; one worker at
  1.03M-in/82k-out; ~36% of output tokens = coordination.
- Write-only memory: 7/23 memory files never read outside authoring task; lessons chain
  1–2 tasks then die; zero cross-project transfer.
- Cold-start abandonment: 3 projects opened EAOS, ran 1–4 shallow tasks, never returned.

## 3. Kernel laws

1. Prompt rules are wishes; exit codes are rules.
2. No artifact without a producer AND a consumer.
3. No store without verbs and a lifecycle (owner, write verb, read verb, audit rule,
   supersession/deletion path).
4. Pipelines for predictable work; cognitive loops for uncertainty — mode is selected,
   never universal.
5. Maker and checker require genuine context isolation; simulated teams are banned.
6. Every mechanism carries a contract: motivating evidence, expected effect, success
   metric, runtime owner, removal condition (`mechanisms.yaml`, validator-enforced).
7. No completion without independently reproducible evidence.

## 4. Execution-mode selection

- Default mode by kind: `feature|chore|refactor|release` → pipeline;
  `bug|incident|question` → cognitive.
- **Cognitive detour (uncertainty-triggered):** any pipeline task may enter a bounded
  cognitive segment when an OBSERVABLE trigger fires: named unknowns in the impact map,
  localization marked low-confidence, or a disproven assumption mid-IMPLEMENT. Detour
  entry/exit is recorded (`eaos probe` / state.json); audit flags unclosed detours.
  Trigger is evidence in artifacts — never a vibe.

## 5. Cognitive state model (runtime-owned, state.json extension)

- **Claims**: {text, type: observed|inferred|assumed, status: active|supported|disproven|
  superseded, evidence_for[], evidence_against[], exceptions[], validated_at_commit}.
  No confidence decimals — categorical types + evidence lists only.
- **Unknowns**: named list, resolved by probes.
- **Probes**: {question, command/action, result ref, claim(s) updated}.
- Attempt ledger and loopback classification (`--class recoverable|hard_blocker`) join
  this model; a retry without a changed claim or class is refused (mechanizes
  retry_must_vary).
- Active for cognitive mode/detours only. Pipeline tasks carry criteria + gates as today.

## 6. Harness & pack architecture

- **Packs** are the unit of modularity: `packs/<name>/pack.yaml` declares contributed
  personas, playbooks, skills, templates, routing fragment, gates. Core: `engineering`
  (default), `ops`, `business`. Enable/disable per install and per project.
- **Compiled prompts:** the `/eaos` command, adapters, and the CLI's config are BUILD
  ARTIFACTS assembled from kernel + enabled packs (`make build`). One source of truth per
  rule; the 355-line god file and hand-mirrored config.json are deleted by generation.
- **Scoped context:** workers receive role-scoped context packs (spec + impact-map refs +
  relevant decisions), never transcript dumps. Enforced: `eaos audit` flags any spawn
  whose input/output token ratio exceeds a sanity bound (evidence: 1.03M/82k worker).
- Model policy: `models.mode: inherit` (default — the user's selected model everywhere) |
  `tiered` (opt-in cost profile where the harness supports per-spawn models).

## 7. Multi-agent mechanics (kept throughout — proven)

- Preserved: fresh-context implementer/reviewer/verifier separation; review fan-out where
  distinct lenses exist; security veto; convergence rule.
- Removed (ceremony): role-play on non-isolating runtimes (solo-mode instead); spawns
  justified only by a routing table when no distinct finding is expected — each fan-out
  member must be able to produce a finding class the others can't (fan-out test).
- Verifier contract unchanged: fresh spawn, spec+diff+commands only, evidence per
  criterion via `eaos verify`.

## 8. Memory architecture (four stores + lifecycle)

- **Working** — the cognitive state model (§5). Owner: CLI. Dies with the task; feeds the
  episode.
- **Episodic** — `runs.jsonl`, one structured line per task (kind, playbook, roster,
  spawns, loopbacks, criteria results, tokens, verdict) + war room as raw record.
  `eaos episode close` writes it. Retrieval: only on similarity to current task.
- **Semantic** — validated facts/ADRs with provenance {source, evidence, commit,
  validated_at, exceptions, status}. Supersession mandatory; generated index; retrieval
  verb + audit check that PLAN consulted it.
- **Procedural** — repo-specific procedures with triggers and failure conditions;
  promoted from episodes ONLY after demonstrated success or independent validation
  (`eaos memory extract → candidate → validate → promote`). Every recurring failure
  becomes a local gate (`eaos learn`-style rules riding the pre-push gate).
- **Global (`~/.claude/eaos/memory/`)** — cross-project patterns, promoted when referenced
  in ≥2 projects; index-line retrieval only; hard budget. EVAL-PENDING before build.
- Law 3 applies to every store. Extraction produces candidates, never trusted memory.

## 9. Runtime CLI contract

- Existing verbs stand: init, task new (gains `--parent`, duplicate-title warning; budgets
  aggregate up the parent tree), append (gains `--file -`), phase, spawn (check-before-
  persist), loopback (gains `--class`), gate, verify (gains `--bulk`), status, report,
  audit (NEW: state-vs-warroom cross-check, phase drift, context-ratio, unclosed detours).
- **Verb budget: ≤6 new verbs total** for cognitive+memory layers (claim, probe, unknown,
  episode, memory, learn — final naming at implementation). Consolidation is a
  requirement, not an option: T-017 proved unergonomic verbs get bypassed.
- Exit codes remain binding; hooks (PreToolUse auto-spawn, Stop auto-audit) close the
  bypass hole without model cooperation.

## 10. Evaluation contract

- Baseline: same tasks through plain Claude Code + good CLAUDE.md (docs/EVAL-PROTOCOL.md;
  bar: better defects/criteria at <2× tokens, else simplify).
- Metrics per run (from runs.jsonl): defects caught, criteria pass rate, false
  completions, tokens by role, coordination share, loopbacks, wall clock.
- Mechanism contracts revisited each eval cycle; removal conditions are executed, not
  admired.

## 11. Migration plan (order is binding)

1. **Eval & capture first** — runs.jsonl + capture-run script + baseline runs. (Rung 2/3;
   still the gap. No architecture work ships ahead of this except where it IS the
   instrumentation.)
2. **Shape** — pack manifests around existing dirs; compiled prompts; generated config;
   delete duplicated prose after each rule is mechanized.
3. **Bookkeeping fixes inside the new shape** — parent-child budgets, audit, ergonomics,
   models.mode, hooks.
4. **Conditional cognitive runtime** (§4–5).
5. **Memory lifecycle** (§8), store by store, each behind its verbs.
6. **Measured optimization** — remove what the numbers don't defend; only then
   tool-neutral extraction.

Backward compatibility: `.eaos/` layouts remain readable; old tasks stay valid; prose
rules are deleted only after their mechanized replacement lands (never before).

## 12. Non-goals

- No universal autonomy claims. No confidence decimals. No automatic promotion of model
  conclusions into memory. No simulated multi-agent on non-isolating runtimes. No
  vector/embedding infrastructure at current scale. No portability expansion before
  measured improvement. No new verbs beyond the budget without retiring one.
