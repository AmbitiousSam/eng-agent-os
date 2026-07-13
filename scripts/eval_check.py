#!/usr/bin/env python3
"""
eval_check.py — schema check for evals/routing-golden.yaml (`make eval`).

This does NOT run the routing eval itself (that's a manual/LLM-judged dry run, see
scripts/eval-routing.md). It just guarantees the fixture file is well-formed and internally
consistent with orchestrator/routing.yaml, so the fixture can't silently drift out of sync
with the routing rules it's meant to test:
  - every case has: task, expected.kind, expected.playbook, expected.roster
  - expected.kind is one of routing.yaml's task_kinds
  - expected.playbook is one of routing.yaml's playbooks
  - every agent in expected.roster is a known agent identifier (routing.yaml models.by_agent)
  - expected.signals (if present) are all declared in routing.yaml's signals list

Exit code 0 = fixture valid; 1 = problems found.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "evals", "routing-golden.yaml")
ROUTING = os.path.join(ROOT, "orchestrator", "routing.yaml")

try:
    import yaml  # type: ignore
except ImportError:
    # Match validate-eaos.py's behavior: degrade, don't fail the whole gate on a missing
    # optional dep. CI installs pyyaml, so the check always runs where it matters.
    print("eval_check: PyYAML not installed — skipping fixture check (pip install pyyaml to enable).")
    sys.exit(0)

errors = []


def read_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    if not os.path.isfile(FIXTURE):
        print(f"MISSING: {FIXTURE}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(ROUTING):
        print(f"MISSING: {ROUTING}", file=sys.stderr)
        sys.exit(1)

    routing = read_yaml(ROUTING) or {}
    fixture = read_yaml(FIXTURE) or {}

    valid_kinds = set(routing.get("task_kinds", []))
    valid_playbooks = set((routing.get("playbooks") or {}).keys())
    # Known agent identifiers: models.by_agent lists every persona the orchestrator can route
    # to (engineering + business + incident-commander + verifier); "orchestrator" itself never
    # appears in a roster.
    by_agent = (routing.get("models") or {}).get("by_agent") or {}
    valid_agents = set(by_agent.keys()) - {"orchestrator"}
    valid_signals = set(routing.get("signals", []))

    if not valid_kinds or not valid_playbooks or not valid_agents:
        errors.append("could not extract task_kinds/playbooks/models.by_agent from routing.yaml "
                       "— has its shape changed?")

    cases = fixture.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append(f"{FIXTURE}: no top-level 'cases' list found")
        cases = []


    for i, case in enumerate(cases):
        where = f"case #{i + 1}"
        if not isinstance(case, dict):
            errors.append(f"{where}: not a mapping")
            continue

        task = case.get("task")
        if not task or not isinstance(task, str):
            errors.append(f"{where}: missing/blank 'task'")
            where = f"case #{i + 1} ({task!r})" if task else where

        expected = case.get("expected")
        if not isinstance(expected, dict):
            errors.append(f"{where}: missing 'expected' block")
            continue

        kind = expected.get("kind")
        if not kind:
            errors.append(f"{where}: missing expected.kind")
        elif kind not in valid_kinds:
            errors.append(f"{where}: expected.kind '{kind}' not in routing.yaml task_kinds")

        playbook = expected.get("playbook")
        if not playbook:
            errors.append(f"{where}: missing expected.playbook")
        elif playbook not in valid_playbooks:
            errors.append(f"{where}: expected.playbook '{playbook}' not in routing.yaml playbooks")

        roster = expected.get("roster")
        if not roster or not isinstance(roster, list):
            errors.append(f"{where}: missing/empty expected.roster")
        else:
            for agent in roster:
                if agent not in valid_agents:
                    errors.append(f"{where}: roster agent '{agent}' not a known agent "
                                  f"(routing.yaml models.by_agent)")

        signals = expected.get("signals")
        if signals:
            if not isinstance(signals, list):
                errors.append(f"{where}: expected.signals must be a list")
            else:
                for sig in signals:
                    if sig not in valid_signals:
                        errors.append(f"{where}: signal '{sig}' not declared in routing.yaml signals")

        complexity = expected.get("complexity")
        if complexity and complexity not in set(routing.get("complexity_levels", [])):
            errors.append(f"{where}: complexity '{complexity}' not in routing.yaml complexity_levels")

    print(f"eval_check: {len(cases)} case(s) checked against {os.path.relpath(ROUTING, ROOT)}")
    if errors:
        print(f"\n{len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("OK — fixture schema and cross-references are valid.")
    sys.exit(0)


if __name__ == "__main__":
    main()
