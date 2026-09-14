"""gradcam_explain — Grad-CAM saliency-map generator for CV models (§4.2).

Returns a structured list compatible with the T10_explainability_report
``visual_explanations`` block.

Production path:  ``pytorch_grad_cam`` (GradCAM / GradCAM++ / HiResCAM)
                  for any torch.nn.Module classifier exposing a
                  convolutional ``target_layer``.
No fallback: when Grad-CAM cannot run no entries are returned and the
                  reason goes to ``reasons``.

Usage
-----
    from src.tools.gradcam_explain import gradcam_explain

    visuals = gradcam_explain(
        model=cv_model,
        images=batch,
        image_ids=["img_001", "img_002"],
        output_dir="/tmp/heatmaps",
    )"""
from aaa.tools.gradcam_explain.explain.gradcam import _explain_gradcam  # noqa: F401
from aaa.tools.gradcam_explain.explain.stub import _batch_size, gradcam_explain  # noqa: F401
from aaa.tools.gradcam_explain.logger import logger  # noqa: F401

__all__ = [
    'logger', '_explain_gradcam', '_batch_size', 'gradcam_explain',
]
