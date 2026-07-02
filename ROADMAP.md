# EAOS Roadmap — crawl, walk, run

North star (see `AGENT_OS.md` §0b): a complete engineering team as an OS — any task in, a
high-performing org's lifecycle out. Kernel is constant; capability grows as playbooks,
guides, and sensors.

## Done (v1 → v2)
- **Kernel:** orchestrator, protocol (sole-writer war room + relay), memory, human gates,
  clarify-only-when-blocking, pre-push gate (self-review → project code checks).
- **Playbooks:** runner + registry; `feature-delivery`, `bug-fix`, `incident-response`
  (read-only/advisory, with `/incident`), `investigation` (`kind: question`).
- **13 personas** incl. codebase-analyst (GROUND: repo map + impact map) and incident-commander.
- **Mechanical enforcement:** `validate-eaos.py` (routing↔personas↔playbooks↔commands↔
  templates cross-checks), `eaos-doctor.sh`, Makefile, pre-push hooks (repo + per-project).
- **Companion tool:** `sre-incident-responder` (standalone read-only diagnosis; shares the
  incident brain).

## Crawl — make the build slice *trustworthy* (next)
1. **Architecture fitness functions** — architect emits enforceable structural tests with ADRs;
   design becomes a computational sensor, not prose.
2. **Sensor fix-instructions** — failing checks return LLM-optimized "how to self-correct"
   output, not just red.
3. **Independent verifier** — a no-authoring-memory subagent grades the done-condition
   (maker≠checker for the stop decision).
4. **Capture real runs** into `examples/runs/` (war room + artifacts + diff) — evidence over claims.
5. **CI:** GitHub Actions running `make test` on push.

## Walk — feel like an org, not a coder
6. **Framing front-end** — PRFAQ/one-pager intake for product-shaped asks; design-review board
   gate for `complex` tasks.
7. **Launch review** — security/privacy/operational-readiness checklist gate before ship.
8. **Context upgrade** — CodeGraph as GROUND backend + `codegraph affected` for scoped
   regression (planned; graceful grep fallback).
9. **Multi-platform installer** — auto-detect Claude Code/Cursor/Windsurf and emit native
   adapters (CodeGraph's installer pattern).

## Run — autonomy + breadth
10. **Loop driver** — scheduled discovery/triage automations feeding the front door; triage
    inbox for the human; run-until-verifiable goals.
11. **Release/experiment playbooks** — progressive rollout, guardrail metrics (human-executed).
12. **Harness templates per topology** — bundles of guides+sensors per service shape (Ashby:
    narrow the variety, deepen the control).
13. **Memory consolidation** — periodic merge/supersede/prune pass + index rebuild.

## Horizon — the operating company
14. **Business pack:** CEO/CTO/PM/finance/marketing personas + opportunity→spec→GTM→build→
    measure playbooks on the same kernel. Engineering becomes one division of the same OS.

**Standing rule (the steering loop):** every recurring failure becomes a new guide, sensor,
validator check, or playbook edit. The OS gets its quality from iteration, not prophecy.
