# Software factories: a study, and what it means for EAOS

Date: 2026-09-17. Status: research, not a spec. Nothing here changes the frozen v3
architecture; it proposes experiments.

Method: primary sources first (repos read through the GitHub API today, StrongDM's factory
site, Huntley's actual prompt files, OpenAI's and Cognition's own posts), secondary
explainers only for framing. Everything below post-dates the assistant's training data, so
each claim carries its source. Numbers marked (secondary) were not checked at the origin.

## 1. The two claims, tested

**Claim A: serious factories do not use libraries of separate persona agents; they rely on
the model and work on using it to the maximum.** Supported, with one precise correction.
What they drop is the *costume* (role prose: "you are a senior architect"). What they keep,
and lean on hard, is the *boundary* (a fresh context, a restricted tool set, a separate
grader). Section 4.

**Claim B: most software factories are fewer than ten files.** True for the minimalist
school, and the smallest is smaller than expected. False for the orchestration-platform
school. The file count also hides that the small ones are heavy in a different place.
Section 3.

## 2. Vocabulary

Three layers, each built from the one below (Osmani):

- **Loop**: gather context, act, check, repeat until a stop condition.
- **Harness**: what makes one loop reliable. Tools, hooks, sandbox, checks, budgets, memory.
- **Factory**: many harnessed loops fed by a queue and drained through a gate into
  production. An org chart made of loops, not a bigger agent.

Two variants of the same pipeline: **lit** (humans approve spec and merge; Stripe still
human-reviews 1,300+ agent PRs a week) and **dark** (Shapiro's Level 5, January 2026: no human
writes or reviews code; StrongDM is the public example). The idea every serious source shares:
generation is nearly free, **verification is the constraint**, and autonomy is granted only
as far as it can be cheaply verified ("back pressure").

## 3. Anatomy: what these things are actually made of

Measured today via `gh api repos/<r>/git/trees/HEAD?recursive=1`:

| Repo | Files | Markdown | Code | What it is |
|---|---|---|---|---|
| strongdm/attractor | 5 | 4 | **0** | Three natural-language specs + README + licence |
| ghuntley/how-to-ralph-wiggum | 12 | 6 | 1 | 5 operative files: 2 prompts, loop.sh, AGENTS.md, plan |
| snarktank/ralph (21.8k stars) | 31 | 7 | 3 | ~6 operative: ralph.sh, prompt.md, prd.json, 2 skills, AGENTS.md |
| obra/superpowers | 195 | 94 | 59 | Skills library |
| msitarzewski/agency-agents | 362 | 325 | 18 | Persona library |
| bmad-code-org/BMAD-METHOD | 592 | 393 | 53 | Persona-driven agile method |
| steveyegge/gastown | 1,563 | 117 | 1,280 | Go orchestration platform: mayor, workers, witness, merge queue |
| **eng-agent-os (EAOS)** | **128** | **104** | **13** | 17 personas, 8 playbooks, 11 skills, runtime CLI |

Reading the small ones, not just counting them:

**Attractor is a repo with no code.** Its README is one instruction: give your coding agent
the URL and tell it to implement Attractor. The product *is* the spec ("NLSpec"). But the
three specs total about 277 KB. So "five files" is true and "small" is not: the mass moved
from code and role prose into a precise specification of an execution engine. What the spec
describes is a graph runner: pipelines declared in Graphviz DOT, nodes backed by pluggable
handlers (LLM task, human gate, parallel, fan-in, tool, manager loop), a checkpoint after
every node, `goal_gate` nodes the pipeline cannot exit past, retry targets, and a
**context-fidelity** setting per edge that decides how much history the next node receives
(section 5).

**Ralph is a shell loop.** `while :; do cat PROMPT.md | claude ; done`. Everything else is
discipline encoded in one prompt file of about 2.9 KB. Huntley's own description is
"monolithic": one process, one repository, deliberately not a multi-agent system.

**The platform school exists and is large.** Gas Town is 1,280 Go files. Factory.ai and 8090
are commercial platforms. What they add over the minimalists is what a factory needs beyond
a harness: a queue, parallel workers in worktrees, stuck-agent detection, a bisecting merge
queue, federation.

So the honest reading of claim B: **the definition layer of a working factory is tiny, and
its size is inversely related to how much it trusts the model.** The minimalists delegate
intelligence to the model and correctness to the target repo's own tests, types and linters.
The platform school spends its code on throughput and recovery, not on telling the model how
to think. Nobody in either school spends files on personas. The persona-heavy repos in the
table are libraries, not factories.

## 4. The persona question

Evidence that the costume does nothing:

- A Stanford/CMU study tested 162 personas across roughly 2,400 questions and four model
  families. Adding a persona did not improve accuracy and sometimes reduced it (secondary;
  consistent with the known "helpful assistant" role-prompting paper).
- Cognition, June 2025: rule out architectures that do not share full context, because
  parallel agents make implicit decisions that conflict.
- Anthropic's own multi-agent research post: multi-agent uses about 15x the tokens of chat
  against about 4x for a single agent, and **token usage alone explained 80% of the
  performance variance**. The swarm was winning largely by spending more. It also says
  domains with many dependencies between steps, which is coding, fit multi-agent poorly.
- Tran and Kiela (arXiv 2604.02460, secondary): at equal token budget a single agent beat
  multi-agent in nearly every condition, except when the single agent's context was degraded.

Evidence that the boundary does a lot:

- Cognition, April 2026, on what now works: a **code-review loop where the reviewer has a
  clean context** catches about 2 bugs per PR, roughly 58% severe, and the clean context
  *improves* the reviewer because there is no context rot. Also "smart friend" escalation to
  a stronger model, and manager-child delegation. Their rule: writes stay single-threaded;
  extra agents contribute **intelligence, not actions**.
- Huntley's build prompt uses up to 500 subagents for search and reading, **exactly one**
  for build and test, and a stronger model only "when complex reasoning is needed". Subagents
  there are context garbage collection and a back-pressure valve. The tiering is by
  difficulty of the step, not by job title.
- StrongDM's evaluator is separate from the builder and grades against scenarios the builder
  never saw. That is a boundary, not a role.

This is the same conclusion the July critique of EAOS reached from the inside: its value in
Claude Code is four mechanical properties (fresh context, maker is not checker, model tiers,
tool scoping), and role-play elsewhere keeps the ceremony without the mechanism. The outside
evidence now agrees, and sharpens it: **of EAOS's 17 personas, what is load-bearing is where
the context boundary sits and which tools cross it. The persona prose is about 9,000 tokens
that the research says buys nothing, and the 280 agency-agents entries listed on every turn
buy less than nothing.**

## 5. How the minimalists "use the model to the maximum"

These are the actual techniques, each traceable to a source above.

Context:
1. **Fresh context per unit of work.** Huntley's working rule is about 170k usable tokens and
   that quality falls as the window fills; community practice treats the first half of the
   window as the sharp zone. Ralph never lets a session get long enough to rot.
2. **State on disk is the only memory.** Plan file, specs, AGENTS.md, git history. "Anything
   not written down did not happen."
3. **Allocate the stack the same way every loop.** Same prompt, same instruction file, same
   specs; only the repository differs.
4. **One item per loop.** Loosen as a project stabilises, tighten the moment it goes sideways.
5. **Subagents as context garbage collection.** Investigation happens in a child whose
   transcript never enters the parent.
6. **A tiny, operational instruction file.** OpenAI: a monolithic AGENTS.md "failed
   immediately"; it crowded out the task, made everything look equally important, and rotted.
   Fix: about 100 lines as an index into structured docs, loaded progressively. Huntley's
   prompt ends with the same warning: a bloated AGENTS.md pollutes every future loop.
7. **Context fidelity as a dial.** Attractor carries `truncate`, `compact`, or a summary of
   roughly 600, 1,500 or 3,000 tokens into the next node, chosen per edge; default `compact`.

Correctness:
8. **Back pressure inside the loop.** Types, compiler, tests, linters, custom static rules
   that fail in the sandbox so the agent corrects itself before review. "The wheel has got
   to turn fast": strictness is balanced against cycle time.
9. **Search before assuming.** The most repeated guardrail: never conclude something is
   unimplemented from one failed search. Huntley calls that nondeterminism the method's
   Achilles heel.
10. **Capture the why in the test**, so a later fresh context can tell a wrong test from a
    wrong implementation.
11. **Scenarios, not tests.** StrongDM: a test in the codebase can be rewritten to match the
    code, or the code rewritten to pass it. A scenario is an end-to-end story stored outside
    the codebase, a holdout set. Success is "satisfaction": the fraction of observed
    trajectories that likely satisfy the user, not a green suite.
12. **Digital twins.** Behavioural clones of Okta, Jira, Slack, Google Docs/Drive/Sheets,
    validated against the live service until differences stop appearing; thousands of
    scenarios an hour with no rate limits.
13. **Legibility for the agent.** OpenAI made the app bootable per git worktree, wired Chrome
    DevTools into the agent runtime, and exposed logs and metrics to it. The repository is
    optimised for the agent to reason about the domain from the repo alone.
14. **Graph, not free loop.** Declare the sanctioned paths; the model is clever inside each
    box and cannot wander between them. Attractor's goal gates are this made mechanical.
15. **Entropy management.** Mechanical architectural invariants, a doc-gardening agent, one
    anti-pattern fixed per night. Agent-written code needs scheduled cleanup.

## 6. Costs and failure modes they admit

- Ralph: about 90% completion on greenfield, unsuitable for legacy code; leaves garbage and
  temp files; recovery is often `git reset --hard`. Reported runs cost 50 to 100+ USD; the
  quoted best case is an MVP for about 297 USD (secondary).
- Ronacher's critique: loop-grown code trends defensive, complex and local; each iteration
  adds a local defence, so the system looks more robust while getting less understandable.
- Fresh context is expensive by design: nothing is amortised across iterations.
- Anthropic's Ralph plugin re-feeds the prompt inside one session, so it does **not** reset
  context; practitioners consider the bash loop superior for that reason.
- StrongDM's guidance of about 1,000 USD per engineer-equivalent per day in tokens
  (secondary): the dark factory is not cheap, it is cheap relative to salaries.
- One orchestration-swap paper (arXiv 2607.06906; its own citer flags a conflict of interest)
  held the model fixed and moved cost per task by 41% and tokens by 38%. Orchestration design
  sets the bill.

## 7. EAOS against this

What EAOS has that none of the minimalists have:

- Binding gates as exit codes; honest verdict vocabulary (`verified` refused on deferral
  evidence; CONDITIONAL exit); high risks that must receive a verdict.
- An audit that reconciles state against the record, with history anchors.
- Stakes-proportional ceremony; human gates; attribution constraints as criteria.
- Attractor's `goal_gate` is the closest analogue, and it is a spec, not a shipped runtime.

What they have that EAOS lacks:

| They do | EAOS today | Evidence it matters here |
|---|---|---|
| Fresh context per unit | One orchestrator session for a whole task | 09-09 run: **~306k tokens of context on average per turn**, about twice the zone practitioners call sharp. The human's complaint was "intellect not up to the mark". |
| ~100-line index + progressive disclosure | ~989 lines / ~15k tokens loaded at start, re-read every turn | cache-read was ~51% of that run's cost |
| Boundaries without costumes | 17 personas (~9k tokens) + 280 agency listings | persona studies; Cognition; Anthropic 80% variance |
| Holdout scenarios | Verifier grades a spec EAOS wrote | reviewed role stack rejected on first real deploy |
| Back pressure in-loop | Most defects caught at REVIEW/STABILIZE | two loop-backs per task, each costing a full agent |
| State on disk as the *only* memory | State is on disk (`.eaos`), but the orchestrator also keeps everything in context | the runtime already built makes fresh-context orchestration possible |

The last row is the important one. EAOS paid, over five review rounds, for exactly the thing
Ralph needs and lacks: a trustworthy on-disk state with `eaos status`, a war room, artifacts
and verdicts. It then does not use it to drop context. **EAOS has the memory layer of a
fresh-context system and runs as a long-context system.**

## 8. Design options this opens (experiments, not decisions)

1. **Fresh-context orchestration.** One orchestrator invocation per phase, resumed from
   `eaos status` plus artifact refs. This is the v3 "compiled prompts" step with a sharper
   goal: the orchestrator's context should stay under ~100k. Measure tokens and defects
   against run 3.
2. **Three boundaries instead of seventeen roles.** Builder, clean-context checker,
   researcher-for-context-GC. Role knowledge moves into checklists inside skills, loaded on
   demand. A/B: same boundaries with and without persona prose. The literature predicts no
   quality loss and a large token drop.
3. **Holdout scenarios as a product mechanism.** The human (or a separate intake pass) writes
   scenarios stored outside the builder's reach; the verifier grades against them. The eval
   instrument already does this; it is not in the product.
4. **In-loop back pressure.** The builder runs the project's own type/test/lint and EAOS's
   static rules before handing off; a hand-off that did not run them is refused by the CLI.
5. **Command as index.** A ~100-line front door; per-phase prompts compiled from packs;
   fidelity modes (`compact` by default) for what crosses a phase boundary.
6. **Keep the runtime.** It is the differentiator: nobody in the table ships honest verdicts
   and an audit. A minimal EAOS is "Ralph's discipline plus EAOS's conscience".
7. **Stop installing all of agency-agents.** Already recommended on token grounds; the
   evidence here removes the quality argument for keeping them.

Sequencing is unchanged: run 3 first as the baseline, then one mechanism per measurement.

## 9. What is not verified

- The persona study and Tran and Kiela are cited through secondary write-ups.
- StrongDM's cost guidance and Ralph's cost anecdotes are secondary.
- Vendor claims (Factory.ai, BCG's 3 to 5x) are marketing until reproduced.
- "File count" measures the definition layer only; it says nothing about outcomes.

## Sources

- https://github.com/strongdm/attractor (README, attractor-spec.md sections 1, 3.4, 4.11, 5.4)
- https://factory.strongdm.ai/ and /techniques, /techniques/dtu, /products/attractor
- https://github.com/ghuntley/how-to-ralph-wiggum (files/PROMPT_build.md, PROMPT_plan.md, loop.sh)
- https://github.com/snarktank/ralph (ralph.sh, prompt.md)
- https://ghuntley.com/ ; https://d-central.tech/agentic-engineering/ralph-loops/
- https://futureagi.com/blog/loop-engineering/ralph-loop/ ; https://lazyralph.com/blog/ralph-wiggum-loop/
- https://howaiworks.ai/blog/geoffrey-huntley-ralph-agentic-coding-loop ; https://wiggum.dev/concepts/the-loop/
- https://addyosmani.com/blog/software-factories/
- https://openai.com/index/harness-engineering/
- https://cognition.com/blog/dont-build-multi-agents ; https://cognition.com/blog/multi-agents-working
- https://www.anthropic.com/engineering/multi-agent-research-system
- https://particula.tech/blog/single-agent-vs-multi-agent-swarm-tax-equal-budget (Tran and Kiela, secondary)
- https://www.linkedin.com/posts/jiwexler_one-of-the-most-popular-pieces-of-advice-activity-7494031916548059137-ErVo (persona study, secondary)
- https://www.developersdigest.tech/blog/harness-engineering-token-budget (arXiv 2607.06906, secondary)
- https://github.com/steveyegge/gastown ; https://gascity.com/ ; https://factory.ai/news/software-factory ; https://www.8090.ai/software-factory
- https://murraycole.com/posts/software-factory ; https://aipatternbook.com/dark-factory ; https://env.dev/guides/ai-dark-factory
