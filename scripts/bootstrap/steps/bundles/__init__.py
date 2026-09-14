"""Step 5: unpack the two bundles into the places the code expects them.

Both archives are accepted with or without a single wrapping folder — a zip
made from inside the folder and one made of the folder itself both work —
because that is the difference between what two people's zip tools produce.
"""
from scripts.bootstrap.steps.bundles.archive import find_prefix, regular_files
from scripts.bootstrap.steps.bundles.spec import BUNDLES, Bundle, BundleError
from scripts.bootstrap.steps.bundles.unpack import unpack

__all__ = ["BUNDLES", "Bundle", "BundleError", "find_prefix", "regular_files", "unpack"]
