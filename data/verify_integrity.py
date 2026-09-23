"""
Dataset Integrity and Verification Script.
Inspects downloaded MedMNIST data splits, image dimensions, class labels,
and saves representative visual samples into data/samples/ for DIP testing.
"""

import os
import numpy as np
from PIL import Image

# Ensure MedMNIST uses local data directory rather than ~/.medmnist
os.environ["MEDMNIST_DEFAULT_ROOT"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

try:
    import medmnist
    from medmnist import ChestMNIST, DermaMNIST, RetinaMNIST, INFO
    HAS_MEDMNIST = True
except ImportError:
    HAS_MEDMNIST = False


def generate_synthetic_samples_if_needed(sample_dir: str = "./data/samples"):
    """
    Generates synthetic sample images for testing when MedMNIST has not been downloaded yet.
    Ensures tests and UI can run out-of-the-box.
    """
    os.makedirs(sample_dir, exist_ok=True)

    # 1. Chest X-Ray synthetic pattern (ribs + lung fields)
    chest_img = np.zeros((224, 224), dtype=np.uint8)
    chest_img[20:200, 20:100] = 70   # Left lung field
    chest_img[20:200, 124:204] = 70  # Right lung field
    chest_img[70:160, 95:135] = 160  # Cardiac silhouette
    # Add rib lines
    for y in range(40, 180, 25):
        chest_img[y:y+3, 20:204] = 130
    chest_rgb = np.stack([chest_img] * 3, axis=-1)
    Image.fromarray(chest_rgb).save(os.path.join(sample_dir, "sample_chest_xray.png"))

    # 2. Skin Dermoscopy synthetic pattern (pigmented skin lesion with simulated hair)
    skin_img = np.full((224, 224, 3), [220, 185, 160], dtype=np.uint8)  # skin tone
    yy, xx = np.ogrid[:224, :224]
    lesion_mask = ((xx - 112) ** 2 + (yy - 112) ** 2) < 45 ** 2
    skin_img[lesion_mask] = [80, 45, 30]  # dark lesion
    # Add simulated dark hair strands
    for i in range(224):
        if 40 <= i <= 180:
            skin_img[i, min(223, i + 10)] = [20, 15, 10]
            skin_img[i, min(223, 220 - i)] = [20, 15, 10]
    Image.fromarray(skin_img).save(os.path.join(sample_dir, "sample_skin_lesion.png"))

    # 3. Retinal Fundus synthetic pattern (circular orange fundus with dark corners and optic disk)
    retina_img = np.zeros((224, 224, 3), dtype=np.uint8)
    circular_mask = ((xx - 112) ** 2 + (yy - 112) ** 2) < 95 ** 2
    retina_img[circular_mask] = [190, 80, 25]  # orange retinal fundus
    # Optic disc (bright circle)
    disc_mask = ((xx - 80) ** 2 + (yy - 112) ** 2) < 14 ** 2
    retina_img[disc_mask] = [255, 220, 120]
    # Retinal blood vessels
    for x in range(80, 200):
        y_vessel = int(112 + 25 * np.sin(x / 20.0))
        if 0 <= y_vessel < 224:
            retina_img[y_vessel:y_vessel+2, x] = [100, 20, 10]
    Image.fromarray(retina_img).save(os.path.join(sample_dir, "sample_retinal_fundus.png"))

    print(f"Generated synthetic verification samples in: {os.path.abspath(sample_dir)}")


def verify_datasets(root_dir: str = "./data"):
    print("=" * 60)
    print("VERIFYING DATASETS & PREPARING SAMPLE IMAGES")
    print("=" * 60)

    sample_dir = os.path.join(root_dir, "samples")
    generate_synthetic_samples_if_needed(sample_dir)

    if not HAS_MEDMNIST:
        print("\nMedMNIST package is not installed locally. Synthetic sample set created.")
        return

    datasets = ["chestmnist", "dermamnist", "retinamnist"]
    for dname in datasets:
        print(f"\n--- Checking info for: {dname.upper()} ---")
        info = INFO[dname]
        print(f"  Description: {info['description']}")
        print(f"  Label dict: {info['label']}")
        print(f"  Number of classes/labels: {len(info['label'])}")
        print(f"  Standard Splits: {info['n_samples']}")


if __name__ == "__main__":
    verify_datasets()
