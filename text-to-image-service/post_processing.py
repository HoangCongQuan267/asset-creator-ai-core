import os
import sys
from pathlib import Path
from PIL import Image
import numpy as np
import cv2
import torch

try:
    from .remove_bg_service.server import process_with_inspyrenet, process_with_bria

    INSPYRENET_AVAILABLE = True
except ImportError as e:
    # Try absolute import if relative fails (e.g. running script directly)
    try:
        from remove_bg_service.server import process_with_inspyrenet, process_with_bria

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

        # Copy original alpha ONLY where main_mask is present
        # This removes other unrelated objects floating around
        final_alpha = cv2.bitwise_and(alpha, alpha, mask=main_mask)

        # 2. Smart Hole Filling
        # Iterate through children (holes) of the best contour
        main_area = cv2.contourArea(contours[best_idx])
        # Threshold: Holes smaller than 2% of the object area are considered "details" and filled.
        # Holes larger than 2% are considered "real background".
        hole_threshold = main_area * 0.02

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

    print("Step 1: Removing Background (Parallel Ensemble)...")

    # 1. Run Bria (Good for Salient Object Detection / Coarse Mask)
    bria_image = None
    try:
        print("  - Running Bria...")
        bria_image = process_with_bria(image)
    except Exception as e:
        print(f"  - Bria failed: {e}")

    # 2. Run InSPyReNet (Good for High Quality Edges / Transparency)
    inspyrenet_image = None
    try:
        print("  - Running InSPyReNet...")
        inspyrenet_image = process_with_inspyrenet(image)
    except Exception as e:
        print(f"  - InSPyReNet failed: {e}")

    # 3. Combine Results (Mask Guidance)
    image_no_bg = None

    if inspyrenet_image and bria_image:
        print("  - Combining models: Using Bria to guide InSPyReNet...")
        # Convert to numpy
        inspy_np = np.array(inspyrenet_image)
        bria_np = np.array(bria_image)

        # Extract Alphas
        inspy_alpha = inspy_np[:, :, 3]
        bria_alpha = bria_np[:, :, 3]

        # Dilate Bria mask slightly to ensure we don't clip InSPyReNet's fine details (hair/fur)
        # We trust Bria for "Is the object here?" but trust InSPyReNet for "Where exactly is the edge?"
        kernel = np.ones((15, 15), np.uint8)  # Moderate dilation
        bria_mask_dilated = cv2.dilate(bria_alpha, kernel, iterations=1)

        # Normalize to 0-1 for multiplication
        mask_guidance = bria_mask_dilated.astype(float) / 255.0

        # Apply guidance: Keep InSPyReNet alpha ONLY where Bria says there is likely an object (plus margin)
        # This removes background clutter that InSPyReNet might have missed
        final_alpha = inspy_alpha.astype(float) * mask_guidance

        inspy_np[:, :, 3] = final_alpha.astype(np.uint8)
        image_no_bg = Image.fromarray(inspy_np)

    elif inspyrenet_image:
        print("  - Using InSPyReNet result only.")
        image_no_bg = inspyrenet_image
    elif bria_image:
        print("  - Using Bria result only (Fallback).")
        image_no_bg = bria_image
    else:
        print("  - All BG removal failed.")
        image.save(output_path)
        return output_path

    print("Step 2: Analyzing Objects...")
    result = get_main_object_mask_and_box(image_no_bg)

    if result:
        final_alpha, box = result
        x1, y1, x2, y2 = box

        # Apply the refined alpha to the image
        img_np = np.array(image_no_bg)
        img_np[:, :, 3] = final_alpha

        image_clean = Image.fromarray(img_np)

        # Crop with padding
        padding = 10
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(width, x2 + padding)
        y2 = min(height, y2 + padding)

        print(f"Found Main Object at: {x1, y1, x2, y2}")
        object_image = image_clean.crop((x1, y1, x2, y2))
    else:
        print("No distinct object found, using full image.")
        object_image = image_no_bg

    # 3. Save
    # If output_path is provided, we save relative to it.
    object_output_path = output_path.with_name(
        f"{output_path.stem}_object{output_path.suffix}"
    )
    object_image.save(object_output_path)
    return object_output_path
