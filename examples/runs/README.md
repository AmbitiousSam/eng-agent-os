# Captured real runs (evidence)

This folder holds **real** `/agentic-os` runs — the credibility artifact no synthetic example
can substitute. Nothing here should be fabricated.

## How to capture a run
After a real task completes in a project, copy its runtime folder in:

```bash
cp -r <project>/.eaos/T-NNN examples/runs/<short-name>/   # war room + artifacts
git add examples/runs/<short-name> && git commit -m "Capture run: <short-name>"
```

Include (redact anything sensitive first): `warroom.md`, `artifacts/` (spec, impact map,
design, review notes, test plan, verifier verdict), and ideally the final `git diff` as
`diff.patch` plus a 5-line `NOTES.md` — what worked, what the loop caught, what you'd tune.

## Why this matters
- It's the proof behind the README's claims (reviewers asked for exactly this).
- It's the regression baseline: when personas/prompts change, replay a captured task and
  compare behavior.
- Lessons here feed the steering loop — recurring friction becomes a guide/sensor/hint tweak.

*(Empty until real runs are committed — synthetic walkthroughs live in `examples/`, not here.)*
