#!/usr/bin/env python3
"""
validate-eaos.py — mechanical consistency checks for the Engineering Agentic OS.

v4 layout (lab/specs/2026-09-17-eaos-v4-architecture.md):
  - the front door is small (bootstrap budget) and pins no model
  - exactly the three boundary agent definitions exist, with tool scopes and no model pin
  - every checklist the front door names exists with name/description/sources frontmatter
  - routing.yaml parses and carries stakes / budget / models.mode / adapters
  - the templates the front door and checklists reference exist
  - nothing installed references the deleted v3 machinery (playbooks, personas, loop)
  - mechanisms.yaml keeps the section-12 schema

Exit code 0 = all good; 1 = problems found. No third-party deps required
(falls back to a tiny YAML-frontmatter parser if PyYAML is missing).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCT = ("agents", "checklists", "templates", "adapters", "runtime")

def P(rel):
    """Repo path for a product-relative name: the product lives under eaos/, and the front
    door (installed as commands/agentic-os.md) is eaos/agentic-os.md in the repo."""
    if rel == "commands/agentic-os.md":
        return os.path.join(ROOT, "eaos", "agentic-os.md")
    if rel.split("/")[0] in PRODUCT:
        return os.path.join(ROOT, "eaos", rel)
    return os.path.join(ROOT, rel)

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
    return os.path.exists(P(rel))

# ---------- 1. core files / dirs present ----------
REQUIRED = ["commands/agentic-os.md", "runtime/routing.yaml", "setup.sh", "README.md",
            "runtime/eaos", "runtime/eaos-hook.sh", "lab/mechanisms.yaml",
            "lab/EVAL-PROTOCOL.md", "adapters/skill-head.md"]
for r in REQUIRED:
    (ok if exists(r) else err)(f"required file: {r}")
for d in ["agents", "checklists", "templates", "adapters"]:
    (ok if os.path.isdir(P(d)) else err)(f"required dir: {d}/")

# ---------- 2. front door: bootstrap budget, no model pin, follow-up rule ----------
cmd_rel = "commands/agentic-os.md"
if exists(cmd_rel):
    text = read(P(cmd_rel))
    est = len(text) // 4
    (ok if est <= 2000 else err)(f"{cmd_rel}: bootstrap ~{est} tokens (budget 2000, v4 C-1)")
    fm = frontmatter(text) or {}
    (ok if "model" not in fm else err)(f"{cmd_rel}: frontmatter pins no model (inherit)")
    (ok if "Do not re-run this command" in text else err)(
        f"{cmd_rel}: states that follow-ups never re-expand the command")
    (ok if "status --packet" in text else err)(f"{cmd_rel}: names the continuation packet")

# ---------- 3. boundary agent definitions: exactly three, scoped tools, no personas ----------
BOUNDARIES = {"eaos-builder": {"Write", "Edit"}, "eaos-reader": set(), "eaos-checker": set()}
# front door token budget: the same estimate the doctor uses (chars / 4), so the gate catches
# a front door that grew past its own bootstrap budget BEFORE a release, not after (v4.5.1).
_fd = read(P(cmd_rel))
_est = len(_fd) // 4
(ok if _est <= 2000 else err)(f"front door ~{_est} tokens (bootstrap budget 2000)")

agent_dir = P("agents")
found = sorted(f[:-3] for f in os.listdir(agent_dir) if f.endswith(".md") and f != "README.md") \
    if os.path.isdir(agent_dir) else []
extra = [a for a in found if a not in BOUNDARIES]
missing = [a for a in BOUNDARIES if a not in found]
(ok if not extra else err)(f"agents/: only the three boundaries (extra: {extra})" if extra
                          else "agents/: only the three boundary definitions")
(ok if not missing else err)(f"agents/: all three boundaries present (missing: {missing})"
                            if missing else "agents/: builder, reader, checker present")
for a in found:
    fm = frontmatter(read(os.path.join(agent_dir, a + ".md"))) or {}
    for field in ["name", "description", "tools"]:
        (ok if field in fm else err)(f"agents/{a}.md: frontmatter has '{field}'")
    (ok if "model" not in fm else err)(f"agents/{a}.md: no model pin (inherit)")
    tools = fm.get("tools")
    tools = set(tools) if isinstance(tools, list) else set(str(tools or "").strip("[]").replace(" ", "").split(","))
    must_lack = BOUNDARIES.get(a, set())
    if a in ("eaos-reader", "eaos-checker"):
        (ok if not ({"Write", "Edit"} & tools) else err)(f"agents/{a}.md: read-only tool scope")
    else:
        (ok if must_lack <= tools else err)(f"agents/{a}.md: can write and edit")
    body_text = read(os.path.join(agent_dir, a + ".md")).lower()
    (ok if "you are a senior" not in body_text and "personality" not in body_text else err)(
        f"agents/{a}.md: no persona costume")

# ---------- 4. checklists named by the front door exist, with frontmatter ----------
CHECKLISTS = ["goal", "intake", "build", "research", "review", "security", "test-adequacy", "verdict",
              "deploy-rehearsal", "operability", "incident", "reporting"]
for c in CHECKLISTS:
    rel = f"checklists/{c}.md"
    if not exists(rel):
        err(f"{rel}: missing (named by the front door)")
        continue
    fm = frontmatter(read(P(rel))) or {}
    for field in ["name", "description", "sources"]:
        (ok if field in fm else err)(f"{rel}: frontmatter has '{field}'")
    lines = read(P(rel)).count("\n")
    (ok if lines <= 90 else warn)(f"{rel}: {lines} lines (on-demand checklists stay short)")

# ---------- 5. routing.yaml parses + v4 shape ----------
routing = None
rp = P("runtime/routing.yaml")
if exists("runtime/routing.yaml"):
    if not HAVE_YAML:
        warn("PyYAML not installed — routing.yaml structural checks skipped (run: pip install pyyaml)")
    else:
        try:
            routing = load_yaml(read(rp))
            ok("routing.yaml parses")
            for key in ["models", "stakes", "budget", "loop_guard", "adapters"]:
                (ok if key in routing else err)(f"routing.yaml has '{key}'")
            (ok if routing.get("models", {}).get("mode") in ("inherit", "tiered") else err)(
                "routing.models.mode is inherit|tiered")
            for lvl in routing.get("stakes", {}).get("levels", []):
                (ok if lvl in routing["stakes"] else err)(f"routing.stakes defines '{lvl}'")
            for key in ["max_agent_spawns_per_task", "reserved_verifier_spawns",
                        "reserved_loopback_spawns", "required_checks", "max_context_tokens"]:
                (ok if key in routing.get("budget", {}) else err)(f"routing.budget has '{key}'")
            ad = routing.get("adapters", {}).get("claude-code", {})
            LEVELS = {"enforced", "measured", "advisory", "planned", "manual"}
            bad = {k: v for k, v in ad.items() if v not in LEVELS}
            (ok if ad and not bad else err)(f"routing.adapters.claude-code uses capability levels only ({bad or 'ok'})")
        except Exception as e:
            err(f"routing.yaml failed to parse: {e}")

# ---------- 6. templates referenced by the front door / checklists / agents exist ----------
refs = set()
for rel in [cmd_rel] + [f"checklists/{c}.md" for c in CHECKLISTS] + [f"agents/{a}.md" for a in found]:
    if exists(rel):
        refs |= set(re.findall(r"templates/([\w-]+\.md)", read(P(rel))))
for t in sorted(refs):
    (ok if exists(f"templates/{t}") else err)(f"referenced template exists: templates/{t}")

# ---------- 7. no installed file references the deleted v3 machinery ----------
DELETED = ["playbooks/", "orchestrator/loop.md", "orchestrator/orchestrator.md",
           "orchestrator/protocol.md", "agency-agents", "skills/"]
for rel in [cmd_rel] + [f"agents/{a}.md" for a in found] + [f"checklists/{c}.md" for c in CHECKLISTS]:
    if not exists(rel):
        continue
    body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", read(P(rel)), count=1, flags=re.S)
    hits = [d for d in DELETED if d in body]   # frontmatter `sources` may name deleted files
    (ok if not hits else err)(f"{rel}: no reference to removed v3 machinery" + (f" ({hits})" if hits else ""))

# ---------- 8. setup.sh installs the front door, the three agents and the checklists ----------
if exists("setup.sh"):
    st = read(P("setup.sh"))
    for needle, label in [("eaos/agentic-os.md", "front door"), ("checklists", "checklists"),
                          ("agency-", "legacy agency-agents cleanup"), ("eaos-hook.sh", "hook script")]:
        (ok if needle in st else err)(f"setup.sh handles {label}")
    (ok if "AGENCY_REPO" not in st else err)("setup.sh no longer clones agency-agents")

# ---------- 9. mechanisms.yaml shape (kernel law 6 / spec section 12) ----------
# Validator checks SHAPE only; the evaluator determines effect.
mech_rel = "lab/mechanisms.yaml"
if exists(mech_rel):
    if HAVE_YAML:
        import yaml as _y
        try:
            mdoc = _y.safe_load(read(P(mech_rel))) or {}
            entries = mdoc.get("mechanisms") or []
            # Full frozen schema (spec section 12): every field present AND typed.
            # guardrails may be an EMPTY list (instrumentation mechanisms) but must exist;
            # evaluation_due_after_runs is a positive int or the explicit string "exempt".
            REQ_PRESENT = ["id", "name", "status", "motivating_evidence", "expected_effect",
                           "primary_metric", "owner", "removal_condition"]
            STATUSES = {"proposed", "instrumented", "active", "validated", "rejected", "retired"}
            seen_ids = set()
            bad = 0
            for m in entries:
                m = m or {}
                mid = m.get("id", "<missing-id>")
                missing = [f for f in REQ_PRESENT if not m.get(f)]
                if missing:
                    err(f"{mech_rel}: {mid} missing fields: {', '.join(missing)}"); bad += 1
                if not re.match(r"^M-\d{3}$", str(mid)):
                    err(f"{mech_rel}: id '{mid}' must match M-NNN"); bad += 1
                if m.get("status") not in STATUSES:
                    err(f"{mech_rel}: {mid} invalid status '{m.get('status')}'"); bad += 1
                if not isinstance(m.get("motivating_evidence"), list) or not m.get("motivating_evidence"):
                    err(f"{mech_rel}: {mid} motivating_evidence must be a non-empty list"); bad += 1
                if "guardrails" not in m or not isinstance(m.get("guardrails"), list):
                    err(f"{mech_rel}: {mid} guardrails must be a list (empty allowed)"); bad += 1
                edr = m.get("evaluation_due_after_runs")
                if not ((isinstance(edr, int) and not isinstance(edr, bool) and edr > 0) or edr == "exempt"):
                    err(f"{mech_rel}: {mid} evaluation_due_after_runs must be a positive int or 'exempt'"); bad += 1
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
