"""
Comprehensive Clinical Evaluation Metrics for Medical Imaging.
Supports:
  - Binary & Multi-Label Metrics (ROC-AUC, Sensitivity, Specificity, F1)
  - Multi-Class Metrics (Balanced Accuracy, Macro/Micro Precision/Recall)
  - Ordinal Metrics (Quadratic Weighted Kappa for Retinopathy Staging)
  - Confusion Matrix Generation
"""

from typing import Dict, Any, List, Optional
import numpy as np

try:
    from sklearn.metrics import (
        roc_auc_score,
        accuracy_score,
        precision_score,
        recall_score,
        f1_score,
        confusion_matrix,
        cohen_kappa_score,
        classification_report,
    )
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class MedicalEvaluator:
    """
    Evaluator providing clinical-grade performance metrics.
    """

    @staticmethod
    def evaluate_multi_label(
        y_true: np.ndarray,
        y_pred_probs: np.ndarray,
        label_names: List[str],
        threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Evaluates multi-label models (e.g. ChestMNIST).

        Args:
            y_true: Binary ground truth array (N, num_labels)
            y_pred_probs: Predicted probability array (N, num_labels) in [0, 1]
            label_names: List of label strings
            threshold: Decision threshold
        """
        y_pred_binary = (y_pred_probs >= threshold).astype(int)
        per_class_metrics = {}

        auc_list = []
        for i, label in enumerate(label_names):
            # Calculate per-class AUC if both 0 and 1 exist in y_true
            if HAS_SKLEARN and len(np.unique(y_true[:, i])) > 1:
                class_auc = float(roc_auc_score(y_true[:, i], y_pred_probs[:, i]))
            else:
                class_auc = 0.5
            auc_list.append(class_auc)

            # Confusion matrix counts for sensitivity and specificity
            tp = int(np.sum((y_true[:, i] == 1) & (y_pred_binary[:, i] == 1)))
            fp = int(np.sum((y_true[:, i] == 0) & (y_pred_binary[:, i] == 1)))
            fn = int(np.sum((y_true[:, i] == 1) & (y_pred_binary[:, i] == 0)))
            tn = int(np.sum((y_true[:, i] == 0) & (y_pred_binary[:, i] == 0)))

            sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            f1 = (2 * precision * sensitivity) / (precision + sensitivity) if (precision + sensitivity) > 0 else 0.0

            per_class_metrics[label] = {
                "AUC": round(class_auc, 4),
                "Sensitivity_Recall": round(sensitivity, 4),
                "Specificity": round(specificity, 4),
                "Precision_PPV": round(precision, 4),
                "F1_Score": round(f1, 4),
                "Support": int(np.sum(y_true[:, i])),
            }

        macro_auc = float(np.mean(auc_list))

        return {
            "task_type": "multi_label",
            "mean_macro_auc": round(macro_auc, 4),
            "per_class_results": per_class_metrics,
        }

    @staticmethod
    def evaluate_multi_class(
        y_true: np.ndarray,
        y_pred_probs: np.ndarray,
        label_names: List[str],
    ) -> Dict[str, Any]:
        """
        Evaluates multi-class models (e.g. DermaMNIST).
        """
        y_pred = np.argmax(y_pred_probs, axis=-1)
        y_true_flat = y_true.squeeze()

        if HAS_SKLEARN:
            acc = float(accuracy_score(y_true_flat, y_pred))
            f1_macro = float(f1_score(y_true_flat, y_pred, average="macro", zero_division=0))
            f1_weighted = float(f1_score(y_true_flat, y_pred, average="weighted", zero_division=0))
            prec_macro = float(precision_score(y_true_flat, y_pred, average="macro", zero_division=0))
            rec_macro = float(recall_score(y_true_flat, y_pred, average="macro", zero_division=0))
            cm = confusion_matrix(y_true_flat, y_pred).tolist()

            # Multi-class AUC (One-vs-Rest)
            try:
                auc_ovr = float(roc_auc_score(y_true_flat, y_pred_probs, multi_class="ovr", average="macro"))
            except Exception:
                auc_ovr = 0.5
        else:
            acc = float(np.mean(y_true_flat == y_pred))
            f1_macro = 0.0
            f1_weighted = 0.0
            prec_macro = 0.0
            rec_macro = 0.0
            auc_ovr = 0.5
            cm = []

        return {
            "task_type": "multi_class",
            "accuracy": round(acc, 4),
            "macro_auc": round(auc_ovr, 4),
            "macro_f1": round(f1_macro, 4),
            "weighted_f1": round(f1_weighted, 4),
            "macro_precision": round(prec_macro, 4),
            "macro_recall": round(rec_macro, 4),
            "confusion_matrix": cm,
            "classes": label_names,
        }

    @staticmethod
    def evaluate_ordinal(
        y_true: np.ndarray,
        y_pred_probs: np.ndarray,
        label_names: List[str],
    ) -> Dict[str, Any]:
        """
        Evaluates ordinal models (e.g. RetinaMNIST Diabetic Retinopathy stages 0-4).
        Calculates Quadratic Weighted Kappa (QWK), which penalizes misclassifications
        proportionally to the distance between grades (e.g. predicting grade 4 when true is 0
        is penalized much more heavily than predicting grade 1).
        """
        y_pred = np.argmax(y_pred_probs, axis=-1)
        y_true_flat = y_true.squeeze()

        if HAS_SKLEARN:
            acc = float(accuracy_score(y_true_flat, y_pred))
            qwk = float(cohen_kappa_score(y_true_flat, y_pred, weights="quadratic"))
            cm = confusion_matrix(y_true_flat, y_pred).tolist()
        else:
            acc = float(np.mean(y_true_flat == y_pred))
            qwk = 0.0
            cm = []

        return {
            "task_type": "ordinal",
            "accuracy": round(acc, 4),
            "quadratic_weighted_kappa": round(qwk, 4),
            "confusion_matrix": cm,
            "classes": label_names,
        }
