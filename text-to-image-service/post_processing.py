import os
import sys
from pathlib import Path
from PIL import Image
import numpy as np
import cv2
import torch

try:
    from .remove_bg_service.server import (
        process_with_inspyrenet,
        process_with_bria,
        process_with_ormbg,
        process_with_hybrid_matting,
        process_with_rembg_hq,
    )

    INSPYRENET_AVAILABLE = True
except ImportError as e:
    # Try absolute import if relative fails (e.g. running script directly)
    try:
        from remove_bg_service.server import (
            process_with_inspyrenet,
            process_with_bria,
            process_with_ormbg,
            process_with_hybrid_matting,
            process_with_rembg_hq,
        )

        INSPYRENET_AVAILABLE = True
    except ImportError as e2:
        print(f"Failed to import remove_bg_service: {e}, {e2}")
        INSPYRENET_AVAILABLE = False


def get_main_object_mask_and_box(image: Image.Image) -> tuple[np.ndarray, tuple] | None:
    """
    Analyzes the alpha channel of an RGBA image to find the 'main' object.
    Heuristic: Combination of Area and Centrality.

    Uses contour hierarchy to:
    1. Identify the main object.
    2. Remove unrelated objects (other islands).
    3. Fill SMALL holes (likely false positives/details).
    4. Keep LARGE holes (likely real background).

    Returns:
        tuple: (processed_alpha, (x1, y1, x2, y2))
               processed_alpha: The refined alpha channel.
               box: The bounding box of the main object.
        or None if no valid object found.
    """
    try:
        # Convert to numpy
        img_np = np.array(image)

        # Extract Alpha channel
        if img_np.shape[2] < 4:
            print("Image is not RGBA, cannot find objects by alpha.")
            return None

        alpha = img_np[:, :, 3]

        # Threshold alpha to get binary mask for connectivity analysis
        _, binary = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)

        # Find contours with hierarchy (RETR_CCOMP) to detect holes
        contours, hierarchy = cv2.findContours(
            binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return None

        # hierarchy is shape (1, N, 4) -> (Next, Prev, First_Child, Parent)
        hierarchy = hierarchy[0]

        width, height = image.size
        center_x, center_y = width / 2, height / 2

        best_score = -1
        best_idx = -1
        best_box = None

        # Iterate over contours
        for i, cnt in enumerate(contours):
            # Check if it's a top-level contour (Parent == -1)
            # This filters out holes from being candidates for "Main Object"
            if hierarchy[i][3] != -1:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)

            # Filter tiny noise
            if w < 10 or h < 10:
                continue

            # Calculate distance from box center to image center
            box_cx = x + w / 2
            box_cy = y + h / 2
            dist_sq = (box_cx - center_x) ** 2 + (box_cy - center_y) ** 2

            max_dist_sq = (width / 2) ** 2 + (height / 2) ** 2
            dist_norm = dist_sq / max_dist_sq

            # Score: Favor large area and closeness to center
            # Weight area more heavily to avoid picking small central debris
            score = area * (1.0 - 0.5 * dist_norm)

            if score > best_score:
                best_score = score
                best_idx = i
                best_box = (x, y, x + w, y + h)

        if best_idx == -1:
            return None

        # Start with a clean alpha channel
        final_alpha = np.zeros_like(alpha)

        # 1. Mask the Main Object (keep its original soft alpha)
        # We create a mask of the main object's outer boundary (Filled)
        main_mask = np.zeros_like(alpha)
        cv2.drawContours(main_mask, contours, best_idx, 255, cv2.FILLED)

        # Dilate the main mask slightly to capture soft edges/glow/hair tips
        # that might be below the threshold (alpha < 10) but visually important.
        kernel_smooth = np.ones((5, 5), np.uint8)
        main_mask = cv2.dilate(main_mask, kernel_smooth, iterations=1)

        # Copy original alpha ONLY where main_mask is present
        # This removes other unrelated objects floating around
        final_alpha = cv2.bitwise_and(alpha, alpha, mask=main_mask)

        # 2. Smart Hole Filling
        # Iterate through children (holes) of the best contour
        main_area = cv2.contourArea(contours[best_idx])
        # Threshold: Holes smaller than 0.5% (was 2%) of the object area are considered "details" and filled.
        # We lowered this because ORMBG/InSPyReNet are very accurate, so large holes are likely real.
        hole_threshold = main_area * 0.005

        child_idx = hierarchy[best_idx][2]
        while child_idx != -1:
            hole_area = cv2.contourArea(contours[child_idx])

            if hole_area < hole_threshold:
                # Small hole -> It's a detail (false positive) -> FILL IT
                # We draw it with 255 (opaque) on the final_alpha
                cv2.drawContours(final_alpha, contours, child_idx, 255, cv2.FILLED)

            # If large hole -> Do nothing (it remains transparent from the original alpha)

            child_idx = hierarchy[child_idx][0]  # Next sibling

        return final_alpha, best_box

    except Exception as e:
        print(f"Error in get_main_object_mask_and_box: {e}")
        return None


def center_object_postprocess(
    image: Image.Image, output_path: Path, text_prompt: str, models_dir: Path
) -> Path | None:
    """
    Post-processes the generated image to extract the central object.

    New Strategy (Reverse Method):
    1. Remove Background (using InSPyReNet via remove_bg_service module).
    2. Find connected components (islands).
    3. Select the 'Main' object (Largest + Central).
    4. Crop to that object.
    5. Save.
    """
    width, height = image.width, image.height

    if not INSPYRENET_AVAILABLE:
        print("center_object postprocess: remove_bg_service not found.")
        # Fallback to simple center crop? Or just save original?
        image.save(output_path)
        return output_path

    print("Step 1: Removing Background (Prioritized Strategy)...")
    image_no_bg = None

    rembg_hq = None
    hybrid = None

    try:
        print("  - Attempting Remove.bg-like Rembg HQ...")
        rembg_hq = process_with_rembg_hq(image)
    except Exception as e:
        print(f"  - Rembg HQ failed: {e}")

    # Priority 1: Hybrid Matting (ORMBG + FBA Matting) - The "Secret Sauce"
    # This aligns with the user's request for "Alpha Matting" and "Refinement Loops".
    try:
        print("  - Attempting Hybrid Matting (ORMBG + FBA Matting)...")
        hybrid = process_with_hybrid_matting(image)
    except Exception as e:
        print(f"  - Hybrid Matting failed: {e}")

    if hybrid is not None:
        if hybrid.mode != "RGBA":
            hybrid = hybrid.convert("RGBA")
        image_no_bg = hybrid
    elif rembg_hq is not None:
        image_no_bg = rembg_hq

    # Priority 2: ORMBG (State-of-the-art Open Source, similar to Remove.bg)
    if image_no_bg is None:
        try:
            print("  - Attempting ORMBG (Fallback)...")
            image_no_bg = process_with_ormbg(image)
        except Exception as e:
            print(f"  - ORMBG failed or not available: {e}")

    # Priority 3: InSPyReNet (High Quality, Transparent Background)
    if image_no_bg is None:
        try:
            print("  - Attempting InSPyReNet...")
            image_no_bg = process_with_inspyrenet(image)
        except Exception as e:
            print(f"  - InSPyReNet failed: {e}")

    if image_no_bg is None:
        print("  - All BG removal failed.")
        image.save(output_path)
        return output_path

    print("Step 2: Cropping to content...")

    # Simple, robust cropping that trusts the model's output
    # mimics remove.bg behavior: just remove transparent pixels
    try:
        if image_no_bg.mode != "RGBA":
            image_no_bg = image_no_bg.convert("RGBA")

        bbox = image_no_bg.getbbox()

        if bbox:
            # Add small padding if desired, or keep tight
            padding = 10
            x1, y1, x2, y2 = bbox
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(width, x2 + padding)
            y2 = min(height, y2 + padding)

            print(f"Found Content at: {x1, y1, x2, y2}")
            object_image = image_no_bg.crop((x1, y1, x2, y2))
        else:
            print("No content found (fully transparent), using full image.")
            object_image = image_no_bg

    except Exception as e:
        print(f"Error during cropping: {e}")
        object_image = image_no_bg

    if object_image.mode != "RGBA":
        object_image = object_image.convert("RGBA")

    alpha = np.array(object_image.split()[-1])
    mask = np.zeros_like(alpha, dtype=np.uint8)
    mask[alpha > 0] = 255

    object_output_path = output_path.with_name(
        f"{output_path.stem}_object{output_path.suffix}"
    )
    mask_output_path = output_path.with_name(
        f"{output_path.stem}_object_mask{output_path.suffix}"
    )

    object_image.save(object_output_path)
    Image.fromarray(mask, mode="L").save(mask_output_path)

    return object_output_path
