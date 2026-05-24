"""
gradcam_explain — Grad-CAM saliency-map generator for CV models (§4.2).

Returns a structured list compatible with the T10_explainability_report
``visual_explanations`` block.

Production path:  ``pytorch_grad_cam`` (GradCAM / GradCAM++ / HiResCAM)
                  for any torch.nn.Module classifier exposing a
                  convolutional ``target_layer``.
Offline/fallback: returns a stub entry per image with no heatmap URI —
                  signals to T10 that the technique was skipped.

Usage
-----
    from src.tools.gradcam_explain import gradcam_explain

    visuals = gradcam_explain(
        model=cv_model,
        images=batch,
        image_ids=["img_001", "img_002"],
        output_dir="/tmp/heatmaps",
    )
"""
from __future__ import annotations

import logging
import os
from typing import Any, Sequence

logger = logging.getLogger(__name__)


def gradcam_explain(
    model: Any = None,
    images: Any = None,
    image_ids: Sequence[str] | None = None,
    output_dir: str | None = None,
    target_layer: Any = None,
    target_class: int | None = None,
    layer_name: str | None = None,
) -> list[dict[str, Any]]:
    """
    Generate Grad-CAM saliency maps for a batch of CV inputs.

    Parameters
    ----------
    model:
        Trained ``torch.nn.Module`` classifier.  Required for production
        path; ``None`` returns the offline stub.
    images:
        Batch of images — ``torch.Tensor`` shape ``(N, C, H, W)`` or a
        sequence of arrays/PIL images.
    image_ids:
        Human-readable identifiers, one per image.  Defaults to
        ``image_0`` … ``image_{N-1}``.
    output_dir:
        Directory in which to write the heatmap PNGs.  Created if
        absent.  Defaults to a temporary path.
    target_layer:
        Convolutional layer to attach the GradCAM hook to.  Required for
        the SHAP path; if ``None`` we attempt heuristic detection.
    target_class:
        Class index to explain.  When ``None`` the top-predicted class
        is used.
    layer_name:
        Free-text layer descriptor written to T10.

    Returns
    -------
    list of dicts matching the T10 ``visual_explanations`` item schema.
    """
    if images is None or _batch_size(images) == 0:
        return []

    n = _batch_size(images)
    ids = list(image_ids) if image_ids else [f"image_{i}" for i in range(n)]

    if model is not None:
        try:
            return _explain_gradcam(
                model, images, ids, output_dir, target_layer, target_class, layer_name
            )
        except Exception as exc:
            logger.info("Grad-CAM unavailable (%s); returning stub entries.", exc)

    return _explain_stub(ids, layer_name)


# ---------------------------------------------------------------------------
# Grad-CAM path
# ---------------------------------------------------------------------------

def _explain_gradcam(  # pragma: no cover
    model: Any,
    images: Any,
    ids: list[str],
    output_dir: str | None,
    target_layer: Any,
    target_class: int | None,
    layer_name: str | None,
) -> list[dict[str, Any]]:
    """Run the real pytorch-grad-cam pipeline."""
    from pytorch_grad_cam import GradCAM  # type: ignore
    from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget  # type: ignore
    import numpy as np  # type: ignore
    import torch  # type: ignore
    from PIL import Image  # type: ignore

    out_dir = output_dir or "/tmp/aaa_gradcam"
    os.makedirs(out_dir, exist_ok=True)

    if target_layer is None:
        # Heuristic: last conv-like child module
        for _, module in reversed(list(model.named_modules())):
            if module.__class__.__name__.lower().startswith("conv"):
                target_layer = module
                break
    if target_layer is None:
        raise RuntimeError("Could not infer a target conv layer.")

    cam = GradCAM(model=model, target_layers=[target_layer])
    if not isinstance(images, torch.Tensor):
        images = torch.as_tensor(np.asarray(images), dtype=torch.float32)

    targets = [ClassifierOutputTarget(target_class)] if target_class is not None else None

    out: list[dict[str, Any]] = []
    for i in range(images.shape[0]):
        single = images[i : i + 1]
        try:
            heatmap = cam(input_tensor=single, targets=targets)[0]
            heatmap_uint8 = (heatmap * 255).clip(0, 255).astype("uint8")
            heatmap_uri = os.path.join(out_dir, f"{ids[i]}_gradcam.png")
            Image.fromarray(heatmap_uint8).save(heatmap_uri)
            out.append(
                {
                    "image_id": ids[i],
                    "heatmap_uri": f"file://{heatmap_uri}",
                    "target_class": str(target_class) if target_class is not None else None,
                    "layer": layer_name,
                }
            )
        except Exception:
            continue
    return out


# ---------------------------------------------------------------------------
# Stub fallback
# ---------------------------------------------------------------------------

def _explain_stub(ids: list[str], layer_name: str | None) -> list[dict[str, Any]]:
    """Return placeholder entries when Grad-CAM cannot run."""
    return [
        {
            "image_id": iid,
            "heatmap_uri": "stub://gradcam-unavailable",
            "target_class": None,
            "layer": layer_name,
        }
        for iid in ids
    ]


def _batch_size(images: Any) -> int:
    try:
        return int(images.shape[0])
    except Exception:
        try:
            return int(len(images))
        except Exception:
            return 0
