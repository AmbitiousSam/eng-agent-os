#!/usr/bin/env python3
"""Measure context growth, command re-expansion and model use in Claude Code session
transcripts. Produces the numbers the v4 spec's diagnosis rests on, reproducibly.

Usage: measure_session_context.py <session.jsonl> [<session.jsonl> ...]

Definitions (stated because the conclusions depend on them):
  - Entries are merged across the given files and DEDUPLICATED by `uuid` (falling back to
    `message.id`): a resumed session replays its predecessor's history, so the same entry
    appears in both files.
  - "context" for an assistant entry = input_tokens + cache_read_input_tokens +
    cache_creation_input_tokens from `message.usage`. Cached tokens ARE counted: they are
    part of what the model attended to on that turn, whatever they cost.
  - ENTRY vs RESPONSE. One model response is written as several entries (one per content
    block) that share a `message.id`. uuid-dedup removes replayed entries but does not merge
    these, so entry-level statistics over-weight responses with more blocks. Response-level
    statistics group entries by `message.id`; where the repeated usage records differ, the
    MAXIMUM context is taken (the most complete record of what was attended to).
    Both views are printed; the response level is the one to compare experimental arms on.
  - Entries whose model is `<synthetic>` (host-generated, not a model call) are EXCLUDED
    from every statistic and their count is reported.
  - Expansion sizes are ESTIMATES (characters / 4), not tokenizer measurements.
  - A "command expansion" is a user entry whose text starts with the marker below.
  - A "compaction" is an entry flagged isCompactSummary or subtype compact_boundary.
  - A turn's "origin" is the most recent human-originated entry before it: `command`
    (an expansion), `plain` (other typed text), or `notification` (task notifications).
Only token counts, timestamps, model ids and session ids are printed — no message content.
"""
import json
import statistics
import sys

MARKER = "# You are the EAOS Orchestrator"


def text_of(content):
    if isinstance(content, str):
        return content
    return " ".join(b.get("text", "") for b in content or []
                    if isinstance(b, dict) and b.get("type") == "text")


def main(paths):
    seen, rows, sessions = set(), [], set()
    for fp in paths:
        for line in open(fp, encoding="utf-8"):
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("sessionId"):
                sessions.add(d["sessionId"])
            key = d.get("uuid") or (d.get("message") or {}).get("id")
            if key is None or key in seen:
                continue
            seen.add(key)
            rows.append(d)
    rows.sort(key=lambda d: d.get("timestamp", ""))

    expansions, compactions, ctx = [], 0, []
    origin = "start"
    by_origin = {}
    responses = {}          # message.id -> {"t", "size", "model", "origin"}
    synthetic = 0
    for d in rows:
        m = d.get("message")
        if d.get("isCompactSummary") or d.get("subtype") == "compact_boundary":
            compactions += 1
        if d.get("type") == "user" and isinstance(m, dict):
            txt = text_of(m.get("content")).lstrip()
            if txt.startswith(MARKER):
                expansions.append(len(txt) // 4)
                origin = "command"
            elif txt.startswith("<task-notification>"):
                origin = "notification"
            elif txt and not txt.startswith("<"):
                origin = "plain"
        if d.get("type") == "assistant" and isinstance(m, dict) and m.get("usage"):
            u = m["usage"]
            size = (u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                    + u.get("cache_creation_input_tokens", 0))
            if size:
                ctx.append((d.get("timestamp", "")[:16], size))
            model = m.get("model", "?")
            if model == "<synthetic>":
                synthetic += 1
                if size:
                    ctx.pop()
                continue
            by_origin.setdefault(origin, {}).setdefault(model, 0)
            by_origin[origin][model] += 1
            rid = m.get("id") or d.get("uuid")
            r = responses.setdefault(rid, {"t": d.get("timestamp", "")[:16], "size": 0,
                                           "model": model, "origin": origin})
            r["size"] = max(r["size"], size)

    vals = [c for _, c in ctx]
    print(f"sessions: {sorted(sessions)}")
    print(f"entries after dedup: {len(rows)}; assistant turns with usage: {len(vals)}")
    print(f"command expansions: {len(expansions)}; tokens each (chars/4): "
          f"median {statistics.median(expansions):.0f}; nominal total {sum(expansions):,}")
    print(f"compaction markers: {compactions}")
    print(f"context per turn: first {vals[0]:,}  median {statistics.median(vals):,.0f}  "
          f"max {max(vals):,}  last {vals[-1]:,}")
    print(f"synthetic entries excluded: {synthetic}")
    rs = [r for r in responses.values() if r["size"]]
    rvals = [r["size"] for r in rs]
    print(f"RESPONSE level (grouped by message.id, max usage): {len(rvals)} responses; "
          f"first {rvals[0]:,}  median {statistics.median(rvals):,.0f}  max {max(rvals):,}  "
          f"last {rvals[-1]:,}")
    dec = [(rs[i]["t"][11:], rvals[i - 1], rvals[i]) for i in range(1, len(rvals))
           if rvals[i] < rvals[i - 1]]
    big = [x for x in dec if x[2] < x[1] * 0.6]
    largest = max(dec, key=lambda x: x[1] - x[2]) if dec else None
    print(f"decreases between consecutive responses: {len(dec)} of {len(rvals) - 1}; "
          f"drops >40%: {len(big)}; largest decrease: {largest}")
    r_origin = {}
    for r in rs:
        r_origin.setdefault(r["origin"], {}).setdefault(r["model"], 0)
        r_origin[r["origin"]][r["model"]] += 1
    print("responses by origin and model:")
    for o, models in r_origin.items():
        print(f"  {o}: {models}")
    step = max(1, len(ctx) // 12)
    print("trajectory:", [(t[11:], f"{c // 1000}k") for t, c in ctx[::step]])
    print("ENTRY level, by origin and model:")
    for o, models in by_origin.items():
        print(f"  {o}: {models}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
