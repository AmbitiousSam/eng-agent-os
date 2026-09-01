# eng-agent-os (EAOS)

**What:** Engineering Agentic OS — a prompt-framework that runs software tasks as a
coordinated team of Claude Code subagents (orchestrator + 17 personas + playbooks + kernel),
with a mechanical runtime CLI enforcing the bookkeeping.

**Stack:** Markdown personas/playbooks/kernel (orchestrator/), bash install (setup.sh),
python3-stdlib tooling (scripts/eaos runtime CLI, validate-eaos.py, eval_check.py,
test_eaos.py). No third-party deps except optional pyyaml for validators.

**Repo:** git@github-personal:AmbitiousSam/eng-agent-os.git · wiki: 9 pages live.

## Key decisions
- **One front door:** `/agentic-os` is the ONLY command; /incident, /triage, /agent-os folded
  into its fast triage (2026-07-13).
- **Binding exit codes:** the `eaos` CLI (scripts/eaos → ~/.claude/eaos/bin/eaos) owns task
  ids, war-room appends, spawn budget (12), loop ceilings (3 same-issue / 8 total), gates,
  evidence-mandatory DoD table; `eaos report` refuses on unverified criteria. Judgment
  (routing, convergence, review quality) deliberately stays prompt-enforced.
- **Honest portability:** Claude Code = full team (isolated subagents, tiers, fresh verifier).
  Other IDEs = adapters/solo-mode.md (grounded single agent + second-session verification).
  Sequential persona role-play is banned — ceremony without mechanism.
- **Evidence before building:** ROADMAP's standing rule; A/B protocol pre-registered in
  docs/EVAL-PROTOCOL.md (EAOS must beat plain CC on defects/criteria at <2x tokens or be
  simplified).

## Verification commands
`make test` (shell syntax + validator + eval fixture + 17 CLI unit tests) · `make doctor` ·
fresh-install test: `CLAUDE_HOME=$(mktemp -d) ./setup.sh && CLAUDE_HOME=<same> ./scripts/eaos-doctor.sh`
