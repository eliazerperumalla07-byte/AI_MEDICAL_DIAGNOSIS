import os
import sys
import unittest
import numpy as np
from PIL import Image

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.pipeline.multi_disease_system import MultiDiseaseDiagnosticSystem
from src.router.modality_classifier import ModalityRouter, MedicalModality


class TestPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.sample_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "samples"))
        self.engine = MultiDiseaseDiagnosticSystem(use_transfer_learning=False)

    def test_modality_router_heuristic_classification(self):
        router = ModalityRouter()

        # Chest image test (grayscale)
        chest_path = os.path.join(self.sample_dir, "sample_chest_xray.png")
        if os.path.exists(chest_path):
            img = np.array(Image.open(chest_path))
            detected, confs = router.route_by_heuristics(img)
            self.assertEqual(detected, MedicalModality.CHEST)

        # Retina image test (dark corners, bright center)
        retina_path = os.path.join(self.sample_dir, "sample_retinal_fundus.png")
        if os.path.exists(retina_path):
            img = np.array(Image.open(retina_path))
            detected, confs = router.route_by_heuristics(img)
            self.assertEqual(detected, MedicalModality.RETINA)

        # Skin image test (skin tones)
        skin_path = os.path.join(self.sample_dir, "sample_skin_lesion.png")
        if os.path.exists(skin_path):
            img = np.array(Image.open(skin_path))
            detected, confs = router.route_by_heuristics(img)
            self.assertEqual(detected, MedicalModality.SKIN)

    def test_end_to_end_chest_diagnosis(self):
        chest_path = os.path.join(self.sample_dir, "sample_chest_xray.png")
        if not os.path.exists(chest_path):
            self.skipTest("Sample image not found")

        result = self.engine.diagnose(chest_path, generate_xai=True)

        self.assertIn("modality", result)
        self.assertIn("primary_diagnosis", result)
        self.assertIn("overall_severity", result)
        self.assertIn("findings", result)
        self.assertEqual(len(result["findings"]), 14)  # 14 thoracic conditions
        self.assertIn("xai", result)
        self.assertIsNotNone(result["xai"]["heatmap"])
        self.assertEqual(result["xai"]["heatmap"].shape, (224, 224))

    def test_end_to_end_skin_diagnosis(self):
        skin_path = os.path.join(self.sample_dir, "sample_skin_lesion.png")
        if not os.path.exists(skin_path):
            self.skipTest("Sample image not found")

        result = self.engine.diagnose(skin_path, generate_xai=True)

        self.assertIn("findings", result)
        self.assertEqual(len(result["findings"]), 7)  # 7 dermatological classes
        self.assertIsNotNone(result["xai"]["heatmap"])

    def test_end_to_end_retina_diagnosis(self):
        retina_path = os.path.join(self.sample_dir, "sample_retinal_fundus.png")
        if not os.path.exists(retina_path):
            self.skipTest("Sample image not found")

        result = self.engine.diagnose(retina_path, generate_xai=True)

        self.assertIn("findings", result)
        self.assertEqual(len(result["findings"]), 5)  # 5 DR grades
        self.assertIsNotNone(result["xai"]["heatmap"])


if __name__ == "__main__":
    unittest.main()
