import os
import sys
import unittest
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.dip.chest_dip import ChestXRayPreprocessor
from src.dip.skin_dip import SkinLesionPreprocessor
from src.dip.retina_dip import RetinalFundusPreprocessor


class TestDIPPreprocessors(unittest.TestCase):

    def setUp(self):
        # Create synthetic test images
        self.grayscale_img = (np.random.rand(224, 224) * 255).astype(np.uint8)
        self.rgb_img = (np.random.rand(224, 224, 3) * 255).astype(np.uint8)

    def test_chest_preprocessor_output(self):
        preprocessor = ChestXRayPreprocessor(target_size=(224, 224))
        normalized, stages = preprocessor.preprocess(self.grayscale_img)

        # Output shape check
        self.assertEqual(normalized.shape, (224, 224, 3))
        # Value range check [0.0, 1.0]
        self.assertTrue(normalized.min() >= 0.0)
        self.assertTrue(normalized.max() <= 1.0)
        # Stages dict check
        self.assertIn("raw", stages)
        self.assertIn("bilateral_denoised", stages)
        self.assertIn("clahe_enhanced", stages)
        self.assertIn("dip_final_visual", stages)

    def test_skin_preprocessor_output(self):
        preprocessor = SkinLesionPreprocessor(target_size=(224, 224))
        normalized, stages = preprocessor.preprocess(self.rgb_img)

        # Output shape check
        self.assertEqual(normalized.shape, (224, 224, 3))
        # Range check
        self.assertTrue(normalized.min() >= 0.0)
        self.assertTrue(normalized.max() <= 1.0)
        # Stages check (DullRazor + Shades-of-Gray)
        self.assertIn("hair_mask", stages)
        self.assertIn("dullrazor_hair_removed", stages)
        self.assertIn("color_constancy", stages)

    def test_retina_preprocessor_output(self):
        preprocessor = RetinalFundusPreprocessor(target_size=(224, 224))
        normalized, stages = preprocessor.preprocess(self.rgb_img)

        # Output shape check
        self.assertEqual(normalized.shape, (224, 224, 3))
        # Range check
        self.assertTrue(normalized.min() >= 0.0)
        self.assertTrue(normalized.max() <= 1.0)
        # Stages check (FOV crop + Ben Graham)
        self.assertIn("cropped_fov", stages)
        self.assertIn("ben_graham_equalized", stages)


if __name__ == "__main__":
    unittest.main()
