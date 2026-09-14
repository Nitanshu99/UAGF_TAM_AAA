"""Model-metadata inference tool — wizard smart defaults for the S6 hand-off."""
from aaa.tools.model_meta.artifact_layout import (
    ARCHIVE_SUFFIXES,
    DIRECTORY,
    SINGLE_FILE,
    WEIGHT_SUFFIXES,
    archive_members,
    infer_artifact_kind,
    suggest_entrypoint,
)
from aaa.tools.model_meta.infer import infer_model_format, suggest_task_type

__all__ = ["infer_model_format", "suggest_task_type", "infer_artifact_kind",
           "archive_members", "suggest_entrypoint", "SINGLE_FILE", "DIRECTORY",
           "ARCHIVE_SUFFIXES", "WEIGHT_SUFFIXES"]
