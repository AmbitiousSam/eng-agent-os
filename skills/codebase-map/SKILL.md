---
name: codebase-map
description: >
  Build or refresh a repo map: stack, structure, run/test commands, conventions, key modules,
  and danger zones. Cached in .eaos/memory/codebase/. Use at GROUND on existing repos.
---

# Codebase Map

Produce `.eaos/memory/codebase/map.md` (template: `templates/codebase-map.md`).

## Build (first run, or full refresh)
1. **Read what's already written:** README, CONTRIBUTING, CLAUDE.md/AGENTS.md, docs/, ADRs.
2. **Detect stack & commands:** read package manifests (package.json, pyproject.toml, go.mod,
   Cargo.toml, pom.xml…), Makefile, Dockerfile, and CI config. Extract the real
   **build / run / test / lint** commands. Verify a command exists before recording it.
3. **Map structure:** `glob`/`ls` the top 2–3 levels; for each major dir write its one-line
   responsibility. Identify entry points (main, server/routes, CLI, jobs).
4. **Infer conventions:** sample a few representative source + test files — note naming, error
   handling, logging, layering, and the test framework/layout.
5. **Key modules:** list the handful of modules other code depends on + their public interface.
6. **Integrations & danger zones:** external services, DB/migrations, auth, payments, generated
   code, public API surfaces. Tag these so routing can pull specialists.
7. Stamp the current git SHA into `.eaos/memory/codebase/map.meta`.

## Refresh (incremental — preferred)
- Compare current `git rev-parse HEAD` to `map.meta`. If unchanged, reuse the map as-is.
- If changed, `git diff --name-only <old>..HEAD`, and update only the sections covering changed
  areas (commands, structure, affected modules). Re-stamp the SHA.

Keep it skimmable — this is a map, not documentation. Cite paths, not prose.
