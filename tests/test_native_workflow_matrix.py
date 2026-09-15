import importlib.util
from pathlib import Path
import tempfile
import unittest


MODULE = Path(__file__).resolve().parents[1] / "tools/run_native_workflow_matrix.py"
spec = importlib.util.spec_from_file_location("run_native_workflow_matrix", MODULE)
matrix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(matrix)


class NativeWorkflowMatrixTests(unittest.TestCase):
    def test_score_trace_accepts_exact_expected_subset(self):
        self.assertEqual([], matrix.score_trace({"bootstrap": "new", "extra": True}, {"bootstrap": "new"}))

    def test_score_trace_exposes_wrong_or_missing_values(self):
        failures = matrix.score_trace({"bootstrap": "resumed"}, {"bootstrap": "new", "flow": "development"})
        self.assertEqual(2, len(failures))
        self.assertIn("bootstrap", failures[0])
        self.assertIn("flow", failures[1])

    def test_output_directory_must_be_empty(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evidence"
            self.assertEqual(output, matrix.prepare_output_dir(output))
            (output / "existing.log").write_text("prior run", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                matrix.prepare_output_dir(output)


if __name__ == "__main__":
    unittest.main()
