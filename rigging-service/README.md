# Rigging Service

This service automates the rigging process for 3D models, transforming static meshes into animatable characters and creatures.

## 🦴 Rigging Workflows

### 1. Humanoid Characters

| Task                    | Tool                     | Notes                                 |
| ----------------------- | ------------------------ | ------------------------------------- |
| **Skeleton Generation** | **RigNet**               | AI-driven skeleton prediction         |
| **Weight Painting**     | **Blender Auto Weights** | Voxel-based heat map skinning         |
| **Control Rig**         | **Rigify**               | Standard Blender biped rig generation |

### 2. Non-Humanoid / Creatures

| Task            | Tool                  | Notes                                       |
| --------------- | --------------------- | ------------------------------------------- |
| **Skeleton**    | **Blender Templates** | Predefined metarigs (Bird, Cat, Wolf, etc.) |
| **Auto Weight** | **Blender**           | Standard auto-weighting                     |
| **Adjustments** | **Manual Fallback**   | Scripted bone repositioning                 |

## 🛠 Libraries

- **RigNet**: Deep learning based rigging (requires specific PyTorch setup).
- **Blender Python (`bpy`)**: Core automation for armature creation, parenting, and weight calculation.

---

## 💻 Setup Guide

### 1. Mac M2 Pro (16GB RAM)

_Target: Blender (Metal) + Local Environment_

For RigNet (AI), you likely need a separate Python environment from Blender's internal python.

**Blender Setup:**
Ensure Blender is aliased (see Retopology service guide).

**RigNet Setup (External Python):**
RigNet often has older dependencies. A conda environment is recommended.

```bash
# Example Conda setup
conda create -n rignet python=3.8
conda activate rignet
# Install PyTorch (MPS support if available for older versions, otherwise CPU)
pip install torch torchvision
# Clone and install RigNet dependencies
git clone https://github.com/zhan-xu/RigNet.git
cd RigNet
pip install -r requirements.txt
# Download pre-trained checkpoints as per RigNet docs
```

### 2. AWS Server (Linux / GPU)

_Target: CUDA_

**Blender Setup:**
`sudo apt-get install blender`

**RigNet Setup:**
Standard CUDA setup for faster inference.

```bash
conda create -n rignet python=3.8
conda activate rignet
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
# ... install RigNet dependencies ...
```

---

## 🚀 Automation Flow (Blender Script Example)

This script demonstrates applying a metarig and auto-weighting using `bpy`.

```python
import bpy

# Clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Import Clean Mesh
bpy.ops.import_scene.fbx(filepath="clean_asset.fbx")
char_mesh = bpy.context.selected_objects[0]
bpy.context.view_layer.objects.active = char_mesh

# 2. Add Armature (Rigify Human Metarig)
# Ensure Rigify addon is enabled in Blender preferences
bpy.ops.preferences.addon_enable(module="rigify")
bpy.ops.object.armature_human_metarig_add()
metarig = bpy.context.object

# Scale rig to match character height (Simple bounding box heuristic)
# In a real pipeline, RigNet would give joint positions to snap bones to.
char_height = char_mesh.dimensions.z
rig_height = metarig.dimensions.z
scale_factor = char_height / rig_height
metarig.scale = (scale_factor, scale_factor, scale_factor)
bpy.ops.object.transform_apply(scale=True)

# 3. Generate Rigify Rig
bpy.ops.pose.rigify_generate()
rig = bpy.data.objects["rig"]

# 4. Parent Mesh to Rig with Auto Weights
bpy.ops.object.select_all(action='DESELECT')
char_mesh.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')

# Export
bpy.ops.export_scene.fbx(filepath="rigged_character.fbx", use_selection=True)
```
