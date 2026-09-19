---
name: research
description: Load for any read-only pass over an existing codebase or live system: repo map, impact map, bug reproduction, or answering a question with evidence.
sources: [agents/codebase-analyst.md, skills/codebase-map/SKILL.md, skills/bug-triage/SKILL.md, playbooks/bug-fix.md, playbooks/investigation.md, templates/impact-map.md, commands/agentic-os.md (Step 2.5), .claude/log.md (2026-09-09 run lessons: "grepped for an expected role name instead of listing"), docs/research/2026-09-17-software-factories-study.md (rule 9)]
---

# Research checklist

## Rules that apply to every research pass
- Read-only. Never edit production code. If the pass reveals something worth changing, the output is a task spec for a build run, never an in-place edit.
- List before grep. Enumerate the live state first (`ls`, directory listings, `list-*` and `describe-*` calls, the actual router table, the actual role list) and read what is there. Do not search for the name you expect to find: a grep for an expected name returns nothing when the real thing is named differently, and nothing looks like absence. (2026-09-09: GROUND grepped for an expected IAM role name instead of listing the roles.)
- Search before assuming. Never conclude that something is unimplemented, absent or unused from one failed search. Try alternate names, locations and the conventions the repo actually uses before writing "not present".
- Ground every claim in a real path or symbol: cite `file:line`, a commit SHA, a metric or a doc. A claim without a citation is a hypothesis; label it as such.
- Cite or say unknown. "Unknown; here is what would resolve it" beats a confident guess. State confidence.
- Cheap by default: a trivial question ("where is X defined?") goes straight to the answer.

## Repo map (durable, cached at `.eaos/memory/codebase/map.md`)
- Read what is already written first: README, CONTRIBUTING, CLAUDE.md or AGENTS.md, docs/, ADRs.
- Detect the stack and commands from package manifests (package.json, pyproject.toml, go.mod, Cargo.toml, pom.xml), Makefile, Dockerfile and CI config. Record the real build, run, test and lint commands and verify each command exists before recording it.
- Map structure two or three levels deep with a one-line responsibility per major directory; identify entry points (main, server routes, CLI, jobs).
- Infer conventions from a few representative source and test files: naming, error handling, logging, layering, test framework and layout.
- List the key modules other code depends on and their public interfaces; list external integrations.
- Tag danger zones: auth, migrations, payments, generated code, public API surfaces. These become signals that pull in the security and other checklists.
- Stamp the git SHA into `.eaos/memory/codebase/map.meta`. Refresh incrementally: if `git rev-parse HEAD` matches, reuse as is; otherwise `git diff --name-only <old>..HEAD` and update only the affected sections, then re-stamp. Refresh after a change that altered structure, commands or key modules.
- If `.codegraph/` exists, prefer `codegraph_context` / `codegraph_search` for structure and `codegraph_impact` / `codegraph_callers` for blast radius; grep, glob and read remain the full fallback and are always the source of the human layer (verified commands, conventions, danger zones), which CodeGraph does not provide.
- Keep it skimmable: paths, not prose.

## Impact map (per task, `templates/impact-map.md`)
- The precise files and symbols to edit; their callers and call sites (blast radius); the tests that cover them; related config and migrations; the danger zones hit; a confidence note separating what is certain from what must be verified during planning.
- If the impact map reveals a danger zone the ask did not mention, add that signal; what the code shows beats how the ask was phrased.

## House pattern
- When the ask names a deliverable class (workflow, pipeline, deploy, release, migration, rollout), check whether this codebase or a sibling repo already demonstrates the house pattern and cite it as the answer in the spec instead of guessing what is meant.

## Bugs: reproduce before fixing
- Turn the report into a concrete trigger. Best: a failing test that captures the wrong behaviour. Otherwise exact repro steps with observed versus expected.
- If you cannot reproduce, stop. Report what you tried and what you need (version, environment, data, logs). Never design a fix for an unreproduced bug.
- Locate: stack traces, error messages, logs, recent `git log` and `git blame` on the suspect area, grep for the failing path. Narrow to the specific functions and lines.
- Root cause in one paragraph: why it happens, not only where. Distinguish root cause from symptom. Note other call sites with the same latent bug.
- Scope the minimal fix and its blast radius into the impact map. The failing test becomes the permanent regression test and must pass after the fix.

## Answering a question
- Restate the question precisely and say what evidence would answer it. Gather evidence: repo or impact map, code paths with `file:line`, git history, metrics or docs as relevant. Answer directly with citations, stated confidence, and the unknowns with what would resolve each. If the answer implies work, draft the task spec.
