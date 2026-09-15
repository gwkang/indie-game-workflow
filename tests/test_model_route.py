import importlib.util
from pathlib import Path
import unittest


PACKAGE = Path(__file__).resolve().parents[1]
MODULE = PACKAGE / "skills/game-workflow-supervision/scripts/resolve_model_route.py"
PROFILE = Path(__file__).resolve().parent / "fixtures/model-routing-profile.json"
spec = importlib.util.spec_from_file_location("resolve_model_route", MODULE)
router = importlib.util.module_from_spec(spec)
spec.loader.exec_module(router)


class ModelRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = router.load_profile(PROFILE)
        cls.available = ["model-judgment", "model-complex", "model-balanced", "model-volume"]

    def test_each_tier_resolves_to_project_preference(self):
        expected = {
            "highest-judgment": ("model-judgment", "high"),
            "complex-execution": ("model-complex", "high"),
            "balanced-execution": ("model-balanced", "medium"),
            "high-volume": ("model-volume", "low"),
        }
        for tier, (model, effort) in expected.items():
            with self.subTest(tier=tier):
                result = router.resolve(self.profile, tier, self.available, True)
                self.assertEqual("override", result["decision"])
                self.assertEqual(model, result["resolvedModel"])
                self.assertEqual(effort, result["reasoningClass"])

    def test_missing_preferred_model_uses_declared_fallback(self):
        result = router.resolve(self.profile, "balanced-execution", ["model-complex"], True)
        self.assertEqual("model-complex", result["resolvedModel"])
        self.assertEqual("preferred-model-unavailable", result["fallbackReason"])

    def test_no_available_candidate_preserves_host_default(self):
        result = router.resolve(self.profile, "high-volume", ["unmapped-model"], True)
        self.assertEqual("host-default", result["decision"])
        self.assertEqual("no-tier-candidate-available", result["fallbackReason"])

    def test_unsupported_override_preserves_host_default(self):
        result = router.resolve(self.profile, "highest-judgment", self.available, False)
        self.assertEqual("host-default", result["decision"])
        self.assertEqual("model-override-unsupported", result["fallbackReason"])

    def test_explicit_unavailable_model_blocks_dispatch(self):
        result = router.resolve(self.profile, "balanced-execution", self.available, True, "requested-model")
        self.assertEqual("blocked", result["decision"])
        self.assertEqual("explicit-model-unavailable", result["fallbackReason"])

    def test_available_explicit_model_is_preserved(self):
        result = router.resolve(self.profile, "high-volume", self.available, True, "model-complex")
        self.assertEqual("override", result["decision"])
        self.assertEqual("model-complex", result["resolvedModel"])
        self.assertEqual("explicit-user", result["resolutionSource"])
        self.assertIsNone(result["reasoningClass"])

    def test_explicit_model_blocks_when_override_is_unsupported(self):
        result = router.resolve(self.profile, "balanced-execution", self.available, False, "model-balanced")
        self.assertEqual("blocked", result["decision"])
        self.assertEqual("explicit-model-override-unsupported", result["fallbackReason"])
        self.assertEqual("explicit-user", result["resolutionSource"])


if __name__ == "__main__":
    unittest.main()
