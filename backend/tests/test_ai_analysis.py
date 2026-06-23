import unittest

from app.services.analysis import fallback_analysis, normalize_analysis


class AiAnalysisTests(unittest.TestCase):
    def test_empty_model_output_keeps_fallback_information(self):
        fallback = fallback_analysis("airockchip/rknn_model_zoo", "RKNN model zoo for RK3588 object detection and YOLO demos", {"language": "Python", "topics": ["rknn"]})

        result = normalize_analysis({}, fallback)

        self.assertTrue(result["summary"])
        self.assertGreater(result["idea_value"], 0)
        self.assertGreaterEqual(result["rk_compatibility"], 8)
        self.assertIn("RK3588", result["target_platforms"])
        self.assertTrue(result["inspired_ideas"])

    def test_blank_model_fields_do_not_override_fallback(self):
        fallback = fallback_analysis("YOLO RKNN demo", "Camera detection using ONNX and RKNN", {})

        result = normalize_analysis({"summary": "", "tags": [], "idea_value": ""}, fallback)

        self.assertEqual(result["summary"], fallback["summary"])
        self.assertEqual(result["tags"], fallback["tags"])
        self.assertEqual(result["idea_value"], fallback["idea_value"])


if __name__ == "__main__":
    unittest.main()
