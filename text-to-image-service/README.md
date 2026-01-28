# Asset Creator AI Core - Text to Image Setup

This guide focuses on setting up the foundational **Text → Image** generation pipeline. It covers the installation and usage of key models like Stable Diffusion XL (SDXL), Kandinsky 2.2, and OpenJourney, tailored for both **Mac M2 (Apple Silicon)** and **AWS G4dn** instances.

## 🎨 Models Overview

These models serve as the foundation for generating game assets (characters, props, backgrounds).

| Model                          | Use Case           | Key Features                                                                                                              |
| ------------------------------ | ------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| **Stable Diffusion XL (SDXL)** | High quality base  | • Production safe for game pipelines<br>• Works for characters, props, backgrounds<br>• Huge ecosystem (LoRA, ControlNet) |
| **Kandinsky 2.2**              | Strong composition | • Excellent at complex scenes and mixing concepts                                                                         |
| **OpenJourney**                | Stylized assets    | • Midjourney-style aesthetics                                                                                             |
| **ControlNet**                 | Precision control  | • Control pose, depth, and line art of generation                                                                         |

## 🛠 Libraries

We utilize the Hugging Face ecosystem:

- **`diffusers`**: The core library for state-of-the-art diffusion models.
- **`transformers`**: Required for the text encoders (CLIP, T5).
- **`accelerate`**: Optimizes training and inference (essential for offloading and mixed precision).
- **`controlnet_aux`**: Helper processors for ControlNet (e.g., extracting canny edges).

---

## 💻 Setup Guide

### Prerequisites

- Python 3.10+ recommended.
- A virtual environment is highly suggested.

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 1. Installation: Mac M2 (16GB RAM)

_Target: Metal Performance Shaders (MPS)_

Apple Silicon Macs use the `mps` device for acceleration. 16GB RAM is sufficient for SDXL with some optimizations.

```bash
# Install PyTorch with MPS support
pip install torch torchvision torchaudio

# Install diffusion libraries
pip install diffusers transformers accelerate controlnet_aux peft
```

**Optimization Tip for Mac M2:**
SDXL is large. To avoid out-of-memory errors on 16GB RAM, use `enable_model_cpu_offload()` in your code (see Usage examples).

### 2. Installation: AWS G4dn (NVIDIA T4)

_Target: CUDA_

G4dn instances typically come with NVIDIA T4 GPUs (16GB VRAM).

```bash
# Install PyTorch with CUDA support (check pytorch.org for the latest command)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install diffusion libraries
pip install diffusers transformers accelerate controlnet_aux peft xformers
```

_Note: `xformers` is recommended for NVIDIA GPUs to speed up attention and reduce memory usage._

---

## 🚀 Usage Examples

### Loading SDXL (Base + Refiner)

This script works on both Mac (MPS) and NVIDIA (CUDA) by detecting the device.

```python
import torch
from diffusers import DiffusionPipeline

# Device selection
device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device != "cpu" else torch.float32

print(f"Running on {device} with {dtype}")

# Load SDXL Base
base = DiffusionPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=dtype,
    variant="fp16",
    use_safetensors=True
)

# Optimization: Offload to CPU when not in use (Crucial for Mac M2 16GB)
base.enable_model_cpu_offload()
# base.to(device) # Use this instead of cpu_offload if you have massive VRAM (A100)

# Generate
prompt = "A cinematic shot of a cyberpunk street food vendor, neon lights, highly detailed, 8k"
image = base(prompt=prompt).images[0]
image.save("generated_asset.png")
```

### Why SDXL?

- **Versatility**: Capable of generating consistent characters and diverse props.
- **Ecosystem**: Extensive library of fine-tuned models and LoRAs available on Civitai and Hugging Face.
- **Production Ready**: High resolution native output (1024x1024) reduces the need for heavy upscaling steps immediately.

### Using ControlNet

ControlNet allows you to guide the generation using input images (e.g., posing a character).

```python
from diffusers import StableDiffusionXLControlNetPipeline, ControlNetModel, AutoencoderKL
from diffusers.utils import load_image
import numpy as np
import cv2

# Load ControlNet (e.g., Canny for edge detection)
controlnet = ControlNetModel.from_pretrained(
    "diffusers/controlnet-canny-sdxl-1.0",
    torch_dtype=torch.float16
)

pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    controlnet=controlnet,
    torch_dtype=torch.float16,
)
pipe.enable_model_cpu_offload()

# Prepare your control image (canny edge map) here...
# image = pipe(prompt, image=canny_image).images[0]
```
