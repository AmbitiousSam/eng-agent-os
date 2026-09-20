# eng-agent-os (EAOS)

**What:** Engineering Agentic OS, v4. A small layer for coding agents. The model leads; EAOS
supplies three things a model cannot give itself and enforces them with a script whose exit codes
are binding: (1) working state that outlives a context (board, goals, `.eaos/` on disk), (2) a check
made without the maker's reasoning (clean-context `eaos-checker`, builder-blind scenarios),
(3) evidence that cannot be talked into existence (checks bound to a code snapshot; `verified`
means executed). The HOST (Claude Code, Cursor, Codex) is the agentic OS: models, tools,
permissions, subagents. EAOS does not manage agents. Personal tool for Siva; distribution is last.

**Stack:** markdown + one python3-stdlib script. No third-party deps.

**Layout (three folders):**
- `eaos/` the product, all the installer copies: `agentic-os.md` (front door, <2000 tokens, gate-enforced),
  `agents/` (eaos-builder, eaos-reader, eaos-checker), `checklists/` (12, on demand, incl. `goal.md`),
  `runtime/` (`eaos` script ~3.9k lines, `eaos-hook.sh`, hook installer, doctor, `routing.yaml`),
  `adapters/` (skill header for Cursor/Codex, capability table), `templates/`.
- `tests/` `bash tests/run.sh` = the whole gate (runtime 195, hooks 96, installer 31, validator 134). Pre-push runs it.
- `lab/` not product: specs, research, review records, `evals/results/` (run scorecard), E0 protocol.
- `install.sh` (curl one-liner -> `~/.eaos-src`), `setup.sh` (`--dry-run`, `--uninstall` removes every version).

**Installed paths:** `~/.claude/commands/agentic-os.md`, `~/.claude/agents/eaos-*.md` (Cursor loads these too),
`~/.agents/skills/agentic-os/SKILL.md` (generated from the front door; Cursor + Codex), `~/.claude/eaos/`,
four hook entries in `~/.claude/settings.json`.

**Repo:** git@github-personal:AmbitiousSam/eng-agent-os.git · MIT · v3 preserved on branch `v3` (release v3.0.0).

## Key decisions
- One entry point: `/agentic-os <anything>`. Fits one chat = task; bigger = goal (`next | status | accept`).
- Two levels, one product: task level and goal level (locked intent contract R-n/A-n, items serve requirements,
  acceptance of the whole by a clean checker). A separate "factory" project was considered and rejected.
- Exit codes are rules, prompt text is a wish. Run-driven only: no runtime change without a real run showing need.
- Hosts own their subagents (v4.5.0): no headless runner, no paste packet. Verify host capability from docs first.
- Spawn budget follows the work (base + 2/unit + 3/goal item + 2 production, ceiling 60); goal-time spawns are
  charged to the item in progress.
- Every view a lead reads must tell one story (gate test `TestWhatTheLeadSeesAgrees`).
- Local gates are the bar; GitHub CI was deleted as outdated.

## Verification
`bash tests/run.sh` · `bash eaos/runtime/eaos-doctor.sh` · before shipping a runtime change, replay audit /
`goal next` / `status --packet` on a COPY of a real `.eaos/` (synergina).
