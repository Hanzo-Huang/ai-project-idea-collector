import unittest

from app.services.rk import rk_signals


class RkCompatibilityTests(unittest.TestCase):
    def test_detects_rk3588_rknn_project(self):
        result = rk_signals("YOLO RKNN demo", "Runs YOLO on RK3588 with camera and RKNN toolkit", {})

        self.assertIn("RK3588", result["target_platforms"])
        self.assertGreaterEqual(result["rk_compatibility"], 8)
        self.assertFalse(result["big_event_relevance"])

    def test_detects_ai_event_relevance(self):
        result = rk_signals("New open-source VLM release", "A model launch with ONNX export for edge devices", {})

        self.assertTrue(result["big_event_relevance"])
        self.assertIn("RK3576", result["target_platforms"])


if __name__ == "__main__":
    unittest.main()
