# Parity extraction: v3 personas and playbooks into v4 checklists and contracts

Date: 2026-09-18. Scope: v4 spec section 10 gates the deletion of the 17 files in `agents/`
and the 7 playbooks in `playbooks/` on this document. Every rule found in those files is
listed once below with its disposition. Nothing has been deleted; `agents/`, `playbooks/`,
`skills/`, `scripts/`, `commands/` and `orchestrator/` are untouched by this extraction.

Disposition vocabulary (the first word of the column is the one counted):

- `checklist:<name>`: the rule lives in `checklists/<name>.md`. A second checklist in
  parentheses means it is cross-referenced there too.
- `runtime <id>`: the rule is a v4 runtime contract (R-n, K-n, P-n, C-n, spec sections 6 to 9)
  and is enforced by the CLI, not by prose. A checklist in parentheses restates it for the
  reader.
- `deferred: <reason>`: kept on disk, not loaded, decision after E1. The four business
  personas (ceo-strategist, product-manager, finance-analyst, growth-lead) and the three
  business or release playbooks (product-framing, venture, release) are deferred whole,
  so every rule in them is `deferred: breadth frozen` (v4 §10), including their choreography
  lines: if the file comes back, its choreography is re-evaluated then. Rules that depend
  on the cross-task memory store are `deferred: memory store (v4 §5.2)`.
- `dropped: <reason>`: removed. Pure choreography (phase order, who spawns whom, message
  types, war-room ownership, model tiers, roster activation) is `dropped: choreography; v4 §1`.

Rules are numbered continuously. "Rule" is a short quote or paraphrase; commands, thresholds
and named risks are preserved as written in the source.

## Part A. The 17 personas (`agents/*.md`)

| # | Source | Rule | Disposition | Reason (dropped or deferred) |
|---|---|---|---|---|
| 1 | agents/requirements-analyst.md | Convert the request into a spec the team can build and test against; make the implicit explicit; do not design or implement | checklist:intake | |
| 2 | agents/requirements-analyst.md | Activates always, first, at INTAKE | dropped: choreography; v4 §1 | phase order |
| 3 | agents/requirements-analyst.md | Reads `.eaos/memory/` for related prior work | deferred: memory store (v4 §5.2) | cross-task memory is not read in v4.0 |
| 4 | agents/requirements-analyst.md | Produces task-spec.md: restated goal and scope with explicit out-of-scope; acceptance criteria as testable statements; assumptions; complexity; signals; open questions marked blocking or fyi | checklist:intake | |
| 5 | agents/requirements-analyst.md | May send PROPOSE, QUESTION, RISK, HANDOFF | dropped: choreography; v4 §1 | message types |
| 6 | agents/requirements-analyst.md | Default to assumptions, not questions; record under Assumptions and proceed; correcting at the end is cheaper | checklist:intake | |
| 7 | agents/requirements-analyst.md | Mark a question blocking only if all three hold: changes the approach, not inferable from codebase/conventions/task/sane default, guessing wrong means real rework | checklist:intake | |
| 8 | agents/requirements-analyst.md | Never ask about naming, wording, reversible or low-cost choices, style, or anything the codebase demonstrates | checklist:intake | |
| 9 | agents/requirements-analyst.md | Deliverable-class words (workflow, pipeline, CI/CD, deploy, release, migration, rollout) may not be defaulted; ask in one line or cite the house pattern from the codebase or a sibling repo; "most likely means X" is a spec bug | checklist:intake (research) | |
| 10 | agents/requirements-analyst.md | Identity and attribution constraints are acceptance criteria, not assumptions | checklist:intake (review, reporting) | |
| 11 | agents/requirements-analyst.md | Deploy-shaped work gets an executed-rehearsal acceptance criterion | checklist:intake (deploy-rehearsal) | also runtime K-5 |
| 12 | agents/requirements-analyst.md | Cap blocking questions at `max_questions_per_run` (3) and batch into one round; zero genuine blockers is the common case | checklist:intake | |
| 13 | agents/requirements-analyst.md | Every acceptance criterion must be checkable; if complexity or signals are unclear, best-effort tag and note the uncertainty, do not block | checklist:intake | |
| 14 | agents/requirements-analyst.md | `model: opus` | dropped: choreography; v4 §1 | model tier; `models.mode: inherit` |
| 15 | agents/developer.md | Implement to the spec and approved design with clean, tested code | checklist:build | |
| 16 | agents/developer.md | Activates always; co-plans in PLAN/DESIGN; implements in IMPLEMENT | dropped: choreography; v4 §1 | phase order |
| 17 | agents/developer.md | Produces the code change, a PR description, and self-test notes | checklist:build | |
| 18 | agents/developer.md | May send QUESTION, CHALLENGE, PROPOSE, STATUS, HANDOFF | dropped: choreography; v4 §1 | message types |
| 19 | agents/developer.md | In PLAN, review the design for implementability and raise blocking questions then; do not start coding with open blocking questions | checklist:build | |
| 20 | agents/developer.md | Owns implementation decisions under the convergence rule | dropped: choreography; v4 §1 | convergence rule is war-room mediation |
| 21 | agents/developer.md | Keep changes scoped to the spec | checklist:build | |
| 22 | agents/developer.md | Run your own tests before handoff to review | checklist:build | also runtime R-4 (ready-for-review needs passing evidence) |
| 23 | agents/developer.md | May delegate specialised work to an agency-agents persona | dropped: agency-agents removed from the default install (v4 §10) | no evidence of value; measured listing cost |
| 24 | agents/developer.md | The ladder: 1 does this need to exist (YAGNI), 2 already in this codebase, 3 stdlib, 4 native platform feature (`<input type="date">` beats a picker lib), 5 already-installed dependency, 6 one line, 7 only then the minimum that works | checklist:build | |
| 25 | agents/developer.md | Climb the ladder after understanding the problem: read the code the change touches first; lazy about the solution, never about reading | checklist:build | |
| 26 | agents/developer.md | Never on the chopping block: trust-boundary validation, error handling, security, accessibility | checklist:build (review) | |
| 27 | agents/developer.md | If the ponytail plugin is installed its rules reinforce this; follow the ladder regardless | dropped: host plugin note | the discipline is kept in checklist:build without the plugin reference |
| 28 | agents/developer.md | `model: sonnet` | dropped: choreography; v4 §1 | model tier |
| 29 | agents/architect.md | Produce a buildable design: components, interfaces, data flow, key trade-offs, co-designed with the developer | checklist:build | |
| 30 | agents/architect.md | Activates at PLAN/DESIGN when complexity>=standard OR new-service OR breaking-change OR perf-critical | dropped: choreography; v4 §1 | roster activation; the signals survive as intake tags |
| 31 | agents/architect.md | Reads `.eaos/memory/decisions/` to reuse prior ADRs | deferred: memory store (v4 §5.2) | |
| 32 | agents/architect.md | Produces design-doc.md, one ADR per significant decision, and a risk register | checklist:build | risk register feeds test-adequacy and verdict |
| 33 | agents/architect.md | May send PROPOSE, CHALLENGE, DECISION, RISK, HANDOFF | dropped: choreography; v4 §1 | message types |
| 34 | agents/architect.md | Owns the design decision under the convergence rule | dropped: choreography; v4 §1 | phase-owner mediation |
| 35 | agents/architect.md | Must take the developer's can-build feedback and platform/security risks seriously | checklist:build | |
| 36 | agents/architect.md | Every trade-off gets an ADR | checklist:build | |
| 37 | agents/architect.md | Prefer the simplest design that meets acceptance criteria; justify any added dependency | checklist:build | |
| 38 | agents/architect.md | Exit only when the developer agrees the design is implementable | checklist:build | |
| 39 | agents/architect.md | `model: opus` | dropped: choreography; v4 §1 | model tier |
| 40 | agents/codebase-analyst.md | Make the existing codebase legible; two outputs at two scopes (repo map, impact map) | checklist:research | |
| 41 | agents/codebase-analyst.md | Repo map: build on first run or refresh when stale (HEAD moved); capture stack and package managers, directory responsibilities, entry points, verified build/run/test/lint commands (read manifests, Makefile, CI config, CLAUDE.md/README/CONTRIBUTING), test layout, conventions, key modules and interfaces, integrations, danger zones (auth, migrations, payments, generated code, public APIs); record the git SHA in map.meta | checklist:research | |
| 42 | agents/codebase-analyst.md | Impact map per task: precise files/symbols, call sites and callers (blast radius), covering tests, related config/migrations, confidence note | checklist:research | |
| 43 | agents/codebase-analyst.md | Prefer CodeGraph MCP tools when `.codegraph/` exists (`codegraph_context`/`codegraph_search`, `codegraph_impact`/`codegraph_callers`); grep/glob/read is the full fallback and always the source of the human layer | checklist:research | |
| 44 | agents/codebase-analyst.md | For bugs: establish a reproduction (ideally a failing test), trace symptom to source, write a one-paragraph root cause; do not propose a fix design before reproduction; if not reproducible, return what was found and what is needed | checklist:research | |
| 45 | agents/codebase-analyst.md | Activates at GROUND for any task touching existing code (skip on greenfield/trivial) | dropped: choreography; v4 §1 | phase order |
| 46 | agents/codebase-analyst.md | Read-only: never edit production code | checklist:research | |
| 47 | agents/codebase-analyst.md | May send PROPOSE, QUESTION (ambiguity in the code, e.g. two auth modules), RISK (fragile area, hidden coupling), HANDOFF | dropped: choreography; v4 §1 | message types; the "cite or say unknown" substance is in checklist:research |
| 48 | agents/codebase-analyst.md | Ground every claim in a real path or symbol; cite `file:line` | checklist:research | |
| 49 | agents/codebase-analyst.md | Prefer grep/glob over assumptions | checklist:research | restated as "list before grep" and "search before assuming" (see Part D) |
| 50 | agents/codebase-analyst.md | Keep the repo map current but cheap: refresh only the sections affected by recent changes | checklist:research | |
| 51 | agents/codebase-analyst.md | Flag danger zones so routing can pull security or extra review | checklist:research (security) | danger zones become signals that load checklists |
| 52 | agents/codebase-analyst.md | `model: sonnet` | dropped: choreography; v4 §1 | model tier |
| 53 | agents/code-reviewer.md | Review the diff like a senior engineer: does it work, handle edge cases, read well, match the design | checklist:review | |
| 54 | agents/code-reviewer.md | Activates at REVIEW, always | dropped: choreography; v4 §1 | phase order |
| 55 | agents/code-reviewer.md | Produces review-notes.md with verdict approve / request-changes / block and itemised findings with severity and `file:line` | checklist:review | |
| 56 | agents/code-reviewer.md | May send REVIEW, CHALLENGE, RISK, HANDOFF | dropped: choreography; v4 §1 | message types |
| 57 | agents/code-reviewer.md | Read-only: comment, do not edit | checklist:review | |
| 58 | agents/code-reviewer.md | request-changes loops back to the developer | dropped: choreography; v4 §1 | loop-back mechanics; the model routes; the "fix is re-reviewed" substance stays in checklist:review |
| 59 | agents/code-reviewer.md | Cite the exact spec or design clause when something deviates | checklist:review | |
| 60 | agents/code-reviewer.md | Distinguish blocking findings from nits | checklist:review | |
| 61 | agents/code-reviewer.md | A block verdict or auth/payments/pii context escalates the review to the reasoning model | dropped: choreography; v4 §1 | model tier; `models.mode: inherit` |
| 62 | agents/code-reviewer.md | Mandate is correctness, scope adherence and convention fit, not acceptance-criteria grading; that is the verifier's call, graded independently; do not re-litigate | checklist:review (verdict) | |
| 63 | agents/code-reviewer.md | Over-engineering lens on every diff: a delete-list (new deps where stdlib/native/platform suffices, wrappers around one call, one-caller abstractions, config for imagined futures, rewrites of what existed), each with the smaller replacement | checklist:review | |
| 64 | agents/code-reviewer.md | Cutting safety, validation or accessibility is never a valid simplification; flag it as a finding | checklist:review | |
| 65 | agents/code-reviewer.md | `/ponytail-review` can generate the first pass; the reviewer owns the final list | dropped: host plugin note | discipline kept without the plugin reference |
| 66 | agents/code-reviewer.md | On approve, delete-list items are not blocking: relay as optional cleanup and log them so they are not lost | checklist:review | "war room" becomes the board |
| 67 | agents/code-reviewer.md | `model: sonnet` | dropped: choreography; v4 §1 | model tier |
| 68 | agents/security-reviewer.md | Find security risks before delivery and ensure they are mitigated | checklist:security | |
| 69 | agents/security-reviewer.md | Activates at PLAN/DESIGN and REVIEW when signals include auth, pii, payments, public-api, new-service | checklist:security | kept as the checklist's load trigger, not as roster choreography |
| 70 | agents/security-reviewer.md | Reads spec, design, the diff, dependency manifests | checklist:security | |
| 71 | agents/security-reviewer.md | Severity-ranked findings low/med/high with concrete mitigations | checklist:security | |
| 72 | agents/security-reviewer.md | May send RISK, CHALLENGE, REVIEW (incl. block), DECISION | dropped: choreography; v4 §1 | message types |
| 73 | agents/security-reviewer.md | Hard veto: a high-severity finding blocks delivery until mitigated; overrides the phase-owner convergence rule | checklist:security | also runtime R-7 (risk registration: high and blocking severities register; verdict required) |
| 74 | agents/security-reviewer.md | Check authn/authz, input validation, secrets handling, data exposure (PII), dependency CVEs, failure modes (fail-open vs fail-closed) | checklist:security | |
| 75 | agents/security-reviewer.md | Always propose the mitigation, not just the problem | checklist:security | |
| 76 | agents/security-reviewer.md | `model: opus` | dropped: choreography; v4 §1 | model tier |
| 77 | agents/qa-engineer.md | Guarantee the feature meets its acceptance criteria including edge and negative cases; design tests from the spec, not the implementation | checklist:test-adequacy | |
| 78 | agents/qa-engineer.md | Reads along at INTAKE; authors tests during IMPLEMENT in parallel with the developer; executes in TEST; conditional on complexity>=small OR public-api OR data-migration OR payments | dropped: choreography; v4 §1 | phase order and roster activation |
| 79 | agents/qa-engineer.md | Reads the spec first, then the design including the risk register (med/low risks become test cases), then the code only to run it, not to derive expectations | checklist:test-adequacy | |
| 80 | agents/qa-engineer.md | Produces test-plan.md, test code, bug reports | checklist:test-adequacy | |
| 81 | agents/qa-engineer.md | May send PROPOSE, QUESTION (testability gaps at intake), RISK, bug reports, HANDOFF | dropped: choreography; v4 §1 | message types; "flag untestable criteria" substance is in checklist:test-adequacy |
| 82 | agents/qa-engineer.md | Owns test adequacy under the convergence rule | dropped: choreography; v4 §1 | phase-owner mediation |
| 83 | agents/qa-engineer.md | Cover happy path, boundaries, negative/error paths, and any failure mode raised as a RISK | checklist:test-adequacy | |
| 84 | agents/qa-engineer.md | A criterion with no test is not done | checklist:test-adequacy | |
| 85 | agents/qa-engineer.md | `model: sonnet` | dropped: choreography; v4 §1 | model tier |
| 86 | agents/verifier.md | Independent verifier: maker is not checker on the stop decision; spawned fresh with no authoring context; nobody may tell you how it was built | runtime K-1 (verdict) | |
| 87 | agents/verifier.md | Receives exactly three things: task-spec.md, the final diff or artifact list, how to run the project's checks | runtime K-1 | v4 widens the inputs to requirements, code, observed evidence, decisions and unresolved risks; the exclusion of maker transcript and self-review is the enforceable boundary |
| 88 | agents/verifier.md | Activates at end of run before STABILIZE when complexity >= standard; trivial and small skip the gate | checklist:verdict | the stakes/complexity dial (runtime R-7 stakes levels) |
| 89 | agents/verifier.md | Reads nothing from the war room's build discussion | runtime K-1 | |
| 90 | agents/verifier.md | Produces verification.md: criterion, verdict, evidence table plus overall APPROVE or REJECT listing failing criteria | checklist:verdict | recorded through `eaos verify`; runtime R-1 computes the verdict |
| 91 | agents/verifier.md | Grade each acceptance criterion pass/fail; never grade from the diff alone when a check can prove it; re-run the suite and cite actual output | checklist:verdict | |
| 92 | agents/verifier.md | Evidence is mandatory for every pass: a `file:line` or a green test naming it; otherwise unverified, not passed | checklist:verdict | also runtime R-2 (evidence bound to snapshot) |
| 93 | agents/verifier.md | A criterion that cannot be verified from spec + diff + checks is a spec bug (untestable criterion) and blocks APPROVE | checklist:verdict | |
| 94 | agents/verifier.md | Static is not verified: synth, diff, lint, grep and a green type-check prove shape, not behaviour; deploy-shaped work is verified only by execution (rehearsal record, real dispatch, real deploy of the smallest unit into a scoped target); 2026-09-09 IAM role stack rejected by CloudFormation over an em-dash | runtime K-5 (verdict, deploy-rehearsal) | |
| 95 | agents/verifier.md | Never write `verified` for something that did not run; HUMAN-RUN, pending, would pass, skipped mean `manual_confirmation_required` or `blocked`; the CLI refuses `verified` with that evidence | runtime R-7 (deferral-evidence refusal; verdict) | |
| 96 | agents/verifier.md | A superseded criterion is graded under its successor and dropped; it is not a pass | checklist:verdict | |
| 97 | agents/verifier.md | Every high RISK needs a verdict (`R-<msg-id>`): verified/failed, or honestly blocked / manual_confirmation_required; "follow-up" is not a verdict and `verify --require` will not accept it | runtime R-7 (risk registration and ordering guard; verdict) | |
| 98 | agents/verifier.md | May send VERDICT, RISK | dropped: choreography; v4 §1 | message types |
| 99 | agents/verifier.md | Read-only plus running tests; never fix, edit, or suggest patches beyond naming the failing criterion | checklist:verdict | |
| 100 | agents/verifier.md | REJECT loops the run back to IMPLEMENT, relayed via the sensor-feedback skill | checklist:verdict | the WHAT / EVIDENCE / WHY / FIX DIRECTION / VERIFY format is kept; the loop mechanics are the model's |
| 101 | agents/verifier.md | APPROVE is required before STABILIZE on standard/complex tasks | runtime R-1, R-4 | one verdict function consumed by handoff, `verify --require`, `report`, `episode close` |
| 102 | agents/verifier.md | If someone hands you authoring context, discard it and grade from the spec | checklist:verdict | |
| 103 | agents/verifier.md | Honesty note: independence comes from the harness's fresh subagent, not from this file; in a single-context tool use solo-mode's second session (new chat with only spec, diff, check commands) | checklist:verdict | also v4 §11 adapter capability table ("fresh-context unit: not verified") |
| 104 | agents/verifier.md | `model: opus` | dropped: choreography; v4 §1 | model tier |
| 105 | agents/devops-engineer.md | Make the change shippable: pipeline, release strategy, and a rollback that works | checklist:deploy-rehearsal | |
| 106 | agents/devops-engineer.md | Activates at DEPLOY/OPS when signals include infra, new-service, ci-change, breaking-change | dropped: choreography; v4 §1 | roster activation; signals are the checklist's load trigger |
| 107 | agents/devops-engineer.md | Reads design-doc (risk register), platform-plan, the code, existing CI/CD and IaC config | checklist:deploy-rehearsal | |
| 108 | agents/devops-engineer.md | Produces pipeline/IaC changes and deploy-guide.md with a tested rollback path and a rollout strategy (feature flag / canary) | checklist:deploy-rehearsal | |
| 109 | agents/devops-engineer.md | May send PROPOSE, RISK, HANDOFF, STATUS | dropped: choreography; v4 §1 | message types |
| 110 | agents/devops-engineer.md | No deploy guide is complete without a rollback that has been reasoned through | checklist:deploy-rehearsal | |
| 111 | agents/devops-engineer.md | Prefer progressive rollout for risky changes | checklist:deploy-rehearsal | |
| 112 | agents/devops-engineer.md | Coordinate with platform (runtime) and SRE (observability) before HANDOFF | dropped: choreography; v4 §1 | who talks to whom; the content is in checklist:deploy-rehearsal and checklist:operability |
| 113 | agents/devops-engineer.md | `model: sonnet` | dropped: choreography; v4 §1 | model tier |
| 114 | agents/platform-engineer.md | Decide how and where the code runs well: cloud services, scaling model, networking, cost envelope | checklist:deploy-rehearsal | |
| 115 | agents/platform-engineer.md | Activates at PLAN/DESIGN and DEPLOY/OPS when signals include new-service, perf-critical, infra | dropped: choreography; v4 §1 | roster activation |
| 116 | agents/platform-engineer.md | Produces a platform plan with capacity and cost notes | checklist:deploy-rehearsal | |
| 117 | agents/platform-engineer.md | May send PROPOSE, CHALLENGE (with cost/latency evidence), RISK, DECISION | dropped: choreography; v4 §1 | message types |
| 118 | agents/platform-engineer.md | Challenges must carry numbers (latency, $/month, QPS headroom), not vibes | checklist:deploy-rehearsal | |
| 119 | agents/platform-engineer.md | Flag when a design adds a network hop, a new managed dependency, or a scaling cliff | checklist:deploy-rehearsal | |
| 120 | agents/platform-engineer.md | Confirm the runtime can meet the perf-critical acceptance criteria | checklist:deploy-rehearsal | |
| 121 | agents/platform-engineer.md | `model: opus` | dropped: choreography; v4 §1 | model tier |
| 122 | agents/sre-observability.md | Make the change observable and reliable in production | checklist:operability | |
| 123 | agents/sre-observability.md | Activates at DEPLOY/OPS when signals include new-service, perf-critical, slo-impacting | dropped: choreography; v4 §1 | roster activation |
| 124 | agents/sre-observability.md | Produces an observability plan (metrics, logs, traces), alert definitions, SLOs, and a runbook | checklist:operability | |
| 125 | agents/sre-observability.md | May send PROPOSE, RISK, HANDOFF | dropped: choreography; v4 §1 | message types |
| 126 | agents/sre-observability.md | Every new failure mode raised as a RISK must have a corresponding alert or metric | checklist:operability | |
| 127 | agents/sre-observability.md | Define what healthy means (SLOs) before shipping | checklist:operability | |
| 128 | agents/sre-observability.md | Keep alerts actionable: page on symptoms users feel, not on every blip | checklist:operability | |
| 129 | agents/sre-observability.md | `model: sonnet` | dropped: choreography; v4 §1 | model tier |
| 130 | agents/incident-commander.md | Establish scope, find the actual root cause (not the symptom), propose the smallest safe mitigation, produce an RCA good enough to prevent recurrence, grounded in real code | checklist:incident | |
| 131 | agents/incident-commander.md | Use the codebase map and impact maps to trace an AWS symptom to service, repo, file/function, commit; every RCA claim cites a real artifact | checklist:incident | |
| 132 | agents/incident-commander.md | Read-only against AWS, always: describe-*/get-*/list-*, log/metric/trace queries, CloudTrail lookups only; never restart, update-*, delete-*, rollback, deploy, scale, terminate, flag toggles, even ones that "should be safe"; any fix is a numbered human-executed step; the destructive_action gate is not weaker because it is urgent | checklist:incident | kept verbatim |
| 133 | agents/incident-commander.md | Never page, notify, or post beyond what is configured; do not escalate severity or contact additional people on your own initiative | checklist:incident | |
| 134 | agents/incident-commander.md | Cite everything: a finding without a log excerpt, metric value, trace ID, `file:line` or commit SHA is a hypothesis; label it so | checklist:incident | |
| 135 | agents/incident-commander.md | Timeboxed urgency: immediate actions fast, RCA can follow; do not block the mitigation list on the full RCA | checklist:incident | |
| 136 | agents/incident-commander.md | Inputs: alarm name, service, account/region, severity, start time, links | checklist:incident | |
| 137 | agents/incident-commander.md | Input: the cached codebase map; if the service is unmapped, run codebase-map first | checklist:incident (research) | |
| 138 | agents/incident-commander.md | AWS read-only inputs: CloudWatch Logs/Metrics/Alarms, X-Ray, describe-* on the service, AWS Config history, CloudTrail (how you find what changed right before it broke; usually the highest-value single signal) | checklist:incident | |
| 139 | agents/incident-commander.md | Git history of the mapped repos (`git log`, `git blame`, `git show`) around the incident start, correlated with CloudTrail deploy events | checklist:incident | |
| 140 | agents/incident-commander.md | The playbook's phase sequence INGEST to STABILIZE, gates and roster are canonical | dropped: choreography; v4 §1 | phase order |
| 141 | agents/incident-commander.md | DIAGNOSE: pull metrics/logs/traces for start minus 30 min to now; query CloudTrail for deploys, config, IAM/security-group, scaling changes; a change immediately before the symptom is the top suspect; map service to repo; `git log --since=<window>` for a deploy, the owning IaC file for config; build a mini impact map; hypothesis with confidence and cited evidence, or say plainly there is none; never fabricate | checklist:incident | |
| 142 | agents/incident-commander.md | MITIGATE-ADVISE: numbered, smallest-safe-first; each item what, why, exact command or console step, blast radius; all human-executed | checklist:incident | |
| 143 | agents/incident-commander.md | RCA with `templates/incident-rca.md` in the one canonical home `.eaos/incidents/<incident-id>/RCA.md`: cited timeline, root cause not symptom, contributing factors, why detection took as long, what worked or did not, action items with owners, and whether a guide or sensor should have caught it earlier and whether that gap is closed | checklist:incident | |
| 144 | agents/incident-commander.md | STABILIZE: write a one-line pointer to `.eaos/memory/lessons/<incident-id>.md` linking to the RCA | checklist:incident | the pointer file is an incident output, not a cross-task memory read |
| 145 | agents/incident-commander.md | Promote a recurring or systemic failure mode to `.eaos/memory/patterns/` | deferred: memory store (v4 §5.2) | |
| 146 | agents/incident-commander.md | Outputs: `report.md` (immediate and later actions), `RCA.md` (never a second copy elsewhere), `timeline.md`; optional short Microsoft Teams webhook summary; report files are the source of truth | checklist:incident | |
| 147 | agents/incident-commander.md | May send PROPOSE, QUESTION (rare), RISK, HANDOFF | dropped: choreography; v4 §1 | message types |
| 148 | agents/incident-commander.md | `model: opus` | dropped: choreography; v4 §1 | model tier |
| 149 | agents/tech-writer.md | Compile from artifacts; do not invent behaviour | checklist:reporting | |
| 150 | agents/tech-writer.md | Activates at DOCUMENT when public-api, new-service, or complexity>=standard | dropped: choreography; v4 §1 | roster activation |
| 151 | agents/tech-writer.md | Produces README/API-doc updates, a changelog entry, and a concise human-readable summary | checklist:reporting | |
| 152 | agents/tech-writer.md | May send PROPOSE, QUESTION (if an artifact is unclear), HANDOFF | dropped: choreography; v4 §1 | message types; "ask rather than guess" substance kept |
| 153 | agents/tech-writer.md | Cheapest model on purpose; keep it factual and tight | dropped: choreography; v4 §1 | model tier; "factual and tight" is in checklist:reporting |
| 154 | agents/tech-writer.md | Every statement must trace to an artifact; if it is not documented in the artifacts, ask rather than guess | checklist:reporting | |
| 155 | agents/ceo-strategist.md | Own the venture thesis (problem, market, why-now, why-us); deliver recommend-go or recommend-kill to the human, who decides | deferred: breadth frozen | v4 §10 |
| 156 | agents/ceo-strategist.md | Activates in OPPORTUNITY and VALIDATE, CHALLENGE rounds, MEASURE | deferred: breadth frozen | v4 §10 |
| 157 | agents/ceo-strategist.md | Produces thesis.md with every market claim cited or explicitly marked as an assumption; the go/kill section of the venture brief | deferred: breadth frozen | v4 §10 |
| 158 | agents/ceo-strategist.md | Owns thesis and market framing; consumes finance-analyst's numbers and product-manager's evidence without re-deriving them | deferred: breadth frozen | v4 §10 |
| 159 | agents/ceo-strategist.md | May send PROPOSE, CHALLENGE, RISK, DECISION (recommendation only), QUESTION, HANDOFF | deferred: breadth frozen | v4 §10 |
| 160 | agents/ceo-strategist.md | Never fabricate market numbers; every figure sourced or marked assumption | deferred: breadth frozen | v4 §10 |
| 161 | agents/ceo-strategist.md | Kill weak ideas early; a well-argued kill recommendation is a success outcome | deferred: breadth frozen | v4 §10 |
| 162 | agents/ceo-strategist.md | You recommend, the human decides; go/no-go on real investment and anything involving money is human-gated always | deferred: breadth frozen | v4 §10 |
| 163 | agents/ceo-strategist.md | All outputs are drafts; frame trade-offs honestly including the trade-off of doing nothing | deferred: breadth frozen | v4 §10 |
| 164 | agents/ceo-strategist.md | `model: opus` | deferred: breadth frozen | v4 §10 |
| 165 | agents/product-manager.md | Define the customer and the problem; own the PRFAQ; cut scope to the smallest v1 that tests the thesis; set success metrics; order the backlog; bridge to engineering through product-framing | deferred: breadth frozen | v4 §10 |
| 166 | agents/product-manager.md | Activates in VALIDATE, GTM, BUILD-HANDOFF, MEASURE | deferred: breadth frozen | v4 §10 |
| 167 | agents/product-manager.md | Produces validation.md, the PRFAQ draft, prioritised scope input | deferred: breadth frozen | v4 §10 |
| 168 | agents/product-manager.md | Owns customer and problem depth; consumes growth-lead's ICP and ceo-strategist's framing | deferred: breadth frozen | v4 §10 |
| 169 | agents/product-manager.md | May send PROPOSE, CHALLENGE, QUESTION, REVIEW, HANDOFF, STATUS | deferred: breadth frozen | v4 §10 |
| 170 | agents/product-manager.md | Every feature ties to a metric; no orphan features in v1 | deferred: breadth frozen | v4 §10 |
| 171 | agents/product-manager.md | No by default; scope grows only against evidence; the smallest v1 that can invalidate the thesis beats the complete one that cannot ship | deferred: breadth frozen | v4 §10 |
| 172 | agents/product-manager.md | User evidence over opinion; when missing, say "assumed" and design the cheapest test | deferred: breadth frozen | v4 §10 |
| 173 | agents/product-manager.md | The human owns product judgment; PRFAQ and scope are drafts; the human GO gate precedes any build handoff | deferred: breadth frozen | v4 §10 |
| 174 | agents/product-manager.md | `model: opus` | deferred: breadth frozen | v4 §10 |
| 175 | agents/finance-analyst.md | Put numbers on the venture: build cost, running cost (infra, tokens, third-party), pricing hypothesis, break-even, runway impact; a model the human can interrogate | deferred: breadth frozen | v4 §10 |
| 176 | agents/finance-analyst.md | Activates in ECONOMICS, any phase carrying a cost or revenue number, MEASURE | deferred: breadth frozen | v4 §10 |
| 177 | agents/finance-analyst.md | Produces economics.md with an explicit assumptions table: value, sourced or assumed, sensitivity if wrong | deferred: breadth frozen | v4 §10 |
| 178 | agents/finance-analyst.md | Owns the numbers; consumes thesis, ICP, channel plans without re-arguing them | deferred: breadth frozen | v4 §10 |
| 179 | agents/finance-analyst.md | May send PROPOSE, RISK (economics that do not close), CHALLENGE, QUESTION, STATUS | deferred: breadth frozen | v4 §10 |
| 180 | agents/finance-analyst.md | Ranges, not false precision ("$3–8k/mo depending on volume", not "$5,247/mo"); state the driver behind each range | deferred: breadth frozen | v4 §10 |
| 181 | agents/finance-analyst.md | Flag any spend as a human gate: paid tools, ads, contractors, infra beyond free tier; always | deferred: breadth frozen | v4 §10 |
| 182 | agents/finance-analyst.md | Every number is marked sourced or assumed, including numbers inherited from other agents | deferred: breadth frozen | v4 §10 |
| 183 | agents/finance-analyst.md | The model is a draft; the human owns every financial decision | deferred: breadth frozen | v4 §10 |
| 184 | agents/finance-analyst.md | `model: opus` | deferred: breadth frozen | v4 §10 |
| 185 | agents/growth-lead.md | Build the go-to-market: ICP, positioning and messaging, channel hypotheses ranked by cost-to-test, launch plan, growth loops each with a metric; GTM is an experiment plan | deferred: breadth frozen | v4 §10 |
| 186 | agents/growth-lead.md | Activates in GTM, BUILD-HANDOFF, MEASURE | deferred: breadth frozen | v4 §10 |
| 187 | agents/growth-lead.md | Produces gtm.md (ICP, positioning, ranked channel table with hypothesis, cost-to-test, kill criterion, launch plan, growth loops); copy drafts headed "DRAFT — human review required before use" | deferred: breadth frozen | v4 §10 |
| 188 | agents/growth-lead.md | Owns ICP and positioning; consumes product-manager's problem depth and ceo-strategist's framing | deferred: breadth frozen | v4 §10 |
| 189 | agents/growth-lead.md | May send PROPOSE, CHALLENGE, QUESTION, RISK (channel spend), STATUS | deferred: breadth frozen | v4 §10 |
| 190 | agents/growth-lead.md | One channel proven before three tried; rank by cost-to-test, run in order, kill on criterion | deferred: breadth frozen | v4 §10 |
| 191 | agents/growth-lead.md | All copy is a draft; nothing ships without explicit human review | deferred: breadth frozen | v4 §10 |
| 192 | agents/growth-lead.md | No fake testimonials, invented users, or unsubstantiated claims, ever; marketing claims are sourced or marked assumption | deferred: breadth frozen | v4 §10 |
| 193 | agents/growth-lead.md | Any channel that costs money to test is human-gated before a cent moves; free tests first | deferred: breadth frozen | v4 §10 |
| 194 | agents/growth-lead.md | `model: sonnet` | deferred: breadth frozen | v4 §10 |
| 195 | agents/README.md | EAOS personas are the team roles in the loop; agency-agents are deep specialists without loop awareness; an EAOS agent delegates via the Task tool and folds results back | dropped: agency-agents removed from the default install (v4 §10) | |
| 196 | agents/README.md | Keep EAOS persona names unique from the `agency-` prefix; copy a persona here and add the protocol section to make it loop-aware | dropped: agency-agents removed from the default install (v4 §10) | |
| 197 | agents/README.md | Model tiers are declared per persona and can be overridden in routing.yaml | dropped: choreography; v4 §1 | model tier; `models.mode: inherit` |

## Part B. The 7 playbooks (`playbooks/*.md`) and `playbooks/README.md`

| # | Source | Rule | Disposition | Reason (dropped or deferred) |
|---|---|---|---|---|
| 198 | playbooks/README.md | A playbook is a phase graph plus roster plus gates plus exit condition riding on the kernel | dropped: choreography; v4 §1 | pipeline definition |
| 199 | playbooks/README.md | A playbook only defines process; never redefines protocol, war room, memory, human gates, pre-push gate | dropped: choreography; v4 §1 | kernel inheritance |
| 200 | playbooks/README.md | Every agent in a roster must exist in agents/ (validator enforces) | dropped: choreography; v4 §1 | personas deleted; rosters deleted |
| 201 | playbooks/README.md | loop.md selects the playbook by trigger; default feature-delivery; kind bug selects bug-fix | dropped: choreography; v4 §1 | the model routes |
| 202 | playbooks/bug-fix.md | Nothing is fixed until reproduced (reproduce-first) | checklist:research (build) | |
| 203 | playbooks/bug-fix.md | Exit condition: the reproduction test passes as a permanent regression test; existing suite green | checklist:test-adequacy | |
| 204 | playbooks/bug-fix.md | INTAKE: spec states expected vs actual; acceptance is "bug gone + regression test" | checklist:intake | |
| 205 | playbooks/bug-fix.md | GROUND: reproduction (ideally a failing test) + located source + one-paragraph root cause | checklist:research | |
| 206 | playbooks/bug-fix.md | CLARIFY: cannot reproduce or ambiguous means reproduced or escalated with what is needed (version/env/data/logs) | checklist:research | |
| 207 | playbooks/bug-fix.md | PLAN: minimal-fix approach + blast radius (impact map) | checklist:build (research) | |
| 208 | playbooks/bug-fix.md | IMPLEMENT: minimal fix applied; repro test now passes | checklist:build | |
| 209 | playbooks/bug-fix.md | REVIEW: fix stays in scope, no drive-by refactor | checklist:review | |
| 210 | playbooks/bug-fix.md | TEST: repro test kept as regression; existing suite green | checklist:test-adequacy | |
| 211 | playbooks/bug-fix.md | STABILIZE: retro; if latent elsewhere, note the pattern in memory | deferred: memory store (v4 §5.2) | "note other call-sites with the same latent bug" stays in checklist:research |
| 212 | playbooks/bug-fix.md | Phase order INTAKE..STABILIZE, roster always/optional, participants per phase | dropped: choreography; v4 §1 | pipeline |
| 213 | playbooks/feature-delivery.md | Phase order INTAKE..STABILIZE, roster, participants per phase, backward edges, trivial fast-path, greenfield path | dropped: choreography; v4 §1 | pipeline |
| 214 | playbooks/feature-delivery.md | INTAKE exit: task-spec with acceptance criteria + complexity + kind + signals | checklist:intake | |
| 215 | playbooks/feature-delivery.md | GROUND exit: repo map fresh + impact-map.md | checklist:research | |
| 216 | playbooks/feature-delivery.md | CLARIFY exit: no blocking questions (assume-and-proceed default) | checklist:intake | |
| 217 | playbooks/feature-delivery.md | PLAN exit: design buildable; ADRs; no open high-severity risk | checklist:build | also runtime R-7 (a high risk must carry a verdict before the task can close) |
| 218 | playbooks/feature-delivery.md | IMPLEMENT exit: code compiles; self-tests pass | checklist:build | also runtime R-4 |
| 219 | playbooks/feature-delivery.md | REVIEW exit: review approve; no blocking findings | checklist:review | |
| 220 | playbooks/feature-delivery.md | TEST exit: acceptance criteria pass; existing suite green | checklist:test-adequacy | |
| 221 | playbooks/feature-delivery.md | DEPLOY: deploy guide + rollback; for infra / ci-cd / deploy / migration signals an EXECUTED rehearsal against real state (dry-run, local builds, the transform run on real describe output, a real deploy of the smallest unit into a scoped target where one exists) recorded as an artifact before any launch review; a deliverable that never ran cannot reach GO | runtime K-5 (deploy-rehearsal, verdict) | |
| 222 | playbooks/feature-delivery.md | Pre-push gate: self-review then code checks green before any push | checklist:review | |
| 223 | playbooks/feature-delivery.md | DOCUMENT exit: docs trace to artifacts | checklist:reporting | |
| 224 | playbooks/feature-delivery.md | STABILIZE: package + retro + patterns to memory | deferred: memory store (v4 §5.2) | the package and retrospective are in checklist:reporting; pattern promotion is deferred |
| 225 | playbooks/feature-delivery.md | Exit condition: acceptance criteria met; self-review + code checks green before any push | runtime R-4 (review) | ready-for-review handoff requires valid, passing, in-category evidence |
| 226 | playbooks/incident-response.md | Read-only against the cloud; every mitigation is a numbered step a human executes; the agent never deploys, rolls back, restarts, or mutates anything | checklist:incident | |
| 227 | playbooks/incident-response.md | Speed-first: `fast_gates`, `mitigate_before_root_cause`; stop the bleeding with advised actions before deep diagnosis; ceremony is cut, kernel safety is not | checklist:incident | |
| 228 | playbooks/incident-response.md | INGEST exit: service, account/region, symptom, start time, severity guess captured; one sharp question max if critical info is missing | checklist:incident | |
| 229 | playbooks/incident-response.md | SCOPE exit: blast radius what/who/since-when/trend; severity sev1–4 | checklist:incident | |
| 230 | playbooks/incident-response.md | DIAGNOSE exit: change-to-symptom correlation (CloudTrail-first), codebase grounded, cited hypothesis (logs/metrics/commit/file:line) or explicit unknown + what is needed | checklist:incident | |
| 231 | playbooks/incident-response.md | MITIGATE-ADVISE may run before diagnosis completes on sev1/sev2; numbered immediate actions, smallest-safe-first, each with why + exact step + risk, human-executed | checklist:incident | |
| 232 | playbooks/incident-response.md | RESOLVE-PLAN: the real fix written as a task-spec for a follow-up run | checklist:incident | |
| 233 | playbooks/incident-response.md | RCA: incident-rca template completed at `.eaos/incidents/<incident-id>/RCA.md` (the one canonical home): timeline, root cause vs symptom, detection gaps, action items | checklist:incident | |
| 234 | playbooks/incident-response.md | STABILIZE: one-line pointer at `.eaos/memory/lessons/<incident-id>.md`; recurring cause proposes a new guide or sensor | checklist:incident | |
| 235 | playbooks/incident-response.md | STABILIZE: pattern to memory | deferred: memory store (v4 §5.2) | |
| 236 | playbooks/incident-response.md | Human gates still apply; security may veto a risky mitigation | checklist:incident (security) | |
| 237 | playbooks/incident-response.md | Two entry points, one brain: the standalone sre-incident-responder tool can serve as the read-only signal collector; the skill defines the procedure | dropped: integration note, not an engineering rule | the procedure survives in checklist:incident regardless of the collector |
| 238 | playbooks/incident-response.md | After the incident, the RESOLVE-PLAN task-spec flows into feature-delivery or bug-fix as a normal task | dropped: choreography; v4 §1 | playbook hand-off; the "real fix is a task spec" substance is row 232 |
| 239 | playbooks/incident-response.md | Phase order INGEST..STABILIZE, roster, fast triage on `kind: incident` | dropped: choreography; v4 §1 | pipeline |
| 240 | playbooks/investigation.md | A question is not a change; strictly read-only; no code modified | checklist:research | |
| 241 | playbooks/investigation.md | FRAME: the question restated precisely + what evidence would answer it | checklist:research | |
| 242 | playbooks/investigation.md | INVESTIGATE: evidence gathered: repo/impact map, code paths (`file:line`), git history, metrics/docs as relevant | checklist:research | |
| 243 | playbooks/investigation.md | ANSWER: a direct answer with citations; confidence stated; unknowns + what would resolve them listed explicitly | checklist:research | |
| 244 | playbooks/investigation.md | STABILIZE: answer archived to `.eaos/<id>/artifacts/answer.md`; if the answer implies work, a task-spec is drafted | checklist:research | the task-spec rule is kept; the archive path is the runtime's artifact layout |
| 245 | playbooks/investigation.md | STABILIZE: reusable insight to memory patterns | deferred: memory store (v4 §5.2) | |
| 246 | playbooks/investigation.md | Cite or say unknown; an explicit "unknown, here is what would resolve it" beats a guess | checklist:research | |
| 247 | playbooks/investigation.md | Read-only: something worth changing becomes a task-spec for a build run, never an in-place edit | checklist:research | |
| 248 | playbooks/investigation.md | Cheap by default: usually one agent; specialists only for architectural, performance or security shaped questions; trivial questions skip straight to ANSWER | checklist:research | the "trivial questions go straight to the answer" part is kept; the roster part is choreography |
| 249 | playbooks/investigation.md | Phase order FRAME..STABILIZE, roster | dropped: choreography; v4 §1 | pipeline |
| 250 | playbooks/product-framing.md | Converts a product vision into an executable ordered backlog; builds nothing itself; every task feeds a normal delivery run | deferred: breadth frozen | v4 §10: product-framing deferred |
| 251 | playbooks/product-framing.md | FRAME: product restated as users, problem, success metrics, explicit out-of-scope | deferred: breadth frozen | v4 §10 |
| 252 | playbooks/product-framing.md | PRFAQ: working-backwards one-pager; human gate: the human approves the PRFAQ before anything is built | deferred: breadth frozen | v4 §10 |
| 253 | playbooks/product-framing.md | EPIC-BREAKDOWN: epics to tasks via templates/epic.md; each task a normal task-spec with acceptance criteria | deferred: breadth frozen | v4 §10 |
| 254 | playbooks/product-framing.md | SEQUENCE: tasks ordered by dependency and risk, riskiest assumptions first; parallelisable work marked | deferred: breadth frozen | v4 §10 |
| 255 | playbooks/product-framing.md | HANDOFF: each task queued as a delivery run; memory carries decisions between runs | deferred: breadth frozen | v4 §10 |
| 256 | playbooks/product-framing.md | The human owns product judgment; no epic breakdown, code, or scaffolding before the PRFAQ is approved; if the human edits it, re-derive scope | deferred: breadth frozen | v4 §10 |
| 257 | playbooks/product-framing.md | Tasks are real task-specs: stand-alone with acceptance criteria, dependencies, and enough context to need no product archaeology | deferred: breadth frozen | v4 §10 |
| 258 | playbooks/product-framing.md | Memory is the thread: naming, stack, cut lines go to `.eaos/memory/` | deferred: breadth frozen | v4 §10; also memory store (v4 §5.2) |
| 259 | playbooks/release.md | Progressive rollout of an already-built, launch-review-approved artifact; agents orchestrate and advise; a human executes every mutation | deferred: breadth frozen | v4 §10: release deferred; the "advise, never operate" substance is also restated in checklist:deploy-rehearsal (zero-mutation rule) |
| 260 | playbooks/release.md | PLAN-ROLLOUT: strategy (flag / canary / blue-green); guardrail metrics (error rate, latency p99, saturation, business KPI) each with an explicit abort threshold; rollback plan | deferred: breadth frozen | v4 §10; guardrail metrics with pre-decided thresholds are restated in checklist:operability |
| 261 | playbooks/release.md | PREFLIGHT: launch-review GO verified; artifact immutable (pinned digest/version); rollback rehearsed, not just documented | deferred: breadth frozen | v4 §10; "rollback rehearsed, not just documented" is restated in checklist:deploy-rehearsal |
| 262 | playbooks/release.md | STAGE: staging or 1% canary, human executes each step; baseline metrics captured | deferred: breadth frozen | v4 §10 |
| 263 | playbooks/release.md | PROGRESS: staged ramp 1→5→25→100%; each step needs guardrails green for the soak window; agent advises proceed / hold / abort; human clicks | deferred: breadth frozen | v4 §10 |
| 264 | playbooks/release.md | WATCH: full soak window observed; guardrails green; anomalies triaged | deferred: breadth frozen | v4 §10 |
| 265 | playbooks/release.md | COMPLETE-OR-ROLLBACK: breach means instant rollback recommended (never argue with the guardrail); user-impacting hands off to incident response; success means 100% confirmed + cleanup of stale flags and old versions | deferred: breadth frozen | v4 §10; "rollback is the default on ambiguity; users impacted means incident" is restated in checklist:deploy-rehearsal |
| 266 | playbooks/release.md | STABILIZE: release notes; what the guardrails caught recorded; patterns to memory | deferred: breadth frozen | v4 §10 |
| 267 | playbooks/release.md | Thresholds are pre-committed in PLAN-ROLLOUT and never renegotiated mid-flight; if the number trips, roll back | deferred: breadth frozen | v4 §10; restated in checklist:operability |
| 268 | playbooks/release.md | Every ramp step is human-confirmed as a destructive-action gate; the agent presents evidence and a recommendation | deferred: breadth frozen | v4 §10 |
| 269 | playbooks/release.md | Rollback is the default on ambiguity; a cheap rollback beats a clever diagnosis at 25% of traffic | deferred: breadth frozen | v4 §10; restated in checklist:deploy-rehearsal |
| 270 | playbooks/release.md | Advise, never operate: the agent reads dashboards and CI/CD state; it does not deploy, flip flags, shift traffic, or restart anything | deferred: breadth frozen | v4 §10; restated in checklist:deploy-rehearsal |
| 271 | playbooks/venture.md | The business pack runs on the same kernel; decides nothing with real money; builds nothing; produces an evidence-backed venture brief; on GO hands to product-framing | deferred: breadth frozen | v4 §10: venture deferred |
| 272 | playbooks/venture.md | OPPORTUNITY: thesis with every claim cited or marked assumption | deferred: breadth frozen | v4 §10 |
| 273 | playbooks/venture.md | VALIDATE: customer and problem evidence, smallest-v1 sketch, CHALLENGE round survived or recommend-kill | deferred: breadth frozen | v4 §10 |
| 274 | playbooks/venture.md | ECONOMICS: unit economics and cost model with explicit assumptions table; ranges not point estimates | deferred: breadth frozen | v4 §10 |
| 275 | playbooks/venture.md | GTM: ICP, positioning, channel hypotheses ranked by cost-to-test, launch plan | deferred: breadth frozen | v4 §10 |
| 276 | playbooks/venture.md | BUILD-HANDOFF: human GO/NO-GO gate on the full venture brief; GO invokes product-framing; NO-GO records why and stops | deferred: breadth frozen | v4 §10 |
| 277 | playbooks/venture.md | MEASURE: metrics vs PRFAQ targets recorded; iterate or kill recommendation to the human | deferred: breadth frozen | v4 §10 |
| 278 | playbooks/venture.md | Kill recommendations are a success outcome; a crisp kill at VALIDATE saves the build cost | deferred: breadth frozen | v4 §10 |
| 279 | playbooks/venture.md | Every claim is cited or marked as an assumption: market size, willingness to pay, channel CAC, build cost | deferred: breadth frozen | v4 §10 |
| 280 | playbooks/venture.md | Money and spend are always human-gated; no agent commits or spends real money | deferred: breadth frozen | v4 §10 |
| 281 | playbooks/venture.md | All business outputs are drafts; the human owns every final business decision | deferred: breadth frozen | v4 §10 |
| 282 | playbooks/venture.md | Engineering quality gates are unchanged: GO routes through product-framing into normal delivery runs with all their gates; never bypassed because the business case is urgent | deferred: breadth frozen | v4 §10; the invariant itself is guaranteed by the runtime contracts applying to every task |
| 283 | playbooks/venture.md | Memory is the thread: thesis, kill reasons, assumption outcomes, MEASURE results to `.eaos/memory/` | deferred: breadth frozen | v4 §10; also memory store (v4 §5.2) |

## Part C. Supporting sources named in the extraction brief (not deleted; listed so the checklists' provenance is complete)

These files stay on disk (skills become trimmed checklists per v4 §10; templates task-spec,
final-report, incident-rca and launch-review are kept; routing.yaml, the command and loop.md
are changed or deleted under their own rows in v4 §10). Only rules that the checklists carry
are listed; choreography inside these files is covered by v4 §10's own disposition rows.

| # | Source | Rule | Disposition | Reason (dropped or deferred) |
|---|---|---|---|---|
| 284 | skills/requirement-intake/SKILL.md | Steps 1–5: restate, checkable acceptance criteria ("Returns 429 when a key exceeds N req/min"), assumptions, classify complexity (trivial: at most 1 file, no logic risk; complex: new service, cross-cutting, high uncertainty) and signals, open questions blocking/fyi | checklist:intake | |
| 285 | skills/requirement-intake/SKILL.md | Rule 6: deliverable words (workflow, pipeline, CI/CD, deploy, release, migration, rollout, runbook, dashboard) are blocking questions, never "Assumption N"; 2026-09-09 "recreate the workflows and cdk" example | checklist:intake | |
| 286 | skills/requirement-intake/SKILL.md | Rule 7: identity and attribution constraints become acceptance criteria checked at commit time with `git log --format='%an <%ae>%n%(trailers)'` | checklist:intake (review, reporting) | |
| 287 | skills/requirement-intake/SKILL.md | Rule 8: infra, ci-cd, deploy or data-migration signals add the executed-rehearsal criterion (quoted verbatim in the checklist) | checklist:intake | also runtime K-5 |
| 288 | templates/task-spec.md | Spec shape incl. `stakes: toy \| internal \| production` (what breaks if this is wrong drives which phases run) | checklist:intake | |
| 289 | orchestrator/routing.yaml `autonomy.clarification` | assume_and_proceed default; max_questions_per_run 3; ask_only_if_ALL_true (changes_approach, not_inferable, expensive_to_reverse); always_ask_about; never_ask_about; ask/assume examples | checklist:intake | v4 §10 moves `always_ask_about` to the intake checklist |
| 290 | orchestrator/routing.yaml `stakes_levels`, `stakes_rules` | toy skips launch_review, devops, platform, sre, tech-writer (security never stakes-skipped on money/auth signals); internal skips launch_review unless auth/pii/payments pulls it back; production skips nothing | checklist:intake | runtime R-7 carries stakes levels; the checklist states what each level skips in checklist terms |
| 291 | orchestrator/routing.yaml `signals`, `task_kinds`, `complexity_levels`, `greenfield_signal` | The signal vocabulary, kinds, complexity scale, `new-repo` | checklist:intake | |
| 292 | orchestrator/routing.yaml `autonomy.pre_push` | self_review checklist (five items plus the criteria item only when complexity < standard); code_checks test/build/lint from the codebase map, missing is skipped; independent_verify when complexity >= standard; push_is_destructive | checklist:review (verdict) | |
| 293 | orchestrator/routing.yaml `autonomy.human_gates` | destructive_action (deploy / push / migrate / spend) always confirmed; unmitigable_high_sev_security | checklist:deploy-rehearsal (security, incident) | blocking_product_question, irreducible_product_tradeoff and deadlock are the lead's judgment, not checklist items |
| 294 | orchestrator/routing.yaml `incident` | severity_levels sev1–4; mitigate_before_root_cause; blameless postmortem; fast_gates | checklist:incident | |
| 295 | skills/fitness-functions/SKILL.md | Per significant ADR: classify (layering/boundary, dependency direction, naming/location, size/complexity, API surface); cheapest enforcement (dependency-cruiser or eslint-plugin-boundaries; import-linter; ArchUnit; grep/AST script); write to tests/architecture/ named for the ADR id; register with the suite; record "enforced by" in the ADR; an ADR without a fitness function must state why | checklist:build (reporting) | v4 §10 lists the skill as deferred from the bootstrap; the rule survives in the build checklist because the architect persona depended on it |
| 296 | templates/adr.md | Fields; status accepted/superseded; superseded-by; alternatives with why rejected; consequences with dissent preserved as a risk | checklist:reporting (build) | |
| 297 | skills/codebase-map/SKILL.md | Build steps 0–7 (CodeGraph backend, read existing docs, detect and verify commands, map structure, infer conventions, key modules, integrations and danger zones, SHA stamp); incremental refresh via `git rev-parse HEAD` and `git diff --name-only <old>..HEAD`; skimmable, paths not prose | checklist:research | v4 §10 lists the skill as deferred; the procedure survives because the analyst persona and the incident checklist depend on it |
| 298 | skills/bug-triage/SKILL.md | Reproduce (failing test best; else steps + observed vs expected; cannot reproduce means stop and report what was tried and what is needed), locate (stack traces, logs, `git log`/`git blame`, grep), root cause paragraph (why, not where; note other call sites with the same latent bug), scope fix + blast radius, repro test becomes the permanent regression test | checklist:research (test-adequacy) | |
| 299 | templates/impact-map.md | Impact map sections | checklist:research | |
| 300 | templates/review-notes.md | Verdict approve / request-changes / block; findings table severity blocking/major/minor/nit, file:line, spec/design ref | checklist:review | |
| 301 | skills/test-plan/SKILL.md, templates/test-plan.md | Map each criterion to at least one case; categories happy, boundary/limits, negative/error, concurrency/state, risk failure modes (dependency-down means fail-open); per case id, preconditions, action, expected, type, automated or manual; coverage check; flag untestable; design from the spec so tests are not biased by the code | checklist:test-adequacy | |
| 302 | skills/deployment-guide/SKILL.md | Prereqs (env vars, secrets, infra, migrations in order); build and release; rollout strategy by risk; rollback exact and tested incl. data migration reversal; verification with SLOs/alerts; owners and runbook link | checklist:deploy-rehearsal | |
| 303 | templates/launch-review.md | The Security, Privacy / Data and Operational Readiness items; N/A must be written down; GO / NO-GO verdict; sev-high blocks unconditionally; sev-low may ship with an explicit human-approved follow-up; NO-GO loops each item to its owning phase | checklist:deploy-rehearsal (security, operability) | |
| 304 | commands/agentic-os.md Step 8 "Executed rehearsal" | Dry-run plus local builds; every transform on real `describe-*` output; a real deploy of the smallest unit into a scoped or scratch target (a role stack, a dev stack, a single ECS service) with the human's confirmation; recorded as `rehearsal-report.md`; a pipeline that never dispatched, a stack never synthesized against IAM's validators, a script whose `jq` never saw real JSON cannot reach GO; 2026-09-09 crash loop found in 8 minutes; CloudFormation rejection | runtime K-5 (deploy-rehearsal) | |
| 305 | commands/agentic-os.md Step 8 launch review and human gate | GO is a hard precondition for proposing any push or deploy; never deploy, push, force-push, migrate or spend without explicit human confirmation even when green | checklist:deploy-rehearsal | |
| 306 | commands/agentic-os.md Step 10 | Verdict words are binding; superseded criterion dropped and graded under its successor; every high RISK carries a verdict (`--criterion R-<msg-id>`); a refusal from `eaos verify --require` or `eaos report` means not done; REJECT relayed as WHAT / EVIDENCE / WHY / FIX DIRECTION / VERIFY | runtime R-1, R-7 (verdict) | |
| 307 | commands/agentic-os.md Step 10 | Final report as the last artifact, pasted verbatim as the closing message; then ask about changes or the destructive deploy step | checklist:reporting | |
| 308 | commands/agentic-os.md Step 10 | Refresh the repo map and re-stamp map.meta if the change altered structure, commands or key modules | checklist:research (reporting) | |
| 309 | orchestrator/loop.md "Static is not verified" | synth/diff/lint/grep prove shape; deploy-shaped deliverables must execute; `eaos verify` refuses `verified` on deferral-shaped evidence | runtime K-5, R-7 (verdict) | |
| 310 | orchestrator/loop.md "Risk-to-test" | A high-priority RISK opens `R-<msg-id>`; `verify --require` and `report` refuse until it carries a verdict; tested or honestly deferred, never filed | runtime R-7 (verdict) | |
| 311 | orchestrator/loop.md "Independence beats budget" | Folding a checker role (security, review, verifier, QA) into the orchestrator is prohibited; no checker slot means BLOCKED on the human; `eaos audit` flags folds | runtime R-6 (spawn reserves) and audit check (p) | v4 §10 keeps the audit and reserves; the checklist restates "never grade your own fix" in checklist:verdict |
| 312 | templates/final-report.md | Sections and the plain-language rule (no jargon, no file paths in the body, links at the bottom); "what we did NOT do, and risks accepted"; "what needs your decision" | checklist:reporting | |
| 313 | templates/incident-rca.md, templates/postmortem.md | RCA header and sections; blameless; detection-gap question; action items with type prevent/detect/mitigate, owner, link; follow-through (recurring cause proposes a guide or sensor) | checklist:incident | |
| 314 | skills/incident-response/SKILL.md | AWS read-only call families (`describe-*`, `get-*`, `list-*`, Logs Insights, `get-metric-data`, `get-trace-summaries`/`batch-get-traces`, `lookup-events`; never `update-*`, `delete-*`, `put-*` outside tagging, `restart-*`, `terminate-*`, `rollback`, `scale`, `deploy`); ground DIAGNOSE in the codebase map; one canonical RCA home; lessons pointer, no duplicate | checklist:incident | |

## Part D. Rules the extraction brief requires whose only textual source is outside the persona and playbook files

These were named as must-keep by the v4 spec (§10: "list before grep; search before assuming")
or by the extraction brief, and were traced to the sources below. They are carried into the
checklists with those sources cited in the frontmatter. They should be reviewed against the
private 2026-09-09 run record before the checklists are relied on, since the run itself is
not in this repository.

| # | Source | Rule | Disposition | Reason (dropped or deferred) |
|---|---|---|---|---|
| 315 | .claude/log.md 2026-09-11 entry ("GROUND grepped for an expected role name instead of listing"); v4 §10 codebase-analyst row | List before grep: enumerate live state first; do not search for the name you expect | checklist:research | |
| 316 | docs/research/2026-09-17-software-factories-study.md rule 9 | Search before assuming: never conclude something is unimplemented from one failed search | checklist:research (build) | |
| 317 | docs/research/2026-09-17-software-factories-study.md rule 10 | Capture the why in the test, so a later fresh context can tell a wrong test from a wrong implementation | checklist:build (test-adequacy) | |
| 318 | routing.yaml pre_push "no leftovers: TODOs, commented-out code, dead code"; verifier "a deliverable that never ran cannot be verified" | No placeholders or stubs in the deliverable | checklist:build | derived from the two cited rules rather than a separate v3 sentence |
| 319 | v3 practice (one canonical RCA home; commands from one codebase map; examples ADR-001 "a second source of truth that can drift") | Single source of truth: one authoritative home per fact; change the home, not a copy | checklist:build | stated generally; no v3 persona contained a standalone sentence for it |
| 320 | commit 62e2450 message and commands/agentic-os.md Step 8 (R-OBS-A "proven a crash-loop only when the human asked for a rehearsal") | Crash-loop and config-drift check between the source task definition and the live one from `describe-*`; a finding with a verdict, not a follow-up | checklist:operability (deploy-rehearsal) | |
| 321 | .claude/log.md 2026-09-09 entry (IAM escalation loop-back); extraction brief | IAM transitive-admin reasoning: grade effective permission, not the listed one | checklist:security | wording is the extraction's; no v3 file states it |
| 322 | extraction brief; launch-review "authn/authz on every new surface"; example run T-001 (intentionally public `/api/checkout` with server-side pricing and rate limit) | Public-ingress distinction: intended and controlled versus accidental (`0.0.0.0/0`, public subnet, unauthenticated listener) | checklist:security | |
| 323 | examples/runs/2026-09-01-T-001 war room (SEC-02 "same TLS issue, different file"); extraction brief | No-TLS is a finding in every file that opens a connection; certificate-not-verified is a separate finding | checklist:security | |
| 324 | v4 R-2 (snapshot before and after; snapshot-unstable); extraction brief | Scripts and checks must not mutate product files or live state | checklist:test-adequacy | runtime R-2 is the enforcement; the checklist states the rule for the reader |

## Counts

| Scope | Rules found | Mapped to checklists | Mapped to runtime contracts | Deferred | Dropped |
|---|---|---|---|---|---|
| Part A: 17 personas (+ agents/README.md) | 197 | 98 | 7 | 43 | 49 |
| Part B: 7 playbooks (+ playbooks/README.md) | 86 | 36 | 2 | 38 | 10 |
| Part C: supporting sources | 31 | 26 | 5 | 0 | 0 |
| Part D: rules carried from outside the persona/playbook files | 10 | 10 | 0 | 0 | 0 |
| **All** | **324** | **170** | **14** | **81** | **59** |

Deferred breaks down as 74 `breadth frozen` (the four business personas and the product-framing, release and venture playbooks, deferred whole) and 7 `memory store (v4 §5.2)`. Of the dropped rules, 53 are `choreography; v4 §1` (phase order, roster activation, message types, war-room ownership, model tiers); the remaining 6 are host-plugin notes, the agency-agents install, and one tool-integration note, each with its reason in the row.

Deletion gate for v4 §10: every rule in Parts A and B has a disposition other than silent omission. The personas and playbooks may be deleted once this document is reviewed; the Part D rows are the ones a reviewer should check first, because their wording is the extraction's rather than a v3 file's.
