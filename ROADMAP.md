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
- **Trust tier:** independent `verifier` (maker≠checker on the done decision, `pre_push.
  independent_verify`), `fitness-functions` skill (ADRs → enforceable structural tests),
  `sensor-feedback` skill (failures relayed as WHAT/EVIDENCE/WHY/FIX/VERIFY).
- **Product tier:** `product-framing` playbook (`kind: product`: FRAME → PRFAQ human gate →
  epics → sequenced backlog) + prfaq/epic templates; CodeGraph-preferred GROUND with grep
  fallback (`integrations.codegraph`); GitHub Actions CI (`make test` on push/PR).
- **Autonomy tier:** `/triage` command + skill (read-only discovery inbox, never auto-starts),
  `launch-review` governance gate (security/privacy/ORR, GO/NO-GO before ship),
  `memory-consolidation` skill (supersede/merge/prune + index rebuild).
- **Smart parallelism** (scales with complexity; sequential for trivial/small) + **IDE
  adapters** (Cursor/Windsurf-Devin/Codex; same `.eaos/` state across tools).

## Next (evidence + hardening)
1. **Capture real runs** into `examples/runs/` (war room + artifacts + diff) — evidence over claims.
2. **Live-test the adapters** in Cursor/Codex/Devin; tune install paths per tool version.
3. **Wire the PromptDiagnoser + triage schedule** — cron/scheduled task invoking `/triage`;
   run-until-verifiable goals once the verifier has a track record.
4. **Design-review board** for `complex` tasks (multi-reviewer challenge round at PLAN).

## Run — later
5. **Release/experiment playbooks** — progressive rollout, guardrail metrics (human-executed).
6. **Harness templates per topology** — bundles of guides+sensors per service shape (Ashby:
   narrow the variety, deepen the control).
7. **Worktree isolation** for heavy fan-out.

## Horizon — the operating company
14. **Business pack:** CEO/CTO/PM/finance/marketing personas + opportunity→spec→GTM→build→
    measure playbooks on the same kernel. Engineering becomes one division of the same OS.

**Standing rule (the steering loop):** every recurring failure becomes a new guide, sensor,
validator check, or playbook edit. The OS gets its quality from iteration, not prophecy.
