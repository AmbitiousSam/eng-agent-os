# EAOS Playbooks

A **playbook** is a named process the OS can run — a phase graph + a roster + gates + an exit
condition. It rides on the **kernel** (orchestrator, protocol, war room, memory, human gates,
pre-push gate) which is constant across every playbook. Adding a new process = adding one file
here, not modifying the engine.

```
kernel  (constant)         playbooks  (pluggable, this folder)
────────────────────       ──────────────────────────────────
orchestrator               feature-delivery.md   (default)
protocol / war room        bug-fix.md
memory                     incident-response.md  (your SRE project)
human gates                rfc.md / release.md / … (future)
pre-push gate              …
harness (guides+sensors)
```

## Playbook schema (YAML frontmatter)

```yaml
---
name: feature-delivery          # unique id
command: /agentic-os            # how it's invoked (a slash command or "auto")
trigger: "kind == feature OR default"   # when the orchestrator selects it
roster:                         # agents this playbook uses (must exist in agents/)
  always:   [requirements, developer, code-reviewer]
  optional: [codebase-analyst, architect, qa-engineer, security-reviewer,
             devops-engineer, platform-engineer, sre-observability, tech-writer]
phases: [INTAKE, GROUND, CLARIFY, PLAN, IMPLEMENT, REVIEW, TEST, DEPLOY, DOCUMENT, STABILIZE]
inherits_kernel: true           # gets protocol, memory, human gates, pre-push gate for free
exit_condition: "acceptance criteria met; self-review + code checks green"
---
```

The body describes each phase's entry/exit gate and participants — same table style as the
kernel loop runner (`orchestrator/loop.md`).

## Rules
- A playbook **only** defines process (phases/roster/gates). It never redefines the kernel —
  protocol, war room, memory, human gates and the pre-push gate are inherited.
- Every agent named in `roster` must exist in `agents/` (the validator enforces this).
- `orchestrator/loop.md` is the **runner**: it selects a playbook (by `trigger`/command) and
  executes its phases under kernel rules.
- Default playbook is `feature-delivery`; if a task is `kind: bug`, `bug-fix` is selected.
  `/agentic-os` behavior is unchanged from v1 — the loop was just extracted into a file.
