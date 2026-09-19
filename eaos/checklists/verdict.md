---
name: verdict
description: Load when grading whether a task's acceptance criteria and risks are met; the evidence bar, the verdict vocabulary, and what may not be called verified.
sources: [agents/verifier.md, commands/agentic-os.md (Step 10), orchestrator/loop.md (Static is not verified, Risk-to-test), orchestrator/routing.yaml (autonomy.pre_push.independent_verify), adapters/solo-mode.md, docs/specs/2026-09-17-eaos-v4-architecture.md (K-1, K-5, R-1, R-2, R-3, R-7)]
---

# Verdict checklist

## Inputs and independence
- Grade from the requirements (acceptance criteria), the delivered code or artifacts, the project's check commands, observed evidence (check outputs, logs, command results), recorded decisions and unresolved risks.
- No maker transcript and no maker self-review. If authoring context is handed over, discard it and grade from the spec. Evidence is not excluded because the maker found it: a log line is a log line (v4 K-1).
- Independence only holds in a genuinely fresh context. Never simulate a checker in the context that built the code: the host spawns `eaos-checker` as a subagent; a host that cannot gets a new chat given only the spec, the board view for checkers and the check commands.
- Trivial and small work: a brief self-score against the criteria suffices. Standard and complex work: the independent check is required before the task can close.

## Evidence per criterion
- Grade each acceptance criterion separately. Record criterion, verdict, evidence.
- Evidence is mandatory for every pass, not only for fails: a `file:line`, or a green test that names the criterion together with its actual output. A criterion without that is unverified, not passed.
- Never grade from the diff alone when a check can prove it. Re-run the suite yourself and cite the real output.
- Evidence is bound to the code it ran against (command, working directory, snapshot, exit status, output). A snapshot change invalidates all prior check evidence; re-run (v4 R-2, R-3).
- A criterion that cannot be verified from spec, diff and checks is stated as such and marked; that is a spec bug (untestable criterion) and it blocks approval.

## Execution beats static checks
- Static is not verified. `synth`, `diff`, `lint`, `grep` and a green type-check prove shape, not behaviour.
- Anything deploy-shaped (infra, pipeline, migration, role, stack) is `verified` only by execution: the rehearsal record, a real dispatch, a real deploy of the smallest unit into a scoped target. (2026-09-09: an IAM role stack passed 35 criteria, review, security and a launch review; CloudFormation rejected it in the first 30 seconds of the first real deploy over an em-dash in a description string.)

## Verdict vocabulary (binding; the CLI refuses anything else)
- `verified`: the criterion executed and the cited evidence shows it holds.
- `failed`: it executed and does not hold; name what failed.
- `blocked`: it could not be executed here (missing access, environment, data); say what is missing.
- `manual_confirmation_required`: only a human can run it and it has not been run.
- Never write `verified` for something that did not run. "HUMAN-RUN", "pending", "would pass", "skipped", "not run", "superseded" in the evidence means the verdict is `manual_confirmation_required` or `blocked`; `eaos verify` refuses `verified` with that evidence.
- A superseded criterion is dropped and graded under its successor. It is not a pass.

## Scenarios (holdouts the maker never saw)
- One grade per scenario with its OWN evidence: the test or command that exercised that scenario and the observed result. The runtime refuses evidence shared between scenarios.
- Leaning on the maker's tests is allowed only after you broke the code and saw that test fail (mutation check); say which mutation.
- `eaos scenario list <task> --for checker` lists end-to-end expectations written at intake
  from the DISCLOSED requirements and held outside the workspace. Grade every one by
  executing it (`eaos scenario grade <task> S-nnn --verdict ... --evidence "<what you ran, what happened>"`);
  `verify --require` refuses while any is ungraded.
- A scenario that fails is revealed to the maker by the fix and becomes regression coverage;
  it is no longer a holdout. Say so in the report.
- A scenario that encodes a requirement the maker was never given is a spec bug: grade it
  `blocked` with that reason, never `failed`.

## Risks
- Every high risk needs a verdict (`R-<msg-id>`): tested to `verified` or `failed`, or honestly `blocked` or `manual_confirmation_required`. "Follow-up" is not a verdict; `verify --require` and `report` refuse until every high risk carries one. A risk is tested or honestly deferred, never filed.
- A matched verdict name does not prove the evidence addresses the risk (v4 R-7 not certified); say in the evidence how it does.

## Output
- Overall verdict: APPROVE, or REJECT listing the specific failing criteria. A refusal from `eaos verify --require` or `eaos report` means the task is not done.
- Relay a rejection as WHAT / EVIDENCE / WHY / FIX DIRECTION / VERIFY, never a raw dump.
- Never fix, edit or suggest patches beyond naming the failing criterion. Never grade your own fix.
