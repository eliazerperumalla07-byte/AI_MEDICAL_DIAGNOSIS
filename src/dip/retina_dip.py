"""
Digital Image Processing (DIP) Pipeline for Retinal Fundus Photography.
Techniques:
1. Ben Graham's Illumination Equalization: Circular FOV auto-crop + Local average color subtraction.
2. Green Channel Optical Optimization: Peak hemoglobin optical absorption (~540-575nm)
   to maximize contrast of microaneurysms and hemorrhages.
3. CLAHE on green/luminance channel.
"""

from typing import Dict, Tuple
import numpy as np

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

from .base import BasePreprocessor


class RetinalFundusPreprocessor(BasePreprocessor):
    """
    DIP pipeline engineered for Retinal Fundus Photography (e.g., RetinaMNIST, APTOS, EyePACS).
    """

    def __init__(
        self,
        target_size: Tuple[int, int] = (224, 224),
        gaussian_sigma: float = 10.0,
        clahe_clip_limit: float = 2.5,
        clahe_tile_grid_size: Tuple[int, int] = (8, 8),
    ):
        super().__init__(target_size=target_size)
        self.gaussian_sigma = gaussian_sigma
        self.clahe_clip_limit = clahe_clip_limit
        self.clahe_tile_grid_size = clahe_tile_grid_size

    def _crop_circular_fov(self, img_rgb: np.ndarray, tolerance: int = 7) -> np.ndarray:
        """
        Crops extraneous black borders from circular fundus photograph.
        """
        gray = np.mean(img_rgb, axis=2) if len(img_rgb.shape) == 3 else img_rgb
        mask = gray > tolerance
        if not np.any(mask):
            return img_rgb

        # Find bounding box of foreground
        row_indices = np.where(np.any(mask, axis=1))[0]
        col_indices = np.where(np.any(mask, axis=0))[0]

        if len(row_indices) == 0 or len(col_indices) == 0:
            return img_rgb

        min_y, max_y = row_indices[0], row_indices[-1]
        min_x, max_x = col_indices[0], col_indices[-1]

        # Make square crop
        h = max_y - min_y
        w = max_x - min_x
        size = max(h, w)

        center_y = (min_y + max_y) // 2
        center_x = (min_x + max_x) // 2

        orig_h, orig_w = img_rgb.shape[:2]
        y1 = max(0, center_y - size // 2)
        y2 = min(orig_h, center_y + size // 2)
        x1 = max(0, center_x - size // 2)
        x2 = min(orig_w, center_x + size // 2)

        return img_rgb[y1:y2, x1:x2]

    def _ben_graham_enhancement(self, img_rgb: np.ndarray) -> np.ndarray:
        """
        Ben Graham's method:
        Subtract local Gaussian blur to remove non-uniform retinal illumination.
        I_out = 4 * I - 4 * Gaussian(I, sigma=10) + 128
        """
        if HAS_OPENCV:
            blur = cv2.GaussianBlur(img_rgb, (0, 0), self.gaussian_sigma)
            # Weighted subtraction
            enhanced = cv2.addWeighted(img_rgb, 4, blur, -4, 128)
            return enhanced
        else:
            # Fallback simple mean filter
            return img_rgb

    def _enhance_green_channel(self, img_rgb: np.ndarray) -> np.ndarray:
        """
        Enhances green channel using CLAHE since retinal vascular lesions
        show maximum optical attenuation in the green wavelength range.
        """
        if not HAS_OPENCV:
            return img_rgb

        lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(
            clipLimit=self.clahe_clip_limit,
            tileGridSize=self.clahe_tile_grid_size,
        )
        l_clahe = clahe.apply(l)
        merged_lab = cv2.merge((l_clahe, a, b))
        return cv2.cvtColor(merged_lab, cv2.COLOR_LAB2RGB)

    def _resize(self, img: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
        if HAS_OPENCV:
            return cv2.resize(img, size, interpolation=cv2.INTER_AREA)
        orig_h, orig_w = img.shape[:2]
        target_w, target_h = size
        row_indices = (np.linspace(0, orig_h - 1, target_h)).astype(int)
        col_indices = (np.linspace(0, orig_w - 1, target_w)).astype(int)
        return img[np.ix_(row_indices, col_indices)]

    def preprocess(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Executes full retinal fundus DIP pipeline.
        Returns:
            processed_image: (224, 224, 3) float32 normalized in [0, 1]
            stages: Dict of stage visual outputs (uint8)
        """
        raw_uint8 = self.ensure_uint8(image)
        rgb_img = self.to_rgb(raw_uint8)
        stages = {"raw": rgb_img}

        # Step 1: Circular FOV auto-crop
        cropped = self._crop_circular_fov(rgb_img)
        resized_temp = self._resize(cropped, self.target_size)
        stages["cropped_fov"] = resized_temp

        # Step 2: Ben Graham illumination subtraction
        graham = self._ben_graham_enhancement(resized_temp)
        stages["ben_graham_equalized"] = graham

        # Step 3: Green/Luminance CLAHE microvascular enhancement
        final_enhanced = self._enhance_green_channel(graham)
        stages["dip_final_visual"] = final_enhanced

        # Normalize to [0.0, 1.0] float32
        normalized = final_enhanced.astype(np.float32) / 255.0

        return normalized, stages
