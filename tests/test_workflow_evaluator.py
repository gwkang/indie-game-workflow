import importlib.util
import json
from pathlib import Path
import unittest


MODULE = Path(__file__).resolve().parents[1] / "tools/workflow_evaluator.py"
spec = importlib.util.spec_from_file_location("workflow_evaluator", MODULE)
evaluator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator)


class WorkflowEvaluatorTests(unittest.TestCase):
    def test_exact_observable_match_passes(self):
        expectations = {"a": {"bootstrap": "new", "supervisorBeforeSpecialist": True}}
        results = [{"caseId": "a", "trace": {"bootstrap": "new", "supervisorBeforeSpecialist": True}}]
        self.assertEqual("pass", evaluator.evaluate(results, expectations)["status"])

    def test_missing_wrong_and_unknown_results_fail(self):
        expectations = {"a": {"bootstrap": "new"}, "b": {"bootstrap": "resumed"}}
        results = [{"caseId": "a", "trace": {"bootstrap": "resumed"}},
                   {"caseId": "extra", "trace": {"bootstrap": "new"}}]
        verdict = evaluator.evaluate(results, expectations)
        self.assertEqual("fail", verdict["status"])
        self.assertEqual(["extra"], verdict["unknownCases"])
        self.assertTrue(any(row["failures"] for row in verdict["cases"]))


if __name__ == "__main__":
    unittest.main()
