#!/usr/bin/env python3
"""
test_eaos.py — stdlib unittest for scripts/eaos.

Runs the CLI as a real subprocess against a fresh tempdir per test (no fixtures on disk,
no imports of eaos internals). Asserts exit codes and key substrings of stdout, matching
the exit-code contract in docs/reviews/2026-07-13-eaos-cli-spec.md.
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest

EAOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eaos")


def run(cwd, *cli_args):
    result = subprocess.run(
        [sys.executable, EAOS, *cli_args],
        cwd=cwd, capture_output=True, text=True,
    )
    return result.returncode, result.stdout, result.stderr


class EaosTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def init(self, **flags):
        args = ["init"]
        for k, v in flags.items():
            args += [f"--{k.replace('_', '-')}", str(v)]
        rc, out, err = run(self.cwd, *args)
        self.assertEqual(rc, 0, err)
        return out

    def new_task(self, title="Sample task"):
        rc, out, err = run(self.cwd, "task", "new", title)
        self.assertEqual(rc, 0, err)
        return out.strip()


class TestInit(EaosTestCase):
    def test_init_creates_layout(self):
        self.init()
        for sub in ("decisions", "patterns", "lessons", "codebase"):
            self.assertTrue(os.path.isdir(os.path.join(self.cwd, ".eaos/memory", sub)))
        with open(os.path.join(self.cwd, ".eaos/config.json")) as f:
            cfg = json.load(f)
        self.assertEqual(cfg["max_agent_spawns_per_task"], 12)
        self.assertEqual(cfg["max_same_issue_loops"], 3)
        self.assertEqual(cfg["max_total_loopbacks"], 8)

    def test_init_idempotent(self):
        self.init(max_spawns=5)
        with open(os.path.join(self.cwd, ".eaos/config.json")) as f:
            cfg1 = json.load(f)
        # second init must NOT clobber existing config, even with different flags
        rc, out, err = run(self.cwd, "init", "--max-spawns", "99")
        self.assertEqual(rc, 0, err)
        with open(os.path.join(self.cwd, ".eaos/config.json")) as f:
            cfg2 = json.load(f)
        self.assertEqual(cfg1, cfg2)
        self.assertEqual(cfg2["max_agent_spawns_per_task"], 5)

    def test_init_overrides_on_first_run(self):
        self.init(max_spawns=2, max_same_issue=1, max_total_loopbacks=4)
        with open(os.path.join(self.cwd, ".eaos/config.json")) as f:
            cfg = json.load(f)
        self.assertEqual(cfg["max_agent_spawns_per_task"], 2)
        self.assertEqual(cfg["max_same_issue_loops"], 1)
        self.assertEqual(cfg["max_total_loopbacks"], 4)


class TestTaskNew(EaosTestCase):
    def test_id_allocation_sequential(self):
        self.init()
        t1 = self.new_task("first")
        t2 = self.new_task("second")
        self.assertEqual(t1, "T-001")
        self.assertEqual(t2, "T-002")
        self.assertTrue(os.path.isdir(os.path.join(self.cwd, ".eaos", t1, "artifacts")))
        with open(os.path.join(self.cwd, ".eaos", t1, "state.json")) as f:
            state = json.load(f)
        self.assertEqual(state["phase"], "INTAKE")
        self.assertEqual(state["title"], "first")

    def test_concurrent_task_new_gets_distinct_ids(self):
        self.init()
        results = []

        def worker(i):
            # Distinct titles: identical titles now collide on the duplicate-fingerprint
            # check (by design — see TestDuplicateDetection), so this test uses distinct
            # titles to isolate what it actually exercises: the id-allocation race.
            rc, out, err = run(self.cwd, "task", "new", f"concurrent {i}")
            results.append((rc, out.strip()))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertTrue(all(rc == 0 for rc, _ in results))
        ids = [out for _, out in results]
        self.assertEqual(len(ids), len(set(ids)), f"duplicate ids allocated: {ids}")
        self.assertEqual(set(ids), {f"T-{n:03d}" for n in range(1, 6)})


class TestAppend(EaosTestCase):
    def test_message_numbering_and_type_validation(self):
        self.init()
        tid = self.new_task()
        rc, out, err = run(self.cwd, "append", tid, "--from", "developer", "--to",
                            "architect", "--type", "PROPOSE", "--body", "first message")
        self.assertEqual(rc, 0, err)
        self.assertIn("msg-001", out)

        rc, out, err = run(self.cwd, "append", tid, "--from", "architect", "--to",
                            "developer", "--type", "REVIEW", "--body", "second message")
        self.assertEqual(rc, 0, err)
        self.assertIn("msg-002", out)

        with open(os.path.join(self.cwd, ".eaos", tid, "state.json")) as f:
            state = json.load(f)
        self.assertEqual(len(state["messages"]), 2)
        self.assertEqual(state["messages"][0]["id"], "msg-001")
        self.assertEqual(state["messages"][1]["id"], "msg-002")

        with open(os.path.join(self.cwd, ".eaos", tid, "warroom.md")) as f:
            warroom = f.read()
        self.assertIn("msg-001", warroom)
        self.assertIn("msg-002", warroom)

    def test_invalid_type_exits_2(self):
        self.init()
        tid = self.new_task()
        rc, out, err = run(self.cwd, "append", tid, "--from", "developer", "--to",
                            "architect", "--type", "BOGUS", "--body", "x")
        self.assertEqual(rc, 2)


class TestSpawn(EaosTestCase):
    def test_spawn_cap_exit_code(self):
        self.init(max_spawns=3)
        tid = self.new_task()
        for i in range(3):
            rc, out, err = run(self.cwd, "spawn", tid, "--agent", f"agent{i}")
            self.assertEqual(rc, 0, err)
        rc, out, err = run(self.cwd, "spawn", tid, "--agent", "one-too-many")
        self.assertEqual(rc, 1)
        self.assertIn("BUDGET EXCEEDED", out)
        self.assertIn("4/3", out)
        # A rejected spawn must NOT consume a slot: after the human drops an agent, the
        # budget still has exactly the cap's worth of successful spawns recorded.
        with open(os.path.join(self.cwd, ".eaos", tid, "state.json")) as f:
            state = json.load(f)
        self.assertEqual(state["spawns"]["count"], 3)
        # And a retry after rejection is still rejected identically (no double-penalty).
        rc, out, err = run(self.cwd, "spawn", tid, "--agent", "retry")
        self.assertEqual(rc, 1)
        self.assertIn("4/3", out)


class TestLoopback(EaosTestCase):
    def test_same_issue_deadlock(self):
        self.init(max_same_issue=3, max_total_loopbacks=100)
        tid = self.new_task()
        for i in range(3):
            rc, out, err = run(self.cwd, "loopback", tid, "--edge", "REVIEW->IMPLEMENT",
                                "--issue", "flaky-test", "--attempt", f"approach {i} -> fail")
            self.assertEqual(rc, 0, err)
        rc, out, err = run(self.cwd, "loopback", tid, "--edge", "REVIEW->IMPLEMENT",
                            "--issue", "flaky-test", "--attempt", "approach 4 -> fail")
        self.assertEqual(rc, 1)
        self.assertIn("DEADLOCK", out)
        self.assertIn("flaky-test", out)

    def test_total_ceiling(self):
        self.init(max_same_issue=100, max_total_loopbacks=3)
        tid = self.new_task()
        for i in range(3):
            rc, out, err = run(self.cwd, "loopback", tid, "--edge", "QA->DEV",
                                "--issue", f"issue-{i}", "--attempt", "x -> fail")
            self.assertEqual(rc, 0, err)
        rc, out, err = run(self.cwd, "loopback", tid, "--edge", "QA->DEV",
                            "--issue", "issue-last", "--attempt", "y -> fail")
        self.assertEqual(rc, 1)
        self.assertIn("CEILING", out)


class TestGate(EaosTestCase):
    def test_require_fails_when_unrecorded_or_failed(self):
        self.init()
        tid = self.new_task()

        rc, out, err = run(self.cwd, "gate", tid, "DESIGN", "--require")
        self.assertEqual(rc, 1)
        self.assertIn("GATE UNMET", out)

        rc, out, err = run(self.cwd, "gate", tid, "DESIGN", "--check", "lint", "--fail")
        self.assertEqual(rc, 0, err)
        rc, out, err = run(self.cwd, "gate", tid, "DESIGN", "--require")
        self.assertEqual(rc, 1)
        self.assertIn("GATE UNMET", out)

        rc, out, err = run(self.cwd, "gate", tid, "DESIGN", "--check", "lint", "--pass")
        self.assertEqual(rc, 0, err)
        rc, out, err = run(self.cwd, "gate", tid, "DESIGN", "--require")
        self.assertEqual(rc, 0, err)


class TestVerify(EaosTestCase):
    def test_evidence_mandatory(self):
        self.init()
        tid = self.new_task()
        rc, out, err = run(self.cwd, "verify", tid, "--criterion", "AC-1",
                            "--verdict", "pass")
        self.assertEqual(rc, 2)

    def test_require_on_empty_fails(self):
        self.init()
        tid = self.new_task()
        rc, out, err = run(self.cwd, "verify", tid, "--require")
        self.assertEqual(rc, 1)
        self.assertIn("UNVERIFIED", out)

    def test_require_passes_when_all_pass(self):
        self.init()
        tid = self.new_task()
        rc, out, err = run(self.cwd, "verify", tid, "--criterion", "AC-1",
                            "--verdict", "pass", "--evidence", "tests/test_x.py::ok")
        self.assertEqual(rc, 0, err)
        rc, out, err = run(self.cwd, "verify", tid, "--require")
        self.assertEqual(rc, 0, err)

    def test_pass_fail_aliases_persist_as_canonical(self):
        self.init()
        tid = self.new_task()
        rc, out, err = run(self.cwd, "verify", tid, "--criterion", "AC-1",
                            "--verdict", "pass", "--evidence", "e1")
        self.assertEqual(rc, 0, err)
        self.assertIn("verified", out)
        rc, out, err = run(self.cwd, "verify", tid, "--criterion", "AC-2",
                            "--verdict", "fail", "--evidence", "e2")
        self.assertEqual(rc, 0, err)
        self.assertIn("failed", out)

        with open(os.path.join(self.cwd, ".eaos", tid, "state.json")) as f:
            state = json.load(f)
        self.assertEqual(state["criteria"]["AC-1"]["verdict"], "verified")
        self.assertEqual(state["criteria"]["AC-2"]["verdict"], "failed")


class TestReport(EaosTestCase):
    def test_refuses_when_unverified(self):
        self.init()
        tid = self.new_task()
        rc, out, err = run(self.cwd, "report", tid)
        self.assertEqual(rc, 1)
        self.assertIn("REFUSED", out)

    def test_report_succeeds_when_verified(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "pass",
            "--evidence", "manual check")
        rc, out, err = run(self.cwd, "report", tid)
        self.assertEqual(rc, 0, err)
        report_path = os.path.join(self.cwd, ".eaos", tid, "artifacts", "final-report.md")
        self.assertTrue(os.path.isfile(report_path))
        with open(report_path) as f:
            content = f.read()
        self.assertIn("AC-1", content)


class TestStatusAndPhase(EaosTestCase):
    def test_status_and_phase_transition(self):
        self.init()
        tid = self.new_task()
        rc, out, err = run(self.cwd, "phase", tid, "DESIGN")
        self.assertEqual(rc, 0, err)
        self.assertIn("INTAKE -> DESIGN", out)

        rc, out, err = run(self.cwd, "status", tid)
        self.assertEqual(rc, 0, err)
        self.assertIn("DESIGN", out)


class TestEpisode(EaosTestCase):
    def test_episode_close_happy_path(self):
        self.init()
        rc, out, err = run(self.cwd, "task", "new", "Sample", "--kind", "bug",
                            "--playbook", "bugfix-v1")
        self.assertEqual(rc, 0, err)
        tid = out.strip()

        run(self.cwd, "spawn", tid, "--agent", "developer")
        run(self.cwd, "spawn", tid, "--agent", "qa")
        run(self.cwd, "spawn", tid, "--agent", "developer")  # dup agent -> dedup in episode
        run(self.cwd, "loopback", tid, "--edge", "QA->DEV", "--issue", "flaky",
            "--attempt", "x -> fail")
        run(self.cwd, "gate", tid, "DESIGN", "--check", "lint", "--pass")
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "pass",
            "--evidence", "e1")

        rc, out, err = run(self.cwd, "episode", "close", tid)
        self.assertEqual(rc, 0, err)

        runs = os.path.join(self.cwd, ".eaos", "runs.jsonl")
        with open(runs) as f:
            lines = [json.loads(l) for l in f if l.strip()]
        self.assertEqual(len(lines), 1)
        ep = lines[0]
        self.assertEqual(ep["schema_version"], 1)
        self.assertEqual(ep["task"], tid)
        self.assertEqual(ep["title"], "Sample")
        self.assertEqual(ep["kind"], "bug")
        self.assertEqual(ep["playbook"], "bugfix-v1")
        self.assertEqual(ep["spawns"], 3)
        self.assertEqual(ep["agents"], ["developer", "qa"])
        self.assertEqual(ep["loopbacks_total"], 1)
        self.assertEqual(ep["loopbacks_by_issue"], {"flaky": 1})
        self.assertEqual(ep["gates"], {"DESIGN": {"pass": 1, "fail": 0}})
        self.assertEqual(ep["criteria"], {"AC-1": "verified"})  # canonical persistence (fix 3)
        self.assertEqual(ep["criteria_verified"], 1)
        self.assertEqual(ep["criteria_total"], 1)
        self.assertEqual(ep["verdict"], "verified")
        self.assertEqual(ep["tokens"], "unavailable")
        self.assertEqual(ep["close_revision"], 1)
        self.assertIn("wall_seconds", ep)

        with open(os.path.join(self.cwd, ".eaos", tid, "state.json")) as f:
            state = json.load(f)
        self.assertEqual(state["status"], "closed")

        rc, out, err = run(self.cwd, "status", tid)
        self.assertEqual(rc, 0, err)
        self.assertIn("episode: closed", out)

    def test_double_close_refused(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "pass",
            "--evidence", "e")
        rc, out, err = run(self.cwd, "episode", "close", tid)
        self.assertEqual(rc, 0, err)
        rc, out, err = run(self.cwd, "episode", "close", tid)
        self.assertEqual(rc, 1)
        self.assertIn("already closed", out + err)

    def test_amend_appends_with_incremented_revision(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "pass",
            "--evidence", "e")
        rc, out, err = run(self.cwd, "episode", "close", tid)
        self.assertEqual(rc, 0, err)
        rc, out, err = run(self.cwd, "episode", "close", tid, "--amend")
        self.assertEqual(rc, 0, err)

        runs = os.path.join(self.cwd, ".eaos", "runs.jsonl")
        with open(runs) as f:
            lines = [json.loads(l) for l in f if l.strip()]
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0]["close_revision"], 1)
        self.assertEqual(lines[1]["close_revision"], 2)
        self.assertEqual(lines[1]["task"], tid)

    def test_task_new_kind_flows_through_to_episode(self):
        self.init()
        rc, out, err = run(self.cwd, "task", "new", "Feature work",
                            "--kind", "feature", "--playbook", "feature-v2")
        self.assertEqual(rc, 0, err)
        tid = out.strip()
        with open(os.path.join(self.cwd, ".eaos", tid, "state.json")) as f:
            state = json.load(f)
        self.assertEqual(state["kind"], "feature")
        self.assertEqual(state["playbook"], "feature-v2")

        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "pass",
            "--evidence", "e")
        run(self.cwd, "episode", "close", tid)
        with open(os.path.join(self.cwd, ".eaos", "runs.jsonl")) as f:
            ep = json.loads(f.readline())
        self.assertEqual(ep["kind"], "feature")
        self.assertEqual(ep["playbook"], "feature-v2")


class TestVerifyConditional(EaosTestCase):
    def test_manual_confirmation_conditional_exit_3(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "pass",
            "--evidence", "e1")
        run(self.cwd, "verify", tid, "--criterion", "AC-2",
            "--verdict", "manual_confirmation_required", "--evidence", "e2")
        rc, out, err = run(self.cwd, "verify", tid, "--require")
        self.assertEqual(rc, 3, err)
        self.assertIn("CONDITIONAL", out)
        self.assertIn("AC-2", out)
        self.assertIn("manual_confirmation_required", out)

    def test_blocked_criterion_conditional_exit_3(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "pass",
            "--evidence", "e1")
        run(self.cwd, "verify", tid, "--criterion", "AC-2", "--verdict", "blocked",
            "--evidence", "e2")
        rc, out, err = run(self.cwd, "verify", tid, "--require")
        self.assertEqual(rc, 3, err)
        self.assertIn("CONDITIONAL", out)
        self.assertIn("AC-2", out)
        self.assertIn("NOT claimed complete", out)

    def test_failed_criterion_require_exit_1(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "fail",
            "--evidence", "e1")
        rc, out, err = run(self.cwd, "verify", tid, "--require")
        self.assertEqual(rc, 1)
        self.assertIn("UNVERIFIED", out)

    def test_report_manual_confirmation_only_wording(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "pass",
            "--evidence", "e1")
        run(self.cwd, "verify", tid, "--criterion", "AC-2",
            "--verdict", "manual_confirmation_required", "--evidence", "e2")
        rc, out, err = run(self.cwd, "report", tid)
        self.assertEqual(rc, 0, err)
        report_path = os.path.join(self.cwd, ".eaos", tid, "artifacts", "final-report.md")
        with open(report_path) as f:
            content = f.read()
        self.assertIn("Pending manual confirmation", content)
        self.assertIn("AC-2", content)
        self.assertIn("release pending manual confirmation", content)
        self.assertNotIn("NOT claiming implementation complete", content)

    def test_report_blocked_wording_not_claiming_complete(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "pass",
            "--evidence", "e1")
        run(self.cwd, "verify", tid, "--criterion", "AC-2", "--verdict", "blocked",
            "--evidence", "e2")
        rc, out, err = run(self.cwd, "report", tid)
        self.assertEqual(rc, 0, err)
        report_path = os.path.join(self.cwd, ".eaos", tid, "artifacts", "final-report.md")
        with open(report_path) as f:
            content = f.read()
        self.assertIn("Unresolved (blocked / not reproducible)", content)
        self.assertIn("NOT claiming implementation complete", content)
        self.assertNotIn("implementation complete;", content)

    def test_failed_criterion_still_blocks_report(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "fail",
            "--evidence", "e1")
        rc, out, err = run(self.cwd, "report", tid)
        self.assertEqual(rc, 1)
        self.assertIn("REFUSED", out)


class TestSaveStateAtomicity(EaosTestCase):
    def test_state_write_then_read_valid_and_no_leftover_tmp(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        run(self.cwd, "spawn", tid, "--agent", "developer")

        state_file = os.path.join(self.cwd, ".eaos", tid, "state.json")
        with open(state_file) as f:
            state = json.load(f)
        self.assertEqual(state["id"], tid)
        self.assertEqual(state["phase"], "DESIGN")

        entries = os.listdir(os.path.join(self.cwd, ".eaos", tid))
        self.assertFalse(any(e.startswith("state.json.tmp") for e in entries),
                          f"leftover tmp file(s): {entries}")


class TestLocking(EaosTestCase):
    def test_concurrent_spawns_both_succeed_serially_with_correct_tree_total(self):
        self.init(max_spawns=10)
        rc, out, err = run(self.cwd, "task", "new", "parent")
        self.assertEqual(rc, 0, err)
        parent = out.strip()
        rc, out, err = run(self.cwd, "task", "new", "child", "--parent", parent)
        self.assertEqual(rc, 0, err)
        child = out.strip()

        results = []

        def worker(task_id, agent):
            rc, out, err = run(self.cwd, "spawn", task_id, "--agent", agent)
            results.append((rc, out, err))

        threads = [
            threading.Thread(target=worker, args=(parent, "agent-a")),
            threading.Thread(target=worker, args=(child, "agent-b")),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertTrue(all(rc == 0 for rc, _, err in results), results)

        with open(os.path.join(self.cwd, ".eaos", parent, "state.json")) as f:
            parent_state = json.load(f)
        with open(os.path.join(self.cwd, ".eaos", child, "state.json")) as f:
            child_state = json.load(f)
        self.assertEqual(parent_state["spawns"]["count"] + child_state["spawns"]["count"], 2)

        rc, out, err = run(self.cwd, "spawn", child, "--agent", "agent-c")
        self.assertEqual(rc, 0, err)
        self.assertIn("tree total 3/10", out)


class TestIdempotency(EaosTestCase):
    def test_spawn_idempotency_key_replay_no_double_spawn(self):
        self.init(max_spawns=5)
        tid = self.new_task()
        rc, out1, err = run(self.cwd, "spawn", tid, "--agent", "developer",
                             "--idempotency-key", "retry-1")
        self.assertEqual(rc, 0, err)

        rc, out2, err = run(self.cwd, "spawn", tid, "--agent", "developer",
                             "--idempotency-key", "retry-1")
        self.assertEqual(rc, 0, err)
        self.assertEqual(out1, out2)

        with open(os.path.join(self.cwd, ".eaos", tid, "state.json")) as f:
            state = json.load(f)
        self.assertEqual(state["spawns"]["count"], 1)


class TestEpisodeCloseIdempotency(EaosTestCase):
    def test_replay_without_amend_succeeds_but_bare_double_close_still_refused(self):
        self.init()
        tid = self.new_task()
        rc, out1, err = run(self.cwd, "episode", "close", tid,
                             "--idempotency-key", "close-1")
        self.assertEqual(rc, 0, err)

        # A retried close with the same key must succeed WITHOUT --amend — that's the
        # real-world case (a hook retrying a call whose response it never saw).
        rc, out2, err = run(self.cwd, "episode", "close", tid,
                             "--idempotency-key", "close-1")
        self.assertEqual(rc, 0, err)
        self.assertEqual(out1, out2)

        # A close with no key (or a different key) is still a genuine double-close.
        rc, out, err = run(self.cwd, "episode", "close", tid)
        self.assertEqual(rc, 1)
        self.assertIn("already closed", out + err)


class TestParentChildBudget(EaosTestCase):
    def test_tree_budget_exceeded_across_parent_and_child(self):
        self.init(max_spawns=2)
        rc, out, err = run(self.cwd, "task", "new", "root task")
        self.assertEqual(rc, 0, err)
        parent = out.strip()
        rc, out, err = run(self.cwd, "task", "new", "child task", "--parent", parent)
        self.assertEqual(rc, 0, err)
        child = out.strip()

        rc, out, err = run(self.cwd, "spawn", parent, "--agent", "a1")
        self.assertEqual(rc, 0, err)
        rc, out, err = run(self.cwd, "spawn", parent, "--agent", "a2")
        self.assertEqual(rc, 0, err)

        rc, out, err = run(self.cwd, "spawn", child, "--agent", "a3")
        self.assertEqual(rc, 1)
        self.assertIn("BUDGET EXCEEDED", out)
        self.assertIn("3/2", out)
        self.assertIn(parent, out)  # names the root of the tree

    def test_parent_must_exist(self):
        self.init()
        rc, out, err = run(self.cwd, "task", "new", "orphan", "--parent", "T-999")
        self.assertEqual(rc, 2)


class TestDuplicateDetection(EaosTestCase):
    def test_exact_duplicate_blocked_and_allow_duplicate_overrides(self):
        self.init()
        rc, out, err = run(self.cwd, "task", "new", "Fix the flaky login test")
        self.assertEqual(rc, 0, err)
        first = out.strip()

        rc, out, err = run(self.cwd, "task", "new", "Fix the flaky login test")
        self.assertEqual(rc, 1)
        self.assertIn("resume it instead", out + err)
        self.assertIn(first, out + err)

        rc, out, err = run(self.cwd, "task", "new", "Fix the flaky login test",
                            "--allow-duplicate", "--reason", "two people paged at once")
        self.assertEqual(rc, 0, err)
        # An identical-title override also trips the overlap warning (fix 4) against
        # `first`, so stdout carries a leading WARN line before the task id.
        self.assertIn("WARN: overlaps", out)
        second = out.strip().splitlines()[-1]
        self.assertNotEqual(first, second)

        with open(os.path.join(self.cwd, ".eaos", second, "state.json")) as f:
            state = json.load(f)
        self.assertEqual(state["duplicate_override_reason"], "two people paged at once")

    def test_allow_duplicate_without_reason_is_usage_error(self):
        self.init()
        self.new_task("some title")
        rc, out, err = run(self.cwd, "task", "new", "some title", "--allow-duplicate")
        self.assertEqual(rc, 2)

    def test_closed_task_does_not_block_duplicate(self):
        self.init()
        tid = self.new_task("Sample task")
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "pass",
            "--evidence", "e")
        run(self.cwd, "episode", "close", tid)
        rc, out, err = run(self.cwd, "task", "new", "Sample task")
        self.assertEqual(rc, 0, err)


class TestAppendFile(EaosTestCase):
    def test_append_file_dash_reads_stdin(self):
        self.init()
        tid = self.new_task()
        result = subprocess.run(
            [sys.executable, EAOS, "append", tid, "--from", "developer", "--to",
             "architect", "--type", "PROPOSE", "--file", "-"],
            cwd=self.cwd, capture_output=True, text=True, input="line one\nline two\n",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with open(os.path.join(self.cwd, ".eaos", tid, "state.json")) as f:
            state = json.load(f)
        self.assertEqual(state["messages"][0]["body"], "line one\nline two")

    def test_append_file_and_body_mutually_exclusive(self):
        self.init()
        tid = self.new_task()
        rc, out, err = run(self.cwd, "append", tid, "--from", "developer", "--to",
                            "architect", "--type", "PROPOSE", "--body", "x", "--file", "-")
        self.assertEqual(rc, 2)


class TestVerifyBulk(EaosTestCase):
    def test_bulk_happy_path(self):
        self.init()
        tid = self.new_task()
        bulk_input = "AC-1 | pass | tests/x.py::ok\n# a comment\n\nAC-2 | fail | tests/y.py::bad\n"
        result = subprocess.run(
            [sys.executable, EAOS, "verify", tid, "--bulk"],
            cwd=self.cwd, capture_output=True, text=True, input=bulk_input,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with open(os.path.join(self.cwd, ".eaos", tid, "state.json")) as f:
            state = json.load(f)
        # pass/fail are accepted input aliases but persist as the canonical enum (fix 3)
        self.assertEqual(state["criteria"]["AC-1"]["verdict"], "verified")
        self.assertEqual(state["criteria"]["AC-2"]["verdict"], "failed")

    def test_bulk_malformed_line_records_nothing(self):
        self.init()
        tid = self.new_task()
        bulk_input = "AC-1 | pass | ev\nthis line has no pipes\n"
        result = subprocess.run(
            [sys.executable, EAOS, "verify", tid, "--bulk"],
            cwd=self.cwd, capture_output=True, text=True, input=bulk_input,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("this line has no pipes", result.stdout)
        with open(os.path.join(self.cwd, ".eaos", tid, "state.json")) as f:
            state = json.load(f)
        self.assertEqual(state.get("criteria", {}), {})

    def test_bulk_replay_with_key_appends_once(self):
        self.init()
        tid = self.new_task()
        bulk_input = "AC-1 | pass | tests/x.py::ok\nAC-2 | fail | tests/y.py::bad\n"

        result1 = subprocess.run(
            [sys.executable, EAOS, "verify", tid, "--bulk",
             "--idempotency-key", "batch-1"],
            cwd=self.cwd, capture_output=True, text=True, input=bulk_input,
        )
        self.assertEqual(result1.returncode, 0, result1.stderr)

        result2 = subprocess.run(
            [sys.executable, EAOS, "verify", tid, "--bulk",
             "--idempotency-key", "batch-1"],
            cwd=self.cwd, capture_output=True, text=True, input=bulk_input,
        )
        self.assertEqual(result2.returncode, 0, result2.stderr)
        self.assertEqual(result1.stdout, result2.stdout)

        with open(os.path.join(self.cwd, ".eaos", tid, "warroom.md")) as f:
            warroom = f.read()
        self.assertEqual(warroom.count("VERIFY criterion=AC-1"), 1)


class TestLoopbackClass(EaosTestCase):
    def test_hard_blocker_exits_1_immediately_regardless_of_counters(self):
        self.init(max_same_issue=100, max_total_loopbacks=100)
        tid = self.new_task()
        rc, out, err = run(self.cwd, "loopback", tid, "--edge", "REVIEW->IMPLEMENT",
                            "--issue", "no-fix-possible", "--attempt", "first try",
                            "--class", "hard_blocker")
        self.assertEqual(rc, 1)
        self.assertIn("BLOCKED — escalate to human", out)

    def test_transient_allows_identical_repeat(self):
        self.init(max_same_issue=100, max_total_loopbacks=100)
        tid = self.new_task()
        rc, out, err = run(self.cwd, "loopback", tid, "--edge", "QA->DEV",
                            "--issue", "flaky", "--attempt", "same text",
                            "--class", "transient")
        self.assertEqual(rc, 0, err)
        rc, out, err = run(self.cwd, "loopback", tid, "--edge", "QA->DEV",
                            "--issue", "flaky", "--attempt", "same text",
                            "--class", "transient")
        self.assertEqual(rc, 0, err)

    def test_recoverable_identical_retry_refused(self):
        self.init(max_same_issue=100, max_total_loopbacks=100)
        tid = self.new_task()
        rc, out, err = run(self.cwd, "loopback", tid, "--edge", "QA->DEV",
                            "--issue", "flaky", "--attempt", "same text")
        self.assertEqual(rc, 0, err)
        rc, out, err = run(self.cwd, "loopback", tid, "--edge", "QA->DEV",
                            "--issue", "flaky", "--attempt", "same text")
        self.assertEqual(rc, 1)
        self.assertIn("retry must vary", out)


class TestAudit(EaosTestCase):
    def test_audit_clean_on_well_run_task(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        run(self.cwd, "spawn", tid, "--agent", "developer")
        run(self.cwd, "gate", tid, "DESIGN", "--check", "lint", "--pass")
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "pass",
            "--evidence", "e1")
        rc, out, err = run(self.cwd, "episode", "close", tid)
        self.assertEqual(rc, 0, err)

        rc, out, err = run(self.cwd, "audit", tid)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("clean", out)

    def test_audit_discrepancy_phase_and_messages(self):
        self.init()
        tid = self.new_task()
        # (b): spawn recorded but phase never left INTAKE
        run(self.cwd, "spawn", tid, "--agent", "developer")
        # (c): warroom shows protocol entries the state never recorded (messages == 0)
        warroom = os.path.join(self.cwd, ".eaos", tid, "warroom.md")
        with open(warroom, "a") as f:
            f.write("\n### Untracked review note\n- id: msg-999\n")

        rc, out, err = run(self.cwd, "audit", tid, "--json")
        self.assertEqual(rc, 1)
        report = json.loads(out)
        by_name = {c["name"]: c["ok"] for c in report["checks"]}
        self.assertFalse(by_name["phase_intake_consistency"])
        self.assertFalse(by_name["messages_vs_warroom"])
        self.assertGreaterEqual(report["discrepancy_count"], 2)


class TestSchemaMigration(EaosTestCase):
    def make_legacy_v1_task(self, task_id="T-001", title="Legacy task"):
        d = os.path.join(self.cwd, ".eaos", task_id)
        os.makedirs(os.path.join(d, "artifacts"), exist_ok=True)
        ts = "2020-01-01T00:00:00"
        with open(os.path.join(d, "warroom.md"), "w") as f:
            f.write(f"# {task_id}: {title}\n\nCreated: {ts}\nStatus: active\n\n"
                     f"## War Room Log\n")
        # Deliberately the *pre-v2* shape: no schema_version, revision, parent,
        # fingerprint, or idempotency_keys.
        state = {
            "id": task_id, "title": title, "kind": None, "playbook": None,
            "created": ts, "status": "active", "phase": "INTAKE",
            "phase_history": [{"phase": "INTAKE", "at": ts}],
            "next_msg_num": 1, "messages": [], "spawns": {"count": 0, "log": []},
            "loopbacks": {"total": 0, "by_issue": {}, "ledger": []},
            "gates": {}, "criteria": {},
        }
        with open(os.path.join(d, "state.json"), "w") as f:
            json.dump(state, f)
        return task_id

    def test_v1_state_file_loads_and_migrates_on_next_save(self):
        self.init()
        tid = self.make_legacy_v1_task()

        rc, out, err = run(self.cwd, "status", tid)
        self.assertEqual(rc, 0, err)

        rc, out, err = run(self.cwd, "phase", tid, "DESIGN")
        self.assertEqual(rc, 0, err)

        with open(os.path.join(self.cwd, ".eaos", tid, "state.json")) as f:
            state = json.load(f)
        self.assertEqual(state["schema_version"], 2)
        self.assertEqual(state["revision"], 1)
        self.assertIsNone(state["parent"])
        self.assertEqual(state["idempotency_keys"], [])

    def test_legacy_pass_fail_verdicts_migrate_on_load(self):
        self.init()
        tid = self.make_legacy_v1_task()
        state_path = os.path.join(self.cwd, ".eaos", tid, "state.json")
        with open(state_path) as f:
            state = json.load(f)
        state["criteria"] = {
            "AC-1": {"verdict": "pass", "evidence": "e1", "at": "2020-01-01T00:00:00"},
            "AC-2": {"verdict": "fail", "evidence": "e2", "at": "2020-01-01T00:00:00"},
        }
        with open(state_path, "w") as f:
            json.dump(state, f)

        rc, out, err = run(self.cwd, "status", tid)
        self.assertEqual(rc, 0, err)
        self.assertIn("verified", out)
        self.assertIn("failed", out)

        # migrate_state() only canonicalizes in-memory; force a save to persist it.
        rc, out, err = run(self.cwd, "phase", tid, "DESIGN")
        self.assertEqual(rc, 0, err)

        with open(state_path) as f:
            migrated = json.load(f)
        self.assertEqual(migrated["criteria"]["AC-1"]["verdict"], "verified")
        self.assertEqual(migrated["criteria"]["AC-2"]["verdict"], "failed")


class TestFingerprintFields(EaosTestCase):
    def test_fingerprint_with_paths_and_criteria_differs_from_title_only(self):
        self.init()
        rc, out, err = run(self.cwd, "task", "new", "Unique title xyz")
        self.assertEqual(rc, 0, err)
        t1 = out.strip()
        with open(os.path.join(self.cwd, ".eaos", t1, "state.json")) as f:
            fp1 = json.load(f)["fingerprint"]

        rc, out, err = run(self.cwd, "task", "new", "Unique title xyz",
                            "--paths", "src/a.py,src/b.py", "--criteria", "AC-1,AC-2")
        self.assertEqual(rc, 0, err)
        t2 = out.strip()
        with open(os.path.join(self.cwd, ".eaos", t2, "state.json")) as f:
            state2 = json.load(f)

        self.assertNotEqual(t1, t2)
        self.assertNotEqual(fp1, state2["fingerprint"])
        self.assertEqual(state2["paths"], ["src/a.py", "src/b.py"])
        self.assertEqual(state2["criteria_ids"], ["AC-1", "AC-2"])

    def test_outcome_changes_fingerprint_too(self):
        self.init()
        rc, out, err = run(self.cwd, "task", "new", "Same title", "--outcome", "outcome A")
        self.assertEqual(rc, 0, err)
        t1 = out.strip()
        rc, out, err = run(self.cwd, "task", "new", "Same title", "--outcome", "outcome B",
                            "--allow-duplicate", "--reason", "different outcome")
        self.assertEqual(rc, 0, err)
        t2 = out.strip().splitlines()[-1]

        with open(os.path.join(self.cwd, ".eaos", t1, "state.json")) as f:
            fp1 = json.load(f)["fingerprint"]
        with open(os.path.join(self.cwd, ".eaos", t2, "state.json")) as f:
            fp2 = json.load(f)["fingerprint"]
        self.assertNotEqual(fp1, fp2)


class TestOverlapWarning(EaosTestCase):
    def test_overlap_warning_fires_at_high_jaccard(self):
        self.init()
        rc, out, err = run(self.cwd, "task", "new",
                            "Fix the flaky login integration test")
        self.assertEqual(rc, 0, err)
        first = out.strip()

        rc, out, err = run(self.cwd, "task", "new",
                            "Fix the flaky login integration spec")
        self.assertEqual(rc, 0, err)
        self.assertIn("WARN: overlaps", out)
        self.assertIn(first, out)
        second = out.strip().splitlines()[-1]

        with open(os.path.join(self.cwd, ".eaos", second, "state.json")) as f:
            state = json.load(f)
        self.assertEqual(len(state["overlap_warnings"]), 1)
        self.assertEqual(state["overlap_warnings"][0]["task"], first)
        self.assertGreaterEqual(state["overlap_warnings"][0]["jaccard"], 0.5)

    def test_no_overlap_warning_at_low_jaccard(self):
        self.init()
        run(self.cwd, "task", "new", "Fix the flaky login test")
        rc, out, err = run(self.cwd, "task", "new",
                            "Add a totally unrelated dashboard widget")
        self.assertEqual(rc, 0, err)
        self.assertNotIn("WARN: overlaps", out)
        with open(os.path.join(self.cwd, ".eaos", out.strip(), "state.json")) as f:
            state = json.load(f)
        self.assertEqual(state["overlap_warnings"], [])


class TestHardBlockerState(EaosTestCase):
    def test_hard_blocker_sets_status_blocked_and_records_reason(self):
        self.init()
        tid = self.new_task()
        rc, out, err = run(self.cwd, "loopback", tid, "--edge", "REVIEW->IMPLEMENT",
                            "--issue", "no-fix-possible", "--attempt", "first try",
                            "--class", "hard_blocker")
        self.assertEqual(rc, 1)
        self.assertIn("BLOCKED — escalate to human", out)

        with open(os.path.join(self.cwd, ".eaos", tid, "state.json")) as f:
            state = json.load(f)
        self.assertEqual(state["status"], "blocked")
        self.assertEqual(state["blocked"]["reason"], "first try")
        self.assertEqual(state["blocked"]["issue"], "no-fix-possible")

    def test_mutating_verbs_refused_on_blocked_task(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "loopback", tid, "--edge", "REVIEW->IMPLEMENT",
            "--issue", "no-fix-possible", "--attempt", "first try",
            "--class", "hard_blocker")

        rc, out, err = run(self.cwd, "spawn", tid, "--agent", "developer")
        self.assertEqual(rc, 1)
        self.assertIn("BLOCKED", out + err)
        self.assertIn("--unblock", out + err)

        rc, out, err = run(self.cwd, "append", tid, "--from", "developer", "--to",
                            "architect", "--type", "PROPOSE", "--body", "x")
        self.assertEqual(rc, 1)
        self.assertIn("BLOCKED", out + err)

        rc, out, err = run(self.cwd, "gate", tid, "DESIGN", "--check", "lint", "--pass")
        self.assertEqual(rc, 1)
        self.assertIn("BLOCKED", out + err)

        rc, out, err = run(self.cwd, "verify", tid, "--criterion", "AC-1",
                            "--verdict", "pass", "--evidence", "e")
        self.assertEqual(rc, 1)
        self.assertIn("BLOCKED", out + err)

        # status/audit/report/loopback remain usable against a blocked task.
        rc, out, err = run(self.cwd, "status", tid)
        self.assertEqual(rc, 0, err)
        rc, out, err = run(self.cwd, "audit", tid)
        self.assertEqual(rc, 0, out + err)

    def test_audit_flags_hard_blocker_ledger_with_active_status(self):
        self.init()
        tid = self.new_task()
        state_path = os.path.join(self.cwd, ".eaos", tid, "state.json")
        with open(state_path) as f:
            state = json.load(f)
        # Simulate a pre-fix-1 state: a hard_blocker ledger entry exists but status was
        # never transitioned to blocked — exactly the discrepancy fix 1 closes.
        state["loopbacks"]["ledger"].append({
            "edge": "REVIEW->IMPLEMENT", "issue": "x", "attempt": "y",
            "class": "hard_blocker", "at": "2026-01-01T00:00:00",
        })
        with open(state_path, "w") as f:
            json.dump(state, f)

        rc, out, err = run(self.cwd, "audit", tid, "--json")
        self.assertEqual(rc, 1)
        report = json.loads(out)
        by_name = {c["name"]: c["ok"] for c in report["checks"]}
        self.assertFalse(by_name["hard_blocker_state_consistency"])

    def test_audit_flags_blocked_status_with_no_blocked_record(self):
        self.init()
        tid = self.new_task()
        state_path = os.path.join(self.cwd, ".eaos", tid, "state.json")
        with open(state_path) as f:
            state = json.load(f)
        state["status"] = "blocked"
        state["blocked"] = None
        with open(state_path, "w") as f:
            json.dump(state, f)

        rc, out, err = run(self.cwd, "audit", tid, "--json")
        self.assertEqual(rc, 1)
        report = json.loads(out)
        by_name = {c["name"]: c["ok"] for c in report["checks"]}
        self.assertFalse(by_name["hard_blocker_state_consistency"])

    def test_unblock_resumes_task(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "loopback", tid, "--edge", "REVIEW->IMPLEMENT",
            "--issue", "no-fix-possible", "--attempt", "first try",
            "--class", "hard_blocker")

        rc, out, err = run(self.cwd, "phase", tid, "DESIGN", "--unblock",
                            "--reason", "human resolved it")
        self.assertEqual(rc, 0, err)

        with open(os.path.join(self.cwd, ".eaos", tid, "state.json")) as f:
            state = json.load(f)
        self.assertEqual(state["status"], "active")
        self.assertIsNone(state["blocked"])
        self.assertEqual(len(state["unblocks"]), 1)
        self.assertEqual(state["unblocks"][0]["reason"], "human resolved it")
        self.assertEqual(state["phase"], "DESIGN")

        # Mutating verbs succeed again once unblocked.
        rc, out, err = run(self.cwd, "spawn", tid, "--agent", "developer")
        self.assertEqual(rc, 0, err)

    def test_unblock_without_reason_is_usage_error(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "loopback", tid, "--edge", "REVIEW->IMPLEMENT",
            "--issue", "no-fix-possible", "--attempt", "first try",
            "--class", "hard_blocker")
        rc, out, err = run(self.cwd, "phase", tid, "DESIGN", "--unblock")
        self.assertEqual(rc, 2)


class TestIdempotencyFingerprint(EaosTestCase):
    """fix A: an idempotency key is bound to a request fingerprint, not just a bare
    string — reusing a key for a materially different request must be refused, never
    silently replayed and never silently re-mutated under the first call's cache slot."""

    def test_verify_conflict_on_reused_key_reviewer_repro(self):
        # The reviewer's exact repro: key K used to verify AC-1, then the same key K
        # reused to verify a *different* criterion with a different verdict. That must
        # be refused outright — AC-2 must never be recorded.
        self.init()
        tid = self.new_task()
        rc, out, err = run(self.cwd, "verify", tid, "--criterion", "AC-1",
                            "--verdict", "verified", "--evidence", "e1",
                            "--idempotency-key", "K")
        self.assertEqual(rc, 0, err)

        rc, out, err = run(self.cwd, "verify", tid, "--criterion", "AC-2",
                            "--verdict", "failed", "--evidence", "e2",
                            "--idempotency-key", "K")
        self.assertEqual(rc, 1)
        self.assertIn("IDEMPOTENCY CONFLICT", out)

        with open(os.path.join(self.cwd, ".eaos", tid, "state.json")) as f:
            state = json.load(f)
        self.assertNotIn("AC-2", state["criteria"])
        self.assertEqual(state["criteria"]["AC-1"]["verdict"], "verified")

    def test_verify_replay_with_identical_args_returns_cached_output(self):
        self.init()
        tid = self.new_task()
        rc, out1, err = run(self.cwd, "verify", tid, "--criterion", "AC-1",
                             "--verdict", "verified", "--evidence", "e1",
                             "--idempotency-key", "K")
        self.assertEqual(rc, 0, err)
        rc, out2, err = run(self.cwd, "verify", tid, "--criterion", "AC-1",
                             "--verdict", "verified", "--evidence", "e1",
                             "--idempotency-key", "K")
        self.assertEqual(rc, 0, err)
        self.assertEqual(out1, out2)
        with open(os.path.join(self.cwd, ".eaos", tid, "state.json")) as f:
            state = json.load(f)
        self.assertEqual(len(state["idempotency_keys"]), 1)

    def test_spawn_conflict_on_reused_key_different_agent(self):
        self.init(max_spawns=5)
        tid = self.new_task()
        rc, out, err = run(self.cwd, "spawn", tid, "--agent", "developer",
                            "--idempotency-key", "K")
        self.assertEqual(rc, 0, err)

        rc, out, err = run(self.cwd, "spawn", tid, "--agent", "qa",
                            "--idempotency-key", "K")
        self.assertEqual(rc, 1)
        self.assertIn("IDEMPOTENCY CONFLICT", out)

        with open(os.path.join(self.cwd, ".eaos", tid, "state.json")) as f:
            state = json.load(f)
        self.assertEqual(state["spawns"]["count"], 1)
        self.assertEqual(state["spawns"]["log"][0]["agent"], "developer")

    def test_bulk_verify_conflict_on_reused_key_different_body(self):
        self.init()
        tid = self.new_task()
        result1 = subprocess.run(
            [sys.executable, EAOS, "verify", tid, "--bulk", "--idempotency-key", "K"],
            cwd=self.cwd, capture_output=True, text=True,
            input="AC-1 | pass | e1\n",
        )
        self.assertEqual(result1.returncode, 0, result1.stderr)

        result2 = subprocess.run(
            [sys.executable, EAOS, "verify", tid, "--bulk", "--idempotency-key", "K"],
            cwd=self.cwd, capture_output=True, text=True,
            input="AC-2 | fail | e2\n",
        )
        self.assertEqual(result2.returncode, 1)
        self.assertIn("IDEMPOTENCY CONFLICT", result2.stdout)

        with open(os.path.join(self.cwd, ".eaos", tid, "state.json")) as f:
            state = json.load(f)
        self.assertNotIn("AC-2", state.get("criteria", {}))
        self.assertIn("AC-1", state.get("criteria", {}))


class TestEpisodeCloseDuplicateRevision(EaosTestCase):
    def test_preexisting_revision_blocks_bare_close_and_appends_nothing(self):
        # fix B: simulate an out-of-band runs.jsonl write for (task, close_revision=1) —
        # e.g. a hand-edited file — that this CLI never produced (state.json is still
        # "active"). A bare close must still refuse rather than append a second
        # close_revision=1 line for the same task.
        self.init()
        tid = self.new_task()
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "pass",
            "--evidence", "e")

        runs = os.path.join(self.cwd, ".eaos", "runs.jsonl")
        fake = {"schema_version": 1, "task": tid, "close_revision": 1, "closed": "x"}
        with open(runs, "w") as f:
            f.write(json.dumps(fake) + "\n")

        rc, out, err = run(self.cwd, "episode", "close", tid)
        self.assertEqual(rc, 1)
        self.assertIn("already closed", out + err)

        with open(runs) as f:
            lines = [l for l in f if l.strip()]
        self.assertEqual(len(lines), 1)


class TestAuditRunsJsonlConsistency(EaosTestCase):
    def test_audit_flags_duplicate_and_gap(self):
        self.init()
        tid = self.new_task()
        runs = os.path.join(self.cwd, ".eaos", "runs.jsonl")
        entries = [
            {"schema_version": 1, "task": tid, "close_revision": 1, "closed": "t1"},
            {"schema_version": 1, "task": tid, "close_revision": 1, "closed": "t2"},  # dup
            {"schema_version": 1, "task": tid, "close_revision": 3, "closed": "t3"},  # gap
        ]
        with open(runs, "w") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")
            f.write(f'{{"task": "{tid}", "close_revision": broken}}\n')  # malformed

        rc, out, err = run(self.cwd, "audit", tid, "--json")
        self.assertEqual(rc, 1)
        report = json.loads(out)
        by_name = {c["name"]: c for c in report["checks"]}
        self.assertFalse(by_name["runs_jsonl_consistency"]["ok"])
        detail = by_name["runs_jsonl_consistency"]["detail"]
        self.assertIn("duplicate", detail)
        self.assertIn("gap", detail)
        self.assertIn("malformed", detail)


class TestTaskNewIdempotency(EaosTestCase):
    def test_replay_same_key_same_args_returns_same_id_and_creates_nothing(self):
        self.init()
        rc, out1, err = run(self.cwd, "task", "new", "Some title", "--kind", "feature",
                             "--idempotency-key", "K")
        self.assertEqual(rc, 0, err)
        t1 = out1.strip()

        rc, out2, err = run(self.cwd, "task", "new", "Some title", "--kind", "feature",
                             "--idempotency-key", "K")
        self.assertEqual(rc, 0, err)
        t2 = out2.strip()
        self.assertEqual(t1, t2)

        task_dirs = [n for n in os.listdir(os.path.join(self.cwd, ".eaos"))
                     if n.startswith("T-")]
        self.assertEqual(len(task_dirs), 1)

    def test_conflict_same_key_different_title(self):
        self.init()
        rc, out, err = run(self.cwd, "task", "new", "Title A", "--idempotency-key", "K")
        self.assertEqual(rc, 0, err)

        rc, out, err = run(self.cwd, "task", "new", "Title B", "--idempotency-key", "K")
        self.assertEqual(rc, 1)
        self.assertIn("IDEMPOTENCY CONFLICT", out)

        task_dirs = [n for n in os.listdir(os.path.join(self.cwd, ".eaos"))
                     if n.startswith("T-")]
        self.assertEqual(len(task_dirs), 1)

    def test_idempotency_store_created_by_init(self):
        self.init()
        self.assertTrue(os.path.isfile(os.path.join(self.cwd, ".eaos", "idempotency.json")))


if __name__ == "__main__":
    unittest.main()
