"""
Base module for Digital Image Processing (DIP) preprocessors.
Defines standard interfaces for all medical imaging modalities.
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple, Any
import numpy as np


class BasePreprocessor(ABC):
    """
    Abstract base class for modality-specific digital image processing.
    Each preprocessor must accept raw input images (RGB or grayscale)
    and produce both:
      1. A normalized tensor/array ready for deep learning inference.
      2. A dictionary of intermediate stage visual arrays for clinical inspection.
    """

    def __init__(self, target_size: Tuple[int, int] = (224, 224)):
        self.target_size = target_size

    @abstractmethod
    def preprocess(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Preprocess an input medical image.

        Args:
            image: Input image as numpy array (H, W) or (H, W, C), uint8 [0, 255] or float [0, 1].

        Returns:
            processed_image: Final processed array resized to target_size, normalized to [0, 1] float32.
            stages: Dict of intermediate processing stages (e.g. {'raw': ..., 'denoised': ..., 'enhanced': ...})
                    formatted as uint8 [0, 255] for visual rendering in UI/notebooks.
        """
        pass

    def ensure_uint8(self, img: np.ndarray) -> np.ndarray:
        """Helper to ensure image is in uint8 format [0, 255]."""
        if img.dtype == np.uint8:
            return img
        if img.max() <= 1.0:
            return (img * 255.0).clip(0, 255).astype(np.uint8)
        return img.clip(0, 255).astype(np.uint8)

    def to_rgb(self, img: np.ndarray) -> np.ndarray:
        """Helper to convert grayscale or multi-channel image to standard 3-channel RGB."""
        if len(img.shape) == 2:
            return np.stack([img] * 3, axis=-1)
        elif len(img.shape) == 3 and img.shape[2] == 1:
            return np.repeat(img, 3, axis=2)
        elif len(img.shape) == 3 and img.shape[2] == 4:
            return img[:, :, :3]
        return img
