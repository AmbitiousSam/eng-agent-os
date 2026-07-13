# EAOS Loop Runner (kernel)

This is the **kernel loop runner**. It does not hardcode one process anymore — it **selects a
playbook** and runs that playbook's phases under kernel rules. The playbooks live in
`playbooks/` (see `playbooks/README.md`). This keeps the engine constant while processes
(feature, bug, incident, rfc, release…) plug in as files.

## How the runner works
1. **Select the playbook** from `routing.yaml > playbooks` by `trigger` (task `kind`) or an
   explicit command (`/agentic-os` → feature-delivery/bug-fix; `/incident` → incident-response…).
2. **Load its phases + roster.** The roster's `always` agents run; `optional` agents activate
   per the conditional signal rules in `routing.yaml`.
3. **Run each phase** with its entry/exit gate. The kernel behaviors below apply to *every*
   playbook — a playbook never redefines them.

## Kernel behaviors inherited by every playbook
- **Protocol & war room** — orchestrator is the sole writer; agents return messages (`protocol.md`).
- **Human gates & clarification policy** — assume-and-proceed default; stop only at the bar
  (`routing.yaml > autonomy`).
- **Pre-push gate** — self-review (maker≠checker) then project code checks, before any push
  (`routing.yaml > autonomy.pre_push`).
- **Memory** — read at PLAN, written at STABILIZE (`.eaos/memory/`).
- **Gate enforcement** — a phase does not advance until its exit gate is met; unmet gates
  (missing info, hard disagreement, loop > `loop_guard.max_same_issue_loops`) escalate to the
  human with a one-paragraph blocker summary.
- **Loop-guard honesty** — `loop_guard`'s ceilings and attempt ledger (`routing.yaml`) are now
  **mechanically enforced** by the `eaos` runtime CLI when installed (`eaos loopback` exit codes
  are binding — a nonzero exit IS the deadlock/ceiling escalation); **prompt-enforced** only in
  the no-CLI fallback, where the orchestrator must write the running loop counter into the war
  room after every backward edge — a written counter is harder to quietly drop than a mental one.
- **Backward edges (iteration)** — any phase may route work backward:
  - REVIEW `request-changes` → IMPLEMENT
  - TEST bug → IMPLEMENT
  - IMPLEMENT finds impact map wrong → GROUND (re-localize)
  - PLAN risk found during IMPLEMENT → PLAN
  - CLARIFY answer changes scope → INTAKE (re-spec)
  - GROUND surfaces a danger zone → re-run routing before PLAN
- **Trivial fast-path** — `complexity == trivial` → quick localize → developer + self-review →
  STABILIZE. No full war room, no specialists.
- **Greenfield path** — nothing to map → GROUND skipped; structure established during PLAN and
  mapped at STABILIZE for future tasks.

## The default process
The default playbook is **`playbooks/feature-delivery.md`** (and **`bug-fix.md`** when
`kind == bug`). These contain the phase tables that used to live in this file — `/agentic-os`
behaves exactly as before; the process was simply extracted into playbooks so new ones (e.g.
`incident-response`) drop in without touching the kernel.

> Adding a process = add a file under `playbooks/` + register it in `routing.yaml > playbooks`.
> The runner and all kernel behaviors above are reused unchanged.

## Loops vs pipelines (kernel design law)

A loop is a **cost with a justification**, never a default. Playbooks are **pipelines** — fixed,
auditable phase sequences — because the process IS knowable upfront. Loops exist only in small
bounded pockets inside them (review loop-back, test-fix, repro attempts), exactly where the
right next action genuinely can't be known in advance. Every such pocket must have all four:
explicit **state** (attempt ledger, not transcripts), an **external ground-truth anchor**
(tests/validator/spec — never the model grading its own trace), a **hard ceiling**
(`loop_guard`), and a **goal anchor** (original acceptance criteria verbatim on every
iteration). Never loop: deterministic transformations, plans knowable upfront, high-stakes
single decisions (single grounded pass + human), or irreversible actions.
