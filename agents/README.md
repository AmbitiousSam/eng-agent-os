# agents/ — the three boundaries

v4 has no persona roster. These three files exist because a boundary is where tool scope
and a fresh context live, and the evidence says the boundary is what matters, not the
costume (`docs/research/2026-09-17-software-factories-study.md`, section 4).

| File | Boundary | Tools |
|---|---|---|
| `eaos-builder.md` | one build unit, fresh context, hands off through the runtime | read, write, edit, bash |
| `eaos-reader.md` | research or a second opinion; posts to the board, never edits | read-only |
| `eaos-checker.md` | clean-context check; records verdicts with executed evidence | read-only |

Role knowledge lives in `checklists/`, loaded on demand. The 17 v3 personas were
parity-extracted into those checklists before deletion:
`docs/reviews/2026-09-18-parity-extraction.md`.
