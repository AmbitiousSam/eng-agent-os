# EAOS v4 architecture: working state, clean checks, honest evidence

Status: **DRAFT rev 2, not frozen.** v3 (`2026-09-01-eaos-v3-architecture.md`) stays the
binding architecture until this one is explicitly frozen.

**Freeze rule.** An experiment reporting does not supersede v3. Supersession requires all
three: an explicit freeze decision recorded in this file, the recorded outcomes of the
experiments it depends on, and passing tests for every contract being adopted. An
unsuccessful or inconclusive experiment therefore activates nothing.

**Implementation note (2026-09-18).** By owner decision the v4 runtime, front door,
boundaries and checklists were built ahead of E0; v3 is preserved at git tag
`e0-baseline` so E0 still runs against exactly the pre-registered v3. The freeze rule above
is unchanged: implementation is not adoption.

Inputs: the 2026-09-09 real run and its review, the software-factory study
(`docs/research/2026-09-17-software-factories-study.md`), harness-effect papers cited
there, and an external review of the v4 proposal (section 3 answers it point by point).

## 1. Principle

> **EAOS constrains actions and evidence, not the model's reasoning process.**

v3 put an orchestrator in front of the model and drove it through a lifecycle. v4 removes
the script. The model plans and routes as it sees fit. EAOS supplies three things a model
cannot give itself, and enforces them at boundaries:

1. **Working state that outlives a context** (the board).
2. **A check made without the maker's reasoning** (the checker, evaluator scenarios).
3. **Evidence and verdicts that cannot be talked into existence** (the runtime).

Good constraints improve performance. The v3 error was prescribing reasoning and routing
where a runtime-enforced boundary would have been enough.

## 2. Diagnosis, with what is measured and what is not

Observed: on real work, plain Cursor is more efficient than Claude Code + EAOS, including
on a machine with one plugin and EAOS only. After six or seven prompts a session degrades.

Measured on the 2026-09-09 transcript. Method, definitions, script and results:
`evals/results/2026-09-09-context-measurement.md` (`scripts/measure_session_context.py`).

| Fact | Value |
|---|---|
| Command expansions (`/agentic-os` re-injected) | 16, estimated at about 6.2k tokens each (characters / 4), about 99k nominal |
| Compaction events | **0** |
| Lead context per response (164 responses) | first 95,696, median 318,552, final **627,909**; grew overall, with 7 small decreases (largest 2.9%) and none above 40% |
| Output tokens, lead vs all 25 subagents | 227k vs 35k |
| Command frontmatter | `model: opus` pinned. All 68 responses following a command expansion ran on opus; all 96 others ran on the user's model |
| Lead role | "You do NOT write the production code, design, or tests yourself" |

An earlier note in this project put re-injection at about 225k tokens. That was wrong by
2.3x: it multiplied by the size of four files, not by the expansion actually injected.

What this supports: **EAOS's instruction and coordination overhead is the leading
explanation for the regression.** Two context mechanisms are observed: repeated command
expansion, and a lead context that never resets. The expansions are part of that context,
not a quantity independent of it, so their sizes cannot be compared as causes: a larger
share of tokens is not a larger causal effect. E0 tests both because both are cheap to
isolate, not because one has been shown to dominate. Forced delegation, the pinned model
and coordination overhead are confounds E0 controls. Nothing here is proven until it runs.

## 3. Answer to the external review

| # | Review point | Position | Reasoning |
|---|---|---|---|
| 1 | Diagnosis plausible, not proven; re-injection first | **Agree on proof; E0 tests both mechanisms** | The transcript shows a second mechanism beside re-expansion: a lead that never reset (0 compactions, 627k). Rev 1 called it the larger cause; rev 2 withdraws that, since a larger token share is not a larger causal effect. E0 isolates two factors, not one: expansion-once and lead reset. The pinned model and the no-code lead are confirmed confounds and are controlled. "A script caps the model" withdrawn as too absolute; section 1 uses the reviewer's sentence. |
| 2 | Board needs metadata; never silently omit a blocker; deterministic filtering first | **Agree, with a smaller link set** | Runtime generates id, revision, scope, author, status, snapshot. The model supplies type, summary, ref, and optionally two links only: `supersedes` and `invalidates`. `depends_on` and `contradicts` are deferred: this project has three measured runs of bookkeeping bypass, and every field the model must fill is a place it will not. Incomplete views are reported, never disguised (section 5.3). |
| 3 | Propagation needs a mechanism, not storage | **Agree fully** | This is the differentiator, so it is a runtime contract (section 6), honest about being boundary-checked, not continuous. |
| 4 | Fix the lead's lifecycle; bounded continuation packet; lead may do small tasks | **Agree, and the data makes it the top item** | "Loaded once" means once per fresh context. Section 7. The lead writing small changes reverses a v3 rule and removes a confound. |
| 5 | Checker: clean reasoning, not restricted evidence; holdouts test disclosed requirements; separate product scenarios from benchmark holdouts | **Agree; my earlier wording was wrong** | A diff alone hides broken callers, config interactions and migrations. The checker reads the repository freely and no maker transcript or self-review is injected (K-1 states the enforceable boundary and its limit). A revealed scenario becomes regression coverage and is recorded as revealed. A same-model checker is separation, not independence of error; a cross-model checker is an adapter option, not a requirement. |
| 6 | "Recorded check run" too weak; do not trust the old runtime | **Agree; one simplification** | Evidence is bound to a code snapshot. v4.0 invalidates **all** check evidence when the snapshot changes. Path-level invalidation is deferred: it is where the complexity explodes and a coarse rule is honest. The runtime distrust is warranted: the episode-close inconsistency was reproduced on 2026-09-17 and fixed the same day (contract R-1). |
| 7 | Host-agnostic is an interface goal; writer ownership needs a mechanism; budget readers | **Agree** | Adapters declare each capability as enforced or advisory, and every final report states the enforcement level it ran under. "Any number of readers" was sloppy: concurrency and tokens are budgeted. |
| 8 | Isolate re-injection, then A/B/C arms that attribute the board's value | **Agree; the reviewer's arms are better than mine** | Plain vs v3 vs v4 could show improvement and not say why. One practical limit: with a single human, review blinding is approximated by pre-registered executed checks scored by script against anonymised directories. |
| — | Keep / change / defer list; drop the ten-file target; preserve hard-won checks | **Agree** | The target is a bootstrap token budget, not a file count. Persona deletion is gated on a parity extraction (section 10). |

### 3.1 Second review (of rev 1), accepted in rev 2

| Finding | Change |
|---|---|
| Verdict function trusted an incomplete risk registry (`--priority blocking` + `severity: high` in the body was never registered) | Reproduced and repaired 2026-09-17: a RISK must carry a severity (flag, body, or legacy priority); `high` and `blocking` register; unclassified risks are refused. Protocol-shaped reproduction is in the suite. R-7 reworded: carried contracts are re-proven, not assumed |
| Adapter guarantees stronger than their mechanisms | Section 11 now separates target, mechanism, verified, and known bypass. Ceiling and reset are **planned, advisory** until probes pass |
| Checker evidence boundary contradictory | K-1 rewritten to an enforceable boundary: nothing is injected; conclusions are re-established independently; useful evidence is not excluded because the maker found it |
| Snapshot hashing underspecified | R-2 defines included inputs, excluded runtime records and outputs, ignored-but-relevant config, and before/after checks |
| E1 decision rule too final | E1 is a pilot with win / loss / tie / inconclusive outcomes; removal needs confirmation on further tasks, and the fallback product is itself evaluated |
| Freeze trigger inconsistent | One rule, in the header |
| Measurements unverified | Artifact and script linked in section 2 |

## 4. Shape

```
             human
               |
             LEAD  (model-led; bounded bootstrap; resets from a continuation packet)
               |  posts / reads budgeted views
   +-----------+------------------------------+
   |                 BOARD                    |   typed, revisioned working state on disk
   +----+-----------------+--------------+----+
        |                 |              |
     WRITER           READERS         CHECKER
  one per workspace   researchers,    no maker transcript;
  (lease), fresh      thinkers,       full repo read; evaluator
  context per unit    reviewers       scenarios the maker never saw
        |                 |              |
        +-----------------+--------------+
                          |
                       RUNTIME   snapshot-bound evidence, one verdict function,
                                 gates, audit, budgets, leases
```

- **Lead.** The user's session. No script. Handles trivial and small work directly. Spawns
  help when a unit benefits from a fresh context or a second view.
- **Writer.** One per shared workspace at a time, held by a runtime lease. Parallel writers
  only on disjoint scopes in separate worktrees, merged through one gate.
- **Readers.** Research, design thinking, review. Parallel, budgeted, post to the board,
  never write product files.
- **Checker.** Clean reasoning context. Nothing of the maker's transcript or self-review
  is injected. It is given requirements, code, observed evidence, decisions and unresolved
  risks, and re-establishes conclusions itself.
- Role knowledge lives in **checklists** loaded on demand (security, deploy rehearsal,
  intake, incident), not in personas.

## 5. The board (task working state)

The war room's useful function, kept; its transcript and relay burden, removed.

### 5.1 Entry

| Field | Source | Notes |
|---|---|---|
| id, revision, at | runtime | stable id; revision bumps on status change |
| scope | runtime from the unit, overridable | task, work unit, component/path globs |
| author | runtime | lead, unit id, checker |
| snapshot | runtime | code snapshot id the entry was made against |
| status | runtime verb | active, resolved, disproven, superseded |
| type | model | claim, finding, decision, risk, question |
| summary | model | at most 400 characters; a summary limit, not an evidence limit |
| ref | model | artifact or file:line holding the reasoning and evidence |
| severity | model, risks only | low, medium, high, blocking |
| supersedes, invalidates | model, optional | the only two link types in v4.0 |

### 5.2 Working state is not memory

The board is per-task working state. Validated cross-task knowledge (v3's decisions,
patterns, lessons) is a separate store and is **deferred**: v4.0 does not read it into
context. Unvalidated memory injected at PLAN is cost without evidence.

### 5.3 Views

`eaos board view --for <unit|checker|lead> --budget <tokens>` returns entries filtered
deterministically: task, scope overlap, unresolved status, then newest revision. No
ranking model in v4.0.

**A view never silently omits a blocking fact.** Blocking risks and active decisions in
scope are included first. If they alone exceed the budget, the view prints what fits,
states `INCOMPLETE: n blocking entries omitted`, lists their ids, and exits 3. The caller
must retrieve them; it cannot treat the view as complete.

## 6. Discovery propagation (contract P)

A passive board gives persistence, not coordination.

- P-1. Every unit starts through `eaos unit start`, which records the board revision and
  code snapshot it began from.
- P-2. At a work boundary the unit runs `eaos board diff --since <rev>`, which returns
  in-scope entries added or changed since it started.
- P-3. An entry with `invalidates` marks the named unit, plan item or decision **stale**.
  Example: a researcher finds refunds use a different authoritative ledger; the builder's
  plan item is marked stale before its implementation can be accepted.
- P-4. Handoff is refused while in-scope changes are unreconciled. Reconciling means each
  one is dispositioned: acted on, or recorded "not applicable because ...".
- P-5. Relevance is a deterministic scope match. False negatives are possible and are
  measured in E1 as "relevant discoveries actually consumed".

Limitation, stated plainly: propagation happens at boundaries. There is no message bus and
no mid-unit interruption in v4.0.

## 7. Context lifecycle (contract C)

- C-1. The front door is a bounded bootstrap, target under 2,000 tokens, loaded once per
  fresh context. A follow-up message is plain conversation. The command never re-expands
  inside a live context.
- C-2. `eaos status --packet` returns a bounded continuation packet: objective and
  acceptance criteria; current code and board revisions; active units and the writer
  lease; in-scope decisions and unresolved blockers; latest check and checker verdict;
  next unresolved action.
- C-3. The lead has an explicit reset path: compact or new session, then the packet.
  Worker transcripts are never replayed.
- C-4. **Planned, advisory until probed.** The lead should reset at unit boundaries once
  its context passes a configured ceiling. A `transcript_path` lets a hook *measure*
  usage. It does not establish that a Stop hook can force a genuinely fresh context or
  prevent further work above the ceiling, and the existing hook suite has deliberate
  fail-open cases (lock contention; the stop loop guard returns success despite drift).
  The ceiling is reported, and reset is recommended, until the probes in section 11 pass.

## 8. Checker and scenarios (contract K)

- K-1. **Boundary, stated so it can be enforced:** do not inject the maker's transcript
  or self-review into the checker. Provide requirements, code, observed evidence (check
  outputs, logs, command results), decisions and unresolved risks. The checker
  independently re-establishes every conclusion it relies on. Evidence is not excluded
  because the maker discovered it: a log line is a log line. Board `ref` artifacts may
  contain maker reasoning and live in the same repository, so a fresh context alone does
  **not** deny access to them. Strict denial needs a filtered workspace or restricted
  artifact access, which is an adapter capability (section 11), not a v4.0 guarantee.
- K-2. Evaluator scenarios test **disclosed** requirements only. A scenario that encodes a
  requirement the maker was never given is a spec bug, not a catch.
- K-3. Two stores. *Product scenarios* are used by the checker during a task; once one is
  revealed by a failure it is marked revealed and becomes regression coverage. *Benchmark
  holdouts* are used only by experiments and are never shown to any agent in a task.
- K-4. Same-model fresh-context checking is separation, not independent error. Adapters
  may offer a different model for the checker.
- K-5. Static is not verified (carried from v3.1): deploy-shaped work must execute.

## 9. Runtime contracts (R)

- R-1. **One authoritative verdict calculation**, consumed by handoff, `verify --require`,
  `report` and `episode close`. Fixed and tested 2026-09-17 after reproduction.
- R-2. Check evidence is bound to the code it ran against: command, working directory,
  snapshot id, exit status, output reference, required check category, or an explicit
  unavailable / not-applicable status. **Snapshot input boundary:**
  - *Included:* `HEAD`, plus the content of tracked-modified and untracked files that are
    not ignored — the product inputs.
  - *Excluded:* `.eaos/` in full (runtime records, check logs, board, evidence), and every
    path ignored by git (build outputs, caches, `node_modules`). Recording a successful
    check must never change the identity of the code it verified.
  - *Ignored but relevant configuration* (for example an untracked `.env` a test reads) is
    named explicitly in project config as snapshot-relevant; by default it is excluded and
    the evidence record says so.
  - The snapshot is taken **before and after** execution. If they differ (a check that
    rewrites product files, such as a formatter or a lockfile update), the evidence is
    recorded against neither and the run is reported as snapshot-unstable.
- R-3. A snapshot change invalidates all check evidence (v4.0 granularity).
- R-4. Two handoff kinds. *Ready for review* requires valid, passing, in-category
  evidence. *Blocked, requesting help* requires none and can never support a success claim.
- R-5. Writer lease: one holder per shared workspace; enforced where the adapter can gate
  edit tools, advisory otherwise. Readers record the snapshot they observed.
- R-6. Budgets: reader concurrency and a per-task token ceiling, alongside the existing
  spawn reserves.
- R-7. Carried from v3.1, **re-proven rather than assumed**: canonical verdicts,
  deferral-evidence refusal, stakes levels, locks, idempotency, history anchors, audit.
  Found defective on 2026-09-17 and repaired with reproductions in the suite: caller
  agreement (episode close), risk **registration** (protocol-shaped risks, invalid explicit
  severity, severity in the idempotency fingerprint), and an **ordering guard** (a verdict
  recorded before its risk does not answer it; ordered by the persisted revision sequence,
  not the one-second wall clock, with both same-second orders tested; a legacy verdict with
  no sequence must be re-recorded). **Not certified:** that a verdict's
  evidence actually addresses the risk it names. `R-<msg-id>` is matched by name. Causal
  risk-to-verdict linkage needs its own design and test and is kept separate from these
  narrower fixes. One verdict function guarantees agreement between callers; it does not
  by itself guarantee a correct verdict. Each carried contract needs its own adversarial reproduction before v4
  relies on it.

The runtime is **not** assumed trustworthy. Each contract above ships with a reproduction
test before it is relied on.

## 10. Disposition of v3

Keep = unchanged. Change = kept with stated edits. Move = content survives in a new home.
Delete = removed. Defer = kept on disk, not loaded, decision after E1.

| v3 component | Disposition | Into / reason |
|---|---|---|
| `commands/agentic-os.md` (461 lines, re-expanded per message, pinned opus) | **Change** | Bounded bootstrap under 2k tokens; no model pin (done 2026-09-17); no re-expansion |
| `orchestrator/orchestrator.md`, `loop.md` phase pipeline | **Delete** | Compulsory choreography. Laws that are runtime-enforced survive as contracts here |
| `orchestrator/protocol.md` war-room prose protocol | **Change** | Becomes the board entry contract (section 5) |
| War room (append-only prose, lead is sole writer and relay) | **Change** | Board: typed, revisioned, budgeted views, no relay |
| `routing.yaml` agents/conditional roster | **Delete** | The model routes. Signals survive as checklist triggers |
| `routing.yaml` stakes levels and rules | **Keep** | The dial for how much of contracts K and R fires |
| `routing.yaml` budget and reserves | **Change** | Adds reader concurrency and token ceiling |
| `routing.yaml` `models.mode: inherit` | **Keep** | Now true: persona and command pins removed |
| `routing.yaml` clarification `always_ask_about` | **Move** | Intake checklist |
| 17 personas | **Delete after parity extraction** | Every rule is mapped to a checklist, a runtime contract, or dropped with a written reason, before any file is removed |
| developer, architect, requirements-analyst | Move | Builder guidance and intake checklist |
| code-reviewer, security-reviewer, qa-engineer, verifier | Move | Checker checklist set (review, security, test adequacy, verdict rules) |
| devops, platform, sre-observability | Move | Deploy-rehearsal and operability checklists |
| codebase-analyst | Move | Research guidance (list before grep; search before assuming) |
| incident-commander | Move | Incident checklist; read-only AWS rule kept verbatim |
| tech-writer | Move | Reporting rules in the final-report template |
| ceo-strategist, product-manager, finance-analyst, growth-lead | **Defer** | Breadth was frozen in the product design; not part of the engineering core |
| 7 playbooks as pipelines | **Delete as pipelines; Move the checks** | feature-delivery gates become contracts; bug-fix repro-first, incident and investigation rules become checklists; product-framing, venture, release deferred |
| Skills: requirement-intake, bug-triage, incident-response, deployment-guide, test-plan, sensor-feedback | **Change** | Become on-demand checklists, trimmed |
| Skills: codebase-map, design-review, fitness-functions, triage, memory-consolidation | **Defer** | Useful, unmeasured; not in the v4.0 bootstrap |
| Templates | **Keep** task-spec, final-report, incident-rca, launch-review; **Defer** the rest |
| `vendor/agency-agents` install (280 listings per turn) | **Delete from default install** | No evidence of value; persona studies; measured listing cost |
| `adapters/*` | **Change** | Capability matrix: enforced vs advisory per host (section 11) |
| `adapters/solo-mode.md` | **Keep** | It is the new-session checker procedure v4 generalises |
| `harnesses/` starter kits | **Defer** |
| `memory/` cross-task stores | **Defer** | Section 5.2 |
| Runtime CLI: init, task, append, phase, spawn, loopback, gate, verify, status, report, episode, session, audit | **Keep, extend** | `phase` and `gate` become optional tools rather than a mandatory pipeline. New: unit, board, snapshot, check, writer. Verb budget revisited at freeze |
| Audit (16 checks) | **Keep** | `messages_vs_warroom`, `spawns_vs_warroom` re-pointed at the board |
| Hooks and installer | **Keep, extend** | Token ceiling on Stop; writer-lease gate on edit tools |
| `mechanisms.yaml` | **Keep** | Each v4 contract registers as a mechanism with a removal condition |
| `docs/EVAL-PROTOCOL.md`, evals | **Keep** | Run 3 is replaced by E0 and E1 below |
| Validator, tests, pre-push gate | **Keep** | Extended per contract |

## 11. Adapters: capability, not equality

A new chat reproduces a context boundary. It does not reproduce permissions or enforcement.
Each adapter declares, and each final report prints:

Four columns, because a target is not a mechanism and a mechanism is not proof. Claude
Code only; every other host starts as *advisory, unverified* in every row.

| Target capability | Implemented mechanism | Verified enforcement | Known bypass / advisory fallback |
|---|---|---|---|
| Fresh-context unit | subagent spawn | not verified: what a subagent inherits from the host is unprobed | host may inherit instructions or memory; on other hosts, new chat + packet, manual |
| No maker reasoning injected into checker | EAOS builds the checker prompt | prompt content is testable; isolation from repo artifacts is not | `ref` artifacts are readable in the same workspace (K-1) |
| Evaluator scenarios hidden from maker | none yet | none | readable if stored in the workspace; needs tool scope or an out-of-tree store |
| Spawn budget and blocked-task gate | `PreToolUse` hook → `eaos spawn` | hook suite, 73 assertions | fail-open by design on lock contention, missing binary, unresolvable session |
| Stop-time audit | `Stop` hook → `eaos audit` | hook suite | stop loop guard returns success despite drift; fail-open on lock contention |
| Writer lease on edit tools | **planned** | none | direct edits and shell-mediated writes (`sed`, redirects, generators) bypass a tool-level gate |
| Token ceiling and lead reset | **planned**; `transcript_path` allows measurement only | none | cannot force a fresh context; usage data may be missing |
| Check capture bound to snapshot | **planned** (`eaos check`) | none | a check run outside the CLI records nothing |

Probes required before any row is promoted from planned or advisory: command
re-invocation inside a live context; behaviour across compaction; direct edits;
shell-mediated writes; missing or malformed usage data. Every final report prints the
enforcement level each capability actually ran under.

## 12. Experiments

Controls for all: same model and version, effort, task, starting commit, permissions and
budget; artifacts scored by pre-registered executed checks against anonymised directories.

**E0: isolate the two context mechanisms on current v3.** Pre-registered in
`evals/results/2026-09-17-E0-preregistration.md`: a 2 x 2 of bootstrap (repeated vs once
per context) by lead (persistent vs fresh session plus bounded continuation), two repeats,
a fixed four-unit task on a pinned repository copy, hidden checks frozen by hash outside
every workspace, snapshots graded offline, and manipulation checks that invalidate a run
whose factor did not actually vary. v3's delegation policy is held constant, not altered.

**E1: attribute the board.**
- A. Plain host with normal repository instructions.
- B. Lean EAOS: same boundaries, checker and runtime, a simple task-state file.
- C. B plus budgeted board views and contract P.

Tasks: one cheap task, and one where a discovery made mid-task must change later work (a
seeded contradiction between a requirement document and the code's reality).

Metrics: correctness and escaped defects; false completion; relevant discoveries actually
consumed; rework from stale assumptions; tokens, cost, wall time.

**E1 is a pilot.** Two tasks establish feasibility and direction. They cannot justify an
irreversible product decision. Scoring is automated and pre-registered against anonymised
artifacts; it is not blinded human review.

Classification is **two-stage**, then a table, implemented and table-tested in
`scripts/experiment_outcome.py`. Each arm runs each task twice. An *invalid* run (an
infrastructure failure: host crash, API or rate-limit error, harness fault) is excluded
first and rerun; a failure caused by the agent's own decisions is a result.

Stage 1, quality, over the repeats: **higher**, **equal** or **lower** when the same
relation holds in every repeat; **ceiling** when both arms score every check in every
repeat; **inconsistent** otherwise. Noise means a difference that does not hold across
repeats, never the absence of a difference.

Stage 2, cost, treatment tokens over baseline, worst repeat decides: **improved** at most
0.80; **comparable** at most 1.20; **higher within budget** at most 2.00; **over budget**
above 2.00. The bar is per task.

| Quality / Cost | improved | comparable | higher within budget | over budget |
|---|---|---|---|---|
| higher | win | win | win | **mixed** |
| equal | efficiency win | tie | **cost regression** | loss |
| lower | loss | loss | loss | loss |
| inconsistent | noise | noise | noise | noise |
| ceiling | ceiling | ceiling | ceiling | ceiling |

Ceiling is inconclusive for quality and still reports its cost column. Mixed is not a
win: the cost is the next thing to cut. Cost regression means the layer bought nothing on
that task at more than 20% extra tokens; it counts against the layer for that task class.
Per-task outcomes are primary; aggregates never hide a per-task miss.

Stop-investing rule (kept aggressive): a loss for B against A on both pilot tasks halts
work on the orchestration layer. **Removal** additionally requires the loss to repeat on at
least three further tasks, with repeats. And the fallback, *checker and runtime only*, is
evaluated as its own arm before it is called the better product. If C beats B only on the
discovery task, the board becomes conditional on complexity, subject to the same
confirmation. That is a valid product outcome.

## 13. Deferred

Ranking or semantic retrieval for views; unrestricted parallelism; long-term memory
promotion; path-level evidence invalidation; `depends_on` / `contradicts` links; mid-unit
interruption; any uniqueness claim in public material; any file-count target.

## 14. Migration order

1. E0 on v3 as it stands (two fixes already landed: no model pin, single verdict function).
2. Parity extraction of personas and playbooks into checklists, reviewed before deletion.
3. Runtime: snapshot, check evidence, unit start, board entries and views, writer lease.
4. Bounded bootstrap and continuation packet.
5. Contract P.
6. E1 pilot, then confirmation tasks. Freezing follows the rule in the header; no
   experiment result activates this architecture by itself.
