---
name: design-review
description: >
  Multi-reviewer design board for complex tasks — a structured challenge round on the
  architect's design before any implementation starts. Use at PLAN when complexity == complex.
---

# Design Review Board

A single, bounded challenge round on the design. Three reviewers attack it from distinct
lenses in parallel, the architect answers once, the phase owner decides. Runs at **PLAN**,
only when `complexity == complex`.

## Procedure

1. **Circulate.** The architect distributes the design-doc plus its ADRs to the board.
2. **Review in parallel — three lenses, one verdict each:**

   | Reviewer | Lens | Looking for |
   |---|---|---|
   | security-reviewer | attack surface, data | authn/z boundaries, data classification and flow, new exposure |
   | platform-engineer | cost, scale, runtime | load/cost estimates **with numbers**, capacity limits, operational burden |
   | qa-engineer | testability, observability | every AC verifiable, failure modes observable, test seams exist |

   Each reviewer returns exactly one of:
   - **APPROVE** — proceed.
   - **CONCERNS** — non-blocking; recorded, does not stop the phase.
   - **OBJECT** — blocking; must carry **evidence and a concrete alternative**. An OBJECT
     without both is downgraded to CONCERNS.

3. **Converge.** The architect responds **once per OBJECT** (kernel convergence rule: one
   exchange, then the phase owner decides). No second round, no thread ping-pong.
   **Security retains a hard veto** — a sustained security OBJECT cannot be overridden by
   the phase owner.
4. **Record.** ADRs updated — overruled objections are captured as **dissent-as-risk**, not
   deleted. Board verdict posted to the war room.
5. **Exit.** The board closes only when there are **zero unresolved OBJECTs** (each one
   resolved by design change, or overruled and logged as risk — security excepted).

## Rules

- **Review the design, not the author.** Objections cite the doc, evidence, and an alternative.
- **Lens discipline.** Stay in lane — no security notes from the platform reviewer. Duplicate
  findings across lenses waste the round and dilute accountability.
- **Reserved for complex.** The board adds roughly one phase of latency; simple and standard
  tasks skip it entirely.
