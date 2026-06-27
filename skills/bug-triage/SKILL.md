---
name: bug-triage
description: >
  Reproduce, locate, and root-cause a bug before any fix. Use at GROUND when kind=bug.
  Produces a failing repro + a root-cause statement in the impact map.
---

# Bug Triage (reproduce-first)

Never design a fix before the bug is reproduced. Steps:

1. **Reproduce.** Turn the report into a concrete trigger. Best: write a **failing test** that
   captures the wrong behavior. Otherwise, exact repro steps + observed vs. expected. If you
   cannot reproduce, STOP and return a QUESTION/RISK with what you tried and what you need
   (version, env, data, logs) — escalate to the human.
2. **Locate.** Trace from the symptom to the source: stack traces, error messages, logs, recent
   `git log`/`git blame` on the suspect area, and `grep` for the failing path. Narrow to the
   specific function(s)/lines.
3. **Root cause.** Write one paragraph: *why* it happens (not just where). Distinguish the root
   cause from the symptom. Note any other call-sites with the same latent bug.
4. **Scope the fix + blast radius.** What's the minimal change? What could it affect? Record in
   `impact-map.md`.
5. **Hand off** to design/implement with: the failing repro test, the root cause, and the touch
   list. The repro test becomes the permanent **regression test** (it must pass after the fix).

Output goes into the task's `impact-map.md`. The failing test goes into the artifacts/test dir.
