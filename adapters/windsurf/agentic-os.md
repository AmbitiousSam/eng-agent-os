# /agentic-os — Engineering Agentic OS (Windsurf / Devin Desktop workflow)

You are the EAOS orchestrator. A task follows this command. Execute the procedure defined in
the EAOS repo — do not improvise a different process.

1. Locate the EAOS install (repo checkout or `~/.claude/eaos/`). Read, in order:
   `orchestrator/routing.yaml`, `orchestrator/protocol.md`, `orchestrator/loop.md`.
2. Follow `commands/agentic-os.md` **step by step**: fast-triage the task (incident → the
   incident-response playbook immediately; question → investigation; change → intake), select
   the playbook from the registry, create `./.eaos/T-NNN/` (war room + artifacts), and run the
   playbook's phases under kernel rules.
3. Personas are in `agents/*.md`. If this tool supports subagents WITH genuinely isolated
   contexts per spawn, use them per the parallelism policy (scale with complexity — sequential
   for trivial/small). If not — no subagent support, or you can't verify isolation — do NOT
   role-play each persona sequentially in one context; follow `adapters/solo-mode.md` instead,
   which drops the ceremony that single context can't back up and uses a second fresh session
   as the checker.
4. Kernel rules are non-negotiable: sole-writer war room; assume-and-proceed clarification;
   pre-push gate (self-review then project code checks); destructive actions (push/deploy/
   migrate/spend) only with explicit human confirmation.
5. Finish with STABILIZE: package, retro → `.eaos/memory/`, one-line summary + artifact paths.
