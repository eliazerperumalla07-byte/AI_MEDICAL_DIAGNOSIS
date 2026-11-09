"""
Generate High-Resolution Figures for the B.Tech Major Project Phase-I Report.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIG_DIR = os.path.join(PROJECT_ROOT, "documentation", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# -------------------------------------------------------------
# 1. Figure 3.1: Block Diagram of Proposed System
# -------------------------------------------------------------
def generate_block_diagram():
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    ax.axis("off")
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)

    # Styling helper
    def draw_box(x, y, w, h, title, subtitle="", color="#e0e7ff", border="#4338ca"):
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.1,rounding_size=0.15",
            facecolor=color, edgecolor=border, linewidth=1.8
        )
        ax.add_patch(rect)
        if subtitle:
            ax.text(x + w/2, y + h*0.62, title, ha="center", va="center", fontsize=9.5, fontweight="bold", color="#1e1b4b")
            ax.text(x + w/2, y + h*0.32, subtitle, ha="center", va="center", fontsize=8, color="#374151")
        else:
            ax.text(x + w/2, y + h/2, title, ha="center", va="center", fontsize=9.5, fontweight="bold", color="#1e1b4b")

    def draw_arrow(x1, y1, x2, y2, label=""):
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(facecolor="#4b5563", edgecolor="#374151", width=1.5, headwidth=6, headlength=7, shrink=0.05)
        )
        if label:
            ax.text((x1+x2)/2, (y1+y2)/2 + 0.15, label, ha="center", va="center", fontsize=7.5, color="#4b5563", fontweight="semibold")

    # Layer 1: Input Image
    draw_box(0.5, 3.4, 2.2, 1.2, "Medical Image Input", "DICOM / PNG / JPEG\n(Chest / Skin / Retina)", color="#f1f5f9", border="#64748b")

    # Layer 2: Modality Router
    draw_box(3.4, 3.4, 2.3, 1.2, "Modality Router", "Spectral Profiling +\nCNN Classification", color="#dbeafe", border="#2563eb")
    draw_arrow(2.7, 4.0, 3.4, 4.0, "RGB / Gray")

    # Layer 3: Specialized DIP Modules
    draw_box(6.4, 5.8, 2.5, 1.1, "Chest X-Ray DIP", "Bilateral Filter + CLAHE\n(Dynamic Range Expand)", color="#fef3c7", border="#d97706")
    draw_box(6.4, 3.45, 2.5, 1.1, "Dermoscopy DIP", "DullRazor Inpainting +\nShades-of-Gray Constancy", color="#fef3c7", border="#d97706")
    draw_box(6.4, 1.1, 2.5, 1.1, "Retinal Fundus DIP", "Ben Graham Circular Crop +\nGreen Channel CLAHE", color="#fef3c7", border="#d97706")

    # Routing Arrows
    ax.annotate("", xy=(6.4, 6.35), xytext=(5.7, 4.2), arrowprops=dict(facecolor="#2563eb", edgecolor="#2563eb", width=1.2, headwidth=5))
    ax.annotate("", xy=(6.4, 4.0), xytext=(5.7, 4.0), arrowprops=dict(facecolor="#2563eb", edgecolor="#2563eb", width=1.2, headwidth=5))
    ax.annotate("", xy=(6.4, 1.65), xytext=(5.7, 3.8), arrowprops=dict(facecolor="#2563eb", edgecolor="#2563eb", width=1.2, headwidth=5))

    ax.text(5.75, 5.6, "Chest", fontsize=8, color="#1e40af", fontweight="bold")
    ax.text(5.95, 4.15, "Skin", fontsize=8, color="#1e40af", fontweight="bold")
    ax.text(5.75, 2.4, "Retina", fontsize=8, color="#1e40af", fontweight="bold")

    # Layer 4: Deep Learning Models
    draw_box(9.5, 5.8, 2.3, 1.1, "Chest Abnormality Model", "DenseNet-121 / CheXNet\n(14 Multi-Label Binary)", color="#ede9fe", border="#7c3aed")
    draw_box(9.5, 3.45, 2.3, 1.1, "Skin Lesion Model", "EfficientNet-B0\n(7 Multi-Class Softmax)", color="#ede9fe", border="#7c3aed")
    draw_box(9.5, 1.1, 2.3, 1.1, "Retinal Staging Model", "ResNet-50\n(5 Ordinal DR Grades)", color="#ede9fe", border="#7c3aed")

    draw_arrow(8.9, 6.35, 9.5, 6.35)
    draw_arrow(8.9, 4.0, 9.5, 4.0)
    draw_arrow(8.9, 1.65, 9.5, 1.65)

    # Layer 5: Explainability & Dashboard Integration
    draw_box(12.3, 4.8, 1.5, 2.1, "Grad-CAM Engine", "Activation Hooks\nSaliency Maps\n70% Contours", color="#fee2e2", border="#dc2626")
    draw_box(12.3, 1.1, 1.5, 3.0, "Clinical Portal\n& Edge AI", "Streamlit UI\nGlassmorphism\nONNX / INT8\n100+ FPS", color="#d1fae5", border="#059669")

    # Model to Output arrows
    draw_arrow(11.8, 6.35, 12.3, 6.0)
    draw_arrow(11.8, 4.0, 12.3, 5.2)
    draw_arrow(11.8, 1.65, 12.3, 4.9)

    draw_arrow(11.8, 6.35, 12.3, 3.6)
    draw_arrow(11.8, 4.0, 12.3, 2.6)
    draw_arrow(11.8, 1.65, 12.3, 1.65)

    plt.title("Fig. 3.1: Block Diagram of the Proposed Multi-Disease Medical AI Diagnostic System", fontsize=12, fontweight="bold", pad=15, color="#111827")
    plt.tight_layout()
    out_path = os.path.join(FIG_DIR, "fig3_1_block_diagram.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated: {out_path}")

# -------------------------------------------------------------
# 2. Figure 3.2: Working Flowchart of the Proposed System
# -------------------------------------------------------------
def generate_flowchart():
    fig, ax = plt.subplots(figsize=(10, 12), dpi=300)
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)

    def draw_flow_box(x, y, w, h, text, shape="rect", color="#e0e7ff", border="#4338ca"):
        if shape == "oval":
            patch = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=0.3", facecolor=color, edgecolor=border, lw=1.8)
        elif shape == "diamond":
            pts = np.array([[x + w/2, y], [x + w, y + h/2], [x + w/2, y + h], [x, y + h/2]])
            patch = patches.Polygon(pts, closed=True, facecolor=color, edgecolor=border, lw=1.8)
        else:
            patch = patches.Rectangle((x, y), w, h, facecolor=color, edgecolor=border, lw=1.8)
        ax.add_patch(patch)
        ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=8.5, fontweight="semibold", color="#111827", multialignment="center")

    def draw_farrow(x1, y1, x2, y2, text=""):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(facecolor="#1e293b", edgecolor="#1e293b", width=1.5, headwidth=5.5, headlength=6))
        if text:
            ax.text((x1+x2)/2 + 0.15, (y1+y2)/2, text, fontsize=8, color="#1e293b", fontweight="bold")

    # Start
    draw_flow_box(3.5, 11.0, 3.0, 0.7, "Start", shape="oval", color="#dcfce7", border="#16a34a")

    # Step 1: Upload
    draw_flow_box(3.0, 9.8, 4.0, 0.8, "Upload Medical Image\n(Chest X-Ray / Skin / Retina)", color="#f8fafc", border="#64748b")
    draw_farrow(5.0, 11.0, 5.0, 10.6)

    # Step 2: Modality Router
    draw_flow_box(2.8, 8.5, 4.4, 0.9, "Modality Router Execution\n(Spectral Heuristic + Neural Classifier)", color="#dbeafe", border="#2563eb")
    draw_farrow(5.0, 9.8, 5.0, 9.4)

    # Step 3: Modality Decision
    draw_flow_box(3.0, 6.9, 4.0, 1.2, "Identify Modality\nType?", shape="diamond", color="#fef3c7", border="#d97706")
    draw_farrow(5.0, 8.5, 5.0, 8.1)

    # 3 Branches: DIP
    draw_flow_box(0.3, 5.2, 2.7, 0.9, "Chest DIP Pipeline\n(Bilateral + CLAHE)", color="#ede9fe", border="#7c3aed")
    draw_flow_box(3.6, 5.2, 2.8, 0.9, "Dermoscopy DIP\n(DullRazor + Shades-of-Gray)", color="#ede9fe", border="#7c3aed")
    draw_flow_box(7.0, 5.2, 2.7, 0.9, "Retinal Fundus DIP\n(Ben Graham + Green CLAHE)", color="#ede9fe", border="#7c3aed")

    # Connect decision to DIP
    ax.annotate("", xy=(1.65, 6.1), xytext=(3.0, 7.5), arrowprops=dict(facecolor="#1e293b", width=1.2, headwidth=4))
    ax.text(1.9, 7.1, "Chest X-Ray", fontsize=7.5, fontweight="bold", color="#1e40af")

    ax.annotate("", xy=(5.0, 6.1), xytext=(5.0, 6.9), arrowprops=dict(facecolor="#1e293b", width=1.2, headwidth=4))
    ax.text(5.1, 6.5, "Skin", fontsize=7.5, fontweight="bold", color="#1e40af")

    ax.annotate("", xy=(8.35, 6.1), xytext=(7.0, 7.5), arrowprops=dict(facecolor="#1e293b", width=1.2, headwidth=4))
    ax.text(7.6, 7.1, "Retina", fontsize=7.5, fontweight="bold", color="#1e40af")

    # Models
    draw_flow_box(0.3, 3.8, 2.7, 0.9, "DenseNet-121 Inference\n(14 Disease Logits + BCE)", color="#fee2e2", border="#dc2626")
    draw_flow_box(3.6, 3.8, 2.8, 0.9, "EfficientNet-B0 Inference\n(7 Lesion Classes + Softmax)", color="#fee2e2", border="#dc2626")
    draw_flow_box(7.0, 3.8, 2.7, 0.9, "ResNet-50 Inference\n(5 DR Severity Grades)", color="#fee2e2", border="#dc2626")

    draw_farrow(1.65, 5.2, 1.65, 4.7)
    draw_farrow(5.0, 5.2, 5.0, 4.7)
    draw_farrow(8.35, 5.2, 8.35, 4.7)

    # Reconvergence
    draw_flow_box(2.2, 2.3, 5.6, 1.0, "Grad-CAM Saliency Computation\n(Deepest Conv Feature Maps & Gradient Hooks)", color="#fef9c3", border="#ca8a04")

    ax.annotate("", xy=(3.5, 3.3), xytext=(1.65, 3.8), arrowprops=dict(facecolor="#1e293b", width=1.2, headwidth=4))
    ax.annotate("", xy=(5.0, 3.3), xytext=(5.0, 3.8), arrowprops=dict(facecolor="#1e293b", width=1.2, headwidth=4))
    ax.annotate("", xy=(6.5, 3.3), xytext=(8.35, 3.8), arrowprops=dict(facecolor="#1e293b", width=1.2, headwidth=4))

    # Output
    draw_flow_box(2.2, 1.0, 5.6, 0.9, "Render Glassmorphic Clinical Report\n(Findings, Risk Level, Probabilities & XAI Contours)", color="#d1fae5", border="#059669")
    draw_farrow(5.0, 2.3, 5.0, 1.9)

    # End
    draw_flow_box(4.0, 0.1, 2.0, 0.6, "End", shape="oval", color="#dcfce7", border="#16a34a")
    draw_farrow(5.0, 1.0, 5.0, 0.7)

    plt.title("Figure 3.2: Working Flowchart of the Proposed Medical Diagnostic System", fontsize=11, fontweight="bold", pad=12, color="#111827")
    plt.tight_layout()
    out_path = os.path.join(FIG_DIR, "fig3_2_flowchart.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated: {out_path}")

if __name__ == "__main__":
    generate_block_diagram()
    generate_flowchart()
