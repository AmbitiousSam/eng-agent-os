#!/usr/bin/env python3
"""
validate-eaos.py — mechanical consistency checks for the Engineering Agentic OS.

Turns the OS's "operating contract" into enforced invariants so the repo doesn't drift:
  - routing.yaml parses and has the required shape
  - every agent persona has valid frontmatter (name/description/model/tools)
  - every agent referenced by routing (always/conditional/model tiers) actually exists
  - every template referenced by skills/command/agents exists on disk
  - every skill has a SKILL.md with frontmatter
  - the slash command and core files are present

Exit code 0 = all good; 1 = problems found. No third-party deps required
(falls back to a tiny YAML-frontmatter parser if PyYAML is missing).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- minimal YAML loader (prefer PyYAML, fall back for frontmatter) ----------
try:
    import yaml  # type: ignore
    def load_yaml(text): return yaml.safe_load(text)
    HAVE_YAML = True
except Exception:  # pragma: no cover
    HAVE_YAML = False
    def load_yaml(text):
        raise RuntimeError("PyYAML not available")

errors, warnings, checks = [], [], []
def ok(msg): checks.append(msg)
def err(msg): errors.append(msg)
def warn(msg): warnings.append(msg)

def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def frontmatter(text):
    """Return dict of the leading --- ... --- YAML block (best-effort)."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return None
    block = m.group(1)
    if HAVE_YAML:
        try:
            return load_yaml(block) or {}
        except Exception:
            pass
    # tiny fallback: top-level "key:" lines only
    fm = {}
    for line in block.splitlines():
        mm = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if mm:
            fm[mm.group(1)] = mm.group(2).strip()
    return fm

def exists(rel):
    return os.path.exists(os.path.join(ROOT, rel))

# ---------- 1. core files / dirs present ----------
REQUIRED = [
    "commands/agentic-os.md", "orchestrator/routing.yaml", "orchestrator/protocol.md",
    "orchestrator/loop.md", "orchestrator/orchestrator.md", "setup.sh", "README.md",
]
for r in REQUIRED:
    (ok if exists(r) else err)(f"required file: {r}")
for d in ["agents", "skills", "templates", "orchestrator"]:
    (ok if os.path.isdir(os.path.join(ROOT, d)) else err)(f"required dir: {d}/")

# ---------- 2. routing.yaml parses + shape ----------
routing = None
rp = os.path.join(ROOT, "orchestrator/routing.yaml")
if exists("orchestrator/routing.yaml"):
    if not HAVE_YAML:
        warn("PyYAML not installed — routing.yaml structural checks skipped (run: pip install pyyaml)")
    else:
        try:
            routing = load_yaml(read(rp))
            ok("routing.yaml parses")
            for key in ["agents", "models", "autonomy"]:
                (ok if key in routing else err)(f"routing.yaml has '{key}'")
            if "agents" in routing:
                for key in ["always", "conditional"]:
                    (ok if key in routing["agents"] else err)(f"routing.agents has '{key}'")
        except Exception as e:
            err(f"routing.yaml failed to parse: {e}")

# ---------- 3. agent personas: frontmatter + collect names ----------
agent_names = {}
agent_dir = os.path.join(ROOT, "agents")
persona_files = []
if os.path.isdir(agent_dir):
    persona_files = [os.path.join("agents", f) for f in os.listdir(agent_dir)
                     if f.endswith(".md") and f.lower() != "readme.md"]
persona_files.append("orchestrator/orchestrator.md")

for rel in sorted(persona_files):
    if not exists(rel):
        continue
    fm = frontmatter(read(os.path.join(ROOT, rel)))
    if not fm:
        err(f"{rel}: missing YAML frontmatter")
        continue
    for field in ["name", "description", "model", "tools"]:
        if not fm.get(field):
            err(f"{rel}: frontmatter missing '{field}'")
    name = fm.get("name")
    if name:
        if name in agent_names:
            err(f"duplicate agent name '{name}' ({rel} and {agent_names[name]})")
        agent_names[name] = rel
if agent_names:
    ok(f"{len(agent_names)} agent personas with valid frontmatter: {', '.join(sorted(agent_names))}")

# ---------- 4. routing agents must exist as personas ----------
def check_names(names, where):
    for n in names:
        (ok if n in agent_names else err)(f"routing '{where}' references agent '{n}' → persona exists")

if routing and "agents" in routing:
    check_names(routing["agents"].get("always", []), "always")
    check_names(list(routing["agents"].get("conditional", {}).keys()), "conditional")
if routing and isinstance(routing.get("models", {}), dict):
    by_agent = routing["models"].get("by_agent", {})
    check_names(list(by_agent.keys()), "models.by_agent")

# ---------- 4b. playbooks: frontmatter + roster agents exist + registry files exist ----------
playbook_names = set()
pb_dir = os.path.join(ROOT, "playbooks")
if os.path.isdir(pb_dir):
    for f in sorted(os.listdir(pb_dir)):
        if not f.endswith(".md") or f.lower() == "readme.md":
            continue
        rel = f"playbooks/{f}"
        fm = frontmatter(read(os.path.join(ROOT, rel)))
        if not fm:
            err(f"{rel}: missing YAML frontmatter")
            continue
        for field in ["name", "trigger", "roster", "phases"]:
            if fm.get(field) is None:
                err(f"{rel}: frontmatter missing '{field}'")
        if fm.get("name"):
            playbook_names.add(fm["name"])
        roster = fm.get("roster") or {}
        if isinstance(roster, dict):
            for grp in ("always", "optional"):
                for n in roster.get(grp, []) or []:
                    (ok if n in agent_names else err)(f"{rel}: roster '{grp}' agent '{n}' → persona exists")
    if playbook_names:
        ok(f"{len(playbook_names)} playbooks with valid frontmatter: {', '.join(sorted(playbook_names))}")
# registry in routing.yaml must point at real playbook files
if routing and isinstance(routing.get("playbooks"), dict):
    for pname, spec in routing["playbooks"].items():
        f = (spec or {}).get("file")
        if f:
            (ok if exists(f) else err)(f"routing.playbooks['{pname}'].file exists: {f}")

# ---------- 4c-pre. playbook phase-table participants must appear in that playbook's roster ----------
# Catches the release/tech-writer class of bug: a phase table names a persona that was never
# added to the roster block. "orchestrator" is exempt — it's the always-present narrator role,
# never a roster-listed spawnable agent (see scripts/eaos-doctor.sh's own comment on this).
# Requires a real YAML parse: the fallback frontmatter parser can't read nested roster lists,
# so without PyYAML this check would flag every participant as un-rostered (false errors).
if os.path.isdir(pb_dir) and HAVE_YAML:
    for f in sorted(os.listdir(pb_dir)):
        if not f.endswith(".md") or f.lower() == "readme.md":
            continue
        rel = f"playbooks/{f}"
        text = read(os.path.join(ROOT, rel))
        fm = frontmatter(text)
        if not fm:
            continue
        roster = fm.get("roster") or {}
        roster_names = set()
        if isinstance(roster, dict):
            for grp in ("always", "optional"):
                roster_names.update(roster.get(grp, []) or [])
        lines = text.splitlines()
        header_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith("|") and "Participants" in line:
                header_idx = i
                break
        if header_idx is None:
            continue
        cols = [c.strip() for c in lines[header_idx].strip().strip("|").split("|")]
        if "Participants" not in cols:
            continue
        p_col = cols.index("Participants")
        for line in lines[header_idx + 2:]:
            if not line.strip().startswith("|"):
                break
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) <= p_col:
                continue
            for name in re.findall(r"[a-z][a-z-]+", cells[p_col]):
                if name in agent_names and name != "orchestrator" and name not in roster_names:
                    err(f"{rel}: phase-table participant '{name}' not in roster (always/optional)")

# ---------- 4c. command files: referenced personas/skills/playbooks must exist ----------
cmd_dir = os.path.join(ROOT, "commands")
if os.path.isdir(cmd_dir):
    for f in sorted(os.listdir(cmd_dir)):
        if not f.endswith(".md"):
            continue
        rel = f"commands/{f}"
        text = read(os.path.join(ROOT, rel))
        for m in re.finditer(r"agents/([\w-]+)\.md", text):
            (ok if exists(f"agents/{m.group(1)}.md") else err)(f"{rel} references agents/{m.group(1)}.md → exists")
        for m in re.finditer(r"skills/([\w-]+)/SKILL\.md", text):
            (ok if exists(f"skills/{m.group(1)}/SKILL.md") else err)(f"{rel} references skills/{m.group(1)} → exists")
        for m in re.finditer(r"playbooks/([\w-]+)\.md", text):
            (ok if exists(f"playbooks/{m.group(1)}.md") else err)(f"{rel} references playbooks/{m.group(1)}.md → exists")

# ---------- 5. skills have SKILL.md + frontmatter ----------
skills_dir = os.path.join(ROOT, "skills")
if os.path.isdir(skills_dir):
    for d in sorted(os.listdir(skills_dir)):
        sp = os.path.join(skills_dir, d, "SKILL.md")
        rel = f"skills/{d}/SKILL.md"
        if not os.path.isfile(sp):
            err(f"skill '{d}' missing SKILL.md")
            continue
        fm = frontmatter(read(sp))
        if not fm or not fm.get("name") or not fm.get("description"):
            err(f"{rel}: frontmatter missing name/description")
        else:
            ok(f"skill ok: {d}")

# ---------- 6. every referenced template exists ----------
ref_sources = list(persona_files) + ["commands/agentic-os.md"]
for d in (os.listdir(skills_dir) if os.path.isdir(skills_dir) else []):
    ref_sources.append(f"skills/{d}/SKILL.md")
referenced = set()
for rel in ref_sources:
    if exists(rel):
        for m in re.finditer(r"templates/([\w-]+\.md)", read(os.path.join(ROOT, rel))):
            referenced.add(m.group(1))
for t in sorted(referenced):
    (ok if exists(f"templates/{t}") else err)(f"referenced template exists: templates/{t}")

# ---------- 6b. orphan templates: every templates/*.md should be referenced somewhere ----------
templates_dir = os.path.join(ROOT, "templates")
if os.path.isdir(templates_dir):
    referenced_all = set(referenced)
    skip_dirs = {".git", "vendor", "node_modules"}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        rel_dir = os.path.relpath(dirpath, ROOT)
        if rel_dir == "templates" or rel_dir.startswith("templates" + os.sep):
            continue
        for fn in filenames:
            if not (fn.endswith(".md") or fn.endswith(".yaml") or fn.endswith(".yml")):
                continue
            try:
                t = read(os.path.join(dirpath, fn))
            except Exception:
                continue
            for m in re.finditer(r"templates/([\w-]+\.md)", t):
                referenced_all.add(m.group(1))
    for fn in sorted(os.listdir(templates_dir)):
        if not fn.endswith(".md") or fn.lower() == "readme.md":
            continue
        if fn in referenced_all:
            ok(f"template referenced: templates/{fn}")
        else:
            warn(f"orphan template (zero references): templates/{fn}")

# ---------- 7. path convention: agent runtime-state paths must use the .eaos/ prefix ----------
# Canon (routing.yaml > runtime): '.eaos/<task-id>/artifacts/…' and '.eaos/memory/…'. A bare
# 'artifacts/<' or 'memory/' path in an agent persona is A3-class drift — flag it. A line that
# already contains '.eaos/' is assumed to be using the canonical form somewhere in it.
for rel in sorted(persona_files):
    if not exists(rel):
        continue
    for i, line in enumerate(read(os.path.join(ROOT, rel)).splitlines(), 1):
        if "artifacts/<" in line and ".eaos/" not in line:
            err(f"{rel}:{i}: bare 'artifacts/<' path — should be under '.eaos/<task-id>/artifacts/'")
        if "memory/" in line and ".eaos/memory" not in line:
            err(f"{rel}:{i}: bare 'memory/' path — should be '.eaos/memory/...'")

# ---------- 8. setup.sh installs every commands/*.md ----------
# (The old check on doctor's need_agents list was removed: doctor now derives the list
# dynamically from agents/*.md, so the hardcoded-list drift class it guarded no longer exists.)
setup_rel = "setup.sh"
if os.path.isdir(cmd_dir) and exists(setup_rel):
    # Match only non-comment lines so a commented-out install line doesn't pass.
    setup_lines = [l for l in read(os.path.join(ROOT, setup_rel)).splitlines()
                   if not l.lstrip().startswith("#")]
    setup_text = "\n".join(setup_lines)
    for f in sorted(os.listdir(cmd_dir)):
        if not f.endswith(".md"):
            continue
        (ok if f"commands/{f}" in setup_text else err)(f"{setup_rel} installs commands/{f}")


# ---------- 9. mechanisms.yaml shape (kernel law 6 / spec section 12) ----------
# Validator checks SHAPE only; the evaluator determines effect.
mech_rel = "mechanisms.yaml"
if exists(mech_rel):
    if HAVE_YAML:
        import yaml as _y
        try:
            mdoc = _y.safe_load(read(os.path.join(ROOT, mech_rel))) or {}
            entries = mdoc.get("mechanisms") or []
            REQ = ["id", "name", "status", "motivating_evidence", "expected_effect",
                   "primary_metric", "owner", "removal_condition"]
            STATUSES = {"proposed", "instrumented", "active", "validated", "rejected", "retired"}
            seen_ids = set()
            bad = 0
            for m in entries:
                mid = (m or {}).get("id", "<missing-id>")
                missing = [f for f in REQ if not (m or {}).get(f)]
                if missing:
                    err(f"{mech_rel}: {mid} missing fields: {', '.join(missing)}"); bad += 1
                if (m or {}).get("status") not in STATUSES:
                    err(f"{mech_rel}: {mid} invalid status '{(m or {}).get('status')}'"); bad += 1
                if mid in seen_ids:
                    err(f"{mech_rel}: duplicate id {mid}"); bad += 1
                seen_ids.add(mid)
            if not bad:
                ok(f"{mech_rel}: {len(entries)} mechanism entries structurally complete")
        except Exception as ex:
            err(f"{mech_rel}: failed to parse — {ex}")
    else:
        warn(f"{mech_rel} present but PyYAML missing — shape check skipped")
else:
    warn(f"{mech_rel} not found — mechanism registry not yet started")

# ---------- report ----------
print("EAOS validation\n" + "=" * 40)
for c in checks:
    print(f"  \033[0;32m✓\033[0m {c}")
for w in warnings:
    print(f"  \033[0;33m!\033[0m {w}")
for e in errors:
    print(f"  \033[0;31m✗\033[0m {e}")
print("=" * 40)
print(f"{len(checks)} passed · {len(warnings)} warnings · {len(errors)} errors")
sys.exit(1 if errors else 0)
