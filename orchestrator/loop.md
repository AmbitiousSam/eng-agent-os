# EAOS Engineering Loop (state machine)

Each phase has an **entry gate**, **participants** (from `routing.yaml`), and an **exit gate**.
Any phase may route work backward (the iteration loop).

| Phase | Entry gate | Participants | Exit gate |
|---|---|---|---|
| **INTAKE** | task received | requirements (+qa reads) | `task-spec.md` with acceptance criteria + complexity + kind + signals |
| **GROUND** | task touches existing code (not greenfield) | codebase-analyst | repo map fresh + `impact-map.md` written; for bugs, a **reproduction** + root cause |
| **CLARIFY** | open blocking questions exist (incl. ones GROUND surfaced) | analyst/dev/architect → human | no `blocking` questions remain |
| **PLAN/DESIGN** | spec approved | architect + developer (+platform/security if signaled) | design approved as buildable; no open high-sev risk; ADRs written |
| **IMPLEMENT** | design approved | developer (qa writes tests in parallel) | code compiles; self-tests pass; PR description done |
| **REVIEW** | implementation ready | code-reviewer (+security if signaled) | review `approve`; no blocking findings |
| **TEST/QA** | review approved | qa-engineer | acceptance criteria pass; critical paths covered |
| **DEPLOY/OPS** | tests pass | devops + platform + sre (as signaled) | deploy guide with tested rollback path; **project code checks (test/build/lint) green before any push/PR** |
| **DOCUMENT** | feature complete | tech-writer | docs reference real artifacts; quick accuracy check passes |
| **STABILIZE** | all above done | orchestrator | final package assembled; retro + patterns written to memory |

## Backward edges (iteration)
- REVIEW `request-changes` → IMPLEMENT
- TEST/QA bug → IMPLEMENT
- IMPLEMENT finds impact map was wrong (extra files needed) → GROUND (re-localize)
- PLAN risk discovered during IMPLEMENT → PLAN/DESIGN
- CLARIFY answer changes scope → INTAKE (re-spec)
- GROUND surfaces a danger zone → re-run routing (pull security/platform) before PLAN

## Bug sub-flow (kind == bug)
GROUND runs `bug-triage`: **reproduce → locate → root-cause** (a failing test is the ideal
repro). The bug is not "understood" until reproduced; if it can't be reproduced, escalate to
the human. IMPLEMENT applies the **minimal** fix; TEST/QA confirms the repro test now passes
and keeps it as a permanent regression test, then runs the existing suite for collateral.

## Trivial fast-path
`complexity == trivial` → (quick `grep`/read to confirm the one spot) → developer makes change
+ self-review → STABILIZE. No full war room, no specialists. A trivial change still gets a
2-minute localization so it lands in the right place.

## Greenfield path
`greenfield` (new repo, nothing to map) → GROUND is skipped; architect/developer establish the
initial structure, which the codebase-analyst maps at STABILIZE for future tasks.

## Gate enforcement
The orchestrator will not advance a phase until its exit gate is met. If a gate cannot be met
(missing info, hard disagreement, repeated loop > `loop_guard.max_same_issue_loops`), it
escalates to the human with a one-paragraph summary of the blocker.
