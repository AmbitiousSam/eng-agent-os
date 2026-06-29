# Customizing EAOS

Everything you'll want to change lives in a few files. After any change, run
`make validate` (or `python3 scripts/validate-eaos.py`) to confirm the repo is still consistent,
then re-run `./setup.sh` to push changes into `~/.claude`.

## Change which models each role uses (cost ↔ quality)
`orchestrator/routing.yaml` → `models`.
- Remap the three **tiers** (`reasoning` / `coding` / `cheap`) to whatever models you have.
  These are the only place model names live; agents reference the tier, not a model.
- Move a specific role between tiers in `models.by_agent` (e.g. put `code-reviewer` on
  `reasoning` if you want stricter reviews and don't mind the cost).
- Tune `escalate_when` / `deescalate_when` for per-call overrides.

## Change which agents run, and when
`orchestrator/routing.yaml` → `agents`.
- `always`: roles that run on every non-trivial task.
- `conditional`: each role + a `when:` rule over complexity/signals.
- Add a new signal to `signals:` and reference it in a `when:` rule to pull a specialist.

## Change the safety / autonomy gates
`orchestrator/routing.yaml` → `autonomy`.
- `mode: autonomous | supervised` (supervised = confirm each phase).
- `human_gates`: when it must stop for you (product question, deadlock, destructive action…).
- `auto_proceed`: what it never asks permission for.
- `loop_guard.max_same_issue_loops`: how many back-and-forths before it escalates a deadlock.

## Change where runtime state lives
`orchestrator/routing.yaml` → `runtime` (defaults: `.eaos/<id>/` per task, `.eaos/memory/`).

## Add or edit an agent persona
Add `agents/<name>.md` with frontmatter `name / description / model / tools`, then reference its
`name` in `routing.yaml`. `make validate` enforces that routing names ↔ persona names match.

## Add a skill (reusable procedure)
Add `skills/<name>/SKILL.md` with `name` + `description` frontmatter and the steps. Reference any
templates as `templates/<file>.md` — the validator checks they exist.

## Make agency-agents optional / update it
EAOS works **standalone**. `setup.sh` clones agency-agents as an *optional* delegate pool.
- To skip it: comment out the clone block (step 1) in `setup.sh`.
- To update it later: `git -C vendor/agency-agents pull` then re-run `./setup.sh`.
- To avoid persona overload, only the EAOS team is on the loop; agency personas are delegated to
  on demand by the developer (they don't auto-activate).

## Tune memory behavior
`memory/README.md` documents retention. Key rules: store decisions/patterns, not transcripts;
ADRs are append-only and superseded by new ADRs; the codebase map refreshes on git SHA change.
Run a periodic cleanup (see memory README) so it doesn't become a context swamp.

## Validate & ship your changes
```bash
make validate     # structural checks
make doctor       # install + project readiness
./setup.sh        # push changes into ~/.claude
```
