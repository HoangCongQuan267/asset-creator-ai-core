# Animation Generation (3D)

This service focuses on generating and applying 3D motions to rigged characters using AI models and standard retargeting tools.

## 🏃 Models (Free)

| Model                            | Use Case                    | Notes                                                                   |
| -------------------------------- | --------------------------- | ----------------------------------------------------------------------- |
| **Motion Diffusion Model (MDM)** | **Text → Motion**           | Generate diverse actions from descriptions (e.g., "person walking sad") |
| **MoDi**                         | **Unconditional / Diverse** | High-quality motion synthesis                                           |
| **Mixamo-like Datasets**         | **Base Motions**            | Pre-recorded motion capture libraries                                   |

## 🛠 Libraries

- **Blender (bpy)**: Retargeting, cleanup, and export.
- **PyTorch3D**: 3D data processing and visualization.
- **retarget-bvh**: Tooling for transferring motion between skeletons.

---

## 💻 Setup Guide

### 1. Mac M2 Pro (16GB RAM)

_Target: CPU / MPS_

Motion generation models are often lighter than image models but require specific PyTorch3D builds.

```bash
# 1. Create Environment
conda create -n animation python=3.9
conda activate animation

# 2. Install PyTorch (MPS)
pip install torch torchvision torchaudio

# 3. Install PyTorch3D (Mac Silicon can be tricky, install from source or specific wheel)
# Recommend installing via conda-forge if available, or building from source:
pip install "git+https://github.com/facebookresearch/pytorch3d.git"

# 4. Install other dependencies
pip install clip transformers smplx
```

### 2. AWS Server (NVIDIA GPU)

_Target: CUDA_

```bash
# 1. Create Environment
conda create -n animation python=3.9
conda activate animation

# 2. Install PyTorch (CUDA)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 3. Install PyTorch3D
pip install "git+https://github.com/facebookresearch/pytorch3d.git"

# 4. Install dependencies
pip install clip transformers smplx
```

---

## 🔄 Pipeline Flow

1. **Rigged Model**: Start with a character (FBX/GLB) with a standard skeleton (e.g., Mixamo, Rigify).
2. **Motion Generation**: Use MDM to generate a motion sequence (usually SMPL format or raw joint rotations).
3. **Retargeting**: Map the generated motion onto the target character's skeleton.
4. **Cleanup**: Loop the animation and fix foot sliding in Blender.
5. **Export**: Final animated mesh in FBX or GLTF.

## 🚀 Usage Example (Blender Retargeting Snippet)

This script (pseudo-code) outlines how to apply a BVH motion to a target armature in Blender.

```python
import bpy

# Load Target Character
bpy.ops.import_scene.fbx(filepath="rigged_character.fbx")
target_rig = bpy.context.selected_objects[0]

# Load Generated Motion (BVH)
bpy.ops.import_anim.bvh(filepath="generated_motion.bvh")
source_rig = bpy.context.selected_objects[0]

# Retargeting Logic (Simplified)
# In production, use an addon like Rokoko or a custom retargeting library
# Here we map bone names conceptually
bone_map = {
    "mixamorig:Hips": "Hips",
    "mixamorig:Spine": "Spine",
    # ...
}

# Apply rotation from source to target frame-by-frame
start_frame = 1
end_frame = 60
bpy.context.scene.frame_start = start_frame
bpy.context.scene.frame_end = end_frame

for frame in range(start_frame, end_frame + 1):
    bpy.context.scene.frame_set(frame)
    for src_bone, tgt_bone in bone_map.items():
        # Get source rotation
        # Apply to target bone (considering rest pose differences)
        pass

    # Keyframe target
    bpy.ops.anim.keyframe_insert_menu(type='Rotation')

# Export
bpy.ops.export_scene.fbx(filepath="animated_character.fbx", bake_anim=True)
```
