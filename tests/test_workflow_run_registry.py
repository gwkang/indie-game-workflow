import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE = Path(__file__).resolve().parents[1] / "skills/game-workflow/scripts/workflow_run_registry.py"
spec = importlib.util.spec_from_file_location("workflow_run_registry", MODULE)
registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry)


class WorkflowRunRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "planning/workflow-runs").mkdir(parents=True)
        (self.root / "planning/workflow-runs/a.md").write_text("run a", encoding="utf-8")
        self.data = {
            "schemaVersion": 1,
            "runs": [{
                "runId": "run-a",
                "recordPath": "planning/workflow-runs/a.md",
                "status": "running",
                "goalRevision": 2,
                "goalKeys": ["workflow", "supervision"],
                "targetPaths": ["packages/workflow-bundle"],
                "conversationKey": "conversation-a"
            }]
        }

    def test_zero_one_and_multiple_matches_are_distinct(self):
        self.assertEqual("new", registry.match(self.data, self.root, goal_keys=["unrelated"])["decision"])
        result = registry.match(self.data, self.root, conversation_key="conversation-a")
        self.assertEqual("resume", result["decision"])
        other = dict(self.data["runs"][0], runId="run-b", recordPath="planning/workflow-runs/a.md")
        data = {"schemaVersion": 1, "runs": [self.data["runs"][0], other]}
        self.assertEqual("select", registry.match(data, self.root, goal_keys=["workflow"])["decision"])

    def test_explicit_identity_beats_weaker_goal_match(self):
        other = dict(self.data["runs"][0], runId="run-b", conversationKey="conversation-b",
                     goalKeys=[f"goal-{index}" for index in range(20)])
        data = {"schemaVersion": 1, "runs": [self.data["runs"][0], other]}
        result = registry.match(data, self.root, run_id="run-a", goal_keys=other["goalKeys"])
        self.assertEqual(["run-a"], [row["runId"] for row in result["matches"]])

    def test_missing_explicit_run_does_not_fall_back_to_other_signals(self):
        result = registry.match(
            self.data,
            self.root,
            run_id="missing-run",
            conversation_key="conversation-a",
            goal_keys=["workflow"],
            target_paths=["packages/workflow-bundle"],
        )
        self.assertEqual("not-found", result["decision"])
        self.assertEqual([], result["matches"])
        self.assertEqual("missing-run", result["requestedRunId"])

    def test_stale_pointer_requires_reconciliation(self):
        data = json.loads(json.dumps(self.data))
        data["runs"][0]["recordPath"] = "planning/workflow-runs/missing.md"
        self.assertEqual("reconcile", registry.match(data, self.root, goal_keys=["workflow"])["decision"])

    def test_explicit_run_ignores_another_matching_stale_pointer(self):
        stale = dict(self.data["runs"][0], runId="run-b",
                     recordPath="planning/workflow-runs/missing.md")
        data = {"schemaVersion": 1, "runs": [self.data["runs"][0], stale]}
        result = registry.match(data, self.root, run_id="run-a", goal_keys=["workflow"])
        self.assertEqual("resume", result["decision"])
        self.assertEqual(["run-a"], [row["runId"] for row in result["matches"]])

    def test_closed_runs_do_not_match(self):
        data = registry.close(json.loads(json.dumps(self.data)), "run-a", "completed")
        self.assertEqual("new", registry.match(data, self.root, goal_keys=["workflow"])["decision"])

    def test_atomic_round_trip_and_path_escape_rejection(self):
        path = self.root / "planning/workflow-runs/active.json"
        registry.write_atomic(path, self.data)
        self.assertEqual(self.data, registry.load(path))
        broken = json.loads(json.dumps(self.data))
        broken["runs"][0]["recordPath"] = "../outside.md"
        with self.assertRaises(registry.RegistryError):
            registry.validate(broken)


if __name__ == "__main__":
    unittest.main()
