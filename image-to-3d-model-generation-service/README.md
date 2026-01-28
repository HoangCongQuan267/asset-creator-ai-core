# Image → 3D Model Generation

This guide covers turning a single image into a rough **3D mesh** using free models and libraries.

## Models (FREE)

| Model             | Notes                        |
| ----------------- | ---------------------------- |
| **Zero123++**     | Multi-view generation        |
| **TripoSR**       | Fast single-image to mesh    |
| **DreamGaussian** | High quality reconstructions |
| **Shap-E**        | Text → 3D baseline           |

## Libraries

- **TripoSR** (Stability AI / Tripo AI)
- **pytorch**
- **open3d**
- **trimesh**

### Setup Guide

TripoSR requires specific dependencies.

#### 1. Mac M2 Pro (16GB RAM)

_Target: CPU / MPS (Partial Support)_

TripoSR relies on `transformers` and `torch`. While inference can run on CPU/MPS, some custom CUDA kernels (like those in `tsr`) might need CPU fallbacks or specific builds.

```bash
# 1. Install PyTorch (MPS support)
pip install torch torchvision torchaudio

# 2. Install TripoSR dependencies
pip install --upgrade transformers diffusers rembg trimesh open3d
pip install einops omegaconf timm

# 3. Clone TripoSR (if running from source)
git clone https://github.com/VAST-AI-Research/TripoSR.git
cd TripoSR
pip install -r requirements.txt
```

_Note: On Mac, if you encounter issues with CUDA-only operators, force execution on CPU for the geometry extraction step._

#### 2. AWS Server (NVIDIA GPU)

_Target: CUDA_

Standard setup for NVIDIA GPUs.

```bash
# 1. Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 2. Install TripoSR dependencies
pip install --upgrade transformers diffusers rembg trimesh open3d
pip install einops omegaconf timm

# 3. Clone TripoSR
git clone https://github.com/VAST-AI-Research/TripoSR.git
cd TripoSR
pip install -r requirements.txt
```

## Output

- Raw mesh (GLB/OBJ)
- ⚠️ Not production ready yet → next step fixes this

## Minimal Flow (TripoSR)

1. **Preprocess**: Remove background from input image (rembg).
2. **Inference**: Run TripoSR to generate 3D representation (NeRF/Tri-plane).
3. **Extraction**: Extract mesh using Marching Cubes.
4. **Export**: Save as .glb or .obj.
5. **Next Step**: Retopology/Cleanup.

### Usage Example

```python
import torch
from transformers import AutoModel, AutoTokenizer
# Pseudo-code for TripoSR usage flow
# See official repo for full inference script

# Load model
model = AutoModel.from_pretrained("stabilityai/TripoSR", trust_remote_code=True)
if torch.cuda.is_available():
    model.to("cuda")
# On Mac M2, you might keep it on CPU if MPS ops are missing
# model.to("cpu")

# ... (Image loading and processing)
# mesh = model.generate(image)
# mesh.export("output.obj")
```
