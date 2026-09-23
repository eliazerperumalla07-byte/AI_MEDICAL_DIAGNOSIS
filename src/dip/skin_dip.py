"""
Digital Image Processing (DIP) Pipeline for Dermoscopic Skin Lesion Images.
Techniques:
1. DullRazor Algorithm: Morphological top-hat filter for hair detection + Telea/Bilinear inpainting.
2. Shades-of-Gray Algorithm: Color constancy normalization to eliminate dermatoscope lighting bias.
3. Contrast Preservation and Edge Sharpening.
"""

from typing import Dict, Tuple
import numpy as np

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

from .base import BasePreprocessor


class SkinLesionPreprocessor(BasePreprocessor):
    """
    DIP pipeline engineered for Dermoscopic Images (e.g., DermaMNIST, ISIC Archive).
    """

    def __init__(
        self,
        target_size: Tuple[int, int] = (224, 224),
        hair_removal_kernel_size: int = 15,
        hair_threshold: int = 10,
        minkowski_norm_p: int = 6,
    ):
        super().__init__(target_size=target_size)
        self.hair_removal_kernel_size = hair_removal_kernel_size
        self.hair_threshold = hair_threshold
        self.minkowski_norm_p = minkowski_norm_p

    def _dull_razor(self, img_rgb: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        DullRazor hair-removal algorithm:
        1. Grayscale morphological black top-hat to detect dark thin hair structures.
        2. Threshold to produce hair mask.
        3. Inpaint masked regions using local neighborhood information.
        """
        if HAS_OPENCV:
            gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
            # Structuring element for hair-like thin linear structures
            ksize = self.hair_removal_kernel_size
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (ksize, ksize))
            # Black top-hat = Closing(I) - I
            blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
            # Threshold to produce binary hair mask
            _, hair_mask = cv2.threshold(blackhat, self.hair_threshold, 255, cv2.THRESH_BINARY)
            # Inpaint original RGB using Telea algorithm
            inpainted = cv2.inpaint(img_rgb, hair_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
            return inpainted, hair_mask
        else:
            # Fallback simple median filter on high variance pixels
            gray = (0.2989 * img_rgb[:, :, 0] + 0.5870 * img_rgb[:, :, 1] + 0.1140 * img_rgb[:, :, 2]).astype(np.uint8)
            hair_mask = np.zeros_like(gray, dtype=np.uint8)
            # Rough local standard deviation estimate
            pad = np.pad(gray, 2, mode="edge")
            H, W = gray.shape
            clean = img_rgb.copy()
            for i in range(H):
                for j in range(W):
                    patch = pad[i : i + 5, j : j + 5]
                    if np.std(patch) > 35 and gray[i, j] < 80:
                        hair_mask[i, j] = 255
                        clean[i, j] = np.mean(patch)
            return clean, hair_mask

    def _shades_of_gray(self, img_rgb: np.ndarray) -> np.ndarray:
        """
        Shades-of-Gray Color Constancy algorithm:
        Estimates the illuminant using Minkowski p-norm and normalizes color channels.
        Formula: L_c = ( 1/N * sum(I_c(x)^p) )^(1/p)
        """
        img_float = img_rgb.astype(np.float32) + 1e-6
        p = self.minkowski_norm_p

        # Compute Minkowski norm per channel
        power_img = np.power(img_float, p)
        illuminant = np.power(np.mean(power_img, axis=(0, 1)), 1.0 / p)

        # Target gray reference (mean of the three illuminants)
        target = np.mean(illuminant)

        # Scale channels
        scale = target / (illuminant + 1e-6)
        corrected = img_float * scale[np.newaxis, np.newaxis, :]
        return np.clip(corrected, 0, 255).astype(np.uint8)

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
        Executes full skin dermoscopy DIP pipeline.
        Returns:
            processed_image: (224, 224, 3) float32 normalized in [0, 1]
            stages: Dict of stage visual outputs (uint8)
        """
        raw_uint8 = self.ensure_uint8(image)
        rgb_img = self.to_rgb(raw_uint8)
        stages = {"raw": rgb_img}

        # Step 1: DullRazor hair removal
        hair_free, hair_mask = self._dull_razor(rgb_img)
        stages["hair_mask"] = hair_mask
        stages["dullrazor_hair_removed"] = hair_free

        # Step 2: Shades-of-Gray color constancy
        color_corrected = self._shades_of_gray(hair_free)
        stages["color_constancy"] = color_corrected

        # Step 3: Resize to target size
        resized = self._resize(color_corrected, self.target_size)
        stages["dip_final_visual"] = resized

        # Normalize to [0.0, 1.0] float32
        normalized = resized.astype(np.float32) / 255.0

        return normalized, stages
