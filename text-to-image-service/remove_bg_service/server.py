from PIL import Image
import ssl
import cv2

# Fix SSL certificate errors on macOS
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

from rembg import remove as rembg_remove, new_session
import numpy as np
import os
from transformers import pipeline
from transparent_background import Remover
import logging
import torch
from .ormbg import ORMBGProcessor

from carvekit.ml.files.models_loc import download_all

from pymatting import (
    estimate_alpha_cf,
    estimate_foreground_ml,
    stack_images,
    load_image,
)


# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Lazy loading cache
_models = {
    "bria": None,
    "inspyrenet": None,
    "rembg": {},
    "ormbg": None,
    "carvekit": {},
    "fba": None,
}


def get_device():
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def get_bria_model():
    if _models["bria"] is None:
        logger.info("Initializing Bria model...")
        _models["bria"] = pipeline(
            "image-segmentation",
            model="briaai/RMBG-1.4",
            trust_remote_code=True,
            device="cpu",
        )
    return _models["bria"]


def get_inspyrenet_model():
    if _models["inspyrenet"] is None:
        logger.info("Initializing InSPyReNet model...")
        device = get_device()
        # Initialize with specific device
        try:
            _models["inspyrenet"] = Remover(device=device)
        except TypeError:
            # Fallback if device argument is not supported in installed version
            _models["inspyrenet"] = Remover()
            _models["inspyrenet"].model.to(device)

    return _models["inspyrenet"]


def get_rembg_session(model_name):
    if model_name not in _models["rembg"]:
        logger.info(f"Initializing Rembg session: {model_name}...")
        _models["rembg"][model_name] = new_session(model_name)
    return _models["rembg"][model_name]


def get_ormbg_processor():
    if _models["ormbg"] is None:
        ormbg_model_path = os.path.expanduser("~/.ormbg/ormbg.pth")
        try:
            logger.info("Initializing ORMBG processor...")
            processor = ORMBGProcessor(ormbg_model_path)
            if torch.cuda.is_available():
                processor.to("cuda")
            else:
                processor.to("cpu")
            _models["ormbg"] = processor
        except FileNotFoundError:
            logger.error(f"ORMBG model file not found: {ormbg_model_path}")
            print(
                "Error: ORMBG model file not found. Please run 'npm run setup-server' to download it."
            )
            # Don't exit here, just raise error or let it fail when used
            raise
    return _models["ormbg"]


from carvekit.ml.wrap.u2net import U2NET
from carvekit.ml.wrap.basnet import BASNET
from carvekit.ml.wrap.fba_matting import FBAMatting
from carvekit.ml.wrap.deeplab_v3 import DeepLabV3
from carvekit.ml.wrap.tracer_b7 import TracerUniversalB7
from carvekit.api.interface import Interface
from carvekit.pipelines.postprocessing import MattingMethod
from carvekit.pipelines.preprocessing import PreprocessingStub
from carvekit.trimap.generator import TrimapGenerator


def initialize_carvekit_model(seg_pipe_class, device="cuda"):
    model = Interface(
        pre_pipe=PreprocessingStub(),
        post_pipe=MattingMethod(
            matting_module=FBAMatting(
                device=device, input_tensor_size=2048, batch_size=1
            ),
            trimap_generator=TrimapGenerator(),
            device=device,
        ),
        seg_pipe=seg_pipe_class(device=device, batch_size=1),
    )
    model.segmentation_pipeline.to("cpu")
    return model


def get_carvekit_model(model_name):
    if model_name not in _models["carvekit"]:
        download_all()  # Ensure models are present
        logger.info(f"Initializing Carvekit model: {model_name}...")

        device = "cuda" if torch.cuda.is_available() else "cpu"

        if model_name == "u2net":
            _models["carvekit"][model_name] = initialize_carvekit_model(U2NET, device)
        elif model_name == "tracer":
            _models["carvekit"][model_name] = initialize_carvekit_model(
                TracerUniversalB7, device
            )
        elif model_name == "basnet":
            _models["carvekit"][model_name] = initialize_carvekit_model(BASNET, device)
        elif model_name == "deeplab":
            _models["carvekit"][model_name] = initialize_carvekit_model(
                DeepLabV3, device
            )
        else:
            raise ValueError(f"Unsupported carvekit model: {model_name}")

    return _models["carvekit"][model_name]


def get_fba_model():
    if _models["fba"] is None:
        download_all()
        logger.info("Initializing FBA Matting model...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # FBAMatting needs to be initialized
        _models["fba"] = FBAMatting(device=device, input_tensor_size=2048, batch_size=1)

    return _models["fba"]


# Processing functions
def process_with_bria(image):
    # Use ORMBG (Local) instead of downloading Bria pipeline
    # Bria AI RMBG-1.4 is the same model as ORMBG
    # This avoids "MaxRetryError" when huggingface.co is unreachable
    logger.info("process_with_bria: Using local ORMBG model (offline fallback)")
    return process_with_ormbg(image)


def process_with_ormbg(image):
    processor = get_ormbg_processor()
    result = processor.process_image(image)
    return result


def process_with_inspyrenet(image):
    model = get_inspyrenet_model()
    device = get_device()

    # Ensure model is on correct device
    if hasattr(model, "model"):
        model.model.to(device)

    result = model.process(image, type="rgba")

    # Move back to CPU to save VRAM
    if hasattr(model, "model"):
        model.model.cpu()

    if device == "cuda":
        torch.cuda.empty_cache()
    elif device == "mps":
        try:
            torch.mps.empty_cache()
        except AttributeError:
            pass  # torch.mps.empty_cache might not exist in older versions

    return result


def process_with_rembg(image, model="u2net"):
    session = get_rembg_session(model)
    return rembg_remove(image, session=session)


def process_with_rembg_hq(image):
    try:
        result = process_with_rembg(image, model="isnet-general-use")
    except Exception:
        result = process_with_rembg(image, model="u2net")

    if result.mode != "RGBA":
        result = result.convert("RGBA")

    rgb = image.convert("RGB")
    alpha = np.array(result)[:, :, 3]
    refined_alpha = closed_form_refinement(rgb, Image.fromarray(alpha))
    alpha_uint8 = np.array(refined_alpha)
    alpha_uint8 = defringe_alpha(alpha_uint8)
    alpha_uint8 = get_largest_component_mask(alpha_uint8)

    output = Image.fromarray(np.array(rgb)).convert("RGBA")
    output.putalpha(Image.fromarray(alpha_uint8))
    return output


def get_largest_component_mask(alpha_mask):
    """
    Keeps only the largest connected component in the alpha mask.
    Removes floating noise islands.
    """
    # Threshold to binary
    _, binary = cv2.threshold(alpha_mask, 127, 255, cv2.THRESH_BINARY)

    # Find connected components
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        binary, connectivity=8
    )

    # If no components (empty image), return original
    if num_labels <= 1:
        return alpha_mask

    # Find largest component (ignoring background at index 0)
    largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])

    # Create mask for largest component
    mask = np.zeros_like(alpha_mask)
    mask[labels == largest_label] = 255

    # Apply mask to original alpha
    # We use the binary mask to clip the original alpha
    # But we want to preserve the soft edges of the largest component.
    # So we dilate the binary mask slightly to include the soft edges of the main object
    # and then mask the original alpha.

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask_dilated = cv2.dilate(mask, kernel, iterations=2)

    return cv2.bitwise_and(alpha_mask, mask_dilated)


def defringe_alpha(alpha_uint8):
    alpha = alpha_uint8.astype(np.float32) / 255.0
    edge_band = (alpha > 0.03) & (alpha < 0.65)
    alpha[edge_band] = np.power(alpha[edge_band], 2.4)

    laplacian = cv2.Laplacian(alpha.astype(np.float32), cv2.CV_32F)
    sharpen_band = (alpha > 0.35) & (alpha < 0.95)
    alpha[sharpen_band] = np.clip(
        alpha[sharpen_band] - 0.35 * laplacian[sharpen_band], 0.0, 1.0
    )

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    edge = cv2.morphologyEx((alpha > 0.01).astype(np.uint8), cv2.MORPH_GRADIENT, kernel)
    alpha = np.clip(alpha - edge.astype(np.float32) * 0.12, 0.0, 1.0)

    alpha[alpha < 0.02] = 0.0
    alpha[alpha > 0.96] = 1.0
    return (alpha * 255).astype(np.uint8)


def closed_form_refinement(image_pil, alpha_pil):
    image = np.asarray(image_pil.convert("RGB")).astype(np.float64) / 255.0
    alpha = np.asarray(alpha_pil).astype(np.float64) / 255.0

    # Build trimap (0, 0.5, 1)
    trimap = np.full_like(alpha, 0.5, dtype=np.float64)
    trimap[alpha > 0.98] = 1.0
    trimap[alpha < 0.02] = 0.0

    refined_alpha = estimate_alpha_cf(image, trimap)

    refined_alpha = np.clip(refined_alpha, 0, 1)

    return Image.fromarray((refined_alpha * 255).astype(np.uint8))


def guided_filter_refinement(image_pil, alpha_pil):
    image = np.array(image_pil.convert("RGB"))
    alpha = np.array(alpha_pil).astype(np.float32) / 255.0

    guide = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0

    radius = 6
    eps = 1e-4

    refined = cv2.ximgproc.guidedFilter(
        guide=guide,
        src=alpha,
        radius=radius,
        eps=eps,
    )

    refined = np.clip(refined, 0, 1)

    return Image.fromarray((refined * 255).astype(np.uint8))


def color_consistency_refinement(alpha, rgb):
    alpha = alpha.astype(np.float32)
    rgb = rgb.astype(np.float32)

    fg_mask = alpha > 0.97
    bg_mask = alpha < 0.03

    if fg_mask.sum() < 50 or bg_mask.sum() < 50:
        return alpha

    fg_colors = rgb[fg_mask]
    bg_colors = rgb[bg_mask]

    fg_mean = fg_colors.mean(axis=0)
    bg_mean = bg_colors.mean(axis=0)

    uncertain = (alpha >= 0.08) & (alpha <= 0.9)

    if not np.any(uncertain):
        return alpha

    colors = rgb[uncertain]

    diff_fg = colors - fg_mean
    diff_bg = colors - bg_mean

    dist_fg = np.sum(diff_fg * diff_fg, axis=1)
    dist_bg = np.sum(diff_bg * diff_bg, axis=1)

    closer_fg = dist_fg + 1e-6 < dist_bg * 0.9
    closer_bg = dist_bg + 1e-6 < dist_fg * 0.9

    alpha_uncertain = alpha[uncertain]

    alpha_uncertain[closer_fg] = np.minimum(
        1.0, alpha_uncertain[closer_fg] * 1.25 + 0.1
    )
    alpha_uncertain[closer_bg] = np.maximum(0.0, alpha_uncertain[closer_bg] * 0.5 - 0.1)

    refined_alpha = alpha.copy()
    refined_alpha[uncertain] = alpha_uncertain

    return refined_alpha


def grabcut_refinement(image_rgb, alpha):
    rgb = image_rgb.astype(np.uint8)
    alpha = alpha.astype(np.float32)

    h, w = alpha.shape[:2]
    if h < 4 or w < 4:
        return alpha

    mask = np.full((h, w), cv2.GC_PR_BGD, np.uint8)

    sure_fg = alpha > 0.97
    sure_bg = alpha < 0.03

    mask[sure_fg] = cv2.GC_FGD
    mask[sure_bg] = cv2.GC_BGD

    if sure_fg.sum() < 50 or sure_bg.sum() < 50:
        return alpha

    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    try:
        cv2.grabCut(
            rgb,
            mask,
            None,
            bgd_model,
            fgd_model,
            3,
            cv2.GC_INIT_WITH_MASK,
        )
    except Exception:
        return alpha

    result_mask = np.where(
        (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1.0, 0.0
    ).astype(np.float32)

    refined = np.maximum(alpha, result_mask)
    refined = np.clip(refined, 0.0, 1.0)

    return refined


def edge_boundary_refinement(image_rgb, alpha):
    alpha = alpha.astype(np.float32)
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)

    edges = cv2.Canny(gray, 60, 140)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    edges = cv2.dilate(edges, kernel, iterations=1)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return alpha

    alpha_seed = (alpha > 0.3).astype(np.uint8) * 255
    best_idx = -1
    best_score = -1
    best_area = 0

    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area < 400:
            continue
        mask = np.zeros_like(alpha_seed)
        cv2.drawContours(mask, [cnt], -1, 255, cv2.FILLED)
        overlap = cv2.bitwise_and(mask, alpha_seed)
        score = overlap.sum()
        if score > best_score or (score == best_score and area > best_area):
            best_score = score
            best_idx = i
            best_area = area

    if best_idx == -1:
        return alpha

    boundary_mask = np.zeros_like(alpha_seed)
    cv2.drawContours(boundary_mask, contours, best_idx, 255, cv2.FILLED)
    boundary_mask = cv2.dilate(boundary_mask, kernel, iterations=1)

    hard_mask = boundary_mask > 0
    alpha = alpha * hard_mask.astype(np.float32)

    binary = (alpha > 0.05).astype(np.uint8)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        binary, connectivity=8
    )
    if num_labels > 1:
        largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        keep = (labels == largest_label).astype(np.float32)
        alpha = alpha * keep

    return alpha


def alpha_boundary_clamp(alpha):
    alpha = alpha.astype(np.float32)
    binary = (alpha > 0.08).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return alpha

    areas = [cv2.contourArea(c) for c in contours]
    best_idx = int(np.argmax(areas))
    hull = cv2.convexHull(contours[best_idx])
    mask = np.zeros_like(binary)
    cv2.drawContours(mask, [hull], -1, 255, cv2.FILLED)

    hard_mask = mask > 0
    return alpha * hard_mask.astype(np.float32)


def subpixel_hair_enhancement(alpha_pil):
    alpha = np.array(alpha_pil).astype(np.float32) / 255.0

    # Target only soft hair region
    hair_zone = (alpha > 0.15) & (alpha < 0.85)

    enhanced = alpha.copy()
    enhanced[hair_zone] = np.power(enhanced[hair_zone], 0.85)

    # Convert to float32 for Laplacian
    enhanced_32 = enhanced.astype(np.float32)
    laplacian = cv2.Laplacian(enhanced_32, cv2.CV_32F)

    enhanced = np.clip(enhanced - 0.08 * laplacian, 0, 1)

    return Image.fromarray((enhanced * 255).astype(np.uint8))


def process_with_hybrid_matting(image):
    """
    Hybrid matting with SHARP edge refinement.
    Preserves hair while producing razor outline.
    """

    # 1️⃣ ORMBG
    ormbg_result = process_with_ormbg(image)
    ormbg_alpha = np.array(ormbg_result)[:, :, 3]

    # 2️⃣ InSPyReNet (optional union)
    try:
        inspyre_result = process_with_inspyrenet(image)
        inspyre_alpha = np.array(inspyre_result)[:, :, 3]
        combined_alpha = np.maximum(ormbg_alpha, inspyre_alpha)
        logger.info("Hybrid Matting: Combined ORMBG + InSPyReNet")
    except Exception as e:
        logger.warning(f"InSPyReNet fallback: {e}")
        combined_alpha = ormbg_alpha

    # 3️⃣ Remove noise islands
    combined_alpha = get_largest_component_mask(combined_alpha)

    # 4️⃣ Build Trimap
    erode_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dilate_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))

    fg_mask = cv2.erode(combined_alpha, erode_kernel, iterations=1)
    bg_mask = cv2.dilate(combined_alpha, dilate_kernel, iterations=1)

    trimap = np.full_like(combined_alpha, 128)
    trimap[fg_mask > 240] = 255
    trimap[bg_mask < 10] = 0

    trimap_pil = Image.fromarray(trimap)
    image_rgb = image.convert("RGB")

    # 5️⃣ FBA Matting
    fba_model = get_fba_model()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    if device == "cuda":
        fba_model.to(device)

    try:
        matte_result = fba_model([image_rgb], [trimap_pil])[0]

        # =========================
        # 🔥 SHARP EDGE REFINEMENT
        # =========================

        alpha = np.array(matte_result).astype(np.float32) / 255.0
        rgb = np.array(image_rgb).astype(np.float32) / 255.0

        # ---- 1️⃣ Detect REAL image edges ----
        gray = cv2.cvtColor((rgb * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 80, 160)
        edges = edges.astype(np.float32) / 255.0

        edge_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        edges = cv2.dilate(edges, edge_kernel, iterations=1)

        # ---- 2️⃣ Edge-locked sharpening ----
        laplacian = cv2.Laplacian(alpha.astype(np.float32), cv2.CV_32F)
        alpha = alpha - 0.22 * laplacian * edges
        alpha = np.clip(alpha, 0.0, 1.0)

        # ---- 3️⃣ Snap strong areas ----
        alpha[alpha > 0.93] = 1.0
        alpha[alpha < 0.015] = 0.0

        # ---- 4️⃣ Preserve hair gradients (no blur) ----
        hair_zone = (alpha > 0.08) & (alpha < 0.9)
        alpha[hair_zone] = np.power(alpha[hair_zone], 0.85)

        alpha = color_consistency_refinement(alpha, rgb)
        alpha = grabcut_refinement((rgb * 255.0).astype(np.uint8), alpha)
        alpha = edge_boundary_refinement((rgb * 255.0).astype(np.uint8), alpha)
        alpha = alpha_boundary_clamp(alpha)

        alpha[alpha < 0.25] = 0.0
        alpha_uint8 = (alpha * 255).astype(np.uint8)
        alpha_uint8 = get_largest_component_mask(alpha_uint8)

        # ---- 6️⃣ Composite ----
        result = Image.fromarray((rgb * 255).astype(np.uint8)).convert("RGBA")
        result.putalpha(Image.fromarray(alpha_uint8))

        return result

    finally:
        if device == "cuda":
            fba_model.to("cpu")
            torch.cuda.empty_cache()


def process_with_carvekit(image, model="u2net"):
    interface = get_carvekit_model(model)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    if device == "cuda":
        interface.segmentation_pipeline.to("cuda")

    processed_image = interface([image])[0]

    if device == "cuda":
        interface.segmentation_pipeline.to("cpu")
        torch.cuda.empty_cache()

    return processed_image
