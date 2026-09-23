"""
Automated Downloader for MedMNIST v2+ Multi-Disease Datasets.
Downloads ChestMNIST (X-Ray), DermaMNIST (Skin), and RetinaMNIST (Retina) at 224x224.
"""

import os
import argparse
from typing import List, Dict

# Set local directory for MedMNIST downloads
os.environ["MEDMNIST_DEFAULT_ROOT"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

try:
    import medmnist
    from medmnist import ChestMNIST, DermaMNIST, RetinaMNIST, INFO
    HAS_MEDMNIST = True
except ImportError:
    HAS_MEDMNIST = False


DATASETS_CONFIG = {
    "chestmnist": {
        "class": "ChestMNIST",
        "description": "Chest X-Ray Multi-Label Thoracic Pathologies (14 labels)",
        "task": "multi-label, binary-class",
    },
    "dermamnist": {
        "class": "DermaMNIST",
        "description": "Dermoscopic Skin Lesion Multi-Class Diagnosis (7 classes)",
        "task": "multi-class",
    },
    "retinamnist": {
        "class": "RetinaMNIST",
        "description": "Retinal Fundus Diabetic Retinopathy Grading (5 ordinal classes)",
        "task": "ordinal-regression / multi-class",
    },
}


def download_all_datasets(size: int = 224, root_dir: str = "./data"):
    """
    Downloads train, val, and test splits for the three target datasets.
    """
    if not HAS_MEDMNIST:
        print("Error: medmnist library is not installed. Run 'pip install medmnist' first.")
        return

    os.makedirs(root_dir, exist_ok=True)
    print(f"==================================================")
    print(f"Downloading MedMNIST Datasets at resolution: {size}x{size}")
    print(f"Storage Directory: {os.path.abspath(root_dir)}")
    print(f"==================================================")

    dataset_map = {
        "chestmnist": ChestMNIST,
        "dermamnist": DermaMNIST,
        "retinamnist": RetinaMNIST,
    }

    results = {}
    for flag, dataset_cls in dataset_map.items():
        print(f"\n[+] Fetching {flag.upper()} ({DATASETS_CONFIG[flag]['description']})...")
        try:
            train_data = dataset_cls(split="train", download=True, size=size, root=root_dir)
            val_data = dataset_cls(split="val", download=True, size=size, root=root_dir)
            test_data = dataset_cls(split="test", download=True, size=size, root=root_dir)

            results[flag] = {
                "train_samples": len(train_data),
                "val_samples": len(val_data),
                "test_samples": len(test_data),
                "total_samples": len(train_data) + len(val_data) + len(test_data),
                "image_shape": train_data[0][0].size if hasattr(train_data[0][0], "size") else "224x224",
            }
            print(f"    ✓ Train: {len(train_data)} | Val: {len(val_data)} | Test: {len(test_data)}")
        except Exception as e:
            print(f"    ✗ Failed to download {flag}: {e}")
            results[flag] = {"error": str(e)}

    print("\nDownload Summary:")
    for k, v in results.items():
        print(f" - {k}: {v}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MedMNIST Dataset Downloader")
    parser.add_argument("--size", type=int, default=224, choices=[28, 64, 128, 224], help="Image resolution")
    parser.add_argument("--dir", type=str, default="./data", help="Output directory")
    args = parser.parse_args()
    download_all_datasets(size=args.size, root_dir=args.dir)
