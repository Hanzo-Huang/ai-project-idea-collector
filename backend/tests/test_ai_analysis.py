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

    def test_rknn_model_zoo_gets_useful_fallback_summary(self):
        text = """
        RKNN Model Zoo is developed based on the RKNPU SDK toolchain and provides deployment examples
        for current mainstream algorithms. Include exporting the RKNN model and using Python API and CAPI
        to infer the RKNN model. Support RK3562, RK3566, RK3568, RK3576, RK3588, RV1126B platforms.
        """

        result = fallback_analysis("airockchip/rknn_model_zoo", text, {"language": "Python", "topics": ["rknn"]})

        self.assertIn("Rockchip RKNPU SDK", result["summary"])
        self.assertIn("RK3576", result["hardware_requirements"])
        self.assertIn("RK3588", result["hardware_requirements"])
        self.assertIn("RKNN Toolkit", result["software_requirements"])
        self.assertGreaterEqual(result["rk_compatibility"], 8)
        self.assertGreater(result["idea_value"], 0)

    def test_rkllm_gets_llm_deployment_summary(self):
        text = """
        RKLLM software stack can help users to quickly deploy AI models to Rockchip chips.
        Users need to run the RKLLM-Toolkit on the computer, convert the trained model into an RKLLM
        format model, and then inference on the development board using the RKLLM C API.
        """

        result = fallback_analysis("airockchip/rknn-llm", text, {"language": "C++", "topics": ["rkllm"]})

        self.assertIn("Rockchip LLM deployment stack", result["summary"])
        self.assertIn("RKLLM Toolkit", result["software_requirements"])
        self.assertTrue(result["inspired_ideas"])


if __name__ == "__main__":
    unittest.main()
