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

    Returns:
        tuple: (mask, (x1, y1, x2, y2))
               mask: A binary mask (255 where main object is, 0 otherwise).
                     Crucially, this preserves holes inside the object if they were detected.
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
        # Using a low threshold to catch soft edges
        _, binary = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)

        # Use Connected Components to find islands
        # connectivity=8 checks 8-neighbors
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            binary, connectivity=8
        )

        if num_labels <= 1:
            # Label 0 is background (all zeros), so if num_labels <= 1, we have no objects
            return None

        width, height = image.size
        center_x, center_y = width / 2, height / 2

        best_score = -1
        best_label = -1
        best_box = None

        # Iterate over labels (skip 0 which is background)
        for i in range(1, num_labels):
            x, y, w, h, area = stats[i]

            # Filter tiny noise
            if w < 10 or h < 10:
                continue

            # Calculate distance from box center to image center
            box_cx = x + w / 2
            box_cy = y + h / 2
            dist_sq = (box_cx - center_x) ** 2 + (box_cy - center_y) ** 2

            max_dist_sq = (width / 2) ** 2 + (height / 2) ** 2
            dist_norm = dist_sq / max_dist_sq

            # Score = Area * (1 - 0.5 * dist_norm)
            score = area * (1.0 - 0.5 * dist_norm)

            if score > best_score:
                best_score = score
                best_label = i
                best_box = (x, y, x + w, y + h)

        if best_label == -1:
            return None

        # Create the mask for the selected object
        # This mask is 255 where labels == best_label, 0 otherwise
        # Since 'labels' was computed from the binary mask, holes (which are 0) remain 0.
        mask = np.where(labels == best_label, 255, 0).astype(np.uint8)

        return mask, best_box

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

        # alpha_matting=True improves the edge quality significantly
        image_no_bg = remove(
            image,
            session=session,
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=10,
        )
    except Exception as e:
        print(f"center_object postprocess: rembg failed: {e}")
        image.save(output_path)
        return output_path

    print("Step 2: Analyzing Objects...")
    result = get_main_object_mask_and_box(image_no_bg)

    if result:
        mask, box = result
        x1, y1, x2, y2 = box

        # Apply the clean mask to the image
        # logic:
        # 1. 'mask' is a binary mask of the main object (with holes).
        # 2. We dilate it slightly to include the soft edges of the original alpha.
        # 3. We use it to zero out other objects from the original alpha.

        # Dilate the binary mask to cover the anti-aliased edges
        kernel = np.ones((5, 5), np.uint8)
        dilated_mask = cv2.dilate(mask, kernel, iterations=1)

        # Normalize to 0/1
        keep_mask = (dilated_mask > 0).astype(np.uint8)

        img_np = np.array(image_no_bg)
        # Multiply original alpha by keep_mask
        # This preserves the soft alpha of the main object, but zeroes out everything else
        img_np[:, :, 3] = img_np[:, :, 3] * keep_mask

        image_clean = Image.fromarray(img_np)

        # Add a small padding?
        padding = 10
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(width, x2 + padding)
        y2 = min(height, y2 + padding)

        print(f"Found Main Object at: {x1, y1, x2, y2}")

        # Crop the image (the one with background removed AND cleaned)
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
