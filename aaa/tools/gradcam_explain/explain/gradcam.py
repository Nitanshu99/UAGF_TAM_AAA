"""Part 2 of the former ``gradcam_explain`` module (auto-split)."""
from __future__ import annotations

import os
from typing import Any

from aaa.tools.gradcam_explain.logger import logger  # noqa: F401


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
    import numpy as np  # type: ignore
    import torch  # type: ignore
    from PIL import Image  # type: ignore
    from pytorch_grad_cam import GradCAM  # type: ignore
    from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget  # type: ignore

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

    # pytorch-grad-cam annotates `targets` as List[Module]; it actually takes
    # the ClassifierOutputTarget callables its own README documents.
    targets: Any = [ClassifierOutputTarget(target_class)] if target_class is not None else None

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
