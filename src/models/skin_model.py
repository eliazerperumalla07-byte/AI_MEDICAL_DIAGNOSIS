"""
Dermoscopic Skin Lesion Multi-Class Classification Model.
Target: 7 dermatological lesion categories (DermaMNIST / HAM10000 / ISIC).
Architectures:
  1. EfficientNet-B0 (Compound scaling for fine pigment textural patterns)
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

SKIN_DISEASE_LABELS: List[str] = [
    "Actinic keratoses / Bowen's (akiec)",
    "Basal cell carcinoma (bcc)",
    "Benign keratosis-like lesions (bkl)",
    "Dermatofibroma (df)",
    "Melanoma (mel)",
    "Melanocytic nevi (nv)",
    "Vascular lesions (vasc)",
]


class SkinLesionModel(nn.Module):
    """
    Dermoscopy Skin Lesion Classifier.
    Outputs normalized probability distribution over 7 classes via Softmax.
    """

    def __init__(self, use_transfer_learning: bool = True, pretrained: bool = False, num_classes: int = 7):
        super().__init__()
        self.num_classes = num_classes
        self.use_transfer_learning = use_transfer_learning
        self.labels = SKIN_DISEASE_LABELS[:num_classes]

        if use_transfer_learning and HAS_TORCHVISION:
            weights = tv_models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
            self.backbone = tv_models.efficientnet_b0(weights=weights)
            in_features = self.backbone.classifier[1].in_features
            self.backbone.classifier = nn.Sequential(
                nn.Dropout(0.4),
                nn.Linear(in_features, 128),
                nn.SiLU(),
                nn.Dropout(0.2),
                nn.Linear(128, num_classes),
            )
            # Last conv layer of EfficientNet-B0
            self.last_conv_layer = self.backbone.features[-1]
        else:
            self.backbone = MedicalBaselineCNN(in_channels=3, num_classes=num_classes)
            self.last_conv_layer = self.backbone.get_last_conv_layer()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Returns raw logits (B, num_classes)."""
        if self.use_transfer_learning and (x.shape[-1] < 64 or x.shape[-2] < 64):
            x = torch.nn.functional.interpolate(x, size=(224, 224), mode="bilinear", align_corners=False)
        return self.backbone(x)

    def predict_probabilities(self, x: torch.Tensor) -> torch.Tensor:
        """Returns softmax probabilities (B, num_classes) summing to 1.0."""
        with torch.no_grad():
            logits = self.forward(x)
            return F.softmax(logits, dim=-1)

    def get_last_conv_layer(self) -> nn.Module:
        """Returns target layer for Grad-CAM."""
        return self.last_conv_layer
