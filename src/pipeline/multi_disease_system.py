"""
Integrated Multi-Disease Medical AI System Pipeline.
Orchestrates:
  Image Input -> Modality Router -> Specialized DIP -> Deep Learning Model -> Grad-CAM -> Diagnostic Report
"""

import os
from typing import Dict, Any, Optional, Union
import numpy as np
import torch
from PIL import Image

from ..dip.chest_dip import ChestXRayPreprocessor
from ..dip.skin_dip import SkinLesionPreprocessor
from ..dip.retina_dip import RetinalFundusPreprocessor
from ..models.chest_model import ChestAbnormalityModel, CHEST_DISEASE_LABELS
from ..models.skin_model import SkinLesionModel, SKIN_DISEASE_LABELS
from ..models.retina_model import RetinalFundusModel, RETINA_DISEASE_LABELS
from ..router.modality_classifier import ModalityRouter, MedicalModality
from ..xai.gradcam import GradCAM


class MultiDiseaseDiagnosticSystem:
    """
    Central orchestration engine for AI-based multi-disease medical image diagnosis.
    """

    def __init__(self, device: Optional[torch.device] = None, use_transfer_learning: bool = True):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.use_transfer_learning = use_transfer_learning

        # 1. Initialize DIP preprocessors
        self.preprocessors = {
            MedicalModality.CHEST: ChestXRayPreprocessor(),
            MedicalModality.SKIN: SkinLesionPreprocessor(),
            MedicalModality.RETINA: RetinalFundusPreprocessor(),
        }

        # 2. Initialize Modality Router
        self.router = ModalityRouter()

        # 3. Initialize Disease Specialist Models
        self.models = {
            MedicalModality.CHEST: ChestAbnormalityModel(use_transfer_learning=use_transfer_learning).to(self.device),
            MedicalModality.SKIN: SkinLesionModel(use_transfer_learning=use_transfer_learning).to(self.device),
            MedicalModality.RETINA: RetinalFundusModel(use_transfer_learning=use_transfer_learning).to(self.device),
        }

        # Load trained weights if available
        weights_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "weights"))
        prefix = "transfer" if use_transfer_learning else "baseline"
        weight_files = {
            MedicalModality.CHEST: f"chest_{prefix}_best.pth",
            MedicalModality.SKIN: f"skin_{prefix}_best.pth",
            MedicalModality.RETINA: f"retina_{prefix}_best.pth",
        }
        for mod, wfile in weight_files.items():
            wpath = os.path.join(weights_dir, wfile)
            if os.path.exists(wpath):
                try:
                    self.models[mod].load_state_dict(torch.load(wpath, map_location=self.device))
                except Exception:
                    pass

        # Set evaluation mode
        for model in self.models.values():
            model.eval()

    def load_image(self, image_source: Union[str, np.ndarray, Image.Image]) -> np.ndarray:
        """Converts file path, PIL image, or array into uint8 RGB numpy array."""
        if isinstance(image_source, str):
            pil_img = Image.open(image_source).convert("RGB")
            return np.array(pil_img, dtype=np.uint8)
        elif isinstance(image_source, Image.Image):
            return np.array(image_source.convert("RGB"), dtype=np.uint8)
        elif isinstance(image_source, np.ndarray):
            if image_source.dtype != np.uint8:
                return (image_source * 255).clip(0, 255).astype(np.uint8)
            return image_source
        else:
            raise ValueError(f"Unsupported image type: {type(image_source)}")

    def diagnose(
        self,
        image_input: Union[str, np.ndarray, Image.Image],
        user_selected_modality: Optional[Union[MedicalModality, str]] = None,
        generate_xai: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes complete diagnostic pipeline:
        1. Routes / validates image modality.
        2. Applies modality-specific DIP.
        3. Runs inference through specialist neural model.
        4. Calculates Grad-CAM explainability heatmaps.
        5. Compiles formatted clinical summary.
        """
        raw_img = self.load_image(image_input)

        # Step 1: Modality Routing & Validation
        detected_modality, router_confidences = self.router.route_by_heuristics(raw_img)

        # If user explicitly specified modality, verify against detected modality
        if user_selected_modality is not None:
            if isinstance(user_selected_modality, str):
                modality_key = MedicalModality(user_selected_modality)
            else:
                modality_key = user_selected_modality
            is_mismatch = (modality_key != detected_modality)
        else:
            modality_key = detected_modality
            is_mismatch = False

        active_modality = modality_key

        # Step 2: Specialized Digital Image Processing (DIP)
        preprocessor = self.preprocessors[active_modality]
        processed_normalized, dip_stages = preprocessor.preprocess(raw_img)

        # Convert to PyTorch Tensor: (H, W, C) -> (1, C, H, W)
        tensor_input = torch.from_numpy(processed_normalized).permute(2, 0, 1).unsqueeze(0).float().to(self.device)

        # Step 3: Deep Learning Model Inference
        model = self.models[active_modality]
        probabilities = model.predict_probabilities(tensor_input).squeeze().cpu().numpy()

        # Step 4: Format modality-specific diagnosis
        diagnostic_findings = []
        primary_diagnosis = ""
        overall_severity = "Low"

        if active_modality == MedicalModality.CHEST:
            # Multi-label analysis (14 abnormalities)
            # Find findings above threshold (e.g. 0.35)
            labels = CHEST_DISEASE_LABELS
            findings = []
            for idx, (label, prob) in enumerate(zip(labels, probabilities)):
                findings.append({
                    "condition": label,
                    "probability": float(prob),
                    "percentage": f"{prob * 100:.1f}%",
                    "flagged": bool(prob >= 0.35),
                })
            # Sort by probability descending
            findings.sort(key=lambda x: x["probability"], reverse=True)
            diagnostic_findings = findings
            flagged_conditions = [f["condition"] for f in findings if f["flagged"]]
            if flagged_conditions:
                primary_diagnosis = f"Detected Suspicions: {', '.join(flagged_conditions[:3])}"
                overall_severity = "Moderate" if len(flagged_conditions) <= 2 else "High Suspicion"
            else:
                primary_diagnosis = "No significant acute thoracic abnormality identified (>35% threshold)"
                overall_severity = "Normal / Low Risk"

            target_xai_class = int(np.argmax(probabilities))

        elif active_modality == MedicalModality.SKIN:
            # Multi-class analysis (7 lesion types)
            labels = SKIN_DISEASE_LABELS
            findings = []
            for label, prob in zip(labels, probabilities):
                findings.append({
                    "condition": label,
                    "probability": float(prob),
                    "percentage": f"{prob * 100:.1f}%",
                })
            findings.sort(key=lambda x: x["probability"], reverse=True)
            diagnostic_findings = findings
            top = findings[0]
            primary_diagnosis = f"{top['condition']} ({top['percentage']})"
            target_xai_class = int(np.argmax(probabilities))
            if "Melanoma" in top["condition"] or "Basal" in top["condition"]:
                overall_severity = "High Suspicion (Malignant Potential)"
            else:
                overall_severity = "Moderate" if top["probability"] < 0.7 else "Benign Pattern Likely"

        elif active_modality == MedicalModality.RETINA:
            # Ordinal Diabetic Retinopathy analysis (5 grades)
            labels = RETINA_DISEASE_LABELS
            findings = []
            for label, prob in zip(labels, probabilities):
                findings.append({
                    "condition": label,
                    "probability": float(prob),
                    "percentage": f"{prob * 100:.1f}%",
                })
            findings.sort(key=lambda x: x["probability"], reverse=True)
            diagnostic_findings = findings
            top = findings[0]
            primary_diagnosis = f"{top['condition']} ({top['percentage']})"
            target_xai_class = int(np.argmax(probabilities))
            if "Severe" in top["condition"] or "Proliferative" in top["condition"]:
                overall_severity = "Urgent / Proliferative Risk"
            elif "Moderate" in top["condition"]:
                overall_severity = "Moderate DR"
            elif "Mild" in top["condition"]:
                overall_severity = "Mild NPDR"
            else:
                overall_severity = "Normal Retina"

        # Step 5: Explainable AI (Grad-CAM)
        heatmap = None
        overlay = None
        contoured = None
        if generate_xai:
            try:
                gradcam = GradCAM(model, model.get_last_conv_layer())
                heatmap = gradcam.generate_heatmap(tensor_input, target_class_idx=target_xai_class)
                visual_base = dip_stages.get("dip_final_visual", raw_img)
                overlay, contoured = gradcam.overlay_heatmap(visual_base, heatmap)
            except Exception as e:
                print(f"Warning: Grad-CAM generation encountered: {e}")

        return {
            "modality": active_modality.value,
            "detected_modality": detected_modality.value,
            "modality_mismatch_warning": is_mismatch,
            "modality_router_confidences": {k.value: v for k, v in router_confidences.items()},
            "primary_diagnosis": primary_diagnosis,
            "overall_severity": overall_severity,
            "findings": diagnostic_findings,
            "dip_stages": dip_stages,
            "xai": {
                "heatmap": heatmap,
                "overlay": overlay,
                "contoured": contoured,
                "target_class": target_xai_class,
            },
        }
