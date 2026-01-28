# Retopology & Remeshing Service

This service handles the critical step of converting raw, high-poly meshes (from Image → 3D steps) into clean, game-ready assets.

## 🛠 Tools Overview

| Tool | Use Case | Notes |
|------|----------|-------|
| **Blender (Python API)** | **Main Pipeline** | Scriptable headless automation |
| **Instant Meshes** | Free Retopology | Good for organic shapes |
| **OpenVDB** | Voxel Remesh | Robust for fixing holes/non-manifold geometry |
| **Quad Remesher** | Optional | Paid plugin, currently skipped |

## ⚙️ Blender Automation Pipeline

We rely on `bpy` (Blender Python) to script the following operations:
1. **Decimate**: Reduce poly count while preserving silhouette.
2. **Remesh**: Create uniform topology (Voxel/Quadriflow).
3. **Clean Normals**: Fix smooth/flat shading artifacts.
4. **UV Unwrap**: Automatically generate UV maps for texturing.

---

## 💻 Setup Guide

### 1. Mac M2 Pro (16GB RAM)
*Target: Blender Metal Backend*

MacOS users should install the standard Blender application to get the full `bpy` environment, or use the `bpy` pip package (experimental). **Recommendation:** Use Blender's bundled python.

1. **Install Blender**: Download [Blender for Apple Silicon](https://www.blender.org/download/).
2. **Alias Blender**: Add to your path for CLI access.
   ```bash
   echo 'alias blender="/Applications/Blender.app/Contents/MacOS/Blender"' >> ~/.zshrc
   source ~/.zshrc
   ```
3. **Install Instant Meshes** (Optional helper):
   ```bash
   brew install instant-meshes
   ```

### 2. AWS Server (Headless Linux)
*Target: CPU / CUDA (Cycles)*

For servers, we run Blender in background mode (`-b`).

1. **Install Blender (Headless)**:
   ```bash
   sudo apt-get update
   sudo apt-get install blender
   # Or download specific version tarball from blender.org for latest features
   ```
2. **Install Instant Meshes (Headless)**:
   *Note: Instant Meshes is GUI-first, but has a CLI mode. You may need to compile from source or find a binary.*

---

## 🚀 Usage Example (Blender Script)

Save this as `process_mesh.py`.

```python
import bpy
import sys

# Clear existing scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Import Mesh (Argument handling would go here)
input_path = "raw_model.obj"
bpy.ops.import_scene.obj(filepath=input_path)
obj = bpy.context.selected_objects[0]
bpy.context.view_layer.objects.active = obj

# 1. Remesh (Voxel)
modifier = obj.modifiers.new(name="Remesh", type='REMESH')
modifier.mode = 'VOXEL'
modifier.voxel_size = 0.05  # Adjust based on scale
bpy.ops.object.modifier_apply(modifier="Remesh")

# 2. Decimate (Reduce Poly Count)
modifier = obj.modifiers.new(name="Decimate", type='DECIMATE')
modifier.ratio = 0.1  # Keep 10% of faces
bpy.ops.object.modifier_apply(modifier="Decimate")

# 3. UV Unwrap (Smart Project)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')

# Export
output_path = "clean_asset.fbx"
bpy.ops.export_scene.fbx(filepath=output_path, use_selection=True)
```

**Run Command:**
```bash
blender -b -P process_mesh.py
```
