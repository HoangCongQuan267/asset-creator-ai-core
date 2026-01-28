# Image → 2D Assets + Animation

This guide covers turning a single generated image into production-ready **2D assets** and **animations** suitable for game engines.

## Static 2D Asset

- Use SDXL output directly for high-quality base images.
- Optional cleanup:
  - **Segment Anything (SAM)** – auto segmentation/cutout for precise masks.
  - **rembg** – fast background removal.

### Quick setup (cleanup tools)

```bash
pip install rembg
# rembg CLI example:
rembg i input.png output.png

# SAM typical setup (community implementation):
pip install segment-anything opencv-python torch torchvision
# You will need to download a SAM checkpoint (e.g., sam_vit_h.pth) from the official repo.
```

### Environment Setup (Local Mac M2 Pro 16GB vs AWS Server)

- Mac M2 Pro (Apple Silicon, 16GB RAM)
  - Acceleration: MPS
  - Recommended installs:
    ```bash
    # Core
    pip install torch torchvision torchaudio
    pip install diffusers transformers accelerate
    # Asset tools
    pip install rembg segment-anything opencv-python
    # Optional: lipsync and motion
    pip install ffmpeg-python  # requires system ffmpeg installed
    ```
  - Device selection in Python:
    ```python
    import torch
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    ```
  - Tips: Prefer `enable_model_cpu_offload()` for large models; keep image sizes moderate when segmenting.

- AWS Server (NVIDIA GPU, e.g., G4dn T4)
  - Acceleration: CUDA
  - Recommended installs:
    ```bash
    # Core (adjust cu version if needed per PyTorch site)
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    pip install diffusers transformers accelerate xformers
    # Asset tools
    pip install rembg segment-anything opencv-python
    # Optional: lipsync and motion
    sudo apt-get update && sudo apt-get install -y ffmpeg
    ```
  - Device selection in Python:
    ```python
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    ```
  - Tips: Use `xformers` to reduce VRAM use for motion models; set `torch_dtype=torch.float16` where supported.

---

## 2D Animation (VERY IMPORTANT)

### Tools & Libraries

- Bone-based animation:
  - **Spine Runtime (export only)** – industry standard; use Spine editor to rig and export.
  - **DragonBones (open)** – free alternative with editor and runtime support.
- AI motion:
  - **AnimateDiff** – generate motion sequences from stills; useful for stylized loops.
- Auto lipsync:
  - **Wav2Lip** – automatic mouth movement synced to audio.

### Flow

- Image
  → Auto segmentation
  → Auto bone placement
  → Keyframe / loop animation
  → Export (sprite sheet / skeletal)

### Export Formats

- Unity: Sprite Sheet / Spine JSON
- Godot: AnimatedSprite / Skeleton2D

✅ Used in real games

---

## Practical Notes

- For SDXL outputs, prefer clean silhouettes and separated layers to simplify rigging.
- SAM helps isolate limbs/props; combine with manual cleanup where needed.
- Spine/DragonBones skeletons benefit from consistent pivot points and layer naming.
- AnimateDiff works best for short loops (idle, breathing, flicker effects) to augment classic bones.
- Wav2Lip integrates with pre-rendered face sprites or layered head rigs.

---

## Minimal Pipeline Example

1. Generate final image (from SDXL).
2. Run rembg to remove background.
3. Use SAM to segment parts and create masks.
4. Import into Spine/DragonBones, place bones, and bind parts.
5. Create idle/loop animations; export:
   - Spine JSON (skeletal) or
   - Sprite sheet (raster).
6. Integrate into Unity (Animator/Spine Runtime) or Godot (AnimatedSprite/Skeleton2D).
