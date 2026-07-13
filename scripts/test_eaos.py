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

        def worker():
            rc, out, err = run(self.cwd, "task", "new", "concurrent")
            results.append((rc, out.strip()))

        threads = [threading.Thread(target=worker) for _ in range(5)]
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


if __name__ == "__main__":
    unittest.main()
