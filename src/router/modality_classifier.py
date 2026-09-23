"""
Modality Router and Image Type Identification.
Classifies incoming medical images into:
  1. Chest X-Ray (Radiograph)
  2. Skin Lesion (Dermoscopy)
  3. Retinal Fundus (Ophthalmology)

Combines optical spectral heuristics with a lightweight neural classifier to prevent
mismatched clinical inference (e.g. evaluating a skin mole with the chest model).
"""

from enum import Enum
from typing import Dict, Tuple, Optional
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class MedicalModality(str, Enum):
    CHEST = "chest_xray"
    SKIN = "skin_dermoscopy"
    RETINA = "retinal_fundus"
    UNKNOWN = "unknown"


class ModalityRouter(nn.Module):
    """
    Intelligent Modality Router combining optical heuristic profiling
    with a lightweight 3-class convolutional classifier.
    """

    MODALITIES = [MedicalModality.CHEST, MedicalModality.SKIN, MedicalModality.RETINA]

    def __init__(self):
        super().__init__()
        # Lightweight 3-stage CNN for modality routing
        self.conv1 = nn.Conv2d(3, 16, 3, padding=1)
        self.conv2 = nn.Conv2d(16, 32, 3, padding=1)
        self.pool = nn.MaxPool2d(4, 4)
        self.fc = nn.Linear(32 * 14 * 14, 3)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool(F.relu(self.conv1(x)))  # 224 -> 56
        x = self.pool(F.relu(self.conv2(x)))  # 56 -> 14
        x = torch.flatten(x, 1)
        return self.fc(x)

    def route_by_heuristics(self, image: np.ndarray) -> Tuple[MedicalModality, Dict[str, float]]:
        """
        Robust optical domain profiling for zero-shot modality classification:
        - Chest X-rays: Virtually zero color saturation (grayscale/monochrome).
        - Retinal Fundus: Circular FOV with high red/orange luminance and prominent black borders.
        - Skin Dermoscopy: High color saturation, fleshy/pink/brown hues, rectangular full-frame illumination.
        """
        img = image.astype(np.float32)
        if img.max() > 1.0:
            img /= 255.0

        if len(img.shape) == 2:
            return MedicalModality.CHEST, {
                MedicalModality.CHEST: 0.99,
                MedicalModality.SKIN: 0.005,
                MedicalModality.RETINA: 0.005,
            }

        H, W, C = img.shape
        r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]

        # 1. Color saturation metric: mean absolute difference between channels
        channel_diff = np.mean(np.abs(r - g) + np.abs(g - b) + np.abs(r - b))

        # 2. Check for circular dark border (retina fundus characteristic)
        corners = [
            img[0 : int(H * 0.1), 0 : int(W * 0.1)],
            img[0 : int(H * 0.1), int(W * 0.9) :],
            img[int(H * 0.9) :, 0 : int(W * 0.1)],
            img[int(H * 0.9) :, int(W * 0.9) :],
        ]
        corner_darkness = np.mean([np.mean(c) for c in corners])
        center = img[int(H * 0.3) : int(H * 0.7), int(W * 0.3) : int(W * 0.7)]
        center_brightness = np.mean(center)

        # Retinal check: dark corners + bright center + moderate color
        is_retina = (corner_darkness < 0.12) and (center_brightness > 0.25) and (channel_diff > 0.04)

        if is_retina:
            conf = min(0.98, 0.7 + (center_brightness - corner_darkness))
            return MedicalModality.RETINA, {
                MedicalModality.RETINA: float(conf),
                MedicalModality.SKIN: float((1.0 - conf) * 0.7),
                MedicalModality.CHEST: float((1.0 - conf) * 0.3),
            }

        # Grayscale / Low color variance check: Chest X-ray
        if channel_diff < 0.035:
            conf = min(0.99, 0.85 + (0.035 - channel_diff) * 4)
            return MedicalModality.CHEST, {
                MedicalModality.CHEST: float(conf),
                MedicalModality.SKIN: float((1.0 - conf) * 0.5),
                MedicalModality.RETINA: float((1.0 - conf) * 0.5),
            }

        # Otherwise: Dermoscopic skin lesion
        skin_conf = min(0.97, 0.75 + channel_diff * 0.5)
        return MedicalModality.SKIN, {
            MedicalModality.SKIN: float(skin_conf),
            MedicalModality.RETINA: float((1.0 - skin_conf) * 0.6),
            MedicalModality.CHEST: float((1.0 - skin_conf) * 0.4),
        }
