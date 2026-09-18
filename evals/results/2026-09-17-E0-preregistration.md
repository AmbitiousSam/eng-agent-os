# E0 pre-registration: two context mechanisms, on EAOS v3 as it stands

Committed BEFORE any run. No participant session sees this file's scoring section or the
hidden checks. Spec: `docs/specs/2026-09-17-eaos-v4-architecture.md` section 12.

## Question

On a multi-message task, how do two context mechanisms affect correctness and cost?

1. **Bootstrap:** the command re-expanded on every message, vs once per context.
2. **Lead lifecycle:** one persistent session, vs a fresh session plus a bounded
   continuation packet after each work unit.

The reset treatment is "fresh session plus bounded continuation", not pure context
deletion: it changes what context is selected as well as how much there is.

This experiment tests EAOS v3 unchanged except for the two fixes already landed (no model
pin; single verdict function). It does not test v4.

## Design

2 x 2, two repeats per cell, eight runs.

| Cell | Bootstrap | Lead |
|---|---|---|
| A | repeated | persistent |
| B | once per context | persistent |
| C | repeated | reset after each unit |
| D | once per context | reset after each unit |

- **Repeated:** every message is sent as `/agentic-os <message>`.
- **Once per context:** the first message in a context is `/agentic-os <message>`; every
  later message in that context is plain text.
- **Persistent:** one session for all eight messages.
- **Reset:** a genuinely new session after each unit. Its first input is the packet, then
  the unit's first message. No adaptive compaction in any cell.
- **Packet:** produced by `scripts/e0_packet.sh <task> <next-unit>` at every unit boundary
  in **all** cells. Reset cells consume it; persistent cells save it unread.

With reset after every unit, the two bootstrap conditions differ only on the second
message of each unit. That is intended: it is what "once per context" means there.

**Run order** (blocked by repeat, seed 20260917): `A1 D1 C1 B1 B2 A2 D2 C2`. The first
block covers all four cells, so a single block is already a complete, if unrepeated, read.

## Task

Base: `pallets/flask` at `d73fa1cdcbd8b1465c151db8924ba58b1dd14e35`, directory
`examples/tutorial` (modules `auth`, `blog`, `db`; templates; a pytest suite). Each run
starts from a fresh identical copy with its own git history and an empty `.eaos/`. Not a
live project.

Four units, two prewritten messages each, sent verbatim and in order. Nothing else is
typed except the packet and, if the run asks a blocking question, the scripted answer
"Use your best judgement and record the assumption."

**Standing constraints, stated in unit 1 message 1 and never repeated by the human:**
no new third-party dependencies; the existing test suite keeps passing; routes that change
or reveal user-owned data use the existing `login_required`; schema changes go in
`schema.sql`.

| Unit | Message 1 | Message 2 |
|---|---|---|
| 1 | Add tags to posts: entered comma-separated on the create and update forms; stored normalized (lowercase, trimmed, de-duplicated); shown under each post on the index. Then the standing constraints. | Also: at most 5 tags per post, each at most 20 characters. Otherwise reject with a flashed error and do not save. |
| 2 | Add a page at `/tag/<name>` listing the posts with that tag, newest first. Tag names on the index link to it. | An unknown tag returns 404, and tag lookup is case-insensitive. |
| 3 | Make delete a soft delete: mark the post deleted instead of removing the row. Deleted posts disappear from the index and tag pages. The author can see and restore them at `/trash`. | Only the author can restore; anyone else gets 403. The update page of a deleted post returns 404. |
| 4 | Add `GET /api/posts` returning non-deleted posts as JSON: id, title, body, author, created as ISO-8601 UTC, and tags as a list. Support `?tag=`. | Rename the user-facing concept from "tags" to "topics" in every template and in the JSON field. Keep `?tag=` working as an alias of `?topic=`. `/tag/<name>` must redirect with 301 to `/topic/<name>`. |

Later units depend on earlier decisions and on constraints stated once, eight messages
earlier. That is the property under test.

## Environment isolation

The baseline tag preserves v3's source, not the environment: the global `~/.claude` now
holds v4. E0 therefore runs from a separate Claude Code config directory built by
`scripts/e0_env.sh` (a worktree at `e0-baseline`, installed with `CLAUDE_HOME=~/.claude-e0`,
hooks wired there), and every session is started with
`CLAUDE_CONFIG_DIR=~/.claude-e0 CLAUDE_HOME=~/.claude-e0 claude`.

v3's installed command names literal global paths (`~/.claude/eaos/...`), which now hold
v4, and a separate config directory does not rewrite prose. The script therefore rewrites
those literals in the installed command to the isolated directory and records the adapted
command's sha256. That is the **only** baseline adaptation and it is hashed in the run log.
The script also verifies the isolated CLI is v3 (no `board` verb) and that the hook script
defaults to the isolated CLI.

Before run 1, confirm on the machine that Claude Code loads the isolated command (its
expansion names the isolated path) and record `claude --version`. **A run whose
transcript invokes the global `~/.claude/eaos/bin/eaos` is invalid**, checked in every
transcript alongside the hidden-check path check.

## Controls

Same in every run, and **verified from the transcript, not from configuration**: model and
version (Claude Fable 5.1), effort (medium), permission mode, EAOS commit (recorded per
run), hooks installed, the host's other plugins unchanged, v3's default delegation policy
(not altered for this experiment), no total-budget cap (usage is recorded, never used to
stop a run). Runs are sequential, never concurrent, never in the same directory.

## Hidden checks

Authored and frozen before execution. Stored at `~/.eaos-holdouts/E0/hidden-checks.md`,
outside the repository and outside every participant workspace, mode 0600, never pasted
into a session. They test **disclosed** requirements only.

`sha256 = 9dfd46e73354d23cf523d1a6db2437c7ba55d622d511a3445579f81207fdbff9`

Known limit: the file is on the same machine. A participant that searched the home
directory could read it. Nothing in any prompt references it, and the transcript of every
run is checked for access to that path; a run that touched it is invalid.

Shape, without content: 4 standing checks scored at every snapshot, plus 5, 5, 6 and 7
unit checks. Maximum 39 per run. One unit-4 check is a regression over earlier units.

## Procedure

1. After each unit, retain a snapshot: `git tag e0-u<n>` plus a copy of the working tree.
2. Run `e0_packet.sh` and save its output, in every cell.
3. Grade every snapshot **offline**, after the run, with an executable harness that
   implements exactly the frozen checks. No check result is ever fed back into a run.
4. Anonymise: run directories are renamed to random labels before grading; the
   cell-to-label map is opened after scores are recorded. Scoring is automated and
   pre-registered. It is not blinded human review.

## Measures

Per run, from `scripts/measure_session_context.py` at the **response level**, plus the
subagent transcripts: hidden-check score per snapshot; total tokens (lead plus subagents,
input, output, cache read, cache create reported separately); context per response (first,
median, max); command expansions; compaction markers; wall time; the first snapshot at
which a previously passing check fails.

## Manipulation checks

If a factor did not actually vary, the run did not test it and is **invalid**.

- Expansions: A = 8, B = 1, C = 8, D = 4.
- Reset cells: the first response of units 2 to 4 has at most 1.5x the context of unit
  1's first response, and the run's maximum context is below every persistent run's.
- Persistent cells: zero compaction markers and no drop above 40% between responses. A
  host-initiated compaction is recorded and the run repeated.
- Model: every response ran on the registered model.

## Analysis

Descriptive. With two repeats per cell there are no significance claims. Report each
cell's scores and costs, the two main effects and the interaction as differences of cell
means, and every run individually.

Each of B, C and D is also classified against A per unit with
`scripts/experiment_outcome.py` (two-stage: quality, then cost; every pair mapped; tested).
Invalid runs are excluded before classification and rerun.

## What would change the plan

- B, C or D beats A within the cost bar in both repeats: that mechanism is adopted in v4
  ahead of anything else, and confirmed on a second task before any claim.
- No cell differs, or every cell hits the ceiling: the task was too easy or the mechanisms
  are not the cause. Harden the task; do not proceed to E1 on this evidence.
- Reset cells score lower: the packet is losing information the transcript carried. That
  is a finding about the packet, not a verdict on resetting.
