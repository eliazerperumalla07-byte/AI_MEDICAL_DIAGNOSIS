"""
Chest Radiography Multi-Label Abnormality Detection Model.
Target: 14 thoracic pathologies (ChestMNIST / NIH ChestX-ray14).
Architectures:
  1. DenseNet-121 (CheXNet backbone with dense feature propagation)
  2. Custom Baseline CNN
"""

from typing import List, Optional
import torch
import torch.nn as nn

try:
    import torchvision.models as tv_models
    HAS_TORCHVISION = True
except ImportError:
    HAS_TORCHVISION = False

from .baseline_cnn import MedicalBaselineCNN

CHEST_DISEASE_LABELS: List[str] = [
    "Atelectasis",
    "Cardiomegaly",
    "Effusion",
    "Infiltration",
    "Mass",
    "Nodule",
    "Pneumonia",
    "Pneumothorax",
    "Consolidation",
    "Edema",
    "Emphysema",
    "Fibrosis",
    "Pleural_Thickening",
    "Hernia",
]


class ChestAbnormalityModel(nn.Module):
    """
    Chest X-ray Multi-Label Classifier.
    Outputs independent probabilities for 14 conditions via Sigmoid.
    """

    def __init__(self, use_transfer_learning: bool = True, pretrained: bool = False, num_classes: int = 14):
        super().__init__()
        self.num_classes = num_classes
        self.use_transfer_learning = use_transfer_learning
        self.labels = CHEST_DISEASE_LABELS[:num_classes]

        if use_transfer_learning and HAS_TORCHVISION:
            # DenseNet-121 (Proven SOTA for chest X-rays, CheXNet)
            weights = tv_models.DenseNet121_Weights.DEFAULT if pretrained else None
            self.backbone = tv_models.densenet121(weights=weights)
            num_features = self.backbone.classifier.in_features
            self.backbone.classifier = nn.Sequential(
                nn.Dropout(0.3),
                nn.Linear(num_features, num_classes),
            )
            self.last_conv_layer = self.backbone.features.denseblock4.denselayer16.conv2
        else:
            self.backbone = MedicalBaselineCNN(in_channels=3, num_classes=num_classes)
            self.last_conv_layer = self.backbone.get_last_conv_layer()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Returns raw logits (B, num_classes)."""
        if self.use_transfer_learning and (x.shape[-1] < 64 or x.shape[-2] < 64):
            x = torch.nn.functional.interpolate(x, size=(224, 224), mode="bilinear", align_corners=False)
        return self.backbone(x)

    def predict_probabilities(self, x: torch.Tensor) -> torch.Tensor:
        """Returns sigmoid probabilities (B, num_classes) in [0, 1]."""
        with torch.no_grad():
            logits = self.forward(x)
            return torch.sigmoid(logits)

    def get_last_conv_layer(self) -> nn.Module:
        """Returns target layer for Grad-CAM."""
        return self.last_conv_layer
