# AI-Based Multi-Disease Detection from Medical Images Using Digital Image Processing and Deep Learning

[![ECE Major Project](https://img.shields.io/badge/ECE%20Project-Major%20Capstone-blue.svg)](https://github.com/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C.svg)](https://pytorch.org/)
[![MedMNIST v2+](https://img.shields.io/badge/MedMNIST-224x224-orange.svg)](https://medmnist.com/)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B.svg)](https://streamlit.io/)

---

## 📌 Executive Summary

This repository hosts an end-to-end framework for **AI-based multi-disease detection from medical imagery**, engineered specifically as an **Electronics & Communication Engineering (ECE) Major Project**. 

Rather than relying on a naive "one-size-fits-all" convolutional network, this project implements a **modular, specialist architecture**:
1. **Intelligent Modality Router**: Automatically identifies incoming image types (Chest Radiograph vs. Skin Dermoscopy vs. Retinal Fundus) using spectral heuristics and convolutional classification, preventing dangerous cross-modality diagnostic errors.
2. **Modality-Specific Digital Image Processing (DIP)**: Tailored ECE image processing pipelines applied prior to neural network inference to eliminate acquisition artifacts, suppress speckle noise, and expand diagnostic dynamic ranges.
3. **Dual-Model Comparative Benchmark**: Directly compares a **Custom 4-Stage CNN Baseline** against **State-of-the-Art (SOTA) Transfer Learning architectures** (DenseNet-121, EfficientNet-B0, ResNet-50).
4. **Explainable AI (XAI)**: High-resolution **Grad-CAM** saliency maps with automated 70th-percentile lesion contouring for clinical interpretability.
5. **Interactive Streamlit Web Dashboard**: Clinical decision support portal featuring side-by-side DIP step visualizers, probability breakdowns, and Grad-CAM opacity overlays.
6. **Edge Hardware Feasibility**: Model quantization (ONNX / INT8) and CPU latency benchmarks for low-power edge deployment (Raspberry Pi 4/5, Jetson Nano).

---

## 🏥 Modality & Model Matrix

| Modality | Primary Dataset (MedMNIST+) | Clinical Task | Specialized DIP Pipeline | Baseline Model | SOTA Transfer Learning | Metrics |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **🫁 Chest** | **ChestMNIST** ($224 \times 224$, 112,120 imgs) | Multi-Label Detection (14 Thoracic Pathologies) | Bilateral Edge-Preserving Denoising + CLAHE ($8\times8$, clip=2.0) | 4-Stage Custom CNN | **DenseNet-121** (CheXNet Backbone) | Multi-label BCE, Per-class ROC-AUC, Micro/Macro F1 |
| **🩺 Skin** | **DermaMNIST** ($224 \times 224$, 10,015 imgs) | Multi-Class Diagnosis (7 Lesion Types) | DullRazor (Black top-hat + Telea inpaint) + Shades-of-Gray | 4-Stage Custom CNN | **EfficientNet-B0** | Categorical Cross-Entropy, Sensitivity, Specificity |
| **👁️ Retina** | **RetinaMNIST** ($224 \times 224$, 1,600 imgs) | Ordinal Severity Grading (5 DR Stages) | Ben Graham circular crop + Local color subtraction + Green CLAHE | 4-Stage Custom CNN | **ResNet-50** | Quadratic Weighted Kappa (QWK), Multi-class AUC |

---

## ⚙️ Digital Image Processing (ECE Core Formulations)

### 1. Chest Radiography: Bilateral Denoising & CLAHE
$$I_{\text{bilateral}}(x) = \frac{1}{W_p} \sum_{x_i \in \Omega} I(x_i) f_r(\|I(x_i) - I(x)\|) g_s(\|x_i - x\|)$$
- Preserves fine pleural and vascular lung markings while attenuating quantum mottle noise.
- Contextual adaptive histogram equalization distributes dynamic range evenly across high-density mediastinal and low-density pulmonary parenchyma.

### 2. Dermoscopy: DullRazor Hair Removal & Color Constancy
- **Hair Detection via Black Top-Hat**: $T_{\text{black}}(I) = (I \bullet B) - I$
- **Inpainting**: Fast-marching Telea algorithm replaces occluding hair pixels with neighbor pigment statistics.
- **Shades-of-Gray Color Constancy**:
  $$e_c = \left( \frac{1}{N} \sum_{x} (I_c(x))^p \right)^{1/p} \quad (p=6)$$
  Normalizes chromatic temperature differences across diverse dermatoscopic illuminants.

### 3. Retinal Fundus: Ben Graham's Illumination Equalization
$$I_{\text{out}}(x, y) = 4 \cdot I(x, y) - 4 \cdot \mathcal{G}_{\sigma=10}(I(x, y)) + 128$$
- Eliminates severe central flash illumination gradients and edge vignetting.
- Green channel ($\lambda \approx 540-575\text{ nm}$) optical extraction maximizes hemoglobin absorption contrast for microaneurysms and hemorrhages.

---

## 📁 Repository Structure

```text
Multi_Disease_Medical_AI/
├── app/
│   └── streamlit_app.py              # Interactive Clinical Web Dashboard
├── data/
│   ├── download_datasets.py          # MedMNIST 224x224 automated downloader
│   ├── verify_integrity.py           # Integrity checker & sample generator
│   └── samples/                      # Sample clinical images for testing
├── hardware/
│   ├── export_onnx.py                # PyTorch to ONNX / INT8 quantization
│   └── edge_benchmark.py             # Latency, parameter count, and FPS benchmark
├── notebooks/
│   ├── 01_data_exploration_and_dip.ipynb   # Colab notebook: Data verification & DIP
│   └── 02_model_training_chest.ipynb       # Colab notebook: DenseNet-121 training & XAI
├── src/
│   ├── dip/                          # Digital Image Processing modules
│   │   ├── base.py                   # BasePreprocessor class
│   │   ├── chest_dip.py              # Bilateral + CLAHE
│   │   ├── skin_dip.py               # DullRazor + Shades-of-Gray
│   │   └── retina_dip.py             # Ben Graham + Green CLAHE
│   ├── models/                       # Deep Learning models
│   │   ├── baseline_cnn.py           # 4-stage Custom CNN baseline
│   │   ├── chest_model.py            # DenseNet-121 multi-label model
│   │   ├── skin_model.py             # EfficientNet-B0 multi-class model
│   │   └── retina_model.py           # ResNet-50 ordinal model
│   ├── router/                       # Modality router
│   │   └── modality_classifier.py    # Zero-shot heuristic & neural routing
│   ├── xai/                          # Explainable AI
│   │   └── gradcam.py                # Grad-CAM heatmap & contouring
│   ├── pipeline/                     # Unified orchestrator
│   │   └── multi_disease_system.py   # MultiDiseaseDiagnosticSystem engine
│   └── evaluation/                   # Clinical evaluation metrics
│       └── metrics.py                # ROC-AUC, QWK, Sensitivity, Specificity
├── tests/                            # Automated test suite
│   ├── test_dip.py
│   ├── test_models.py
│   └── test_pipeline.py
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start Guide

### Step 1: Clone and Set Up Environment
```bash
git clone <your-repo-url>
cd Multi_Disease_Medical_AI

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Generate Sample Data & Verify
```bash
python3 data/verify_integrity.py
```

### Step 3: Run Edge Hardware Benchmark
```bash
python3 hardware/edge_benchmark.py
```

### Step 4: Launch Interactive Clinical Dashboard
```bash
streamlit run app/streamlit_app.py
```

---

## ☁️ Google Colab Training Workflow

For training without local GPUs:
1. Open [Google Colab](https://colab.research.google.com/).
2. Select **Runtime -> Change runtime type -> T4 GPU**.
3. Upload `notebooks/01_data_exploration_and_dip.ipynb` and run the cells to download the $224 \times 224$ datasets and visualize the DIP transformations.
4. Upload `notebooks/02_model_training_chest.ipynb` to train the DenseNet-121 model and generate Grad-CAM heatmaps.
5. Download trained weights (`.pth`) to use inside the local Streamlit dashboard!
