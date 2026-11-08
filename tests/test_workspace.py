import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("workspace", Path(__file__).resolve().parents[1] / "scripts/workspace.py")
workspace = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workspace)


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "project.json"
        self.work = workspace.Workspace(self.path)
        self.work.init("Improve deployment score and understand the method", "demo")

    def tearDown(self):
        self.temp.cleanup()

    def test_late_result_keeps_newer_budget_and_learning_state(self):
        self.work.record({"outcome": "fresh state", "budget": {"remaining": 4000}, "learning": {"state": "user_completed"}})
        self.work.next({"id": "new-plan", "instruction": "current work"})
        self.work.record({"action_id": "old-job", "outcome": "late observation", "budget": {"remaining": 8000}, "learning": {"state": "pending"}})
        state = self.work.status()
        self.assertEqual(state["budget"]["remaining"], 4000)
        self.assertEqual(state["learning"]["state"], "user_completed")
        self.assertEqual(state["recent_experiments"][-1]["proposed_budget"]["remaining"], 8000)

    def test_resume_carries_real_command_result_and_next_action(self):
        command = {"id": "object-probe", "kind": "cpu", "cwd": "/project", "command": ["python", "probe.py"], "expected_results": ["raw.json"]}
        self.work.next(command)
        self.work.start("object-probe")
        self.work.record({"id": "exp-1", "action_id": "object-probe", "hypothesis": "new representation reaches missed objects", "control": "baseline-v1",
                          "outcome": "no new correct outputs", "evidence": ["raw.json"],
                          "next_action": {"id": "inspect-coverage", "instruction": "Read raw.json and separate generation from selection failures"}})
        resumed = workspace.Workspace(self.path).status()
        self.assertEqual(resumed["recent_experiments"][0]["control"], "baseline-v1")
        self.assertEqual(resumed["next_action"]["id"], "inspect-coverage")
        self.assertIsNone(resumed["champion"])

    def test_tests_do_not_promote_and_explicit_real_measurement_can(self):
        self.work.record({"outcome": "54 tests passed"})
        self.assertIsNone(self.work.status()["champion"])
        with self.assertRaises(ValueError):
            self.work.record({"outcome": "tests pass", "adopt": {"candidate": "v2", "basis": "tests", "measurement": "54 PASS", "evidence": ["tests.log"]}})
        self.work.record({"outcome": "same frozen outputs in 20% less runtime", "adopt": {"candidate": "v2", "basis": "cost",
            "measurement": {"control_seconds": 100, "candidate_seconds": 80, "output_comparison": "identical"}, "evidence": ["paired-run.json"]}})
        self.assertEqual(self.work.status()["champion"]["candidate"], "v2")

    def test_uncertain_remote_is_not_resent_and_cpu_can_continue(self):
        remote = {"id": "upload-v2", "kind": "remote", "remote_id": "kaggle-v2", "instruction": "Push the prepared private notebook once"}
        self.work.next(remote)
        self.work.start("upload-v2")
        with self.assertRaises(ValueError): self.work.start("upload-v2")
        with self.assertRaises(ValueError): self.work.next(remote)
        self.work.next({"id": "cpu-diagnosis", "kind": "cpu", "instruction": "Inspect the retained raw result"})
        self.work.start("cpu-diagnosis")
        self.work.record({"outcome": "provider history confirms notebook accepted", "remote": {"id": "kaggle-v2", "state": "running", "provider_id": "owner/kernel/7", "observation": "Official kernel version 7 RUNNING"},
            "next_action": {"id": "monitor-v2", "kind": "monitor", "remote_id": "kaggle-v2", "instruction": "Read version 7 status and collect outputs when complete"}})
        self.assertEqual(self.work.start("monitor-v2")["action"]["kind"], "monitor")
        self.assertEqual(self.work.status()["remote_jobs"]["kaggle-v2"]["provider_id"], "owner/kernel/7")

    def test_positive_no_write_observation_allows_host_to_choose_retry(self):
        self.work.next({"id": "push", "kind": "remote", "remote_id": "upload", "instruction": "Push once"})
        self.work.start("push")
        self.work.record({"outcome": "Official history confirms no request was accepted", "remote": {"id": "upload", "state": "no_write", "observation": "Exact version absent from fresh provider history"},
            "next_action": {"id": "retry-push", "kind": "remote", "remote_id": "upload", "instruction": "Retry after fixing the network failure"}})
        self.work.start("retry-push")
        self.assertEqual(self.work.status()["remote_jobs"]["upload"]["state"], "uncertain")

    def test_unknown_remote_retains_full_action_after_switch_to_cpu_and_restart(self):
        remote = {"id": "save-seven", "kind": "remote", "remote_id": "trial-A", "cwd": "/project",
                  "command": ["kaggle", "kernels", "push", "-p", "packet-seven"],
                  "instruction": "Save owner/exact-notebook, expected version 7", "expected_results": ["provider.json"]}
        self.work.next(remote)
        self.work.start("save-seven")
        self.work.next({"id": "local-analysis", "instruction": "Inspect existing failures while the remote write is uncertain"})
        resumed = workspace.Workspace(self.path)
        saved = resumed.status()["remote_jobs"]["trial-A"]
        self.assertEqual(saved["action"], dict(remote, status="started"))
        self.assertEqual(saved["state"], "uncertain")
        resumed.record({"outcome": "Exact notebook accepted", "remote": {"id": "trial-A", "state": "running",
                        "provider_id": "owner/exact-notebook/7", "observation": "Official version 7 RUNNING"}})
        self.assertEqual(resumed.status()["remote_jobs"]["trial-A"]["action"], dict(remote, status="started"))
        resumed.next(dict(remote, id="renamed-save"))
        with self.assertRaises(ValueError):
            resumed.start("renamed-save")

    def test_delayed_result_keeps_observations_without_replacing_current_plan_or_champion(self):
        current_adoption = {"candidate": "current", "basis": "quality", "measurement": {"score": .8}, "evidence": ["current-run.json"]}
        self.work.record({"outcome": "Current consumer measured", "adopt": current_adoption})
        champion = self.work.status()["champion"]
        self.work.next({"id": "current-plan", "instruction": "Evaluate the current consumer"})
        self.work.start("current-plan")
        current_plan = self.work.status()["next_action"]
        old_adoption = {"candidate": "old-candidate", "basis": "quality", "measurement": {"score": .75}, "evidence": ["old-run.json"]}
        proposed = {"id": "old-followup", "instruction": "Investigate the old candidate"}
        self.work.record({"action_id": "old-job", "outcome": "Late job completed", "evidence": ["old-run.json"],
                          "remote": {"id": "old-remote", "state": "completed", "observation": "Actual old job COMPLETE"},
                          "adopt": old_adoption, "next_action": proposed})
        resumed = workspace.Workspace(self.path).status()
        self.assertEqual(resumed["next_action"], current_plan)
        self.assertEqual(resumed["champion"], champion)
        self.assertEqual(resumed["remote_jobs"]["old-remote"]["state"], "completed")
        entry = resumed["recent_experiments"][-1]
        self.assertEqual(entry["evidence"], ["old-run.json"])
        self.assertEqual(entry["proposed_next"], proposed)
        self.assertEqual(entry["proposed_adopt"], old_adoption)
        self.assertNotIn("next_action", entry)
        self.assertNotIn("adopt", entry)
        self.work.next(proposed)
        self.assertEqual(self.work.status()["next_action"]["id"], "old-followup")

    def test_current_or_no_action_result_can_still_record_adoption_and_next_step(self):
        for task in (None, {"id": "active", "instruction": "Measure current consumer"}):
            with self.subTest(task=task):
                other = workspace.Workspace(Path(self.temp.name) / ("empty.json" if task is None else "active.json"))
                other.init("Measure the actual consumer", "demo")
                if task is not None:
                    other.next(task)
                    other.start(task["id"])
                result = {"action_id": "active", "outcome": "Consumer measurements available",
                          "adopt": {"candidate": "consumer-v2", "basis": "cost", "measurement": {"before": 100, "after": 80}, "evidence": ["timing.json"]},
                          "next_action": {"id": "inspect-results", "instruction": "Read the measured regressions"}}
                state = other.record(result)
                self.assertEqual(state["champion"]["candidate"], "consumer-v2")
                self.assertEqual(state["next_action"]["id"], "inspect-results")
                self.assertNotIn("proposed_adopt", state["recent_experiments"][-1])

    def test_failed_atomic_replace_preserves_previous_readable_record(self):
        before = self.path.read_bytes()
        with patch.object(workspace.os, "replace", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError): self.work.record({"outcome": "not persisted"})
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_learning_and_budget_do_not_block_next_cpu_action(self):
        self.work.record({"outcome": "GPU unavailable, theory resource prepared", "budget": {"gpu_remaining": 0, "source": "official quota page"}, "learning": {"state": "resources_ready", "resource": "selected chapter"}})
        self.work.next({"id": "read-code", "instruction": "Check the current solver representation"})
        self.assertEqual(self.work.start("read-code")["action"]["id"], "read-code")
        self.assertEqual(self.work.status()["learning"]["state"], "resources_ready")

    def test_legacy_import_is_read_only_and_keeps_actual_provider_ids(self):
        database = Path(self.temp.name) / "old.sqlite3"
        db = sqlite3.connect(database)
        db.executescript("CREATE TABLE tasks(id INTEGER,competition TEXT,state TEXT,spec TEXT,result TEXT); CREATE TABLE intents(id INTEGER,task INTEGER,state TEXT,operation TEXT,receipt TEXT);")
        db.execute("INSERT INTO tasks VALUES(1,'demo','waiting',?,?)", (json.dumps({"action": "collect frozen outputs", "identity": {"method": "baseline"}}), json.dumps({"monitor_due": 1})))
        db.execute("INSERT INTO intents VALUES(3,1,'confirmed',?,?)", (json.dumps({"kind": "save", "target": "owner/kernel/7"}), json.dumps({"provider_id": "owner/kernel/7", "evidence": ["official.json"]})))
        db.commit(); db.close()
        before = database.read_bytes()
        state = self.work.migrate_legacy(database, "demo")
        self.assertEqual(database.read_bytes(), before)
        self.assertEqual(state["legacy_pending"][0]["id"], "legacy-task-1")
        self.assertEqual(state["remote_jobs"]["legacy-intent-3"]["provider_observation"]["provider_id"], "owner/kernel/7")
        self.assertIsNone(state["next_action"])


if __name__ == "__main__":
    unittest.main()
