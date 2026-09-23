import os
import sys
import time
import argparse
from typing import Dict, Any
import numpy as np
import torch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.models.baseline_cnn import MedicalBaselineCNN
from src.models.chest_model import ChestAbnormalityModel
from src.models.skin_model import SkinLesionModel
from src.models.retina_model import RetinalFundusModel


def count_parameters(model: torch.nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def benchmark_model_latency(
    model: torch.nn.Module,
    input_shape: tuple = (1, 3, 224, 224),
    num_warmup: int = 5,
    num_runs: int = 20,
) -> Dict[str, Any]:
    """
    Measures CPU latency in milliseconds and parameters.
    """
    model.eval()
    device = torch.device("cpu")
    model.to(device)

    dummy_input = torch.randn(*input_shape, device=device)

    # Warmup
    with torch.no_grad():
        for _ in range(num_warmup):
            _ = model(dummy_input)

    # Timing
    latencies = []
    with torch.no_grad():
        for _ in range(num_runs):
            t0 = time.perf_counter()
            _ = model(dummy_input)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)  # ms

    params = count_parameters(model)
    mean_lat = float(np.mean(latencies))
    std_lat = float(np.std(latencies))
    fps = 1000.0 / mean_lat if mean_lat > 0 else 0.0

    return {
        "parameters": params,
        "params_millions": round(params / 1e6, 3),
        "mean_latency_ms": round(mean_lat, 2),
        "std_latency_ms": round(std_lat, 2),
        "throughput_fps": round(fps, 1),
    }


def run_benchmark():
    print("=" * 70)
    print("ECE EDGE HARDWARE FEASIBILITY BENCHMARK (CPU RUNTIME)")
    print("=" * 70)

    models_to_test = {
        "Custom Baseline CNN": MedicalBaselineCNN(num_classes=14),
        "Chest Model (Baseline)": ChestAbnormalityModel(use_transfer_learning=False),
        "Skin Model (Baseline)": SkinLesionModel(use_transfer_learning=False),
        "Retina Model (Baseline)": RetinalFundusModel(use_transfer_learning=False),
    }

    print(f"{'Model Architecture':<30} | {'Params (M)':<10} | {'Latency (ms)':<14} | {'Throughput (FPS)':<16}")
    print("-" * 75)

    for name, model in models_to_test.items():
        res = benchmark_model_latency(model)
        print(f"{name:<30} | {res['params_millions']:<10} | {res['mean_latency_ms']:<6} ± {res['std_latency_ms']:<4} | {res['throughput_fps']:<16}")

    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
