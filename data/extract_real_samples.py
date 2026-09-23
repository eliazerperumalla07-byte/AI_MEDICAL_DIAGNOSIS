"""
Extract Real Clinical Samples from MedMNIST .npz files into data/samples/
for testing and Streamlit dashboard visual verification.
"""

import os
import numpy as np
from PIL import Image

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SAMPLES_DIR = os.path.join(DATA_DIR, "samples")

CHEST_LABELS = [
    "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration", "Mass",
    "Nodule", "Pneumonia", "Pneumothorax", "Consolidation", "Edema",
    "Emphysema", "Fibrosis", "Pleural_Thickening", "Hernia"
]

SKIN_LABELS = [
    "Actinic keratoses (akiec)",
    "Basal cell carcinoma (bcc)",
    "Benign keratosis-like lesions (bkl)",
    "Dermatofibroma (df)",
    "Melanoma (mel)",
    "Melanocytic nevi (nv)",
    "Vascular lesions (vasc)",
]

RETINA_LABELS = [
    "Grade 0: Normal",
    "Grade 1: Mild NPDR",
    "Grade 2: Moderate NPDR",
    "Grade 3: Severe NPDR",
    "Grade 4: Proliferative DR",
]


def extract_samples():
    os.makedirs(SAMPLES_DIR, exist_ok=True)
    print("=" * 60)
    print("EXTRACTING REAL CLINICAL SAMPLES FROM DATASETS")
    print("=" * 60)

    # 1. ChestMNIST
    chest_npz = os.path.join(DATA_DIR, "chestmnist.npz")
    if os.path.exists(chest_npz):
        data = np.load(chest_npz)
        images = data["train_images"]
        labels = data["train_labels"]

        # Find an image that has abnormalities
        positive_indices = [i for i, l in enumerate(labels) if np.sum(l) >= 2]
        idx = positive_indices[0] if positive_indices else 0

        img = images[idx]
        active_conditions = [CHEST_LABELS[i] for i, val in enumerate(labels[idx]) if val == 1]
        print(f"[+] Extracted Chest X-Ray #{idx}: Conditions = {active_conditions or ['Normal']}")

        # Resize to 224x224 for DIP and inference
        pil_img = Image.fromarray(img).resize((224, 224), Image.Resampling.LANCZOS)
        pil_img.save(os.path.join(SAMPLES_DIR, "real_chest_xray.png"))
        # Also update default sample
        pil_img.save(os.path.join(SAMPLES_DIR, "sample_chest_xray.png"))

    # 2. DermaMNIST
    derma_npz = os.path.join(DATA_DIR, "dermamnist.npz")
    if os.path.exists(derma_npz):
        data = np.load(derma_npz)
        images = data["train_images"]
        labels = data["train_labels"]

        # Find Melanoma (class 4) or Basal Cell Carcinoma (class 1)
        mel_indices = [i for i, l in enumerate(labels) if l[0] == 4]
        idx = mel_indices[0] if mel_indices else 0

        img = images[idx]
        label_name = SKIN_LABELS[int(labels[idx][0])]
        print(f"[+] Extracted Skin Lesion #{idx}: Category = {label_name}")

        pil_img = Image.fromarray(img).resize((224, 224), Image.Resampling.LANCZOS)
        pil_img.save(os.path.join(SAMPLES_DIR, "real_skin_lesion.png"))
        pil_img.save(os.path.join(SAMPLES_DIR, "sample_skin_lesion.png"))

    # 3. RetinaMNIST
    retina_npz = os.path.join(DATA_DIR, "retinamnist.npz")
    if os.path.exists(retina_npz):
        data = np.load(retina_npz)
        images = data["train_images"]
        labels = data["train_labels"]

        # Find Moderate/Severe DR (grade 2 or 3)
        dr_indices = [i for i, l in enumerate(labels) if l[0] >= 2]
        idx = dr_indices[0] if dr_indices else 0

        img = images[idx]
        grade_name = RETINA_LABELS[int(labels[idx][0])]
        print(f"[+] Extracted Retinal Fundus #{idx}: Severity = {grade_name}")

        pil_img = Image.fromarray(img).resize((224, 224), Image.Resampling.LANCZOS)
        pil_img.save(os.path.join(SAMPLES_DIR, "real_retinal_fundus.png"))
        pil_img.save(os.path.join(SAMPLES_DIR, "sample_retinal_fundus.png"))

    print("\n✓ Successfully extracted real clinical images into:")
    print(f"  {SAMPLES_DIR}")


if __name__ == "__main__":
    extract_samples()
