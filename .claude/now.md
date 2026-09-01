# Now (as of 2026-07-13 session end)

**State:** clean, all pushed (HEAD 0bbc97f). Wiki live (9 pages). Validator 136/0, CLI tests
17/17, fresh-install → doctor Healthy.

## Next (ranked, trust ladder)
1. **Capture a real run** into examples/runs/ — run `/agentic-os <real task>` on any project,
   hand the `.eaos/T-NNN/` folder over for sanitizing. Still ZERO captured runs; the
   loop-arch diagram is unproven until one exists.
2. **Routing dry-run eval:** 16 cases in evals/routing-golden.yaml per scripts/eval-routing.md.
3. **A/B protocol:** docs/EVAL-PROTOCOL.md — pre-registered bar (beat plain CC on
   defects/criteria at <2x tokens, else simplify).
4. Parked until real-usage friction: compiled prompts, role fusion, phase-checkpointed
   orchestrator, shellcheck in CI (ROADMAP backlog).

## User machine TODO
- Re-run `./setup.sh` (drops legacy /incident /triage /agent-os commands), restart Claude Code.
- Optional: `find ~/.claude/{agents,commands,eaos} -name '*.bak' -delete` after reviewing.
