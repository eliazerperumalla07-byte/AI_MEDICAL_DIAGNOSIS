"""
Explainable AI (XAI) Module: Grad-CAM (Gradient-weighted Class Activation Mapping).
Generates saliency heatmaps highlighting anatomical/pathological regions influencing
the model's prediction, with automated lesion contouring and bounding contours.
"""

from typing import Tuple, Optional, Dict, Any
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False


class GradCAM:
    """
    Grad-CAM engine for PyTorch convolutional backbones.
    Hooks into activations and gradients of the target convolutional layer.
    """

    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.gradients: Optional[torch.Tensor] = None
        self.activations: Optional[torch.Tensor] = None
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0].detach()

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)

    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        target_class_idx: Optional[int] = None,
    ) -> np.ndarray:
        """
        Computes Grad-CAM heatmap for a given input tensor and class index.

        Args:
            input_tensor: (1, 3, H, W) normalized float tensor.
            target_class_idx: Int class index. If None, uses top predicted class.

        Returns:
            heatmap: (H, W) float32 array in [0.0, 1.0].
        """
        self.model.eval()
        self.model.zero_grad()

        # Forward pass
        logits = self.model(input_tensor)

        if target_class_idx is None:
            target_class_idx = int(torch.argmax(logits, dim=-1).item())

        score = logits[0, target_class_idx]
        score.backward(retain_graph=True)

        if self.gradients is None or self.activations is None:
            # Fallback uniform heatmap if gradients were not captured
            _, _, H, W = input_tensor.shape
            return np.zeros((H, W), dtype=np.float32)

        # Global average pooling of gradients: weights alpha_k
        weights = torch.mean(self.gradients, dim=[2, 3], keepdim=True)  # (1, C, 1, 1)

        # Weighted combination of forward activation maps
        cam = torch.sum(weights * self.activations, dim=1, keepdim=True)  # (1, 1, h, w)

        # Apply ReLU (we only care about features that have a positive influence)
        cam = F.relu(cam)

        # Upsample to match original input size (H, W)
        _, _, H, W = input_tensor.shape
        cam = F.interpolate(cam, size=(H, W), mode="bilinear", align_corners=False)

        cam_np = cam.squeeze().cpu().numpy()

        # Normalize to [0, 1]
        cam_min, cam_max = cam_np.min(), cam_np.max()
        if cam_max - cam_min > 1e-8:
            heatmap = (cam_np - cam_min) / (cam_max - cam_min)
        else:
            heatmap = np.zeros_like(cam_np)

        return heatmap.astype(np.float32)

    def overlay_heatmap(
        self,
        original_img: np.ndarray,
        heatmap: np.ndarray,
        alpha: float = 0.45,
        colormap: int = 2,  # cv2.COLORMAP_JET
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Overlays heatmap on original RGB image and extracts suspicious lesion contours.

        Args:
            original_img: (H, W, 3) uint8 or float.
            heatmap: (H, W) float32 in [0, 1].
            alpha: Transparency factor for heatmap.

        Returns:
            overlay: (H, W, 3) uint8 blended image.
            contoured: (H, W, 3) uint8 blended image with highlighted lesion boundary contours.
        """
        if original_img.dtype != np.uint8:
            orig_uint8 = (original_img * 255.0).clip(0, 255).astype(np.uint8)
        else:
            orig_uint8 = original_img.copy()

        H, W = orig_uint8.shape[:2]

        if HAS_OPENCV:
            heatmap_resized = cv2.resize(heatmap, (W, H))
            heatmap_uint8 = (heatmap_resized * 255).astype(np.uint8)
            colored_cam = cv2.applyColorMap(heatmap_uint8, colormap)
            colored_cam = cv2.cvtColor(colored_cam, cv2.COLOR_BGR2RGB)

            # Blend
            blended = cv2.addWeighted(orig_uint8, 1.0 - alpha, colored_cam, alpha, 0)

            # Lesion boundary: contour regions above 70th percentile
            thresh_val = int(np.percentile(heatmap_uint8, 70))
            _, binary_mask = cv2.threshold(heatmap_uint8, max(50, thresh_val), 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            contoured = blended.copy()
            cv2.drawContours(contoured, contours, -1, (255, 230, 0), 2)  # Bright yellow outline

            return blended, contoured
        else:
            # Fallback color overlay without opencv
            r_heat = (heatmap * 255).astype(np.uint8)
            b_heat = ((1.0 - heatmap) * 255).astype(np.uint8)
            g_heat = np.zeros_like(r_heat)
            pseudo_color = np.stack([r_heat, g_heat, b_heat], axis=-1)
            blended = (orig_uint8 * (1.0 - alpha) + pseudo_color * alpha).clip(0, 255).astype(np.uint8)
            return blended, blended
