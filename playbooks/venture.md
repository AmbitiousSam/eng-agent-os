---
name: venture
command: /agentic-os
trigger: "kind == venture"
roster:
  always: [ceo-strategist, product-manager]
  optional: [finance-analyst, growth-lead, architect]
phases: [OPPORTUNITY, VALIDATE, ECONOMICS, GTM, BUILD-HANDOFF, MEASURE]
inherits_kernel: true
exit_condition: "human go/no-go made on an evidence-backed venture brief; if GO, product-framing backlog started + GTM plan ready"
---

# Playbook: Venture

For venture-shaped asks — "should we build X", "is there a market for…", "how would we
monetize…". The BUSINESS pack (horizon) runs on the **same kernel** as engineering: war room
protocol, memory, human gates, assume-and-proceed clarification. It decides nothing with real
money and builds nothing itself — it produces an evidence-backed venture brief for the human,
and on GO hands build work to `playbooks/product-framing.md` and the engineering playbooks.

| Phase | Entry gate | Participants | Exit gate |
|---|---|---|---|
| **OPPORTUNITY** | venture ask received | ceo-strategist | thesis stated — problem, market, why-now, why-us — with every claim cited or marked assumption |
| **VALIDATE** | thesis stated | product-manager, ceo-strategist | customer + problem evidence gathered, smallest-v1 sketch drafted; CHALLENGE round vs ceo-strategist survived → validated problem, or **recommend-kill** |
| **ECONOMICS** | problem validated | finance-analyst (+architect for build cost) | unit-economics + cost model with explicit assumptions table; ranges not point estimates |
| **GTM** | economics drafted | growth-lead, product-manager | ICP, positioning, channel hypotheses ranked by cost-to-test, launch plan |
| **BUILD-HANDOFF** | venture brief assembled | **HUMAN GO/NO-GO gate on the full venture brief** | GO → invoke `playbooks/product-framing.md` → engineering playbooks build it; exit when the backlog exists. NO-GO → record why to memory, stop |
| **MEASURE** | v1 launched | product-manager, growth-lead, finance-analyst, ceo-strategist | metrics vs PRFAQ targets recorded to `.eaos/memory/`; iterate or kill recommendation delivered to the human |

## Rules
- **Kill recommendations are a success outcome, not a failure.** The playbook exists to make
  go/kill cheap and evidence-backed. A crisp kill at VALIDATE saves the entire build cost.
- **Every claim is cited or marked as an assumption.** Market size, willingness to pay,
  channel CAC, build cost — no unmarked numbers anywhere in the brief.
- **Money and spend are always human-gated.** No agent commits, recommends committing without
  flagging, or spends real money. Go/no-go on real investment belongs to the human, full stop.
- **All business outputs are drafts.** The brief, the PRFAQ, the copy, the model — the human
  owns every final business decision. Agents recommend; the human decides.
- **Engineering quality gates are unchanged.** The business pack feeds the same kernel — GO
  routes through product-framing into normal feature-delivery runs with all their gates. It
  never bypasses them, shortcuts review, or ships "because the business case is urgent".
- **Memory is the thread.** Thesis, kill reasons, assumption outcomes, and MEASURE results go
  to `.eaos/memory/` so the next venture starts smarter, not from zero.
