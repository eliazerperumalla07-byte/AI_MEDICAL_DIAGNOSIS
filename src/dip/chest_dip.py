"""
Digital Image Processing (DIP) Pipeline for Chest X-Ray Images.
Techniques:
1. Bilateral Filtering: Noise reduction while preserving anatomical bone/lung boundaries.
2. CLAHE (Contrast Limited Adaptive Histogram Equalization): Dynamic range enhancement
   across mediastinal, cardiac, and pulmonary parenchyma.
3. Contrast Normalization: Robust Min-Max intensity scaling.
"""

from typing import Dict, Tuple
import numpy as np

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

from .base import BasePreprocessor


class ChestXRayPreprocessor(BasePreprocessor):
    """
    DIP pipeline engineered for Chest Radiographs (e.g., ChestMNIST, NIH ChestX-ray14).
    """

    def __init__(
        self,
        target_size: Tuple[int, int] = (224, 224),
        clahe_clip_limit: float = 2.0,
        clahe_tile_grid_size: Tuple[int, int] = (8, 8),
        bilateral_d: int = 9,
        bilateral_sigma_color: float = 75.0,
        bilateral_sigma_space: float = 75.0,
    ):
        super().__init__(target_size=target_size)
        self.clahe_clip_limit = clahe_clip_limit
        self.clahe_tile_grid_size = clahe_tile_grid_size
        self.bilateral_d = bilateral_d
        self.bilateral_sigma_color = bilateral_sigma_color
        self.bilateral_sigma_space = bilateral_sigma_space

    def _apply_bilateral_filter(self, img_gray: np.ndarray) -> np.ndarray:
        if HAS_OPENCV:
            return cv2.bilateralFilter(
                img_gray,
                d=self.bilateral_d,
                sigmaColor=self.bilateral_sigma_color,
                sigmaSpace=self.bilateral_sigma_space,
            )
        # Fallback: simple Gaussian-like 3x3 kernel when cv2 is unavailable
        kernel = np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]], dtype=np.float32) / 16.0
        pad = np.pad(img_gray, 1, mode="edge")
        H, W = img_gray.shape
        filtered = np.zeros_like(img_gray, dtype=np.float32)
        for i in range(H):
            for j in range(W):
                filtered[i, j] = np.sum(pad[i : i + 3, j : j + 3] * kernel)
        return filtered.clip(0, 255).astype(np.uint8)

    def _apply_clahe(self, img_gray: np.ndarray) -> np.ndarray:
        if HAS_OPENCV:
            clahe = cv2.createCLAHE(
                clipLimit=self.clahe_clip_limit,
                tileGridSize=self.clahe_tile_grid_size,
            )
            return clahe.apply(img_gray)
        # Fallback: standard global histogram equalization
        hist, bins = np.histogram(img_gray.flatten(), 256, [0, 256])
        cdf = hist.cumsum()
        cdf_normalized = cdf * 255 / cdf[-1]
        equalized = np.interp(img_gray.flatten(), bins[:-1], cdf_normalized)
        return equalized.reshape(img_gray.shape).astype(np.uint8)

    def _resize(self, img: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
        if HAS_OPENCV:
            return cv2.resize(img, size, interpolation=cv2.INTER_AREA)
        # Fallback nearest-neighbor / slice sampling
        orig_h, orig_w = img.shape[:2]
        target_w, target_h = size
        row_indices = (np.linspace(0, orig_h - 1, target_h)).astype(int)
        col_indices = (np.linspace(0, orig_w - 1, target_w)).astype(int)
        return img[np.ix_(row_indices, col_indices)]

    def preprocess(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Executes full chest DIP pipeline.
        Returns:
            processed_image: (224, 224, 3) float32 normalized in [0, 1]
            stages: Dict of stage visual outputs (uint8)
        """
        raw_uint8 = self.ensure_uint8(image)
        stages = {"raw": raw_uint8}

        # Convert to single-channel grayscale if multi-channel
        if len(raw_uint8.shape) == 3:
            if HAS_OPENCV:
                gray = cv2.cvtColor(raw_uint8, cv2.COLOR_RGB2GRAY)
            else:
                gray = (0.2989 * raw_uint8[:, :, 0] + 0.5870 * raw_uint8[:, :, 1] + 0.1140 * raw_uint8[:, :, 2]).astype(np.uint8)
        else:
            gray = raw_uint8.copy()
        stages["grayscale"] = gray

        # Step 1: Bilateral edge-preserving filtering
        denoised = self._apply_bilateral_filter(gray)
        stages["bilateral_denoised"] = denoised

        # Step 2: CLAHE contrast enhancement
        enhanced = self._apply_clahe(denoised)
        stages["clahe_enhanced"] = enhanced

        # Step 3: Resize to target size
        resized = self._resize(enhanced, self.target_size)
        stages["resized"] = resized

        # Step 4: Expand to 3-channel RGB for pre-trained CNN backbones
        rgb_enhanced = np.stack([resized] * 3, axis=-1)
        stages["dip_final_visual"] = rgb_enhanced

        # Normalize to [0.0, 1.0] float32 for model tensor input
        normalized = rgb_enhanced.astype(np.float32) / 255.0

        return normalized, stages
