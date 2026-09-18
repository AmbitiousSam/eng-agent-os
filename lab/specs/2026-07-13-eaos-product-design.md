# EAOS productization — design (2026-07-13)

Decided in brainstorm session. Strategy: **prove, then publish** — personal tool → OSS
adoption → portfolio asset, in that order. Each phase gates the next.

## Identity

- **Name: EAOS.** A name, not an acronym; "Engineering Agentic OS" survives only as the
  README subtitle. Collision-checked: GitHub clean in-category, npm free, PyPI squatted by a
  dead placeholder (use `eaos-cli` or PEP-541 if pip distribution ever matters).
- **Repo:** `eng-agent-os` → **`eaos`** (GitHub auto-redirects, wiki included).
- **Command:** `/agentic-os` → **`/eaos`** — one name for command, CLI binary, state dir,
  brand. `/agentic-os` kept as alias for one release, then removed.
- **Tagline:** *Delegate without dread. The coding-agent OS that refuses to say done without
  evidence.*
- **Positioning:** BMAD gives you a team of prompts; Ruflo gives you a platform; **EAOS gives
  you a gate** — prompts for judgment, exit codes for discipline.

## Wedge

Never-ship-broken × fire-and-forget: hand it a task, come back to an evidence-backed result;
the mechanical gate (`eaos verify --require` / `eaos report` refusal) is what makes the
walking-away safe. Everything else in the repo serves this claim or gets frozen.

## Scope policy

- **Frozen breadth:** venture/business pack, harness templates, product-framing extras stay
  in-repo, marked experimental, zero maintenance promise. Possible future extraction to
  separate repos. Wedge gets all investment.
- **Integration policy (three tiers):**
  1. **Core, zero deps:** gate + verifier + playbooks + personas. Must work bare, everywhere.
  2. **Measured-recommended:** agency-agents, codegraph, ponytail, rtk stay auto-detected
     optionals; promotion to "recommended" happens ONLY via A/B arms (bare vs +integration)
     with pinned versions. No hard dependencies, ever — the wedge claim must survive bare.
  3. **Experimental/personal:** graphify as a GROUND alternative — dogfood only.
- Only new integration class worth scouting: stronger evidence sensors for the verifier
  (e.g. mutation testing), because it deepens the wedge.

## Phase 1 — Personal tool (~4 weeks)

1. Rename lands first (one commit: repo, command, docs, wiki sweep; alias kept).
2. Dogfood: every real task through `/eaos`, no exceptions. One-line friction note per run
   into `.eaos/memory/lessons/`.
3. Weekly `/eaos triage` on the eaos repo itself; friction → fixes.
4. Deliverables: 3–5 sanitized runs in `examples/runs/`, routing eval executed once,
   personal verdict recorded.
- **Gate to Phase 2:** "do I reach for it or around it?" — reach-for-it on ≥80% of real
  tasks. If "around it": simplify (gate-only extraction, Approach B) instead of launching.

## Phase 2 — OSS launch (only on evidence)

Assets, priority order: (1) 30-second asciinema — gate REFUSED → fix → OK; (2) A/B results
table in README (honest numbers, even modest); (3) one browsable captured run; (4) 5-minute
quickstart. Surfaces: Show HN, r/ClaudeAI, r/cursor, awesome-claude-code PR, Claude Code
plugin marketplace. Success: 200★ in 90 days OR 3 unsolicited user reports.

## Phase 3 — Portfolio

Case study assembled from phase 1–2 artifacts. Success: one written case study.

## Kill criterion (standing)

If the pre-registered A/B (docs/EVAL-PROTOCOL.md) shows EAOS does not beat plain Claude Code
on defects/criteria at <2× tokens: pivot to the gate alone (extract `eaos` CLI + verifier
pattern as the product), archive the team layer.

## Competitive context (2026-07)

Ruflo ~59k★ (heavy platform, "overkill" criticism) · BMAD-METHOD (closest: persona team,
md-only, no runtime enforcement) · GitHub spec-kit / OpenSpec / Kiro (spec-first, user
orchestrates) · metaswarm (issue→PR SDLC, multi-CLI) · buildermethods/agent-os (name
collision — reason for the rename) · native Agent Teams (platform absorbing the layer from
below). EAOS's ownable ground: binding exit codes, honest degradation, ops-inclusive
lifecycle, published evidence.
