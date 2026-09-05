# Hook accelerators (M-007, mechanisms.yaml)

**What they do:** three Claude Code hooks — `PreToolUse` (matcher `Task|Agent`),
`PostToolUse` (matcher `Bash`) and `Stop` — all invoke `scripts/eaos-hook.sh`, which
shells out to the real `eaos` CLI so `eaos spawn` and `eaos audit` happen without the
model choosing to run them, and so the session is bound to its task the moment
`eaos task new` runs. Evidence: three real runs measured bookkeeping bypass (spawns/appends
skipped mid-flow) even with prompt-level instructions to run them.

**Accelerator, not authority (spec §11).** The eaos runtime/adapter wrapper stays the
one authoritative mutation path. Hooks are a host-level shortcut that fires it
automatically when the host reliably delivers the event; `eaos audit` remains the final
reconciliation backstop whether or not a hook ran. A hook that claimed to be
fail-closed without proof would be a bigger risk than no hook — see the adapter tests
below.

## Which task a hook acts on (session-scoped)

Every hook payload carries the host's `session_id`. The hook resolves its task through
`eaos session resolve --session <id>`, which reads `.eaos/sessions/<session-id>` — never
the global `.eaos/CURRENT` alone. Two Claude sessions in one checkout therefore cannot
attribute each other's spawns or audit each other's tasks (review round 4, HIGH-4). The
rules live in the CLI in one place and are unit-tested:

1. The session's mapping names an **active** task → that task. (A mapping to a closed
   task is stale: dropped, then continue.)
2. No mapping, and exactly **one** active task in the project → bind the session to it
   and use it. There is nothing else it could be.
3. No `session_id` at all (a host without one) → `.eaos/CURRENT`, only if it names an
   active task **and** it is the only active task.
4. Anything else — zero or two-or-more active tasks with no mapping — → **fail open.**
   Ambiguity never becomes a guess.

How the mapping is created: the `PostToolUse` hook on `Bash` sees `eaos task new` in the
command and the new id in its stdout, and runs `eaos session bind` (mechanical — no model
cooperation). `eaos task new --session <id>` and `$EAOS_SESSION_ID` do the same for
wrappers that know their session. `eaos episode close` re-points every session bound to
the closing task at its parent if that parent is still active (child work done, parent
continues), else removes the mapping. `.eaos/CURRENT` remains as the single-session legacy
pointer (`eaos status` with no id still reads it).

## Fail-open vs. the two fail-closed cases

Every infrastructure problem — no `.eaos/` directory, no installed `eaos` binary,
unparseable hook JSON, no resolvable task, an `eaos` usage/exit-2 error, and **exit 4 =
lock contention** (another eaos process held a lock for the 2-second timeout; nothing was
mutated, and an audit that could not take its snapshot is not evidence of drift) — exits
`0` silently. The accelerator must never become a wall on its own bugs (review round 4,
HIGH-2: before this, a busy lock returned exit 1 and the hook treated it as a policy
verdict). Exactly two cases are intentionally fail-closed, both driven by a real `eaos`
**policy** verdict:

| Event | Trigger | Result |
|---|---|---|
| `PreToolUse` | `eaos spawn` exits 1 **and** names the reason (`BUDGET EXCEEDED` or task `BLOCKED`) | exit 2 — **blocks the tool call**; the ceiling is binding |
| `Stop` | `eaos audit` **completed** and exits 1 (bookkeeping drift found) | exit 2 — tells the **model** to reconcile and continues the turn (never a human wall) |

The `Stop` hook also honors `stop_hook_active`: if the current stop is already a retry
of a previous hook block, it exits 0 immediately rather than blocking again.
`PostToolUse` can never block by contract; a failed bind only means the fallback rules
above apply later.

**Audit under concurrency.** `eaos audit` reads every input it compares (state, war
room, revision journal, runs.jsonl, the parent-tree snapshot) under project lock → task
lock — one coherent snapshot — and computes the checks after releasing both. A legitimate
concurrent mutation can therefore never land between two reads and masquerade as drift
(review round 4, HIGH-1: the reviewer measured 3/100 false stop-blocks; this repo's
harness measured 100/100 before the fix, 0/40 after, `TestAuditCoherentSnapshot`).

## Adapter tests

`scripts/test_eaos_hooks.sh` feeds crafted hook JSON to `eaos-hook.sh` in a real tempdir
project and asserts, scenario by scenario: (a) a spawn is recorded; (b) idempotent under a
repeated `tool_use_id`; (c) an over-budget spawn blocks with `BUDGET EXCEEDED` in stderr;
(d) no task, (e) a non-Task/Agent tool, and a JSON parse failure all fail open silently;
(f) a `Stop` against hand-edited (drifted) state blocks with the audit detail in stderr;
(g) `stop_hook_active` short-circuits even with drift present; (h) the installer merges
idempotently and uninstalls only its own entries; (i) a hostile `subagent_type` carrying
`$(…)`, backticks and quote-breaks never executes (canary file absent) and is stored
literally; (j) a held lock makes both `pretool` and `stop` exit 0 with nothing recorded;
(k) two sessions in one checkout each land on their own task, an unmapped third session
records nothing, and each session's `Stop` audits only its own task; (l) `posttool` binds
the session from `eaos task new` stdout and ignores unrelated Bash calls; (m) the
installer keeps a `0600` settings file `0600`, creates `0600` backups, refuses a malformed
`hooks` shape untouched, and produces a command that executes from a path with spaces.
These are the "adapter-specific tests" spec §11 requires before any fail-closed claim.

## Install / uninstall

`setup.sh` installs the hook *script* to `~/.claude/eaos/bin/eaos-hook.sh` but never
wires it into `settings.json` — that's a real fail-closed gate on your own future tool
calls, so it's opt-in:

```
./scripts/install-eaos-hooks.sh              # merge our three hook entries in
./scripts/install-eaos-hooks.sh --uninstall  # remove only our entries
```

The installer backs up `settings.json` to `settings.json.bak-<ns>-<pid>` (exclusive
create, mode `0600`, so two runs in one second cannot overwrite one backup) before any
real change, **preserves the original file mode** of `settings.json` (a private `0600`
file stays `0600` — review round 4, HIGH-3), shell-quotes the hook path, is idempotent
(detects its own entries by exact command string — re-running after an upgrade adds only
the entries that are missing, e.g. the newer `PostToolUse` one), refuses with the file
untouched if an existing `hooks`/`PreToolUse`/`PostToolUse`/`Stop` value has an
unexpected shape, and never touches an unrelated hook already on the same event.
`eaos-doctor.sh` reports whether the script and the `settings.json` wiring are present —
as a note, never a failure, since EAOS runs fine without either.

## Honest limitation

A host that doesn't deliver `PreToolUse`/`PostToolUse`/`Stop` hook events at all — or a
tool invocation this hook's matcher doesn't cover — gets prompt-level instruction plus
`eaos audit` only, exactly like before M-007 existed. Hooks narrow the bypass window; they
do not close every path to it. And by rule 4 above, a session the hook cannot
unambiguously place gets no acceleration rather than a wrong attribution.
