# Context measurement: the 2026-09-09 real run

Reproducible source for the numbers in the v4 spec's diagnosis (section 2). Only token
counts, timestamps, model ids and session ids appear here; the transcripts are private and
stay on the machine that produced them.

## How to reproduce

```
python3 scripts/measure_session_context.py \
  ~/.claude/projects/<project>/d51e1002-00e4-498d-a790-354c0bfacea1.jsonl \
  ~/.claude/projects/<project>/78da0f1b-487b-4fce-a24c-c12327bbca34.jsonl
```

## Method

- **Sources.** Two Claude Code session files for one project. The second is a resume of the
  first after the first process exited mid-task, and replays its history.
- **Deduplication.** Entries merged across both files and deduplicated by `uuid`, falling
  back to `message.id`. 965 entries remain.
- **Context.** For each assistant entry with usage:
  `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`. Cached tokens are
  counted because they are part of what the model attended to, whatever they cost.
- **Entry level vs response level.** One model response is written as several entries, one
  per content block, sharing a `message.id`. Deduplicating by `uuid` removes replayed
  entries but does not merge these, so entry-level statistics give more weight to
  responses with more blocks. Response-level statistics group by `message.id`; where
  repeated usage records differ, the maximum is taken. **Compare experimental arms at the
  response level.** Both are reported below.
- **Synthetic entries.** Entries whose model is `<synthetic>` are host-generated, not model
  calls. They are excluded from every statistic; one was excluded here.
- **Command expansion.** A user entry whose text starts with the command's first heading.
  Sizes are **estimates** at four characters per token, not tokenizer measurements.
- **Compaction.** An entry flagged `isCompactSummary` or `subtype: compact_boundary`.
- **Origin of a turn.** The most recent human-originated entry before it: a command
  expansion, other typed text, or a background-task notification.

## Results (run 2026-09-17)

| Measure | Entry level | Response level |
|---|---|---|
| Count | 396 entries | 164 responses |
| Context: first | 95,696 | 95,696 |
| Context: median | 314,335 | 318,552 |
| Context: max and last | 627,909 | 627,909 |

| Measure | Value |
|---|---|
| Command expansions | 16 |
| Estimated tokens per expansion | median 6,177; nominal total 99,288 |
| Compaction markers | 0 |
| Decreases between consecutive responses | 7 of 163 |
| Largest decrease | 578,694 to 561,828, about 2.9% |
| Decreases of more than 40% | 0 |

The context **grew overall, not monotonically**: seven small decreases, none consistent
with a compaction or reset.

Trajectory (UTC, thousands of tokens): 12:06 95k, 12:21 137k, 12:28 162k, 12:43 207k,
13:02 256k, 14:06 288k, 14:32 318k, 14:53 363k, 15:26 410k, 15:48 477k, 15:56 504k,
17:20 576k, end 627k.

By origin and model, synthetic entry excluded:

| Origin | opus, entries | fable, entries | opus, responses | fable, responses |
|---|---|---|---|---|
| command expansion | 140 | 0 | 68 | 0 |
| task notification | 0 | 232 | 0 | 86 |
| plain typed text | 0 | 16 | 0 | 6 |
| before the first command | 0 | 8 | 0 | 4 |

## What this does and does not show

Shows: the command was re-expanded 16 times; the lead context never compacted and grew
overall to about 628k; every response that followed a command expansion ran on
`claude-opus-5` and no other response did (68 of 68, and 0 of 96), which matches the `model: opus` pin then present in
the command frontmatter (removed 2026-09-17).

Does not show: any causal effect on quality. The expansions are part of the context, not a
quantity independent of it, so "the context is larger" is not "its causal effect is
larger". How much of the observed degradation came from context size, re-expansion, the
pinned model, forced delegation or coordination overhead is what experiment E0 in the v4
spec is for.

An earlier estimate in this project put re-expansion at about 225k tokens. That figure
multiplied by the size of four files rather than by the expansion actually injected, and is
superseded by the table above.
