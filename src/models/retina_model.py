"""
Retinal Fundus Photography Diabetic Retinopathy Severity Grading Model.
Target: 5 DR severity grades (RetinaMNIST / APTOS / EyePACS).
Architectures:
  1. ResNet-50 (Residual connections for subtle microvascular lesion staging)
  2. Custom Baseline CNN
"""

from typing import List
import torch
import torch.nn as nn
import torch.nn.functional as F

try:
    import torchvision.models as tv_models
    HAS_TORCHVISION = True
except ImportError:
    HAS_TORCHVISION = False

from .baseline_cnn import MedicalBaselineCNN

RETINA_DISEASE_LABELS: List[str] = [
    "Grade 0: No Diabetic Retinopathy (Normal)",
    "Grade 1: Mild Non-Proliferative DR",
    "Grade 2: Moderate Non-Proliferative DR",
    "Grade 3: Severe Non-Proliferative DR",
    "Grade 4: Proliferative Diabetic Retinopathy",
]


class RetinalFundusModel(nn.Module):
    """
    Retinal Fundus Severity Classifier.
    Outputs probability distribution across 5 ordinal DR stages.
    """

    def __init__(self, use_transfer_learning: bool = True, pretrained: bool = False, num_classes: int = 5):
        super().__init__()
        self.num_classes = num_classes
        self.use_transfer_learning = use_transfer_learning
        self.labels = RETINA_DISEASE_LABELS[:num_classes]

        if use_transfer_learning and HAS_TORCHVISION:
            weights = tv_models.ResNet50_Weights.DEFAULT if pretrained else None
            self.backbone = tv_models.resnet50(weights=weights)
            in_features = self.backbone.fc.in_features
            self.backbone.fc = nn.Sequential(
                nn.Dropout(0.3),
                nn.Linear(in_features, 128),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(128, num_classes),
            )
            # Last conv layer of ResNet-50 is the last conv in layer4
            self.last_conv_layer = self.backbone.layer4[-1].conv3
        else:
            self.backbone = MedicalBaselineCNN(in_channels=3, num_classes=num_classes)
            self.last_conv_layer = self.backbone.get_last_conv_layer()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Returns raw logits (B, num_classes)."""
        if self.use_transfer_learning and (x.shape[-1] < 64 or x.shape[-2] < 64):
            x = torch.nn.functional.interpolate(x, size=(224, 224), mode="bilinear", align_corners=False)
        return self.backbone(x)

    def predict_probabilities(self, x: torch.Tensor) -> torch.Tensor:
        """Returns softmax probabilities (B, num_classes)."""
        with torch.no_grad():
            logits = self.forward(x)
            return F.softmax(logits, dim=-1)

    def get_last_conv_layer(self) -> nn.Module:
        """Returns target layer for Grad-CAM."""
        return self.last_conv_layer
