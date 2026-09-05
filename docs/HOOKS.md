# Hook accelerators (M-007, mechanisms.yaml)

**What they do:** two Claude Code hooks — `PreToolUse` (matcher `Task|Agent`) and `Stop`
— both invoke `scripts/eaos-hook.sh`, which shells out to the real `eaos` CLI so
`eaos spawn` and `eaos audit` happen without the model choosing to run them. Evidence:
three real runs measured bookkeeping bypass (spawns/appends skipped mid-flow) even with
prompt-level instructions to run them.

**Accelerator, not authority (spec §11).** The eaos runtime/adapter wrapper stays the
one authoritative mutation path. Hooks are a host-level shortcut that fires it
automatically when the host reliably delivers the event; `eaos audit` remains the final
reconciliation backstop whether or not a hook ran. A hook that claimed to be
fail-closed without proof would be a bigger risk than no hook — see the adapter tests
below.

**Fail-open vs. the two fail-closed cases.** Every infrastructure problem — no
`.eaos/CURRENT`, no installed `eaos` binary, unparseable hook JSON, an `eaos` usage/exit-2
error — exits `0` silently. The accelerator must never become a wall on its own bugs.
Exactly two cases are intentionally fail-closed, both driven by a real `eaos` exit code:

| Event | Trigger | Result |
|---|---|---|
| `PreToolUse` | `eaos spawn <CURRENT>` exits 1 (budget exceeded or task BLOCKED) | exit 2 — **blocks the tool call**; the ceiling is binding |
| `Stop` | `eaos audit <CURRENT>` exits 1 (bookkeeping drift found) | exit 2 — tells the **model** to reconcile and continues the turn (never a human wall) |

The `Stop` hook also honors `stop_hook_active`: if the current stop is already a retry
of a previous hook block, it exits 0 immediately rather than blocking again.

**What `.eaos/CURRENT` is.** `eaos task new` now writes the new task id to
`.eaos/CURRENT` (a project lock); `eaos episode close` removes it once that same task
closes. `eaos status` (no id) reads it too, so a human or the hook script can always
find "the" active task without it being named explicitly.

**Adapter tests.** `scripts/test_eaos_hooks.sh` feeds crafted hook JSON to
`eaos-hook.sh` in a real tempdir project and asserts: a spawn is recorded and idempotent
under a repeated `tool_use_id`; an over-budget spawn blocks with `BUDGET EXCEEDED` in
stderr; a missing `CURRENT`, a non-Task/Agent tool, and a JSON parse failure all fail
open silently; a `Stop` call against hand-edited (drifted) state blocks with the audit
detail in stderr; `stop_hook_active` short-circuits even with drift present. These are
the "adapter-specific tests" spec §11 requires before any fail-closed claim.

**Install / uninstall.** `setup.sh` installs the hook *script* to
`~/.claude/eaos/bin/eaos-hook.sh` but never wires it into `settings.json` — that's a
real fail-closed gate on your own future tool calls, so it's opt-in:

```
./scripts/install-eaos-hooks.sh              # merge our two hook entries in
./scripts/install-eaos-hooks.sh --uninstall  # remove only our entries
```

The installer backs up `settings.json` to `settings.json.bak-<epoch>` before any real
change, is idempotent (detects its own entries by exact command string), and never
touches an unrelated hook already on the same event. `eaos-doctor.sh` reports whether
the script and the `settings.json` wiring are present — as a note, never a failure,
since EAOS runs fine without either.

**Honest limitation.** A host that doesn't deliver `PreToolUse`/`Stop` hook events at
all — or a tool invocation this hook's matcher doesn't cover — gets prompt-level
instruction plus `eaos audit` only, exactly like before M-007 existed. Hooks narrow the
bypass window; they do not close every path to it.
