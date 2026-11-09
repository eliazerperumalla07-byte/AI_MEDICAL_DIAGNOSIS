"""
Generate DIP Pipeline and Grad-CAM Results Figures for the Project Report.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.dip.chest_dip import ChestXRayPreprocessor
from src.dip.skin_dip import SkinLesionPreprocessor
from src.dip.retina_dip import RetinalFundusPreprocessor
from src.pipeline.multi_disease_system import MultiDiseaseDiagnosticSystem

FIG_DIR = os.path.join(PROJECT_ROOT, "documentation", "figures")
SAMPLES_DIR = os.path.join(PROJECT_ROOT, "data", "samples")

def generate_dip_figure():
    c_prep = ChestXRayPreprocessor()
    s_prep = SkinLesionPreprocessor()
    r_prep = RetinalFundusPreprocessor()

    c_img = np.array(Image.open(os.path.join(SAMPLES_DIR, "real_chest_xray.png")))
    s_img = np.array(Image.open(os.path.join(SAMPLES_DIR, "real_skin_lesion.png")))
    r_img = np.array(Image.open(os.path.join(SAMPLES_DIR, "real_retinal_fundus.png")))

    _, c_stages = c_prep.preprocess(c_img)
    _, s_stages = s_prep.preprocess(s_img)
    _, r_stages = r_prep.preprocess(r_img)

    fig, axes = plt.subplots(3, 4, figsize=(14, 10), dpi=300)

    # Row 1: Chest
    axes[0, 0].imshow(c_stages["raw"], cmap="gray")
    axes[0, 0].set_title("(a) Raw Radiograph", fontsize=9, fontweight="bold")
    axes[0, 1].imshow(c_stages["bilateral_denoised"], cmap="gray")
    axes[0, 1].set_title("(b) Bilateral Denoised", fontsize=9, fontweight="bold")
    axes[0, 2].imshow(c_stages["clahe_enhanced"], cmap="gray")
    axes[0, 2].set_title("(c) CLAHE Contrast", fontsize=9, fontweight="bold")
    axes[0, 3].imshow(c_stages["dip_final_visual"])
    axes[0, 3].set_title("(d) Final Normalized", fontsize=9, fontweight="bold")

    # Row 2: Skin
    axes[1, 0].imshow(s_stages["raw"])
    axes[1, 0].set_title("(e) Raw Dermoscopy", fontsize=9, fontweight="bold")
    axes[1, 1].imshow(s_stages["hair_mask"], cmap="gray")
    axes[1, 1].set_title("(f) DullRazor Hair Mask", fontsize=9, fontweight="bold")
    axes[1, 2].imshow(s_stages["color_constancy"])
    axes[1, 2].set_title("(g) Shades-of-Gray Constancy", fontsize=9, fontweight="bold")
    axes[1, 3].imshow(s_stages["dip_final_visual"])
    axes[1, 3].set_title("(h) Final Normalized", fontsize=9, fontweight="bold")

    # Row 3: Retina
    axes[2, 0].imshow(r_stages["raw"])
    axes[2, 0].set_title("(i) Raw Fundus", fontsize=9, fontweight="bold")
    axes[2, 1].imshow(r_stages["cropped_fov"])
    axes[2, 1].set_title("(j) Circular FOV Crop", fontsize=9, fontweight="bold")
    axes[2, 2].imshow(r_stages["ben_graham_equalized"])
    axes[2, 2].set_title("(k) Ben Graham Equalization", fontsize=9, fontweight="bold")
    axes[2, 3].imshow(r_stages["dip_final_visual"])
    axes[2, 3].set_title("(l) Green-CLAHE Microvascular", fontsize=9, fontweight="bold")

    for ax in axes.flat:
        ax.axis("off")

    plt.suptitle("Fig. 4.2: Digital Image Processing (DIP) Multi-Stage Enhancement Across Modalities", fontsize=12, fontweight="bold", y=0.98)
    plt.tight_layout()
    out_path = os.path.join(FIG_DIR, "fig4_2_dip_pipeline.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated: {out_path}")

def generate_xai_figure():
    engine = MultiDiseaseDiagnosticSystem(use_transfer_learning=False)

    c_path = os.path.join(SAMPLES_DIR, "real_chest_xray.png")
    s_path = os.path.join(SAMPLES_DIR, "real_skin_lesion.png")
    r_path = os.path.join(SAMPLES_DIR, "real_retinal_fundus.png")

    c_res = engine.diagnose(c_path, generate_xai=True)
    s_res = engine.diagnose(s_path, generate_xai=True)
    r_res = engine.diagnose(r_path, generate_xai=True)

    fig, axes = plt.subplots(3, 3, figsize=(11, 10), dpi=300)

    # Chest
    axes[0, 0].imshow(c_res["dip_stages"]["dip_final_visual"])
    axes[0, 0].set_title("Chest: DIP Input", fontsize=9, fontweight="bold")
    axes[0, 1].imshow(c_res["xai"]["overlay"])
    axes[0, 1].set_title("Chest: Grad-CAM Saliency", fontsize=9, fontweight="bold")
    axes[0, 2].imshow(c_res["xai"]["contoured"])
    axes[0, 2].set_title("Chest: Lesion Contours", fontsize=9, fontweight="bold")

    # Skin
    axes[1, 0].imshow(s_res["dip_stages"]["dip_final_visual"])
    axes[1, 0].set_title("Skin: DIP Input", fontsize=9, fontweight="bold")
    axes[1, 1].imshow(s_res["xai"]["overlay"])
    axes[1, 1].set_title("Skin: Grad-CAM Saliency", fontsize=9, fontweight="bold")
    axes[1, 2].imshow(s_res["xai"]["contoured"])
    axes[1, 2].set_title("Skin: Lesion Contours", fontsize=9, fontweight="bold")

    # Retina
    axes[2, 0].imshow(r_res["dip_stages"]["dip_final_visual"])
    axes[2, 0].set_title("Retina: DIP Input", fontsize=9, fontweight="bold")
    axes[2, 1].imshow(r_res["xai"]["overlay"])
    axes[2, 1].set_title("Retina: Grad-CAM Saliency", fontsize=9, fontweight="bold")
    axes[2, 2].imshow(r_res["xai"]["contoured"])
    axes[2, 2].set_title("Retina: Lesion Contours", fontsize=9, fontweight="bold")

    for ax in axes.flat:
        ax.axis("off")

    plt.suptitle("Fig. 4.4: Grad-CAM Explainable AI Saliency Heatmaps & Pathology Localization", fontsize=12, fontweight="bold", y=0.98)
    plt.tight_layout()
    out_path = os.path.join(FIG_DIR, "fig4_4_gradcam.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated: {out_path}")

if __name__ == "__main__":
    generate_dip_figure()
    generate_xai_figure()
