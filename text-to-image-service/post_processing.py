import os
from pathlib import Path
from PIL import Image
import numpy as np
import cv2

# Set U2NET_HOME to project models directory to avoid permission issues
# This must be done before importing rembg or running it
os.environ["U2NET_HOME"] = str(Path(__file__).parent / "models" / "u2net")

# Try importing dependencies early
try:
    from rembg import remove, new_session

    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

# Global session cache to prevent re-initialization and re-download checks
_SESSION = None


def get_rembg_session():
    global _SESSION
    if _SESSION is None:
        # Check if model exists to avoid unnecessary download attempts
        # We now use 'isnet-general-use' as it is often better for general object segmentation
        model_name = "isnet-general-use"
        u2net_home = os.environ.get("U2NET_HOME")
        if u2net_home:
            # isnet-general-use saves as isnet-general-use.onnx
            model_path = Path(u2net_home) / f"{model_name}.onnx"
            if model_path.exists():
                print(f"Using existing {model_name} model at: {model_path}")

        # Initialize session (will download if missing)
        _SESSION = new_session(model_name)
    return _SESSION


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
    1. Remove Background (using Rembg).
    2. Find connected components (islands).
    3. Select the 'Main' object (Largest + Central).
    4. Crop to that object.
    5. Save.
    """
    width, height = image.width, image.height

    if not REMBG_AVAILABLE:
        print("center_object postprocess: rembg not found. Please install it.")
        # Fallback to simple center crop? Or just save original?
        # Let's just return None to indicate failure or save original.
        # For now, saving original as fallback.
        image.save(output_path)
        return output_path

    print("Step 1: Removing Background...")
    try:
        # Rembg expects PIL image and returns PIL image (RGBA)
        # Use cached session to avoid re-downloading/re-initializing
        session = get_rembg_session()

        # We disable alpha_matting here because we want the raw prediction first.
        # Alpha matting can sometimes erode small details.
        # ISNet provides high quality alpha directly.
        image_no_bg = remove(image, session=session, alpha_matting=False)
    except Exception as e:
        print(f"center_object postprocess: rembg failed: {e}")
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
