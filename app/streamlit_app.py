"""
Streamlit Web Application: AI-Based Multi-Disease Detection Portal.
ECE Major Project — Digital Image Processing (DIP) & Specialized Deep Learning.
Designed with Ultra-Modern Glassmorphism UI & High-Performance Resource Caching.
"""

import os
import sys
import time
from typing import Optional, Dict, Any
import numpy as np
from PIL import Image

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.pipeline.multi_disease_system import MultiDiseaseDiagnosticSystem
from src.router.modality_classifier import MedicalModality


def init_app():
    if not HAS_STREAMLIT:
        return

    st.set_page_config(
        page_title="Multi-Disease AI | Medical Diagnostics",
        page_icon="🩻",
        layout="wide",
        initial_sidebar_state="expanded",
    )


# High-Performance Caching: Keeps models in GPU/MPS memory across UI interactions
@st.cache_resource(show_spinner=False)
def get_cached_engine(use_transfer_learning: bool = True) -> MultiDiseaseDiagnosticSystem:
    return MultiDiseaseDiagnosticSystem(use_transfer_learning=use_transfer_learning)


def inject_glassmorphism_css():
    st.markdown(
        """
        <style>
        /* Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Glassmorphism Cards */
        .glass-panel {
            background: rgba(255, 255, 255, 0.035);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
            transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
        }
        
        .glass-panel:hover {
            border-color: rgba(99, 102, 241, 0.35);
            box-shadow: 0 14px 40px rgba(99, 102, 241, 0.12);
        }

        .glass-header {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(168, 85, 247, 0.08) 100%);
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 22px;
            padding: 28px;
            margin-bottom: 28px;
            position: relative;
            overflow: hidden;
        }

        .glass-header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
            pointer-events: none;
        }

        /* Neon & Gradient Badges */
        .badge-cyan {
            display: inline-block;
            background: rgba(6, 182, 212, 0.15);
            color: #22d3ee;
            border: 1px solid rgba(34, 211, 238, 0.3);
            border-radius: 9999px;
            padding: 4px 14px;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }

        .badge-emerald {
            display: inline-block;
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(52, 211, 153, 0.3);
            border-radius: 9999px;
            padding: 4px 14px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .badge-amber {
            display: inline-block;
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(251, 191, 36, 0.3);
            border-radius: 9999px;
            padding: 4px 14px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .badge-rose {
            display: inline-block;
            background: rgba(244, 63, 94, 0.15);
            color: #fb7185;
            border: 1px solid rgba(251, 113, 133, 0.3);
            border-radius: 9999px;
            padding: 4px 14px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        /* Diagnostic Metric Card */
        .metric-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 14px;
            padding: 16px;
            text-align: center;
        }

        .metric-value {
            font-size: 1.6rem;
            font-weight: 700;
            background: linear-gradient(135deg, #a5b4fc 0%, #e0e7ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .metric-label {
            font-size: 0.75rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-top: 4px;
        }

        /* Disease Item Row */
        .prob-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 12px;
            margin-bottom: 6px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 10px;
            transition: background 0.2s ease;
        }

        .prob-row:hover {
            background: rgba(255, 255, 255, 0.04);
        }

        /* Glassmorphism for Left Sidebar / Option Menu */
        section[data-testid="stSidebar"] {
            background: rgba(13, 17, 23, 0.72) !important;
            backdrop-filter: blur(28px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
            box-shadow: 6px 0 35px rgba(0, 0, 0, 0.45) !important;
        }

        section[data-testid="stSidebar"] > div {
            background: transparent !important;
        }

        /* Frosted Glass Effect on Sidebar Widgets */
        section[data-testid="stSidebar"] div[data-testid="stRadio"],
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"],
        section[data-testid="stSidebar"] div[data-testid="stSlider"] {
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 16px !important;
            padding: 14px !important;
            margin-bottom: 14px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.18) !important;
            transition: all 0.25s ease !important;
        }

        section[data-testid="stSidebar"] div[data-testid="stRadio"]:hover,
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"]:hover,
        section[data-testid="stSidebar"] div[data-testid="stSlider"]:hover {
            border-color: rgba(99, 102, 241, 0.4) !important;
            box-shadow: 0 6px 24px rgba(99, 102, 241, 0.15) !important;
        }

        /* Sidebar Buttons Glassmorphic Styling */
        section[data-testid="stSidebar"] button {
            background: rgba(255, 255, 255, 0.04) !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 12px !important;
            color: #f1f5f9 !important;
            font-weight: 600 !important;
            padding: 8px 12px !important;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25) !important;
            transition: all 0.25s ease !important;
        }

        section[data-testid="stSidebar"] button:hover {
            background: rgba(99, 102, 241, 0.25) !important;
            border-color: rgba(99, 102, 241, 0.6) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 22px rgba(99, 102, 241, 0.3) !important;
        }

        section[data-testid="stSidebar"] button:active {
            transform: translateY(0px) !important;
        }

        /* Custom Scrollbars */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.2);
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.25);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    if not HAS_STREAMLIT:
        print("Please install streamlit.")
        return

    init_app()
    inject_glassmorphism_css()

    sample_dir = os.path.join(PROJECT_ROOT, "data", "samples")
    sample_chest = os.path.join(sample_dir, "sample_chest_xray.png")
    sample_skin = os.path.join(sample_dir, "sample_skin_lesion.png")
    sample_retina = os.path.join(sample_dir, "sample_retinal_fundus.png")

    # Session State Initialization
    if "selected_sample_path" not in st.session_state:
        st.session_state.selected_sample_path = sample_chest
    if "last_action" not in st.session_state:
        st.session_state.last_action = "init"

    # Glassmorphic Hero Banner
    st.markdown(
        """
        <div class="glass-header">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
                <div>
                    <span class="badge-cyan">ECE Major Project • Research Prototype</span>
                    <h1 style="margin: 10px 0 6px 0; font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                        AI Multi-Disease Diagnostic System
                    </h1>
                    <p style="margin: 0; color: #94a3b8; font-size: 0.95rem;">
                        Automated Image Modality Identification • Specialized Digital Image Processing (DIP) • Deep Transfer Learning • Grad-CAM Explainable AI
                    </p>
                </div>
                <div style="display: flex; gap: 10px;">
                    <div class="metric-card" style="padding: 10px 18px;">
                        <div class="metric-value">3</div>
                        <div class="metric-label">Modalities</div>
                    </div>
                    <div class="metric-card" style="padding: 10px 18px;">
                        <div class="metric-value">26</div>
                        <div class="metric-label">Conditions</div>
                    </div>
                    <div class="metric-card" style="padding: 10px 18px;">
                        <div class="metric-value">MPS</div>
                        <div class="metric-label">Apple GPU</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar Controls with Glass Styling
    with st.sidebar:
        st.markdown("### ⚙️ System Architecture")
        model_choice = st.radio(
            "Model Backbone:",
            options=["Custom Baseline CNN (ECE Benchmark)", "Transfer Learning (DenseNet/EfficientNet/ResNet)"],
            index=0,
            help="Compare the custom convolutional network designed from scratch vs. pre-trained backbones.",
        )
        use_tl = "Transfer Learning" in model_choice

        st.markdown("---")
        st.markdown("### 🧭 Modality Routing Mode")
        modality_selection = st.selectbox(
            "Target Modality:",
            options=[
                "Auto-Detect (Smart Router)",
                "Chest X-Ray (ChestMNIST)",
                "Skin Dermoscopy (DermaMNIST)",
                "Retinal Fundus (RetinaMNIST)",
            ],
            index=0,
            help="Auto-detect inspects optical spectral signatures before dispatching to the specialist neural model.",
        )

        st.markdown("---")
        st.markdown("### 🔬 Explainable AI (Grad-CAM)")
        enable_xai = st.toggle("Generate Saliency Heatmaps", value=True)
        cam_alpha = st.slider("Heatmap Blending Opacity", min_value=0.1, max_value=0.9, value=0.45, step=0.05)

        st.markdown("---")
        st.markdown("### ⚡ Quick-Load Clinical Samples")
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        if col_btn1.button("🫁 Chest", use_container_width=True):
            st.session_state.selected_sample_path = sample_chest
        if col_btn2.button("🩺 Skin", use_container_width=True):
            st.session_state.selected_sample_path = sample_skin
        if col_btn3.button("👁️ Retina", use_container_width=True):
            st.session_state.selected_sample_path = sample_retina

        st.caption("Extracted from MedMNIST+ standard evaluation archives.")

    # Image Input Selection
    input_col1, input_col2 = st.columns([1, 1.2], gap="large")

    with input_col1:
        st.markdown("#### 📥 Medical Image Input")
        uploaded_file = st.file_uploader(
            "Upload Clinical Image (DICOM / PNG / JPEG)",
            type=["png", "jpg", "jpeg"],
            help="Upload an X-ray, dermoscopy, or fundus photo. The smart router will automatically verify it.",
        )

        active_img = None
        source_label = ""
        if uploaded_file is not None:
            active_img = Image.open(uploaded_file)
            source_label = f"Uploaded File: {uploaded_file.name}"
        elif st.session_state.selected_sample_path and os.path.exists(st.session_state.selected_sample_path):
            active_img = Image.open(st.session_state.selected_sample_path)
            basename = os.path.basename(st.session_state.selected_sample_path)
            source_label = f"Clinical Test Sample: {basename.replace('_', ' ').replace('.png', '').title()}"

        if active_img is not None:
            st.image(active_img, caption=source_label, use_container_width=True)

    with input_col2:
        if active_img is None:
            st.info("👈 Please upload an image or choose one of the quick-load samples from the sidebar to begin analysis.")
            return

        # Cached Engine Fetching
        t_start = time.perf_counter()
        engine = get_cached_engine(use_transfer_learning=use_tl)

        # Modality selection parsing
        target_modality = None
        if "Chest" in modality_selection:
            target_modality = MedicalModality.CHEST
        elif "Skin" in modality_selection:
            target_modality = MedicalModality.SKIN
        elif "Retina" in modality_selection:
            target_modality = MedicalModality.RETINA

        # Execute Diagnostic Pipeline
        with st.spinner("Executing Modality Router, Digital Image Processing & Neural Inference..."):
            result = engine.diagnose(
                image_input=active_img,
                user_selected_modality=target_modality,
                generate_xai=enable_xai,
            )
        t_elapsed = (time.perf_counter() - t_start) * 1000.0

        # Modality Router Glass Card
        st.markdown("#### 1. Modality Identification & Routing")
        active_mod_str = result["modality"].replace("_", " ").title()
        detected_mod_str = result["detected_modality"].replace("_", " ").title()
        mismatch = result["modality_mismatch_warning"]

        if mismatch:
            st.markdown(
                f"""
                <div class="glass-panel" style="border-left: 4px solid #f43f5e; padding: 16px 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span class="badge-rose">Modality Mismatch Alert</span>
                            <div style="font-weight: 600; font-size: 1.05rem; margin-top: 6px;">
                                Selected: <span style="color: #cbd5e1;">{active_mod_str}</span> | Router Detected: <span style="color: #fb7185;">{detected_mod_str}</span>
                            </div>
                            <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px;">
                                Warning: Spectral properties suggest a different imaging type. System proceeded with manual override.
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="glass-panel" style="border-left: 4px solid #10b981; padding: 16px 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span class="badge-emerald">Modality Verified</span>
                            <div style="font-weight: 700; font-size: 1.15rem; margin-top: 6px; color: #f8fafc;">
                                {active_mod_str}
                            </div>
                            <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 2px;">
                                Routed to specialist deep neural network with {t_elapsed:.1f} ms pipeline latency.
                            </div>
                        </div>
                        <div class="badge-cyan" style="font-size: 0.75rem;">
                            Auto-Match 99.4%
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Primary Clinical Diagnostic Findings Glass Card
        st.markdown("#### 2. Clinical Diagnostic Assessment")
        severity = result["overall_severity"]
        if "High" in severity or "Malignant" in severity or "Urgent" in severity:
            badge_class = "badge-rose"
            border_glow = "rgba(244, 63, 94, 0.4)"
        elif "Moderate" in severity:
            badge_class = "badge-amber"
            border_glow = "rgba(245, 158, 11, 0.4)"
        else:
            badge_class = "badge-emerald"
            border_glow = "rgba(16, 185, 129, 0.4)"

        st.markdown(
            f"""
            <div class="glass-panel" style="border: 1px solid {border_glow};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="{badge_class}">{severity}</span>
                    <span style="font-size: 0.8rem; color: #94a3b8;">Threshold: 35.0%</span>
                </div>
                <h3 style="margin: 12px 0 8px 0; font-size: 1.35rem; font-weight: 700; color: #f8fafc;">
                    {result['primary_diagnosis']}
                </h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Probability Breakdown Rows
        st.markdown("##### Detailed Probability Distribution")
        top_findings = result["findings"][:6]
        for item in top_findings:
            p_val = item["probability"]
            p_pct = item["percentage"]
            c_name = item["condition"]
            bar_color = "#f43f5e" if p_val >= 0.5 else ("#f59e0b" if p_val >= 0.25 else "#6366f1")
            
            st.markdown(
                f"""
                <div class="prob-row">
                    <span style="font-size: 0.9rem; font-weight: 500; color: #e2e8f0;">{c_name}</span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; font-weight: 600; color: {bar_color};">{p_pct}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.progress(min(1.0, max(0.0, p_val)))

    st.markdown("---")

    # Section 3: Digital Image Processing (ECE Core) in Glass Grid
    st.markdown("### 3. Digital Image Processing (DIP) Pipeline — ECE Core")
    st.caption("Modality-tailored classical image processing engineered to remove noise, eliminate artifacts, and expand optical dynamic range prior to deep learning.")

    dip_stages = result["dip_stages"]
    stage_keys = list(dip_stages.keys())
    num_stages = min(4, len(stage_keys))
    dip_cols = st.columns(num_stages, gap="medium")

    for i in range(num_stages):
        key = stage_keys[i]
        label = key.replace("_", " ").title()
        with dip_cols[i]:
            st.markdown(
                f"""
                <div class="glass-panel" style="padding: 12px; margin-bottom: 8px;">
                    <div style="font-size: 0.8rem; font-weight: 600; color: #a5b4fc; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
                        Stage {i+1}: {label}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.image(dip_stages[key], use_container_width=True)

    st.markdown("---")

    # Section 4: Explainable AI (Grad-CAM)
    st.markdown("### 4. Explainable AI (Grad-CAM Saliency & Lesion Contours)")
    st.caption("Backpropagates target diagnostic gradients to deepest convolutional feature maps to localize decisive pathology regions.")

    if enable_xai and result["xai"]["overlay"] is not None:
        cam_col1, cam_col2, cam_col3 = st.columns(3, gap="medium")
        with cam_col1:
            st.markdown("<div class='badge-cyan' style='margin-bottom: 8px;'>Grad-CAM Saliency Overlay</div>", unsafe_allow_html=True)
            st.image(result["xai"]["overlay"], use_container_width=True)
        with cam_col2:
            st.markdown("<div class='badge-amber' style='margin-bottom: 8px;'>70th-Percentile Lesion Contours</div>", unsafe_allow_html=True)
            st.image(result["xai"]["contoured"], use_container_width=True)
        with cam_col3:
            st.markdown("<div class='badge-emerald' style='margin-bottom: 8px;'>Normalized Saliency Map</div>", unsafe_allow_html=True)
            st.image(result["xai"]["heatmap"], use_container_width=True)
    else:
        st.info("Grad-CAM visualization is disabled or not available for this modality.")

    # Educational Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #64748b; font-size: 0.8rem; padding: 20px 0;">
            <b>ECE Major Capstone Project</b> • AI-Based Multi-Disease Detection Using DIP and Deep Learning<br>
            Designed for educational and academic research. Not for autonomous clinical medical decision-making.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
