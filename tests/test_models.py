import os
import sys
import unittest
import torch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.models.baseline_cnn import MedicalBaselineCNN
from src.models.chest_model import ChestAbnormalityModel
from src.models.skin_model import SkinLesionModel
from src.models.retina_model import RetinalFundusModel


class TestModels(unittest.TestCase):

    def setUp(self):
        # Batch size 2, 3 channels, 224x224
        self.dummy_input = torch.randn(2, 3, 224, 224)

    def test_baseline_cnn_forward(self):
        model = MedicalBaselineCNN(in_channels=3, num_classes=14)
        output = model(self.dummy_input)
        self.assertEqual(output.shape, (2, 14))
        self.assertIsNotNone(model.get_last_conv_layer())

    def test_chest_model_forward_and_probs(self):
        model = ChestAbnormalityModel(use_transfer_learning=False, num_classes=14)
        logits = model(self.dummy_input)
        self.assertEqual(logits.shape, (2, 14))

        probs = model.predict_probabilities(self.dummy_input)
        self.assertEqual(probs.shape, (2, 14))
        self.assertTrue((probs >= 0.0).all() and (probs <= 1.0).all())
        self.assertIsNotNone(model.get_last_conv_layer())

    def test_skin_model_forward_and_probs(self):
        model = SkinLesionModel(use_transfer_learning=False, num_classes=7)
        logits = model(self.dummy_input)
        self.assertEqual(logits.shape, (2, 7))

        probs = model.predict_probabilities(self.dummy_input)
        self.assertEqual(probs.shape, (2, 7))
        # Softmax should sum to approximately 1.0
        sums = probs.sum(dim=-1)
        self.assertTrue(torch.allclose(sums, torch.ones_like(sums), atol=1e-5))

    def test_retina_model_forward_and_probs(self):
        model = RetinalFundusModel(use_transfer_learning=False, num_classes=5)
        logits = model(self.dummy_input)
        self.assertEqual(logits.shape, (2, 5))

        probs = model.predict_probabilities(self.dummy_input)
        self.assertEqual(probs.shape, (2, 5))
        sums = probs.sum(dim=-1)
        self.assertTrue(torch.allclose(sums, torch.ones_like(sums), atol=1e-5))


if __name__ == "__main__":
    unittest.main()
