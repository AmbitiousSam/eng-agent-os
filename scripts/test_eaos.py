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
        self.assertEqual(cfg["max_agent_spawns_per_task"], 15)
        self.assertEqual(cfg["reserved_verifier_spawns"], 1)
        self.assertEqual(cfg["reserved_loopback_spawns"], 2)
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
        self.init(max_spawns=3, reserve_verifier=0, reserve_loopbacks=0)  # hard cap only
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
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "verified", "--evidence", "ran it")
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
        self.init(max_spawns=2, reserve_verifier=0, reserve_loopbacks=0)
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
        self.assertNotIn("phase_intake_consistency", by_name)   # retired in v4
        self.assertFalse(by_name["messages_vs_warroom"])
        self.assertGreaterEqual(report["discrepancy_count"], 1)


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


class TestParentTreeBudgetConsistency(EaosTestCase):
    """audit check (k): dangling parents, cycles, and a tree-wide spawn total over the
    configured cap — all detected from a single scan of every task's parent field."""

    def audit_check(self, tid):
        rc, out, err = run(self.cwd, "audit", tid, "--json")
        report = json.loads(out)
        by_name = {c["name"]: c for c in report["checks"]}
        return rc, by_name["parent_tree_budget_consistency"]

    def test_tree_cap_lowered_flags_discrepancy_from_either_task(self):
        # Reviewer's exact repro: parent+child, 2 total spawns, cap dropped to 1 after
        # the fact — auditing EITHER task must catch it.
        self.init(max_spawns=10)
        rc, out, err = run(self.cwd, "task", "new", "root task")
        self.assertEqual(rc, 0, err)
        parent = out.strip()
        rc, out, err = run(self.cwd, "task", "new", "child task", "--parent", parent)
        self.assertEqual(rc, 0, err)
        child = out.strip()
        run(self.cwd, "spawn", parent, "--agent", "a1")
        run(self.cwd, "spawn", child, "--agent", "a2")

        cfg_path = os.path.join(self.cwd, ".eaos", "config.json")
        with open(cfg_path) as f:
            cfg = json.load(f)
        cfg["max_agent_spawns_per_task"] = 1
        with open(cfg_path, "w") as f:
            json.dump(cfg, f)

        for tid in (parent, child):
            rc, check = self.audit_check(tid)
            self.assertEqual(rc, 1)
            self.assertFalse(check["ok"])
            self.assertIn("tree spawn total 2 exceeds cap 1", check["detail"])
            self.assertIn(parent, check["detail"])
            self.assertIn(child, check["detail"])

    def test_clean_tree_is_ok_with_root_total_cap(self):
        self.init(max_spawns=10)
        rc, out, err = run(self.cwd, "task", "new", "root task")
        self.assertEqual(rc, 0, err)
        parent = out.strip()
        rc, out, err = run(self.cwd, "task", "new", "child task", "--parent", parent)
        self.assertEqual(rc, 0, err)
        child = out.strip()
        run(self.cwd, "spawn", parent, "--agent", "a1")
        run(self.cwd, "spawn", child, "--agent", "a2")

        # Overall audit rc is unrelated here (spawning without a phase change trips the
        # unrelated phase_intake_consistency check) — only this specific check matters.
        _, check = self.audit_check(parent)
        self.assertTrue(check["ok"])
        self.assertIn(f"root={parent}", check["detail"])
        self.assertIn("total=2/10", check["detail"])
        self.assertIn(child, check["detail"])

    def test_dangling_parent_flagged(self):
        self.init()
        tid = self.new_task("orphan-to-be")
        state_path = os.path.join(self.cwd, ".eaos", tid, "state.json")
        with open(state_path) as f:
            state = json.load(f)
        state["parent"] = "T-999"
        with open(state_path, "w") as f:
            json.dump(state, f)

        rc, check = self.audit_check(tid)
        self.assertEqual(rc, 1)
        self.assertFalse(check["ok"])
        self.assertIn("dangling", check["detail"])
        self.assertIn(tid, check["detail"])

    def test_cycle_flagged(self):
        self.init()
        rc, out, err = run(self.cwd, "task", "new", "task A")
        self.assertEqual(rc, 0, err)
        a = out.strip()
        rc, out, err = run(self.cwd, "task", "new", "task B")
        self.assertEqual(rc, 0, err)
        b = out.strip()

        a_path = os.path.join(self.cwd, ".eaos", a, "state.json")
        b_path = os.path.join(self.cwd, ".eaos", b, "state.json")
        with open(a_path) as f:
            a_state = json.load(f)
        with open(b_path) as f:
            b_state = json.load(f)
        a_state["parent"] = b
        b_state["parent"] = a
        with open(a_path, "w") as f:
            json.dump(a_state, f)
        with open(b_path, "w") as f:
            json.dump(b_state, f)

        for tid in (a, b):
            rc, check = self.audit_check(tid)
            self.assertEqual(rc, 1)
            self.assertFalse(check["ok"])
            self.assertIn("cycle", check["detail"])
            self.assertIn(a, check["detail"])
            self.assertIn(b, check["detail"])


class TestRevisionMonotonicity(EaosTestCase):
    """audit check (l): .eaos/<id>/revisions.jsonl, appended by save_state under the
    caller's already-held task lock, cross-checked against the live state.json."""

    def audit_check(self, tid):
        rc, out, err = run(self.cwd, "audit", tid, "--json")
        report = json.loads(out)
        by_name = {c["name"]: c for c in report["checks"]}
        return rc, by_name["revision_monotonicity"]

    def journal_lines(self, tid):
        path = os.path.join(self.cwd, ".eaos", tid, "revisions.jsonl")
        with open(path) as f:
            return [json.loads(l) for l in f if l.strip()]

    def test_normal_mutation_sequence_is_clean(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        run(self.cwd, "spawn", tid, "--agent", "developer")
        run(self.cwd, "gate", tid, "DESIGN", "--check", "lint", "--pass")

        lines = self.journal_lines(tid)
        self.assertEqual([e["revision"] for e in lines], [1, 2, 3, 4])
        for e in lines:
            self.assertIn("at", e)
            self.assertIn("state_sha256", e)

        rc, check = self.audit_check(tid)
        self.assertEqual(rc, 0)
        self.assertTrue(check["ok"])
        self.assertEqual(check["detail"], "clean")

    def test_rollback_flagged_as_regression(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        run(self.cwd, "spawn", tid, "--agent", "developer")

        state_path = os.path.join(self.cwd, ".eaos", tid, "state.json")
        with open(state_path) as f:
            state = json.load(f)
        self.assertEqual(state["revision"], 3)
        state["revision"] = 1  # reviewer's exact repro: revision 3 rolled back to 1
        with open(state_path, "w") as f:
            json.dump(state, f, indent=2)
            f.write("\n")

        rc, check = self.audit_check(tid)
        self.assertEqual(rc, 1)
        self.assertFalse(check["ok"])
        self.assertIn("regression", check["detail"])

    def test_out_of_band_edit_without_revision_change_flagged_as_hash_mismatch(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")

        state_path = os.path.join(self.cwd, ".eaos", tid, "state.json")
        with open(state_path) as f:
            state = json.load(f)
        state["title"] = "tampered title"  # revision left untouched
        with open(state_path, "w") as f:
            json.dump(state, f, indent=2)
            f.write("\n")

        rc, check = self.audit_check(tid)
        self.assertEqual(rc, 1)
        self.assertFalse(check["ok"])
        self.assertIn("does not match current state.json", check["detail"])
        self.assertNotIn("regression", check["detail"])

    def test_pre_journal_task_seeds_journal_on_next_mutation(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")  # revision 2; journal has [1, 2]

        # A TRUE legacy task: written before the journal existed, so it carries neither
        # a revisions.jsonl nor the journal_enabled genesis marker. (Deleting only the
        # journal is now the loss case — see TestJournalLoss.)
        journal_path = os.path.join(self.cwd, ".eaos", tid, "revisions.jsonl")
        os.remove(journal_path)
        state_path = os.path.join(self.cwd, ".eaos", tid, "state.json")
        with open(state_path) as f:
            state = json.load(f)
        del state["journal_enabled"]
        del state["journal_start_revision"]
        with open(state_path, "w") as f:
            json.dump(state, f, indent=2)
            f.write("\n")
        open(os.path.join(self.cwd, ".eaos", "heads.jsonl"), "w").close()  # no anchor either

        rc, check = self.audit_check(tid)
        self.assertEqual(rc, 0)
        self.assertTrue(check["ok"])
        self.assertIn("no journal yet (pre-journal task)", check["detail"])

        # The next mutation reseeds the journal at whatever revision it lands on (3),
        # not 1 — this is not a discrepancy.
        run(self.cwd, "gate", tid, "DESIGN", "--check", "lint", "--pass")
        self.assertEqual([e["revision"] for e in self.journal_lines(tid)], [3])

        rc, check = self.audit_check(tid)
        self.assertEqual(rc, 0)
        self.assertTrue(check["ok"])
        self.assertIn("journal started at revision 3", check["detail"])

    def test_journal_gap_flagged(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        run(self.cwd, "spawn", tid, "--agent", "developer")
        run(self.cwd, "gate", tid, "DESIGN", "--check", "lint", "--pass")

        journal_path = os.path.join(self.cwd, ".eaos", tid, "revisions.jsonl")
        with open(journal_path) as f:
            raw_lines = [l for l in f if l.strip()]
        self.assertEqual(len(raw_lines), 4)
        kept = [l for l in raw_lines if json.loads(l)["revision"] != 2]
        with open(journal_path, "w") as f:
            f.writelines(kept)

        rc, check = self.audit_check(tid)
        self.assertEqual(rc, 1)
        self.assertFalse(check["ok"])
        self.assertIn("not strictly increasing", check["detail"])


class TestJournalLoss(EaosTestCase):
    """Round 4 medium-1: a journal-enabled task (genesis marker written by every
    save_state) whose revisions.jsonl is missing or empty has LOST history."""

    def audit_check(self, tid):
        rc, out, err = run(self.cwd, "audit", tid, "--json")
        by_name = {c["name"]: c for c in json.loads(out)["checks"]}
        return rc, by_name["revision_monotonicity"]

    def test_state_carries_genesis_marker(self):
        self.init()
        tid = self.new_task()
        with open(os.path.join(self.cwd, ".eaos", tid, "state.json")) as f:
            self.assertTrue(json.load(f)["journal_enabled"])

    def test_truncated_journal_flagged(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        open(os.path.join(self.cwd, ".eaos", tid, "revisions.jsonl"), "w").close()
        rc, check = self.audit_check(tid)
        self.assertEqual(rc, 1)
        self.assertIn("journal empty for a journal-enabled task", check["detail"])

    def test_deleted_journal_flagged(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        os.remove(os.path.join(self.cwd, ".eaos", tid, "revisions.jsonl"))
        rc, check = self.audit_check(tid)
        self.assertEqual(rc, 1)
        self.assertIn("journal missing for a journal-enabled task", check["detail"])


class TestAuditCoherentSnapshot(EaosTestCase):
    """Round 4 HIGH-1: legitimate concurrent mutations must never read as drift.
    Before the fix this failed ~100/100 in the reviewer's harness."""

    def test_concurrent_spawns_never_false_fail_audit(self):
        self.init(max_spawns=1000)
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")  # spawning in INTAKE is real drift (check b)
        stop = threading.Event()
        errors = []

        def mutate():
            i = 0
            while not stop.is_set() and i < 150:
                rc, out, err = run(self.cwd, "spawn", tid, "--agent", f"dev{i}")
                if rc not in (0, 4):
                    errors.append((rc, out, err))
                i += 1

        t = threading.Thread(target=mutate)
        t.start()
        failures = []
        for _ in range(40):
            rc, out, err = run(self.cwd, "audit", tid)
            if rc == 1:
                failures.append(out)
        stop.set()
        t.join()
        self.assertEqual(errors, [])
        self.assertEqual(failures, [], f"false drift during legitimate spawns: {failures[:2]}")


class TestLockContentionExitCode(EaosTestCase):
    """Round 4 HIGH-2: lock contention is infrastructure (exit 4), never a policy verdict
    (exit 1) — a hook must be able to tell them apart and fail open on 4."""

    def test_held_project_lock_exits_4_and_mutates_nothing(self):
        self.init()
        tid = self.new_task()
        lock = os.path.join(self.cwd, ".eaos", ".lock")
        with open(lock, "w") as f:
            f.write("999999")
        try:
            rc, out, err = run(self.cwd, "spawn", tid, "--agent", "developer")
            self.assertEqual(rc, 4, err)
            self.assertIn("lock busy", err)
            rc, out, err = run(self.cwd, "audit", tid)
            self.assertEqual(rc, 4, err)
        finally:
            os.remove(lock)
        rc, out, err = run(self.cwd, "status", tid)
        self.assertIn("Spawns: 0/", out)


class TestSessionScopedCurrent(EaosTestCase):
    """Round 4 HIGH-4: .eaos/sessions/<session-id> maps a host session to ITS task;
    `session resolve` is the one rule a hook uses, and it fails open on ambiguity."""

    def resolve(self, sid=None):
        args = ["session", "resolve"] + (["--session", sid] if sid else [])
        rc, out, err = run(self.cwd, *args)
        return rc, out.strip(), err.strip()

    def test_two_sessions_attribute_to_their_own_tasks(self):
        self.init()
        rc, t1, _ = run(self.cwd, "task", "new", "alpha migration", "--session", "s1")
        rc, t2, _ = run(self.cwd, "task", "new", "beta dashboard", "--session", "s2")
        t1, t2 = t1.strip().splitlines()[-1], t2.strip().splitlines()[-1]
        self.assertEqual(self.resolve("s1")[1], t1)
        self.assertEqual(self.resolve("s2")[1], t2)
        # global CURRENT still points at the latest — the legacy pointer is not the rule
        with open(os.path.join(self.cwd, ".eaos", "CURRENT")) as f:
            self.assertEqual(f.read().strip(), t2)

    def test_unmapped_session_with_two_active_tasks_fails_open(self):
        self.init()
        run(self.cwd, "task", "new", "one", "--session", "s1")
        run(self.cwd, "task", "new", "two", "--session", "s2")
        rc, out, err = self.resolve("s3")
        self.assertEqual(rc, 1)
        self.assertIn("no mapping", err)
        self.assertFalse(os.path.exists(os.path.join(self.cwd, ".eaos", "sessions", "s3")))

    def test_unmapped_session_never_adopts_the_sole_active_task(self):
        """Round 5 item 1: the only active task may belong to a session with no binder;
        adopting it misattributes spawns and blocks THIS session on THAT budget."""
        self.init()
        tid = self.new_task()
        rc, out, err = self.resolve("s9")
        self.assertEqual(rc, 1)
        self.assertIn("never adopts", err)
        self.assertFalse(os.path.exists(os.path.join(self.cwd, ".eaos", "sessions", "s9")))

    def test_no_session_id_fails_open_once_any_session_is_tracked(self):
        self.init()
        tid = self.new_task()
        self.assertEqual(self.resolve()[1], tid)              # true no-session host
        run(self.cwd, "session", "bind", tid, "--session", "s1")
        rc, out, err = self.resolve()
        self.assertEqual(rc, 1)
        self.assertIn("sessions are tracked", err)

    def test_no_session_id_uses_current_only_when_unambiguous(self):
        self.init()
        tid = self.new_task()
        self.assertEqual(self.resolve()[1], tid)
        self.new_task("another")
        rc, out, err = self.resolve()
        self.assertEqual(rc, 1)
        self.assertIn("ambiguous", err)

    def test_env_var_binds_session_on_task_new(self):
        self.init()
        env = dict(os.environ, EAOS_SESSION_ID="env-sess")
        r = subprocess.run([sys.executable, EAOS, "task", "new", "env bound"],
                           cwd=self.cwd, capture_output=True, text=True, env=env)
        tid = r.stdout.strip()
        self.assertEqual(self.resolve("env-sess")[1], tid)

    def test_close_retargets_session_to_active_parent_else_removes(self):
        self.init()
        parent = self.new_task("parent")
        rc, child, _ = run(self.cwd, "task", "new", "child", "--parent", parent,
                           "--session", "s1")
        child = child.strip()
        self.assertEqual(self.resolve("s1")[1], child)
        run(self.cwd, "verify", child, "--criterion", "AC-1", "--verdict", "verified", "--evidence", "ran it")
        run(self.cwd, "episode", "close", child)
        self.assertEqual(self.resolve("s1")[1], parent)
        run(self.cwd, "verify", parent, "--criterion", "AC-1", "--verdict", "verified", "--evidence", "ran it")
        run(self.cwd, "episode", "close", parent)
        rc, out, err = self.resolve("s1")
        self.assertEqual(rc, 1)
        self.assertIn("no active task", err)
        self.assertFalse(os.path.exists(os.path.join(self.cwd, ".eaos", "sessions", "s1")))

    def test_bind_refuses_closed_task_and_rejects_bad_ids(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "verified", "--evidence", "ran it")
        run(self.cwd, "episode", "close", tid)
        rc, out, err = run(self.cwd, "session", "bind", tid, "--session", "s1")
        self.assertEqual(rc, 1)
        rc, out, err = run(self.cwd, "session", "bind", tid, "--session", "../evil")
        self.assertEqual(rc, 2)
        rc, out, err = run(self.cwd, "session", "bind", tid, "--session", ".hidden")
        self.assertEqual(rc, 2)


class TestFreshBind(EaosTestCase):
    """Round 5 item 2: the PostToolUse binder's `session bind --fresh` accepts only a
    recently created task that no other session claims — untrusted command text/stdout
    cannot hijack an established task."""

    def set_created(self, tid, iso):
        path = os.path.join(self.cwd, ".eaos", tid, "state.json")
        with open(path) as f:
            st = json.load(f)
        st["created"] = iso
        with open(path, "w") as f:
            json.dump(st, f)

    def test_fresh_bind_accepts_just_created_unclaimed_task(self):
        self.init()
        tid = self.new_task()
        rc, out, err = run(self.cwd, "session", "bind", tid, "--session", "s1", "--fresh")
        self.assertEqual(rc, 0, err)

    def test_fresh_bind_refuses_old_task(self):
        self.init()
        tid = self.new_task()
        self.set_created(tid, "2026-01-01T00:00:00")
        rc, out, err = run(self.cwd, "session", "bind", tid, "--session", "s1", "--fresh")
        self.assertEqual(rc, 1)
        self.assertIn("created", err)
        self.assertFalse(os.path.exists(os.path.join(self.cwd, ".eaos", "sessions", "s1")))

    def test_fresh_bind_refuses_task_claimed_by_another_session(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "session", "bind", tid, "--session", "owner")
        rc, out, err = run(self.cwd, "session", "bind", tid, "--session", "intruder", "--fresh")
        self.assertEqual(rc, 1)
        self.assertIn("already bound", err)
        # the same session re-binding its own task is fine (hook retry)
        rc, out, err = run(self.cwd, "session", "bind", tid, "--session", "owner", "--fresh")
        self.assertEqual(rc, 0, err)


class TestTaskNewIdempotencySession(EaosTestCase):
    """Round 5 item 4: the session is part of the task-new request."""

    def test_same_key_from_other_session_conflicts(self):
        self.init()
        rc, out, err = run(self.cwd, "task", "new", "x", "--session", "sa",
                           "--idempotency-key", "k1")
        self.assertEqual(rc, 0)
        rc, out, err = run(self.cwd, "task", "new", "x", "--session", "sb",
                           "--idempotency-key", "k1")
        self.assertEqual(rc, 1)
        self.assertIn("IDEMPOTENCY CONFLICT", out)
        self.assertFalse(os.path.exists(os.path.join(self.cwd, ".eaos", "sessions", "sb")))

    def test_replay_rebinds_session(self):
        self.init()
        rc, out, err = run(self.cwd, "task", "new", "x", "--session", "sa",
                           "--idempotency-key", "k1")
        tid = out.strip()
        os.remove(os.path.join(self.cwd, ".eaos", "sessions", "sa"))  # mapping lost
        rc, out, err = run(self.cwd, "task", "new", "x", "--session", "sa",
                           "--idempotency-key", "k1")
        self.assertEqual((rc, out.strip()), (0, tid))
        with open(os.path.join(self.cwd, ".eaos", "sessions", "sa")) as f:
            self.assertEqual(f.read().strip(), tid)


class TestProjectHeadAnchor(EaosTestCase):
    """Round 5 item 3: head truncation and coordinated state+journal rollback."""

    def check(self, tid, name):
        rc, out, err = run(self.cwd, "audit", tid, "--json")
        by_name = {c["name"]: c for c in json.loads(out)["checks"]}
        return rc, by_name[name]

    def test_journal_head_truncation_flagged(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        run(self.cwd, "spawn", tid, "--agent", "developer")
        jp = os.path.join(self.cwd, ".eaos", tid, "revisions.jsonl")
        with open(jp) as f:
            lines = f.readlines()
        with open(jp, "w") as f:
            f.writelines(lines[1:])   # drop the HEAD, keep the tail intact
        rc, check = self.check(tid, "revision_monotonicity")
        self.assertEqual(rc, 1)
        self.assertIn("journal head truncated", check["detail"])

    def test_coordinated_rollback_of_state_and_journal_flagged(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        tdir = os.path.join(self.cwd, ".eaos", tid)
        with open(os.path.join(tdir, "state.json"), "rb") as f:
            old_state = f.read()
        with open(os.path.join(tdir, "revisions.jsonl"), "rb") as f:
            old_journal = f.read()
        run(self.cwd, "spawn", tid, "--agent", "developer")
        run(self.cwd, "gate", tid, "DESIGN", "--check", "lint", "--pass")
        # restore BOTH files to the earlier consistent pair — inside the task dir the
        # journal and state agree perfectly
        with open(os.path.join(tdir, "state.json"), "wb") as f:
            f.write(old_state)
        with open(os.path.join(tdir, "revisions.jsonl"), "wb") as f:
            f.write(old_journal)
        rc, l = self.check(tid, "revision_monotonicity")
        self.assertTrue(l["ok"], l["detail"])           # the in-dir check is fooled...
        rc, n = self.check(tid, "project_head_anchor")
        self.assertEqual(rc, 1)
        self.assertFalse(n["ok"])                        # ...the project anchor is not
        self.assertIn("rollback", n["detail"])

    def test_clean_history_is_clean(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        run(self.cwd, "spawn", tid, "--agent", "developer")
        rc, n = self.check(tid, "project_head_anchor")
        self.assertEqual((rc, n["detail"]), (0, "clean"))


class TestLockStealAudit(EaosTestCase):
    """Round 5 item 6: a stolen stale lock is a discrepancy until acknowledged."""

    def test_steal_recorded_and_flagged_until_acknowledged(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        lock = os.path.join(self.cwd, ".eaos", tid, ".lock")
        with open(lock, "w") as f:
            f.write("1")
        old = 1_500_000_000
        os.utime(lock, (old, old))
        rc, out, err = run(self.cwd, "spawn", tid, "--agent", "developer")
        self.assertEqual(rc, 0, err)
        self.assertIn("stealing", err)
        rc, out, err = run(self.cwd, "audit", tid, "--json")
        self.assertEqual(rc, 1)
        m = {c["name"]: c for c in json.loads(out)["checks"]}["lock_steals"]
        self.assertIn("unacknowledged", m["detail"])   # the steal line itself must not ack
        with open(os.path.join(self.cwd, ".eaos", tid, "warroom.md")) as f:
            self.assertIn("LOCK STOLEN", f.read())
        rc, out, err = run(self.cwd, "append", tid, "--from", "human", "--to", "orchestrator",
                           "--type", "STATUS",
                           "--body", "lock-steal-ack: re-ran status, spawns/warroom agree")
        self.assertEqual(rc, 0, err)
        rc, out, err = run(self.cwd, "audit", tid, "--json")
        self.assertEqual(rc, 0, out)
        m = {c["name"]: c for c in json.loads(out)["checks"]}["lock_steals"]
        self.assertIn("acknowledged", m["detail"])


class TestReservedVerifierSpawn(EaosTestCase):
    """Real run 2026-09-09 (T-001 msg-039): at 12/12 the orchestrator applied the fix and
    re-graded it itself. The top slot(s) of the cap are reserved for a verifier."""

    def test_last_slot_refuses_non_verifier_and_accepts_verifier(self):
        self.init(max_spawns=3, reserve_loopbacks=0)  # verifier reserve 1 -> 2 general + 1 verifier
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        self.assertEqual(run(self.cwd, "spawn", tid, "--agent", "developer")[0], 0)
        self.assertEqual(run(self.cwd, "spawn", tid, "--agent", "qa-engineer")[0], 0)
        rc, out, err = run(self.cwd, "spawn", tid, "--agent", "developer")
        self.assertEqual(rc, 1)
        self.assertIn("RESERVED for a verifier", out)
        rc, out, err = run(self.cwd, "spawn", tid, "--agent", "verifier")
        self.assertEqual(rc, 0, out)
        rc, out, err = run(self.cwd, "spawn", tid, "--agent", "verifier")
        self.assertEqual(rc, 1)  # hard cap still binds the verifier too
        self.assertIn("BUDGET EXCEEDED", out)
        rc, out, err = run(self.cwd, "status", tid)
        self.assertIn("Spawns: 3/3", out)

    def test_reserve_configurable_to_zero(self):
        self.init(max_spawns=1, reserve_verifier=0, reserve_loopbacks=0)
        tid = self.new_task()
        self.assertEqual(run(self.cwd, "spawn", tid, "--agent", "developer")[0], 0)


class TestDoneWithoutEpisodeClose(EaosTestCase):
    """Real run 2026-09-09: 3 of 3 tasks reached DONE and never ran episode close."""

    def check(self, tid):
        rc, out, err = run(self.cwd, "audit", tid, "--json")
        return rc, {c["name"]: c for c in json.loads(out)["checks"]}["done_without_episode_close"]

    def test_done_without_close_is_a_discrepancy_until_closed(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DONE")
        rc, c = self.check(tid)
        self.assertEqual(rc, 1)
        self.assertIn("episode close", c["detail"])
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "verified", "--evidence", "ran it")
        rc, out, err = run(self.cwd, "episode", "close", tid)
        self.assertEqual(rc, 0, err)
        rc, c = self.check(tid)
        self.assertTrue(c["ok"])

    def test_active_task_not_yet_done_is_fine(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        rc, c = self.check(tid)
        self.assertTrue(c["ok"])


class TestVerifyDeferralLint(EaosTestCase):
    """Real run 2026-09-09 T-002: 'verified' with evidence 'HUMAN-RUN ... pending' and
    'SUPERSEDED ... satisfied-by-supersession' let --require exit 0."""

    def test_verified_with_deferral_evidence_is_refused(self):
        self.init()
        tid = self.new_task()
        for ev in ("HUMAN-RUN by spec design; recorded as manual-confirmation pending",
                   "SUPERSEDED by AC-32; graded as satisfied-by-supersession",
                   "not yet run — needs the role to exist"):
            rc, out, err = run(self.cwd, "verify", tid, "--criterion", "AC-27",
                               "--verdict", "verified", "--evidence", ev)
            self.assertEqual(rc, 2, ev)
            self.assertIn("reads like a deferral", err)
        rc, out, err = run(self.cwd, "verify", tid, "--require")
        self.assertEqual(rc, 1)  # nothing was recorded

    def test_honest_verdicts_with_same_evidence_are_accepted(self):
        self.init()
        tid = self.new_task()
        rc, out, err = run(self.cwd, "verify", tid, "--criterion", "AC-27",
                           "--verdict", "manual_confirmation_required",
                           "--evidence", "HUMAN-RUN: real dispatch pending role creation")
        self.assertEqual(rc, 0, err)
        rc, out, err = run(self.cwd, "verify", tid, "--require")
        self.assertEqual(rc, 3)

    def test_bulk_path_lints_too(self):
        self.init()
        tid = self.new_task()
        r = subprocess.run([sys.executable, EAOS, "verify", tid, "--bulk"], cwd=self.cwd,
                           input="AC-1 | verified | test_x green\nAC-2 | verified | skipped, human-run\n",
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        rc, out, err = run(self.cwd, "status", tid)
        self.assertNotIn("AC-1", out)  # batch is all-or-nothing


class TestOpenRisks(EaosTestCase):
    """Risk-to-test law: a high RISK must get a verdict before --require/report pass."""

    def test_high_risk_blocks_require_until_graded(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "verified",
            "--evidence", "tests green")
        rc, out, err = run(self.cwd, "append", tid, "--from", "sre-observability", "--to",
                           "orchestrator", "--type", "RISK", "--priority", "high",
                           "--body", "compliance crash-loops on next rebuild")
        self.assertEqual(rc, 0, err)
        msg = out.split()[1]
        rc, out, err = run(self.cwd, "verify", tid, "--require")
        self.assertEqual(rc, 1)
        self.assertIn("high RISK(s) without a verdict", out)
        self.assertIn(msg, out)
        rc, out, err = run(self.cwd, "report", tid)
        self.assertEqual(rc, 1)
        run(self.cwd, "verify", tid, "--criterion", f"R-{msg}", "--verdict", "failed",
            "--evidence", "rehearsal: image exits 1 'no ingress credentials'")
        rc, out, err = run(self.cwd, "verify", tid, "--require")
        self.assertEqual(rc, 1)  # failed is honest and still not done
        run(self.cwd, "verify", tid, "--criterion", f"R-{msg}", "--verdict", "blocked",
            "--evidence", "product decision needed: API keys vs auth-disabled")
        rc, out, err = run(self.cwd, "verify", tid, "--require")
        self.assertEqual(rc, 3)  # CONDITIONAL, not complete

    def test_low_priority_risk_does_not_open_a_slot(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "verified",
            "--evidence", "tests green")
        run(self.cwd, "append", tid, "--from", "dev", "--to", "orchestrator", "--type", "RISK",
            "--priority", "low", "--body", "nit")
        rc, out, err = run(self.cwd, "verify", tid, "--require")
        self.assertEqual(rc, 0)


class TestLoopbackReserve(EaosTestCase):
    """Zero-slack rosters were the 2026-09-09 blunder: cap 5 = 2 planning + 2 loop-back + 1
    verifier. Planning into the reserve is refused; a recorded loop-back opens it."""

    def test_planning_cap_then_loopback_opens_reserve(self):
        self.init(max_spawns=5)
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        self.assertEqual(run(self.cwd, "spawn", tid, "--agent", "developer")[0], 0)
        self.assertEqual(run(self.cwd, "spawn", tid, "--agent", "code-reviewer")[0], 0)
        rc, out, err = run(self.cwd, "spawn", tid, "--agent", "tech-writer")
        self.assertEqual(rc, 1)
        self.assertIn("planning cap is 2 of 5", out)
        # a verifier is never held back by the loop-back reserve
        self.assertEqual(run(self.cwd, "spawn", tid, "--agent", "verifier")[0], 0)
        rc, out, err = run(self.cwd, "loopback", tid, "--edge", "REVIEW->IMPLEMENT",
                           "--issue", "sec-10", "--attempt", "remove bootstrap assume")
        self.assertEqual(rc, 0, err)
        self.assertEqual(run(self.cwd, "spawn", tid, "--agent", "developer")[0], 0)
        rc, out, err = run(self.cwd, "status", tid)
        self.assertIn("Spawns: 4/5", out)


class TestCheckerFoldAudit(EaosTestCase):
    def test_folded_checker_is_a_discrepancy(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        run(self.cwd, "append", tid, "--from", "orchestrator", "--to", "all", "--type",
            "DECISION", "--body", "Security RE-REVIEW folded: orchestrator performs the "
            "mechanical diff check security described as '5-minute'")
        rc, out, err = run(self.cwd, "audit", tid, "--json")
        self.assertEqual(rc, 1)
        c = {x["name"]: x for x in json.loads(out)["checks"]}["checker_role_folded"]
        self.assertIn("maker=checker", c["detail"])

    def test_folding_a_non_checker_is_not_flagged(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        run(self.cwd, "append", tid, "--from", "orchestrator", "--to", "all", "--type",
            "DECISION", "--body", "tech-writer FOLDED into orchestrator (budget)")
        rc, out, err = run(self.cwd, "audit", tid, "--json")
        c = {x["name"]: x for x in json.loads(out)["checks"]}["checker_role_folded"]
        self.assertTrue(c["ok"])


class TestSingleVerdictAuthority(EaosTestCase):
    """v4 runtime contract R-1: episode close derives its verdict from the same function
    verify --require and report use. Reproduced 2026-09-17: open high RISK -> verify and
    report refused, episode still recorded 'verified'."""

    def test_open_high_risk_closes_as_unverified(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "verified",
            "--evidence", "tests green")
        run(self.cwd, "append", tid, "--from", "sre", "--to", "orchestrator", "--type", "RISK",
            "--priority", "high", "--body", "crash-loop on next rebuild")
        self.assertEqual(run(self.cwd, "verify", tid, "--require")[0], 1)
        self.assertEqual(run(self.cwd, "report", tid)[0], 1)
        rc, out, err = run(self.cwd, "episode", "close", tid)
        self.assertEqual(rc, 0, err)
        with open(os.path.join(self.cwd, ".eaos", "runs.jsonl")) as f:
            ep = json.loads(f.readlines()[-1])
        self.assertEqual(ep["verdict"], "unverified")

    def test_command_does_not_pin_a_model_under_inherit(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, "commands", "agentic-os.md")) as f:
            head = f.read().split("---")[1]
        with open(os.path.join(root, "orchestrator", "routing.yaml")) as f:
            routing = f.read()
        if "\n  mode: inherit" in routing:
            self.assertNotIn("\nmodel:", head,
                             "command frontmatter pins a model while routing says inherit")


class TestRiskRegistry(EaosTestCase):
    """v4 review 2, finding 1: one verdict function guarantees agreement, not correctness.
    The registry it trusts must not miss a protocol-shaped risk."""

    def setup_task(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "verified",
            "--evidence", "tests green")
        return tid

    def risk(self, tid, *extra, body="production crash remains unresolved"):
        return run(self.cwd, "append", tid, "--from", "sre", "--to", "orchestrator",
                   "--type", "RISK", "--body", body, *extra)

    def test_protocol_shaped_risk_blocks_completion_and_episode(self):
        """The reviewer's exact reproduction: priority blocking + 'severity: high' in body."""
        tid = self.setup_task()
        rc, out, err = self.risk(tid, "--priority", "blocking",
                                 body="severity: high; production crash remains unresolved")
        self.assertEqual(rc, 0, err)
        self.assertEqual(run(self.cwd, "verify", tid, "--require")[0], 1)
        run(self.cwd, "phase", tid, "DONE")
        run(self.cwd, "episode", "close", tid)
        with open(os.path.join(self.cwd, ".eaos", "runs.jsonl")) as f:
            self.assertEqual(json.loads(f.readlines()[-1])["verdict"], "unverified")

    def test_every_registration_path(self):
        for extra, body in ((("--severity", "high"), "x"), (("--severity", "critical"), "x"),
                            (("--priority", "blocking"), "x"), (("--priority", "high"), "x"),
                            ((), "Severity = HIGH, mitigation: none yet")):
            tid = self.setup_task()
            self.assertEqual(self.risk(tid, *extra, body=body)[0], 0, (extra, body))
            self.assertEqual(run(self.cwd, "verify", tid, "--require")[0], 1, (extra, body))
            self.tmp.cleanup(); self.setUp()

    def test_unclassified_risk_is_refused_not_silently_dropped(self):
        tid = self.setup_task()
        rc, out, err = self.risk(tid)
        self.assertEqual(rc, 2)
        self.assertIn("needs a severity", err)

    def test_low_and_medium_do_not_block(self):
        tid = self.setup_task()
        self.assertEqual(self.risk(tid, "--severity", "low")[0], 0)
        self.assertEqual(self.risk(tid, "--severity", "medium", body="second")[0], 0)
        self.assertEqual(run(self.cwd, "verify", tid, "--require")[0], 0)


class TestRiskSeverityContract(EaosTestCase):
    """v4 review 3: severity is part of the request, and an explicit flag wins or fails."""

    def setup_task(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        return tid

    def test_same_key_different_severity_is_a_conflict(self):
        tid = self.setup_task()
        base = ["append", tid, "--from", "sre", "--to", "o", "--type", "RISK", "--body", "x",
                "--idempotency-key", "risk-1"]
        self.assertEqual(run(self.cwd, *base, "--severity", "low")[0], 0)
        rc, out, err = run(self.cwd, *base, "--severity", "high")
        self.assertEqual(rc, 1)
        self.assertIn("IDEMPOTENCY CONFLICT", out + err)
        rc, out, err = run(self.cwd, *base, "--severity", "low")      # exact retry
        self.assertEqual(rc, 0)
        self.assertIn("msg-001", out)
        # equivalent spelling resolves to the same canonical severity -> still a replay
        self.assertEqual(run(self.cwd, *base, "--severity", "LOW")[0], 0)

    def test_invalid_explicit_severity_never_falls_back(self):
        tid = self.setup_task()
        rc, out, err = run(self.cwd, "append", tid, "--from", "sre", "--to", "o", "--type",
                           "RISK", "--severity", "hihg", "--priority", "low",
                           "--body", "severity: high")
        self.assertEqual(rc, 2)
        self.assertIn("invalid --severity", err)
        rc, out, err = run(self.cwd, "status", tid)
        self.assertNotIn("msg-001", out)

    def test_valid_flag_still_escalated_by_blocking_priority(self):
        tid = self.setup_task()
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "verified",
            "--evidence", "tests green")
        self.assertEqual(run(self.cwd, "append", tid, "--from", "sre", "--to", "o", "--type",
                             "RISK", "--severity", "low", "--priority", "blocking",
                             "--body", "x")[0], 0)
        self.assertEqual(run(self.cwd, "verify", tid, "--require")[0], 1)

    def test_verdict_recorded_before_the_risk_does_not_answer_it(self):
        tid = self.setup_task()
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "verified",
            "--evidence", "tests green")
        # pre-clear the predictable id, THEN raise the risk
        run(self.cwd, "verify", tid, "--criterion", "R-msg-001", "--verdict", "verified",
            "--evidence", "looks fine")
        path = os.path.join(self.cwd, ".eaos", tid, "state.json")
        with open(path) as f:
            st = json.load(f)
        st["criteria"]["R-msg-001"]["at"] = "2020-01-01T00:00:00"   # make the order unambiguous
        with open(path, "w") as f:
            json.dump(st, f)
        run(self.cwd, "append", tid, "--from", "sre", "--to", "o", "--type", "RISK",
            "--severity", "high", "--body", "crash-loop")
        rc, out, err = run(self.cwd, "verify", tid, "--require")
        self.assertEqual(rc, 1)
        self.assertIn("msg-001", out)


class TestRiskVerdictOrdering(EaosTestCase):
    """Review 4 finding 1: order by persisted sequence, not by a one-second wall clock."""

    SAME = "2026-09-17T12:00:00"

    def setup_task(self):
        self.init()
        tid = self.new_task()
        run(self.cwd, "phase", tid, "DESIGN")
        run(self.cwd, "verify", tid, "--criterion", "AC-1", "--verdict", "verified",
            "--evidence", "tests green")
        return tid

    def force_same_second(self, tid):
        path = os.path.join(self.cwd, ".eaos", tid, "state.json")
        with open(path) as f:
            st = json.load(f)
        for r in st.get("open_risks", []):
            r["at"] = self.SAME
        st["criteria"]["R-msg-001"]["at"] = self.SAME
        with open(path, "w") as f:
            json.dump(st, f)
        return st

    def risk(self, tid):
        return run(self.cwd, "append", tid, "--from", "sre", "--to", "o", "--type", "RISK",
                   "--severity", "high", "--body", "crash-loop")

    def verdict(self, tid):
        return run(self.cwd, "verify", tid, "--criterion", "R-msg-001", "--verdict",
                   "verified", "--evidence", "rehearsal ran clean")

    def test_verdict_before_risk_same_second_does_not_answer(self):
        tid = self.setup_task()
        self.verdict(tid)
        self.risk(tid)
        self.force_same_second(tid)
        rc, out, err = run(self.cwd, "verify", tid, "--require")
        self.assertEqual(rc, 1)
        self.assertIn("msg-001", out)

    def test_verdict_after_risk_same_second_answers(self):
        tid = self.setup_task()
        self.risk(tid)
        self.verdict(tid)
        st = self.force_same_second(tid)
        self.assertGreater(st["criteria"]["R-msg-001"]["seq"], st["open_risks"][0]["seq"])
        self.assertEqual(run(self.cwd, "verify", tid, "--require")[0], 0)

    def test_legacy_verdict_without_sequence_must_be_re_recorded(self):
        tid = self.setup_task()
        self.risk(tid)
        self.verdict(tid)
        path = os.path.join(self.cwd, ".eaos", tid, "state.json")
        with open(path) as f:
            st = json.load(f)
        del st["criteria"]["R-msg-001"]["seq"]          # a record from before this change
        del st["open_risks"][0]["seq"]
        with open(path, "w") as f:
            json.dump(st, f)
        self.assertEqual(run(self.cwd, "verify", tid, "--require")[0], 1)
        self.verdict(tid)                                # re-verification gets a sequence
        self.assertEqual(run(self.cwd, "verify", tid, "--require")[0], 0)


class TestExperimentOutcome(unittest.TestCase):
    """Review 4 finding 2: two-stage classification, every (quality, cost) pair mapped."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "experiment_outcome.py")
        spec = importlib.util.spec_from_file_location("experiment_outcome", path)
        cls.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.m)

    def test_quality_stage(self):
        q = self.m.quality
        self.assertEqual(q([(7, 5), (6, 5)], 7), "higher")
        self.assertEqual(q([(5, 5), (6, 6)], 7), "equal")
        self.assertEqual(q([(4, 5), (3, 6)], 7), "lower")
        self.assertEqual(q([(7, 5), (4, 5)], 7), "inconsistent")
        self.assertEqual(q([(6, 6), (7, 5)], 7), "inconsistent")   # equal once, higher once
        self.assertEqual(q([(7, 7), (7, 7)], 7), "ceiling")
        self.assertEqual(q([(7, 7), (6, 6)], 7), "equal")          # ceiling needs every repeat

    def test_cost_stage_takes_the_worst_repeat(self):
        c = self.m.cost
        self.assertEqual(c([(70, 100), (80, 100)]), "improved")
        self.assertEqual(c([(70, 100), (95, 100)]), "comparable")
        self.assertEqual(c([(100, 100), (120, 100)]), "comparable")
        self.assertEqual(c([(100, 100), (150, 100)]), "higher_within_budget")
        self.assertEqual(c([(90, 100), (201, 100)]), "over_budget")
        self.assertEqual(c([(200, 100), (200, 100)]), "higher_within_budget")   # 2.0x is within

    def test_every_pair_has_exactly_one_outcome(self):
        m = self.m
        for qv in m.QUALITY:
            for cv in m.COST:
                self.assertIn(m.OUTCOME[(qv, cv)], m.OUTCOMES, (qv, cv))
        self.assertEqual(len(m.OUTCOME), len(m.QUALITY) * len(m.COST))

    def test_the_cases_the_review_named(self):
        m = self.m
        self.assertEqual(m.OUTCOME[("equal", "improved")], "efficiency_win")      # not Noise
        self.assertEqual(m.OUTCOME[("equal", "comparable")], "tie")
        self.assertEqual(m.OUTCOME[("equal", "higher_within_budget")], "cost_regression")
        self.assertEqual(m.OUTCOME[("higher", "over_budget")], "mixed")
        self.assertEqual(m.OUTCOME[("higher", "higher_within_budget")], "win")
        self.assertEqual(m.OUTCOME[("ceiling", "improved")], "ceiling")
        self.assertEqual(m.OUTCOME[("inconsistent", "improved")], "noise")
        self.assertEqual(m.OUTCOME[("lower", "improved")], "loss")

    def test_invalid_runs_are_excluded_before_classification(self):
        r = self.m.classify([(7, 5), (6, 5)], [(100, 100), (110, 100)], 7, invalid=True)
        self.assertEqual(r["outcome"], "invalid")
        r = self.m.classify([(7, 7), (7, 7)], [(60, 100), (70, 100)], 7)
        self.assertEqual((r["outcome"], r["cost"]), ("ceiling", "improved"))     # cost still reported


class V4Case(EaosTestCase):
    """v4 runtime verbs run inside a real git repo (snapshots need one)."""

    def setUp(self):
        super().setUp()
        subprocess.run(["git", "init", "-q"], cwd=self.cwd, check=True)
        subprocess.run(["git", "config", "user.email", "t@t"], cwd=self.cwd, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=self.cwd, check=True)
        with open(os.path.join(self.cwd, "app.py"), "w") as f:
            f.write("X = 1\n")
        subprocess.run(["git", "add", "."], cwd=self.cwd, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=self.cwd, check=True)
        self.init()
        self.tid = self.new_task()
        run(self.cwd, "phase", self.tid, "DESIGN")

    def unit(self, title="work", kind="build", scope="app.py"):
        rc, out, err = run(self.cwd, "unit", "start", self.tid, "--title", title,
                           "--kind", kind, "--scope", scope)
        self.assertEqual(rc, 0, err)
        return out.strip()

    def snap(self):
        return run(self.cwd, "snapshot")[1].strip()

    def edit(self, text="Y = 2\n"):
        with open(os.path.join(self.cwd, "app.py"), "a") as f:
            f.write(text)


class TestSnapshot(V4Case):
    def test_product_edits_change_it_and_runtime_records_do_not(self):
        a = self.snap()
        run(self.cwd, "append", self.tid, "--from", "a", "--to", "b", "--type", "STATUS",
            "--body", "runtime record only")
        self.assertEqual(self.snap(), a)                       # .eaos/ excluded
        os.makedirs(os.path.join(self.cwd, "__pycache__"))
        with open(os.path.join(self.cwd, "__pycache__", "x.pyc"), "w") as f:
            f.write("cache")
        self.assertEqual(self.snap(), a)                       # cache noise excluded
        self.edit()
        self.assertNotEqual(self.snap(), a)                    # tracked modification
        with open(os.path.join(self.cwd, "new.py"), "w") as f:
            f.write("N = 1\n")
        b = self.snap()
        self.assertNotEqual(b, a)                              # untracked product file
        self.assertEqual(len(a), 64)


class TestCheckEvidence(V4Case):
    def test_passing_check_binds_to_snapshot_and_handoff_needs_it(self):
        u = self.unit()
        rc, out, err = run(self.cwd, "unit", "handoff", self.tid, u, "--ready")
        self.assertEqual(rc, 1)
        self.assertIn("no check recorded against the current code", out)
        rc, out, err = run(self.cwd, "check", self.tid, "--category", "test",
                           "--cmd", "python3 -c 'import sys; sys.exit(0)'", "--unit", u)
        self.assertEqual(rc, 0, out + err)
        self.assertIn("snapshot=", out)
        rc, out, err = run(self.cwd, "unit", "handoff", self.tid, u, "--ready")
        self.assertEqual(rc, 0, out)
        log = os.listdir(os.path.join(self.cwd, ".eaos", self.tid, "checks"))
        self.assertEqual(len(log), 1)

    def test_failing_check_records_and_refuses_ready(self):
        u = self.unit()
        rc, out, err = run(self.cwd, "check", self.tid, "--category", "test", "--cmd", "false")
        self.assertEqual(rc, 1)
        self.assertIn("CHECK FAILED", out)
        self.assertEqual(run(self.cwd, "unit", "handoff", self.tid, u, "--ready")[0], 1)
        rc, out, err = run(self.cwd, "unit", "handoff", self.tid, u, "--blocked",
                           "--reason", "tests fail on the ledger path")
        self.assertEqual(rc, 0)
        self.assertIn("not a success claim", out)

    def test_code_change_after_check_invalidates_all_evidence(self):
        u = self.unit()
        run(self.cwd, "check", self.tid, "--category", "test", "--cmd", "true")
        self.edit()
        rc, out, err = run(self.cwd, "unit", "handoff", self.tid, u, "--ready")
        self.assertEqual(rc, 1)
        self.assertIn("no check recorded against the current code", out)

    def test_check_that_mutates_product_files_is_unstable(self):
        rc, out, err = run(self.cwd, "check", self.tid, "--category", "lint",
                           "--cmd", "echo Z=3 >> app.py")
        self.assertEqual(rc, 1)
        self.assertIn("SNAPSHOT-UNSTABLE", out)

    def test_unavailable_never_satisfies_ready(self):
        """v4 review 1, finding 1: unavailable explains BLOCKED or an auditable waiver."""
        u = self.unit()
        rc, out, err = run(self.cwd, "check", self.tid, "--category", "test", "--unavailable")
        self.assertEqual(rc, 2)
        rc, out, err = run(self.cwd, "check", self.tid, "--category", "test", "--unavailable",
                           "--reason", "no test suite exists in this repository")
        self.assertEqual(rc, 0, err)
        rc, out, err = run(self.cwd, "unit", "handoff", self.tid, u, "--ready")
        self.assertEqual(rc, 1)
        self.assertIn("UNAVAILABLE", out)
        self.assertIn("not a pass", out)
        # explicit, auditable waiver: allowed, and completion becomes CONDITIONAL
        rc, out, err = run(self.cwd, "unit", "handoff", self.tid, u, "--ready", "--waive", "test")
        self.assertEqual(rc, 2)                                         # needs --reason
        rc, out, err = run(self.cwd, "unit", "handoff", self.tid, u, "--ready", "--waive", "test",
                           "--reason", "repo has no suite; checker will exercise manually")
        self.assertEqual(rc, 0, out)
        self.assertIn("WAIVED", out)
        run(self.cwd, "verify", self.tid, "--criterion", "AC-1", "--verdict", "verified",
            "--evidence", "manual exercise")
        rc, out, err = run(self.cwd, "verify", self.tid, "--require")
        self.assertEqual(rc, 3)
        self.assertIn("waived", out)
        run(self.cwd, "phase", self.tid, "DONE")
        run(self.cwd, "episode", "close", self.tid)
        with open(os.path.join(self.cwd, ".eaos", "runs.jsonl")) as f:
            self.assertEqual(json.loads(f.readlines()[-1])["verdict"], "conditional-manual")

    def test_latest_result_decides_a_newer_failure_blocks(self):
        """v4 review 1, finding 2."""
        u = self.unit()
        self.assertEqual(run(self.cwd, "check", self.tid, "--category", "test", "--cmd", "true")[0], 0)
        self.assertEqual(run(self.cwd, "check", self.tid, "--category", "test", "--cmd", "false")[0], 1)
        rc, out, err = run(self.cwd, "unit", "handoff", self.tid, u, "--ready")
        self.assertEqual(rc, 1)
        self.assertIn("FAILED", out)
        self.assertEqual(run(self.cwd, "check", self.tid, "--category", "test", "--cmd", "true")[0], 0)
        self.assertEqual(run(self.cwd, "unit", "handoff", self.tid, u, "--ready")[0], 0)

    def test_read_units_need_no_evidence(self):
        u = self.unit(kind="read")
        self.assertEqual(run(self.cwd, "unit", "handoff", self.tid, u, "--ready")[0], 0)


class TestBoard(V4Case):
    def post(self, *extra, summary="a finding", type_="finding"):
        return run(self.cwd, "board", "post", self.tid, "--type", type_, "--summary", summary,
                   *extra)

    def test_summary_cap_and_ref(self):
        rc, out, err = self.post(summary="x" * 401)
        self.assertEqual(rc, 2)
        self.assertIn("400", err)
        rc, out, err = self.post(summary="x" * 400, *["--ref", "notes.md"])
        self.assertEqual(rc, 0, err)

    def test_runtime_metadata_is_generated(self):
        self.post()
        with open(os.path.join(self.cwd, ".eaos", self.tid, "state.json")) as f:
            e = json.load(f)["board"]["entries"]["B-001"]
        for k in ("id", "revision", "author", "status", "snapshot", "seq", "at"):
            self.assertIn(k, e)
        self.assertEqual((e["revision"], e["status"], e["author"]), (1, "active", "lead"))

    def test_invalidates_marks_unit_stale_and_reconcile_clears(self):
        u = self.unit()
        run(self.cwd, "check", self.tid, "--category", "test", "--cmd", "true")
        r = self.unit(title="research", kind="read")
        rc, out, err = self.post("--unit", r, "--invalidates", u,
                                 summary="refunds use a different ledger")
        self.assertEqual(rc, 0, err)
        rc, out, err = run(self.cwd, "unit", "handoff", self.tid, u, "--ready")
        self.assertEqual(rc, 1)
        self.assertIn("STALE", out)
        self.assertIn("unreconciled", out)
        rc, out, err = run(self.cwd, "board", "reconcile", self.tid, u, "--entry", "B-001",
                           "--disposition", "not-applicable")
        self.assertEqual(rc, 2)                                   # needs a note
        rc, out, err = run(self.cwd, "board", "reconcile", self.tid, u, "--entry", "B-001",
                           "--disposition", "acted")
        self.assertEqual(rc, 0, err)
        self.assertEqual(run(self.cwd, "unit", "handoff", self.tid, u, "--ready")[0], 0)

    def test_out_of_scope_changes_do_not_block(self):
        u = self.unit(scope="app.py")
        run(self.cwd, "check", self.tid, "--category", "test", "--cmd", "true")
        self.post("--scope", "docs/**", summary="docs only")
        self.assertEqual(run(self.cwd, "unit", "handoff", self.tid, u, "--ready")[0], 0)

    def test_diff_since_unit_start(self):
        u = self.unit(scope="app.py")
        self.post(summary="in scope", *["--scope", "app.py"])
        self.post(summary="elsewhere", *["--scope", "docs/**"])
        rc, out, err = run(self.cwd, "board", "diff", self.tid, "--unit", u)
        self.assertEqual(rc, 0)
        self.assertIn("B-001", out)
        self.assertNotIn("B-002", out)

    def test_view_never_silently_omits_blocking(self):
        for i in range(4):
            self.post("--severity", "blocking", type_="risk", summary=f"blocking {i} " + "x" * 200)
        rc, out, err = run(self.cwd, "board", "view", self.tid, "--for", "checker",
                           "--budget", "60")
        self.assertEqual(rc, 3)
        self.assertIn("INCOMPLETE", out)
        rc, out, err = run(self.cwd, "board", "view", self.tid, "--for", "checker",
                           "--budget", "5000")
        self.assertEqual(rc, 0)
        self.assertNotIn("INCOMPLETE", out)

    def test_checker_view_excludes_maker_claims(self):
        self.post(type_="claim", summary="I implemented it correctly")
        self.post(type_="decision", summary="tags stored lowercase")
        rc, out, err = run(self.cwd, "board", "view", self.tid, "--for", "checker")
        self.assertNotIn("B-001", out)
        self.assertIn("B-002", out)
        rc, out, err = run(self.cwd, "board", "view", self.tid, "--for", "lead")
        self.assertIn("B-001", out)

    def test_risk_posts_register_for_verdict(self):
        run(self.cwd, "verify", self.tid, "--criterion", "AC-1", "--verdict", "verified",
            "--evidence", "green")
        self.post("--severity", "high", type_="risk", summary="crash-loop")
        self.assertEqual(run(self.cwd, "verify", self.tid, "--require")[0], 1)
        run(self.cwd, "verify", self.tid, "--criterion", "R-B-001", "--verdict", "blocked",
            "--evidence", "product decision pending")
        self.assertEqual(run(self.cwd, "verify", self.tid, "--require")[0], 3)

    def test_supersedes_and_resolve(self):
        self.post(type_="decision", summary="old")
        self.post(type_="decision", summary="new", *["--supersedes", "B-001"])
        rc, out, err = run(self.cwd, "board", "view", self.tid)
        self.assertNotIn("B-001", out)
        run(self.cwd, "board", "resolve", self.tid, "B-002", "--status", "resolved")
        rc, out, err = run(self.cwd, "board", "view", self.tid)
        self.assertNotIn("B-002", out)


class TestWriterLease(V4Case):
    def test_one_writer_and_release_on_ready(self):
        u1, u2 = self.unit("a"), self.unit("b")
        self.assertEqual(run(self.cwd, "writer", "claim", self.tid, "--unit", u1)[0], 0)
        rc, out, err = run(self.cwd, "writer", "claim", self.tid, "--unit", u2)
        self.assertEqual(rc, 1)
        self.assertIn("WRITER HELD", out)
        run(self.cwd, "check", self.tid, "--category", "test", "--cmd", "true")
        self.assertEqual(run(self.cwd, "unit", "handoff", self.tid, u1, "--ready")[0], 0)
        self.assertEqual(run(self.cwd, "writer", "claim", self.tid, "--unit", u2)[0], 0)

    def test_lease_is_per_workspace_across_tasks(self):
        """v4 review 1, finding 5: two tasks in one directory share one pen."""
        u1 = self.unit("a")
        self.assertEqual(run(self.cwd, "writer", "claim", self.tid, "--unit", u1)[0], 0)
        t2 = self.new_task("second task")
        rc, out, err = run(self.cwd, "unit", "start", t2, "--title", "b", "--kind", "build")
        u2 = out.strip()
        rc, out, err = run(self.cwd, "writer", "claim", t2, "--unit", u2)
        self.assertEqual(rc, 1)
        self.assertIn(f"{self.tid}/{u1}", out)
        self.assertTrue(os.path.exists(os.path.join(self.cwd, ".eaos", "writer.json")))
        # blocked handoff releases the pen
        run(self.cwd, "unit", "handoff", self.tid, u1, "--blocked", "--reason", "stuck")
        self.assertEqual(run(self.cwd, "writer", "claim", t2, "--unit", u2)[0], 0)
        # abandoned holder: only --force --reason recovers it, logged to both tasks
        rc, out, err = run(self.cwd, "writer", "release", self.tid, "--unit", u1)
        self.assertEqual(rc, 1)
        rc, out, err = run(self.cwd, "writer", "release", self.tid, "--unit", u1, "--force")
        self.assertEqual(rc, 2)
        rc, out, err = run(self.cwd, "writer", "release", self.tid, "--unit", u1, "--force",
                           "--reason", "holder session died")
        self.assertEqual(rc, 0, err)
        with open(os.path.join(self.cwd, ".eaos", t2, "warroom.md")) as f:
            self.assertIn("FORCE", f.read())


class TestCompletionConsumesUnits(V4Case):
    """v4 review 1, finding 3: blocked, stale or active units and void evidence block a
    verified outcome; cancel is the explicit disposition."""

    def verified_ac(self):
        run(self.cwd, "verify", self.tid, "--criterion", "AC-1", "--verdict", "verified",
            "--evidence", "green")

    def episode_verdict(self):
        run(self.cwd, "phase", self.tid, "DONE")
        run(self.cwd, "episode", "close", self.tid)
        with open(os.path.join(self.cwd, ".eaos", "runs.jsonl")) as f:
            return json.loads(f.readlines()[-1])["verdict"]

    def test_blocked_unit_blocks_completion_until_cancelled_or_ready(self):
        u = self.unit()
        self.verified_ac()
        run(self.cwd, "unit", "handoff", self.tid, u, "--blocked", "--reason", "cannot run tests")
        rc, out, err = run(self.cwd, "verify", self.tid, "--require")
        self.assertEqual(rc, 1)
        self.assertIn("BLOCKED", out)
        self.assertEqual(run(self.cwd, "report", self.tid)[0], 1)
        rc, out, err = run(self.cwd, "unit", "cancel", self.tid, u)
        self.assertEqual(rc, 2)                                         # reason required
        rc, out, err = run(self.cwd, "unit", "cancel", self.tid, u, "--reason", "out of scope")
        self.assertEqual(rc, 0, err)
        # no build unit remains -> criteria decide
        self.assertEqual(run(self.cwd, "verify", self.tid, "--require")[0], 0)

    def test_blocked_build_closes_unverified(self):
        u = self.unit()
        self.verified_ac()
        run(self.cwd, "unit", "handoff", self.tid, u, "--blocked", "--reason", "cannot run tests")
        self.assertEqual(self.episode_verdict(), "unverified")

    def test_evidence_void_after_edit_blocks_completion(self):
        u = self.unit()
        self.verified_ac()
        run(self.cwd, "check", self.tid, "--category", "test", "--cmd", "true")
        self.assertEqual(run(self.cwd, "unit", "handoff", self.tid, u, "--ready")[0], 0)
        self.assertEqual(run(self.cwd, "verify", self.tid, "--require")[0], 0)
        self.edit()                                                     # code changed after handoff
        rc, out, err = run(self.cwd, "verify", self.tid, "--require")
        self.assertEqual(rc, 1)
        self.assertIn("void", out)
        run(self.cwd, "check", self.tid, "--category", "test", "--cmd", "true")
        self.assertEqual(run(self.cwd, "verify", self.tid, "--require")[0], 0)

    def test_stale_unit_blocks_completion(self):
        u = self.unit()
        self.verified_ac()
        run(self.cwd, "check", self.tid, "--category", "test", "--cmd", "true")
        r = self.unit("research", kind="read")
        run(self.cwd, "board", "post", self.tid, "--type", "finding", "--summary", "ledger differs",
            "--unit", r, "--invalidates", u)
        run(self.cwd, "unit", "handoff", self.tid, r, "--ready")
        rc, out, err = run(self.cwd, "verify", self.tid, "--require")
        self.assertEqual(rc, 1)
        self.assertIn("STALE", out)


class TestNoGitSnapshot(EaosTestCase):
    def test_tree_hash_changes_with_product_edits(self):
        """v4 review 1, finding 4: outside git the snapshot must still track product files."""
        self.init()
        with open(os.path.join(self.cwd, "app.py"), "w") as f:
            f.write("before\n")
        a = run(self.cwd, "snapshot")[1].strip()
        with open(os.path.join(self.cwd, "app.py"), "w") as f:
            f.write("after\n")
        b = run(self.cwd, "snapshot")[1].strip()
        self.assertNotEqual(a, b)
        self.assertEqual(run(self.cwd, "snapshot")[1].strip(), b)          # deterministic
        run(self.cwd, "task", "new", "x")                                   # .eaos/ changes
        self.assertEqual(run(self.cwd, "snapshot")[1].strip(), b)          # excluded


class TestPacketAndContext(V4Case):
    def test_packet_is_bounded_and_names_next_action(self):
        u = self.unit()
        run(self.cwd, "board", "post", self.tid, "--type", "decision", "--summary", "utc only")
        rc, out, err = run(self.cwd, "status", "--packet", self.tid)
        self.assertEqual(rc, 0, err)
        for s in ("CONTINUATION PACKET", "snapshot", u, "B-001", "next:"):
            self.assertIn(s, out)
        self.assertLess(len(out), 6000)

    def test_context_ceiling_is_advisory_exit_3(self):
        self.assertEqual(run(self.cwd, "ctx", self.tid, "--tokens", "1000")[0], 0)
        rc, out, err = run(self.cwd, "ctx", self.tid, "--tokens", "160000")
        self.assertEqual(rc, 3)
        self.assertIn("advisory", out)
        rc, out, err = run(self.cwd, "status", "--packet", self.tid)
        self.assertIn("OVER CEILING", out)


class TestWaiverPath(V4Case):
    """v4 review 2, finding 1: the whole conditional path — handoff with a waiver, verify,
    REPORT, episode — including a manual criterion alongside the waiver."""

    def test_handoff_verify_report_episode_with_waiver_and_manual(self):
        u = self.unit()
        run(self.cwd, "check", self.tid, "--category", "test", "--unavailable",
            "--reason", "runner unavailable")
        rc, out, err = run(self.cwd, "unit", "handoff", self.tid, u, "--ready", "--waive", "test",
                           "--reason", "runner unavailable")
        self.assertEqual(rc, 0, out)
        run(self.cwd, "verify", self.tid, "--criterion", "AC-1", "--verdict", "verified",
            "--evidence", "independent behaviour check")
        run(self.cwd, "verify", self.tid, "--criterion", "AC-2", "--verdict",
            "manual_confirmation_required", "--evidence", "needs the owner to click through")
        rc, out, err = run(self.cwd, "verify", self.tid, "--require")
        self.assertEqual(rc, 3, out)
        self.assertIn("waived", out)
        self.assertIn("AC-2", out)
        rc, out, err = run(self.cwd, "report", self.tid)
        self.assertEqual(rc, 0, err + out)
        with open(os.path.join(self.cwd, ".eaos", self.tid, "artifacts", "final-report.md")) as f:
            rep = f.read()
        self.assertIn("Waived required checks", rep)
        self.assertIn("runner unavailable", rep)
        run(self.cwd, "phase", self.tid, "DONE")
        rc, out, err = run(self.cwd, "episode", "close", self.tid)
        self.assertEqual(rc, 0, err)
        with open(os.path.join(self.cwd, ".eaos", "runs.jsonl")) as f:
            self.assertEqual(json.loads(f.readlines()[-1])["verdict"], "conditional-manual")
        rc, out, err = run(self.cwd, "status", "--packet", self.tid)
        self.assertIn("waived", out)


class TestUnitLockContract(V4Case):
    """v4 review 2, finding 2: exit 4 means nothing mutated, for unit state AND the lease."""

    def test_contention_leaves_unit_and_lease_unchanged(self):
        u = self.unit()
        self.assertEqual(run(self.cwd, "writer", "claim", self.tid, "--unit", u)[0], 0)
        lock = os.path.join(self.cwd, ".eaos", ".lock")
        with open(lock, "w") as f:
            f.write("999999")
        try:
            rc, out, err = run(self.cwd, "unit", "handoff", self.tid, u, "--blocked",
                               "--reason", "stuck")
            self.assertEqual(rc, 4, err)
        finally:
            os.remove(lock)
        with open(os.path.join(self.cwd, ".eaos", self.tid, "state.json")) as f:
            self.assertEqual(json.load(f)["units"][u]["status"], "active")
        self.assertTrue(os.path.exists(os.path.join(self.cwd, ".eaos", "writer.json")))

    def test_stale_holder_is_recovered_on_claim(self):
        """Crash between the state write and the lease removal leaves a lease held by a
        non-active unit; the next claim recovers it and logs the recovery."""
        u = self.unit()
        run(self.cwd, "writer", "claim", self.tid, "--unit", u)
        # simulate the crash: mark the unit blocked out of band, leave writer.json in place
        path = os.path.join(self.cwd, ".eaos", self.tid, "state.json")
        with open(path) as f:
            st = json.load(f)
        st["units"][u]["status"] = "blocked"
        with open(path, "w") as f:
            json.dump(st, f)
        u2 = self.unit("next")
        rc, out, err = run(self.cwd, "writer", "claim", self.tid, "--unit", u2)
        self.assertEqual(rc, 0, out)
        with open(os.path.join(self.cwd, ".eaos", self.tid, "warroom.md")) as f:
            self.assertIn("recovered stale lease", f.read())


class TestScenarios(V4Case):
    """v4 K-2/K-3: builder-blind, checker-graded, binding on completion."""

    def setUp(self):
        super().setUp()
        self.scn_home = tempfile.mkdtemp()
        os.environ["EAOS_SCENARIO_HOME"] = self.scn_home

    def tearDown(self):
        os.environ.pop("EAOS_SCENARIO_HOME", None)
        super().tearDown()

    def add(self, title="expired link", req="links expire after 7 days"):
        rc, out, err = run(self.cwd, "scenario", "add", self.tid, "--title", title,
                           "--given", "a link created 8 days ago", "--when", "it is visited",
                           "--then", "the response does not redirect", "--requirement", req)
        self.assertEqual(rc, 0, err)
        return out.strip()

    def test_content_lives_outside_the_workspace(self):
        sid = self.add()
        inside = subprocess.run(["grep", "-rl", "8 days ago", self.cwd], capture_output=True, text=True)
        self.assertEqual(inside.stdout.strip(), "")            # nothing in the workspace
        self.assertTrue(any("T-001" in f for f in os.listdir(os.path.join(self.scn_home, os.listdir(self.scn_home)[0]))))
        with open(os.path.join(self.cwd, ".eaos", self.tid, "warroom.md")) as f:
            wr = f.read()
        self.assertIn(sid, wr)
        self.assertNotIn("8 days ago", wr)                     # the war room carries the id only

    def test_incomplete_scenario_refused(self):
        rc, out, err = run(self.cwd, "scenario", "add", self.tid, "--title", "x", "--given", "g")
        self.assertEqual(rc, 2)

    def test_ungraded_scenario_blocks_completion(self):
        sid = self.add()
        run(self.cwd, "verify", self.tid, "--criterion", "AC-1", "--verdict", "verified",
            "--evidence", "green")
        rc, out, err = run(self.cwd, "verify", self.tid, "--require")
        self.assertEqual(rc, 1)
        self.assertIn(sid, out)
        rc, out, err = run(self.cwd, "scenario", "grade", self.tid, sid, "--verdict", "verified",
                           "--evidence", "created a link with created_at -8d; GET /abc -> 410")
        self.assertEqual(rc, 0, err)
        self.assertEqual(run(self.cwd, "verify", self.tid, "--require")[0], 0)

    def test_grade_needs_executed_evidence(self):
        sid = self.add()
        rc, out, err = run(self.cwd, "scenario", "grade", self.tid, sid, "--verdict", "verified")
        self.assertEqual(rc, 2)
        rc, out, err = run(self.cwd, "scenario", "grade", self.tid, sid, "--verdict", "verified",
                           "--evidence", "would pass once the runner is available")
        self.assertEqual(rc, 2)
        self.assertIn("deferral", err)

    def test_shared_evidence_across_scenarios_refused(self):
        a = self.add(); b = self.add(title="unknown link", req="unknown links 404")
        ev = "Covered by executed tests in route.test.ts; mutation-checked"
        self.assertEqual(run(self.cwd, "scenario", "grade", self.tid, a, "--verdict", "verified", "--evidence", ev)[0], 0)
        rc, out, err = run(self.cwd, "scenario", "grade", self.tid, b, "--verdict", "verified", "--evidence", "  covered by executed tests in route.test.ts;  mutation-checked")
        self.assertEqual(rc, 2)
        self.assertIn("identical", err)
        rc, out, err = run(self.cwd, "scenario", "grade", self.tid, b, "--verdict", "verified",
                           "--evidence", "route.test.ts 'unknown slug' -> 404; flipping the lookup made it fail")
        self.assertEqual(rc, 0, err)

    def test_failure_reveals_and_becomes_regression(self):
        sid = self.add()
        rc, out, err = run(self.cwd, "scenario", "grade", self.tid, sid, "--verdict", "failed",
                           "--evidence", "GET /abc redirected 302 to the target")
        self.assertEqual(rc, 0, err)
        self.assertIn("revealed", out)
        rc, out, err = run(self.cwd, "scenario", "list", self.tid, "--revealed")
        self.assertIn(sid, out)
        self.assertEqual(run(self.cwd, "verify", self.tid, "--require")[0], 1)   # failed is honest
        rc, out, err = run(self.cwd, "scenario", "list", self.tid, "--for", "checker")
        self.assertIn("given:", out)


class TestSessionResumeBind(V4Case):
    """Run 8: a fresh context resuming a task never ran `task new`, so nothing bound it."""

    def test_orphan_task_binds_and_claimed_task_refuses(self):
        rc, out, err = run(self.cwd, "session", "bind", self.tid, "--session", "ctx2", "--resume")
        self.assertEqual(rc, 0, err)
        rc, out, err = run(self.cwd, "session", "bind", self.tid, "--session", "ctx3", "--resume")
        self.assertEqual(rc, 1)
        self.assertIn("already bound", err)
        self.assertEqual(run(self.cwd, "session", "resolve", "--session", "ctx2")[1].strip(), self.tid)

    def test_session_working_another_active_task_refuses(self):
        other = run(self.cwd, "task", "new", "second task", "--kind", "chore")[1].strip().splitlines()[-1]
        run(self.cwd, "session", "bind", other, "--session", "ctx2")
        rc, out, err = run(self.cwd, "session", "bind", self.tid, "--session", "ctx2", "--resume")
        self.assertEqual(rc, 1)
        self.assertIn("is working", err)

    def test_legacy_dir_without_state_is_silent(self):
        os.makedirs(os.path.join(self.cwd, ".eaos", "T-900"))
        rc, out, err = run(self.cwd, "task", "new", "third", "--kind", "chore")
        self.assertEqual(rc, 0, err)
        self.assertNotIn("no state.json", out + err)


class TestCloseNeedsAJudgement(V4Case):
    """Run 10: a mistyped verify chained with episode close shut the task with zero criteria."""

    def test_zero_criteria_close_refused_then_abandon_or_verify(self):
        other = run(self.cwd, "task", "new", "never judged", "--kind", "chore", "--stakes", "toy")[1].strip().splitlines()[-1]
        rc, out, err = run(self.cwd, "episode", "close", other)
        self.assertEqual(rc, 1)
        self.assertIn("--abandon", err)
        self.assertEqual(run(self.cwd, "episode", "close", other, "--abandon")[0], 2)
        rc, out, err = run(self.cwd, "episode", "close", other, "--abandon", "--reason", "nothing to fix")
        self.assertEqual(rc, 0, err)
        self.assertIn("unverified", out)

    def test_status_is_an_alias_of_verdict(self):
        rc, out, err = run(self.cwd, "verify", self.tid, "--criterion", "AC-1", "--status", "verified",
                           "--evidence", "grep found the line")
        self.assertEqual(rc, 0, err)


if __name__ == "__main__":
    unittest.main()
