---
name: memory-consolidation
description: >
  Periodic memory hygiene — merge duplicates, supersede stale decisions, prune dead
  lessons, rebuild the index.
---

# Memory Consolidation

Memory that only grows becomes noise. Run this **monthly or after ~10 tasks** to keep
`.eaos/memory/` small, current, and trustworthy.

## Procedure

1. **decisions/** — Find contradicting or duplicate ADRs. Keep the newer one; mark the
   older one `Status: superseded` with a `Superseded-by: <file>` line. **Never delete**
   a decision — the history of *why we changed our mind* is the valuable part.
2. **patterns/** — Merge near-duplicate patterns into one (keep the clearer writeup,
   fold in examples from the other). Patterns unreferenced in the last **N=10 tasks**
   move to `patterns/_archive/` — out of the index, not out of existence.
3. **lessons/** — Look for recurring lessons (**≥2 occurrences** of the same failure
   class). Recurrence means the lesson isn't being applied: promote it into a pattern,
   or propose a guide/sensor change (this is the steering loop — lessons that repeat
   should become structure). Then compress lessons older than one release into a single
   summary file; keep conclusions, drop the play-by-play.
4. **codebase/** — Check `map.meta`: is the recorded SHA still current for the repo?
   If not, flag the map for a GROUND refresh. Do not refresh it here.
5. **Rebuild `memory/index.md`** — one line per **ACTIVE** decision and pattern only.
   Superseded and archived items do not appear; the index is what every task loads,
   so it earns its size in tokens.
6. **Report.** Write a short consolidation report — what was merged, superseded,
   archived, and any proposed steering changes — to `lessons/consolidation-<date>.md`.

## Rule

Consolidation is **read-mostly and reversible**: it archives, never deletes; it keeps
conclusions, never transcripts. Anything it demotes can be restored from `_archive/`
or a superseded file. If a merge feels lossy, don't merge — flag it for the human.
