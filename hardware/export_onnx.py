import os
import sys
import argparse
from typing import Dict
import torch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.models.baseline_cnn import MedicalBaselineCNN
from src.models.chest_model import ChestAbnormalityModel
from src.models.skin_model import SkinLesionModel
from src.models.retina_model import RetinalFundusModel


def export_model_to_onnx(
    model: torch.nn.Module,
    output_path: str,
    input_shape: tuple = (1, 3, 224, 224),
    opset_version: int = 14,
):
    """
    Exports a PyTorch model to ONNX format with graph optimization.
    """
    model.eval()
    dummy_input = torch.randn(*input_shape)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Exporting model to ONNX: {output_path}...")
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=opset_version,
        do_constant_folding=True,
        input_names=["medical_image_input"],
        output_names=["disease_logits"],
        dynamic_axes={"medical_image_input": {0: "batch_size"}, "disease_logits": {0: "batch_size"}},
    )

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✓ Successfully exported ONNX model ({size_mb:.2f} MB)")


def export_all_models(output_dir: str = "./hardware/exported_models"):
    """
    Exports all three specialist disease models and baseline model to ONNX.
    """
    models = {
        "chest_model": ChestAbnormalityModel(use_transfer_learning=False),
        "skin_model": SkinLesionModel(use_transfer_learning=False),
        "retina_model": RetinalFundusModel(use_transfer_learning=False),
        "baseline_cnn": MedicalBaselineCNN(num_classes=14),
    }

    for name, model in models.items():
        out_path = os.path.join(output_dir, f"{name}.onnx")
        try:
            export_model_to_onnx(model, out_path)
        except Exception as e:
            print(f"✗ Failed to export {name}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export models to ONNX")
    parser.add_argument("--out", type=str, default="./hardware/exported_models", help="Export directory")
    args = parser.parse_args()
    export_all_models(args.out)
