"""
Modular Training Script for Multi-Disease Medical AI.
Supports:
  - Modalities: Chest (ChestMNIST), Skin (DermaMNIST), Retina (RetinaMNIST)
  - Model Types: Baseline CNN vs Transfer Learning (DenseNet-121, EfficientNet-B0, ResNet-50)
  - Hardware: Automatic Apple Silicon GPU (MPS) / CUDA / CPU
  - Validation metrics: ROC-AUC, Macro F1, Quadratic Weighted Kappa (QWK)
"""

import os
import sys
import argparse
import time
from typing import Tuple, Dict, Any
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.models.baseline_cnn import MedicalBaselineCNN
from src.models.chest_model import ChestAbnormalityModel, CHEST_DISEASE_LABELS
from src.models.skin_model import SkinLesionModel, SKIN_DISEASE_LABELS
from src.models.retina_model import RetinalFundusModel, RETINA_DISEASE_LABELS
from src.evaluation.metrics import MedicalEvaluator


def get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def load_dataset_tensors(data_dir: str, modality: str, subset_size: int = -1) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """
    Loads train, val, and test arrays from local .npz files.
    """
    filename_map = {
        "chest": "chestmnist.npz",
        "skin": "dermamnist.npz",
        "retina": "retinamnist.npz",
    }
    npz_path = os.path.join(data_dir, filename_map[modality])
    if not os.path.exists(npz_path):
        raise FileNotFoundError(f"Dataset archive not found: {npz_path}. Run download_datasets.py first.")

    data = np.load(npz_path)
    train_x, train_y = data["train_images"], data["train_labels"]
    val_x, val_y = data["val_images"], data["val_labels"]
    test_x, test_y = data["test_images"], data["test_labels"]

    if subset_size > 0 and subset_size < len(train_x):
        print(f"[*] Prototyping mode: Subsetting training set to {subset_size} samples.")
        train_x, train_y = train_x[:subset_size], train_y[:subset_size]
        val_sub = max(100, int(subset_size * 0.15))
        val_x, val_y = val_x[:val_sub], val_y[:val_sub]

    # Preprocessing to PyTorch float tensors: (N, H, W, C) -> (N, C, H, W) normalized to [0, 1]
    def prepare_tensor(arr: np.ndarray) -> torch.Tensor:
        if len(arr.shape) == 3:  # Grayscale (N, H, W)
            arr = np.repeat(arr[:, np.newaxis, :, :], 3, axis=1)
        elif len(arr.shape) == 4 and arr.shape[-1] in [1, 3]:  # (N, H, W, C)
            if arr.shape[-1] == 1:
                arr = np.repeat(arr, 3, axis=-1)
            arr = np.transpose(arr, (0, 3, 1, 2))
        return torch.from_numpy(arr).float() / 255.0

    tx, vx, tex = prepare_tensor(train_x), prepare_tensor(val_x), prepare_tensor(test_x)
    ty, vy, tey = torch.from_numpy(train_y).float(), torch.from_numpy(val_y).float(), torch.from_numpy(test_y).float()

    train_loader = DataLoader(TensorDataset(tx, ty), batch_size=32, shuffle=True)
    val_loader = DataLoader(TensorDataset(vx, vy), batch_size=32, shuffle=False)
    test_loader = DataLoader(TensorDataset(tex, tey), batch_size=32, shuffle=False)

    return train_loader, val_loader, test_loader


def get_model(modality: str, model_type: str) -> nn.Module:
    use_tl = (model_type == "transfer")
    if modality == "chest":
        return ChestAbnormalityModel(use_transfer_learning=use_tl, num_classes=14)
    elif modality == "skin":
        return SkinLesionModel(use_transfer_learning=use_tl, num_classes=7)
    elif modality == "retina":
        return RetinalFundusModel(use_transfer_learning=use_tl, num_classes=5)
    else:
        raise ValueError(f"Unknown modality: {modality}")


def train_model(
    modality: str = "chest",
    model_type: str = "transfer",
    epochs: int = 5,
    lr: float = 1e-4,
    subset_size: int = -1,
    data_dir: str = "./data",
    weights_dir: str = "./weights",
    results_dir: str = "./results",
):
    os.makedirs(weights_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    device = get_device()
    print("=" * 65)
    print(f"TRAINING PIPELINE — ECE MAJOR PROJECT")
    print(f"Modality: {modality.upper()} | Architecture: {model_type.upper()}")
    print(f"Device: {device} | Epochs: {epochs} | LR: {lr}")
    print("=" * 65)

    train_loader, val_loader, test_loader = load_dataset_tensors(data_dir, modality, subset_size)
    print(f"Batches: Train={len(train_loader)} | Val={len(val_loader)} | Test={len(test_loader)}")

    model = get_model(modality, model_type).to(device)

    # Loss criterion
    if modality == "chest":
        criterion = nn.BCEWithLogitsLoss()
    else:
        criterion = nn.CrossEntropyLoss()

    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    history = {"train_loss": [], "val_loss": [], "val_metric": []}
    best_val_score = -1.0
    best_model_path = os.path.join(weights_dir, f"{modality}_{model_type}_best.pth")

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        model.train()
        train_loss = 0.0

        for images, targets in train_loader:
            images = images.to(device)
            targets = targets.to(device)

            if modality != "chest":
                targets = targets.squeeze().long()

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * images.size(0)

        train_loss /= len(train_loader.dataset)
        scheduler.step()

        # Validation
        model.eval()
        val_loss = 0.0
        all_preds, all_targets = [], []

        with torch.no_grad():
            for images, targets in val_loader:
                images = images.to(device)
                targets = targets.to(device)

                if modality != "chest":
                    targets = targets.squeeze().long()

                outputs = model(images)
                loss = criterion(outputs, targets)
                val_loss += loss.item() * images.size(0)

                if modality == "chest":
                    probs = torch.sigmoid(outputs)
                else:
                    probs = torch.softmax(outputs, dim=-1)

                all_preds.append(probs.cpu().numpy())
                all_targets.append(targets.cpu().numpy())

        val_loss /= len(val_loader.dataset)
        all_preds = np.vstack(all_preds)
        all_targets = np.vstack(all_targets) if modality == "chest" else np.concatenate(all_targets)

        # Compute clinical validation metric
        if modality == "chest":
            eval_res = MedicalEvaluator.evaluate_multi_label(all_targets, all_preds, CHEST_DISEASE_LABELS)
            metric_val = eval_res["mean_macro_auc"]
            metric_name = "Macro AUC"
        elif modality == "skin":
            eval_res = MedicalEvaluator.evaluate_multi_class(all_targets, all_preds, SKIN_DISEASE_LABELS)
            metric_val = eval_res["accuracy"]
            metric_name = "Accuracy"
        elif modality == "retina":
            eval_res = MedicalEvaluator.evaluate_ordinal(all_targets, all_preds, RETINA_DISEASE_LABELS)
            metric_val = eval_res["quadratic_weighted_kappa"]
            metric_name = "QWK"

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["val_metric"].append(metric_val)

        epoch_time = time.time() - t0
        print(f"Epoch [{epoch:02d}/{epochs:02d}] ({epoch_time:.1f}s) — Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | {metric_name}: {metric_val:.4f}")

        if metric_val > best_val_score:
            best_val_score = metric_val
            torch.save(model.state_dict(), best_model_path)
            print(f"  ⭐ Checkpoint saved! Best {metric_name}: {metric_val:.4f} -> {best_model_path}")

    # Plot learning curves
    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    plt.plot(range(1, epochs + 1), history["train_loss"], label="Train Loss", marker="o")
    plt.plot(range(1, epochs + 1), history["val_loss"], label="Val Loss", marker="s")
    plt.title(f"{modality.upper()} — Loss Curve")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(range(1, epochs + 1), history["val_metric"], label=metric_name, color="green", marker="^")
    plt.title(f"{modality.upper()} — Validation {metric_name}")
    plt.xlabel("Epoch")
    plt.ylabel(metric_name)
    plt.legend()
    plt.grid(True)

    curve_path = os.path.join(results_dir, f"{modality}_{model_type}_learning_curves.png")
    plt.tight_layout()
    plt.savefig(curve_path, dpi=150)
    plt.close()
    print(f"\n✓ Training completed! Learning curves saved to: {curve_path}")

    return history, best_val_score


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Disease Model Training")
    parser.add_argument("--modality", type=str, default="chest", choices=["chest", "skin", "retina"], help="Medical modality")
    parser.add_argument("--model", type=str, default="transfer", choices=["baseline", "transfer"], help="Model architecture")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--subset", type=int, default=-1, help="Subset size for fast prototyping (-1 for all)")
    parser.add_argument("--data", type=str, default="./data", help="Data directory")
    args = parser.parse_args()

    train_model(
        modality=args.modality,
        model_type=args.model,
        epochs=args.epochs,
        lr=args.lr,
        subset_size=args.subset,
        data_dir=args.data,
    )
