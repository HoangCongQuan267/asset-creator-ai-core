from ultralytics import YOLOWorld
from PIL import Image
import torch
import ssl
import os
from pathlib import Path

# Fix SSL certificate errors on Mac
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Global variable to cache the model
_MODEL = None
ROOT_DIR = Path(__file__).resolve().parent
MODELS_DIR = ROOT_DIR / "models"
YOLO_DIR = MODELS_DIR / "yolo"


def get_model(model_name="yolov8s-worldv2.pt"):
    """
    Lazy loads the YOLO-World model.
    Using 'yolov8s-worldv2.pt' as a good balance of speed/accuracy.
    """
    global _MODEL
    if _MODEL is None:
        print(f"Loading YOLO-World model: {model_name}...")

        # Check if model exists locally in models/yolo/
        local_model_path = YOLO_DIR / model_name
        if local_model_path.is_file():
            print(f"Found local model at {local_model_path}")
            _MODEL = YOLOWorld(str(local_model_path))
        else:
            # Fallback to default download behavior (usually to current dir or ~/.cache/ultralytics)
            # We ensure YOLO_DIR exists so we could potentially move it there later if we wanted,
            # but for now we let Ultralytics handle the download if it's missing.
            # The SSL fix above should allow the download to proceed.
            _MODEL = YOLOWorld(model_name)

    return _MODEL


def detect_largest_box(image: Image.Image, text_prompt: str):
    """
    Detects the largest bounding box in the image matching the text_prompt.

    Args:
        image (PIL.Image.Image): Input image.
        text_prompt (str): The object description to detect (e.g. "sword", "potion").

    Returns:
        tuple or None: (x1, y1, x2, y2) of the largest box, or None if nothing detected.
    """
    if not text_prompt or not isinstance(text_prompt, str):
        return None

    try:
        model = get_model()

        # YOLO-World expects a list of categories/classes
        # We treat the entire prompt as the category we are looking for.
        # Ideally, this should be a short noun phrase (e.g., "sword").
        # If the prompt is long, it might be worth extracting the main noun,
        # but for now we pass it as is, or maybe truncate/clean it.
        # For this implementation, we assume the prompt describes the object.
        model.set_classes([text_prompt])

        # Run inference
        # conf=0.1 to catch even faint matches, we will filter by size
        results = model.predict(image, conf=0.1, verbose=False)

        largest_area = 0.0
        largest_box = None

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                # box.xyxy is a tensor of shape (1, 4) -> [x1, y1, x2, y2]
                coords = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = coords

                area = (x2 - x1) * (y2 - y1)
                if area > largest_area:
                    largest_area = area
                    largest_box = (x1, y1, x2, y2)

        return largest_box

    except Exception as e:
        print(f"Error in detect_largest_box: {e}")
        return None
