from PIL import Image
import io
import shutil
import ssl

# Fix SSL certificate errors on macOS
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

from rembg import remove as rembg_remove, new_session
import time
import numpy as np
import tempfile
import uuid
import os
import subprocess
from transformers import pipeline
from transparent_background import Remover
import logging
import asyncio
from datetime import datetime, timedelta
import torch
from .ormbg import ORMBGProcessor
from typing import Dict
from contextlib import contextmanager

from carvekit.ml.files.models_loc import download_all

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Lazy loading cache
_models = {"bria": None, "inspyrenet": None, "rembg": {}, "ormbg": None, "carvekit": {}}


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


# Processing functions
def process_with_bria(image):
    model = get_bria_model()
    result = model(image, return_mask=True)
    mask = result
    if not isinstance(mask, Image.Image):
        mask = Image.fromarray((mask * 255).astype("uint8"))
    no_bg_image = Image.new("RGBA", image.size, (0, 0, 0, 0))
    no_bg_image.paste(image, mask=mask)
    return no_bg_image


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
