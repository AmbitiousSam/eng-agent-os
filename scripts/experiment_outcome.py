#!/usr/bin/env python3
"""Outcome classification for paired-arm experiments (v4 spec section 12).

Two stages, then a table. Every (quality, cost) pair maps to exactly one outcome, so no
result is unclassifiable and none matches two rows.

  quality(scores, max_score)  scores = [(treatment, baseline), ...] one pair per repeat
  cost(tokens)                tokens = [(treatment, baseline), ...] one pair per repeat
  classify(...)               -> {"quality", "cost", "outcome"}

An INVALID run (infrastructure failure: host crash, API or rate-limit error, harness
fault) is excluded before classification. A failure caused by the agent's own decisions is
a result, not an invalid run.
"""
QUALITY = ("higher", "equal", "lower", "inconsistent", "ceiling")
COST = ("improved", "comparable", "higher_within_budget", "over_budget")
OUTCOMES = ("win", "mixed", "efficiency_win", "tie", "cost_regression", "loss", "noise",
            "ceiling", "invalid")

COST_IMPROVED_MAX = 0.80      # at most 80% of baseline tokens, in every repeat
COST_COMPARABLE_MAX = 1.20    # within 20% either way
COST_BUDGET_MAX = 2.00        # the pre-registered bar: at most 2.0x baseline, per task


def quality(scores, max_score):
    """ceiling: both arms perfect in EVERY repeat. higher/lower/equal: the same relation
    in EVERY repeat. Anything else is inconsistent — noise means a difference that does
    not hold across repeats, NOT the absence of a difference."""
    if all(t == max_score and b == max_score for t, b in scores):
        return "ceiling"
    rel = {(t > b) - (t < b) for t, b in scores}
    if rel == {1}:
        return "higher"
    if rel == {-1}:
        return "lower"
    if rel == {0}:
        return "equal"
    return "inconsistent"


def cost(tokens):
    """The WORST repeat decides: one over-budget repeat is over budget."""
    order = {name: i for i, name in enumerate(COST)}
    worst = "improved"
    for t, b in tokens:
        r = t / b
        if r <= COST_IMPROVED_MAX:
            cat = "improved"
        elif r <= COST_COMPARABLE_MAX:
            cat = "comparable"
        elif r <= COST_BUDGET_MAX:
            cat = "higher_within_budget"
        else:
            cat = "over_budget"
        if order[cat] > order[worst]:
            worst = cat
    return worst


OUTCOME = {}
for _c in COST:
    OUTCOME[("higher", _c)] = "mixed" if _c == "over_budget" else "win"
    OUTCOME[("lower", _c)] = "loss"                    # cheaper but worse is still a loss
    OUTCOME[("inconsistent", _c)] = "noise"
    OUTCOME[("ceiling", _c)] = "ceiling"               # quality inconclusive; cost reported
OUTCOME[("equal", "improved")] = "efficiency_win"
OUTCOME[("equal", "comparable")] = "tie"
OUTCOME[("equal", "higher_within_budget")] = "cost_regression"   # same quality, >20% dearer
OUTCOME[("equal", "over_budget")] = "loss"


def classify(scores, tokens, max_score, invalid=False):
    if invalid:
        return {"quality": None, "cost": None, "outcome": "invalid"}
    q, c = quality(scores, max_score), cost(tokens)
    return {"quality": q, "cost": c, "outcome": OUTCOME[(q, c)]}
