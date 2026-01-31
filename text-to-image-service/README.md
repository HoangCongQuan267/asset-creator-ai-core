# Asset Creator AI Core - Text to Image Service

This service provides a high-quality, optimized pipeline for generating game assets using **SDXL-Lightning**. It is designed to run efficiently on **Mac (M1/M2/M3)** and **AWS Servers (NVIDIA GPUs)**.

## 📂 Directory Structure

```
text-to-image-service/
├── main.py               # Main generation script
├── download_models.sh    # Script to download essential models
├── models/               # Place your local models here
│   ├── checkpoints/      # Main Models (SDXL .safetensors from Civitai/HF)
│   ├── loras/            # LoRA weights (Styles, Characters, Items)
│   └── vae/              # Custom VAEs (Color fixers)
└── outputs/              # Generated images will be saved here
```

---

## 💻 Installation Guide

### Prerequisites

- Python 3.10+
- `git`

### 1. Mac Setup (Apple Silicon - M1/M2/M3)

**Target: Metal Performance Shaders (MPS)**

1.  Create and activate a virtual environment:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  Install dependencies (PyTorch with MPS support):
    ```bash
    pip install torch torchvision torchaudio
    pip install diffusers transformers accelerate controlnet_aux peft compel safetensors huggingface_hub
    ```

### 2. AWS Server Setup (NVIDIA GPU - G4dn/G5)

**Target: CUDA**

1.  Update system and install Python 3.10 venv:

    ```bash
    sudo apt update
    sudo apt install python3.10-venv -y
    ```

2.  Create and activate a virtual environment:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  Install dependencies (PyTorch with CUDA support):
    ```bash
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    pip install diffusers transformers accelerate controlnet_aux peft compel safetensors huggingface_hub xformers
    ```
    _(Note: `xformers` is highly recommended for NVIDIA GPUs for speed)._

---

## 📥 Downloading & Installing Models

To generate unique game styles (pixel art, anime, realism), you need:

- A base SDXL checkpoint (the main diffusion model).
- Optional LoRA weights (styles, characters, items).

### 1. Automatic Download (Recommended)

We provide a helper script to download commonly used assets (VAE + example LoRA):

```bash
cd text-to-image-service
chmod +x download_models.sh
./download_models.sh
```

This script will populate:

- `models/vae/sdxl-vae-fp16-fix/` – recommended VAE for SDXL.
- `models/loras/StickersRedmond.safetensors` – example style LoRA.

### 2. Base Checkpoints (SDXL)

By default, the Python pipeline uses:

- `stabilityai/stable-diffusion-xl-base-1.0` as the base model.
- `ByteDance/SDXL-Lightning` as the LoRA repo with `sdxl_lightning_4step_lora.safetensors`.

You can keep this online-only (Hugging Face will cache weights), or download a local copy:

```bash
cd text-to-image-service/models/checkpoints
git lfs install
git clone https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0 my_sdxl_base
```

Then run the generator pointing at the local directory:

```bash
cd text-to-image-service
python3 main.py --base-model models/checkpoints/my_sdxl_base
```

### 3. LoRAs (Styles / Characters)

On AWS, you often cannot browse. Use `wget` or `curl` to grab LoRAs directly from Civitai or Hugging Face.

#### Option A: LoRAs from HuggingFace

Example: Download SDXL-Lightning LoRA weights locally (optional, for offline use):

```bash
cd text-to-image-service/models/loras
wget https://huggingface.co/ByteDance/SDXL-Lightning/resolve/main/sdxl_lightning_4step_lora.safetensors
```

Then run:

```bash
cd text-to-image-service
python3 main.py \
  --lora models/loras/sdxl_lightning_4step_lora.safetensors
```

#### Option B: LoRAs / Checkpoints from Civitai

Go to Civitai on your PC, right-click the "Download" button, and copy the link.

```bash
# Example: Downloading a LoRA style
cd text-to-image-service/models/loras

# Use -O to specify the filename (important for Civitai links)
wget -O line_art_style.safetensors "https://civitai.com/api/download/models/XXXXXX"
```

You can then reference this LoRA in the pipeline:

```bash
cd text-to-image-service
python3 main.py --lora models/loras/line_art_style.safetensors
```

---

## 🚀 Usage

### Running the Generator

1.  Navigate to the directory:

    ```bash
    cd text-to-image-service
    ```

2.  Run the script:

    ```bash
    # Generic entrypoint (auto device)
    python3 main.py

    # Mac-specific entrypoint (prefers MPS)
    python3 main_mac.py

    # AWS-specific entrypoint (prefers CUDA)
    python3 main_aws.py
    ```

3.  Follow the prompts:
    - Positive Prompt: Describe your asset.
    - Negative Prompt: Press Enter for defaults.

4.  Result: Check `outputs/` folder.

### Choosing Model Checkpoints (ComfyUI-style)

The Python pipeline lets you control which checkpoint and LoRA are used, similar to ComfyUI.

Key flags:

- `--base-model`: base checkpoint (Hugging Face model id or local directory).
- `--lora`: LoRA to apply (Hugging Face repo, directory, or `.safetensors` file).
- `--lora-weight`: filename of the LoRA weight when using a repo or directory.

Defaults (if you do nothing):

- Base model: `stabilityai/stable-diffusion-xl-base-1.0`
- LoRA: `ByteDance/SDXL-Lightning`
- LoRA weight: `sdxl_lightning_4step_lora.safetensors`

Examples:

```bash
# 1. Default base model + SDXL-Lightning LoRA (online)
python3 main.py

# 2. Use a local base checkpoint directory
python3 main.py --base-model models/checkpoints/my_sdxl_base

# 3. Use a specific style LoRA from Civitai
python3 main.py --lora models/loras/line_art_style.safetensors

# 4. Disable LoRA entirely (pure base model)
python3 main.py --lora none
```

You can also control defaults via environment variables:

- `ASSET_TTI_BASE_MODEL`
- `ASSET_TTI_LORA`
- `ASSET_TTI_LORA_WEIGHT`
- `ASSET_TTI_HEIGHT`, `ASSET_TTI_WIDTH`, `ASSET_TTI_STEPS`, `ASSET_TTI_GUIDANCE`

### Mac vs AWS: Example Commands

Mac (M1/M2/M3, MPS):

```bash
python3 main_mac.py
```

AWS (G4dn/G5, CUDA):

```bash
python3 main_aws.py
```

The script will:

- Prefer CUDA on AWS when available.
- Prefer MPS on Apple Silicon when CUDA is not present.
- Fall back to CPU otherwise.

### ⚡ SDXL-Lightning (Fast Generation)

This tool is optimized for SDXL-Lightning (4-step) on top of SDXL.

- Speed: Generates 1024x1024 images in seconds.
- Quality: Comparable to full SDXL but much faster.
- Offline Mode: Clone the base SDXL model into `models/checkpoints/` and optionally download the SDXL-Lightning LoRA into `models/loras/`, then point `--base-model` and `--lora` at those paths.

---

## 🔧 Troubleshooting

**Mac (MPS) Issues:**

- If you see "Out of Memory", ensure other heavy apps are closed. The script uses `enable_model_cpu_offload()` to fit SDXL into 8GB/16GB RAM.

**AWS Issues:**

- If CUDA is not found, verify NVIDIA drivers are installed: `nvidia-smi`.
