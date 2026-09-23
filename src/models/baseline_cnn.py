"""
Modular Custom CNN Baseline Architecture for Medical Image Classification.
Designed as an ECE benchmark to measure empirical gains from Transfer Learning.
"""

from typing import Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F


class ConvBlock(nn.Module):
    """Convolutional building block: Conv2D -> BatchNorm -> LeakyReLU -> MaxPool2D -> Dropout."""

    def __init__(self, in_channels: int, out_channels: int, pool: bool = True, dropout_rate: float = 0.2):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.bn = nn.BatchNorm2d(out_channels)
        self.pool = nn.MaxPool2d(2, 2) if pool else nn.Identity()
        self.dropout = nn.Dropout2d(dropout_rate) if dropout_rate > 0 else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv(x)
        x = self.bn(x)
        x = F.leaky_relu(x, negative_slope=0.1)
        x = self.pool(x)
        x = self.dropout(x)
        return x


class MedicalBaselineCNN(nn.Module):
    """
    4-Stage Custom Convolutional Neural Network.
    Parameters are kept reasonable (~1.2M params) for fast training and baseline comparison.
    """

    def __init__(self, in_channels: int = 3, num_classes: int = 14, dropout_rate: float = 0.3):
        super().__init__()
        self.stage1 = ConvBlock(in_channels, 32, pool=True, dropout_rate=0.1)     # 224 -> 112
        self.stage2 = ConvBlock(32, 64, pool=True, dropout_rate=0.2)             # 112 -> 56
        self.stage3 = ConvBlock(64, 128, pool=True, dropout_rate=0.2)            # 56 -> 28
        self.stage4 = ConvBlock(128, 256, pool=True, dropout_rate=dropout_rate)  # 28 -> 14

        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.stage1(x)
        x = self.stage2(x)
        x = self.stage3(x)
        x = self.stage4(x)
        x = self.global_pool(x)
        logits = self.classifier(x)
        return logits

    def get_last_conv_layer(self) -> nn.Module:
        """Returns the final convolutional layer for Grad-CAM explainability."""
        return self.stage4.conv
