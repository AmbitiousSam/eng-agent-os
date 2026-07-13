# EAOS Roadmap — crawl, walk, run

North star (see `AGENT_OS.md` §0b): a complete engineering team as an OS — any task in, a
high-performing org's lifecycle out. Kernel is constant; capability grows as playbooks,
guides, and sensors.

## Done (v1 → v2)
- **Kernel:** orchestrator, protocol (sole-writer war room + relay), memory, human gates,
  clarify-only-when-blocking, pre-push gate (self-review → project code checks).
- **Playbooks:** runner + registry; `feature-delivery`, `bug-fix`, `incident-response`
  (read-only/advisory), `investigation` (`kind: question`).
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
- **Autonomy tier:** triage skill (read-only discovery inbox via the front door, never auto-starts),
  `launch-review` governance gate (security/privacy/ORR, GO/NO-GO before ship),
  `memory-consolidation` skill (supersede/merge/prune + index rebuild).
- **Smart parallelism** (scales with complexity; sequential for trivial/small) + **IDE
  adapters** (Cursor/Windsurf-Devin/Codex; same `.eaos/` state across tools).

- **Governance:** design-review board (`complexity == complex`, three lenses, security veto) +
  release playbook (progressive rollout, pre-committed guardrails, human executes every ramp).
- **Harness templates** (`harnesses/`): web-api-service, spa-dashboard, event-processor —
  guide+sensor bundles instantiated at PLAN for new services; worktree-isolation rule for
  complex fan-out.
- **Business pack (horizon reached):** ceo-strategist, product-manager, finance-analyst,
  growth-lead + `venture` playbook (opportunity → validate → economics → GTM → human GO/NO-GO
  → product-framing → measure). Same kernel, same gates — engineering is now one division of
  the OS.

- **`eaos` mechanical runtime CLI** (`scripts/eaos`, installed to `~/.claude/eaos/bin/eaos`):
  task ids, war-room append/sequencing, spawn budget, loop-back ceilings + attempt ledger,
  phase gates, and the DoD table are now computational — exit codes are binding, not sentences
  a model may skip. `eaos report` refuses to assemble the final package on an unverified task.
  Deliberately still prompt-enforced (judgment, not bookkeeping): which playbook/roster to
  route to, the one-exchange convergence rule on disagreements, and review/security quality.

## Backlog — from the v2.0 design review (inventions, ranked)

1. **Compiled prompts** — `agentic-os.md` + all adapters become build artifacts assembled
   from single-source rule fragments (`make build-command`); kills the 7-file parallelism /
   4-file clarification duplication and adapter drift.
2. **Golden eval set** — 15–20 canned tasks with expected kind/playbook/roster; `make eval`
   guards routing behavior against persona/hint edits.
3. **Role fusion by complexity** — standard tasks get one fused `ops` persona (three lenses);
   only complex splits into devops+platform+sre. Same for business pack.
4. **Phase-checkpointed orchestrator** — `phase-state.md` at each boundary; optional fresh
   context per phase (RALF). Bounds orchestrator context growth; makes resume real.
5. Smaller: index-only memory reads enforced · setup checksum warning (repo vs ~/.claude
   drift) · shellcheck + eval in CI · exercise worktree isolation.

## Remaining — requires real usage, not more building
1. **Capture real runs** into `examples/runs/` (folder + guide ready) — evidence over claims.
2. **Live-test the adapters** in Cursor/Codex/Devin; tune install paths per tool version.
3. **Schedule `/agentic-os triage`** in your environment (cron / scheduled task / CI nightly).
4. **Wire the PromptDiagnoser** in `sre-incident-responder` to your LLM provider.
5. **Tune from friction:** every misroute → a hint tweak; every recurring failure → a new
   guide/sensor/validator check. The steering loop is now the roadmap.

**Standing rule (the steering loop):** every recurring failure becomes a new guide, sensor,
validator check, or playbook edit. The OS gets its quality from iteration, not prophecy.
