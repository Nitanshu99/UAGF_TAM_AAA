"""Grad-CAM entry point: saliency maps, or nothing and the reason."""
from __future__ import annotations

from typing import Any, Sequence

from aaa.tools.gradcam_explain.explain.gradcam import _explain_gradcam  # noqa: F401
from aaa.tools.gradcam_explain.logger import logger  # noqa: F401


def _batch_size(images: Any) -> int:
    try:
        return int(images.shape[0])
    except Exception:
        try:
            return int(len(images))
        except Exception:
            return 0


def gradcam_explain(
    model: Any = None,
    images: Any = None,
    image_ids: Sequence[str] | None = None,
    output_dir: str | None = None,
    target_layer: Any = None,
    target_class: int | None = None,
    layer_name: str | None = None,
    reasons: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Generate Grad-CAM saliency maps for a batch of CV inputs.

    Parameters
    ----------
    model:
        Trained ``torch.nn.Module`` classifier.  Required for production
        path; ``None`` returns no maps.
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
    list of dicts matching the T10 ``visual_explanations`` item schema; empty
    when Grad-CAM did not run (a stub entry per image once stood in for maps
    that were never drawn, T-20260913-061).
    """
    if images is None or _batch_size(images) == 0:
        return []

    n = _batch_size(images)
    ids = list(image_ids) if image_ids else [f"image_{i}" for i in range(n)]

    if model is None:
        return []
    try:
        return _explain_gradcam(
            model, images, ids, output_dir, target_layer, target_class, layer_name
        )
    except Exception as exc:
        logger.info("Grad-CAM unavailable (%s); no saliency maps reported.", exc)
        if reasons is not None:
            reasons.append(f"Grad-CAM could not run on the supplied images: {exc}")
        return []
