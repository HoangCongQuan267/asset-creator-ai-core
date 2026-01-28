# Export to Real Game Engines

This final stage ensures that all generated assets are formatted correctly for integration into major game engines.

## 🎮 Supported Formats

| Engine            | Primary Format            | Notes                                                    |
| ----------------- | ------------------------- | -------------------------------------------------------- |
| **Unity**         | **FBX** (Preferred), GLTF | Standard pipeline uses FBX; GLTF supported via packages. |
| **Unreal Engine** | **FBX**                   | Industry standard for UE5 character pipelines.           |
| **Godot**         | **GLTF** (Preferred)      | First-class support for GLTF 2.0.                        |

## ✅ Production Guarantees

Our pipeline ensures the following deliverables:

1. **Clean Topology**: Quads/tris optimized for deformation; no N-gons.
2. **Single Skeleton**: A unified armature hierarchy (root bone at 0,0,0).
3. **Animation Clips**: Baked actions (Idle, Walk, Run, Attack) embedded in the file or as separate animation files.
4. **PBR Textures**: Albedo, Normal, Roughness, and Metallic maps properly assigned or packed.

---

## 💻 Setup Guide

### 1. Mac M2 Pro & AWS Server

_Target: Blender (CLI)_

The export process is primarily driven by Blender's Python API, which works identically on both Mac and Linux servers.

**Requirements:**

- Blender 3.6+ (for best GLTF/FBX support).
- `bpy` script (see below).

---

## 🚀 Export Script Example (Blender)

This script automates the final verification and export for different engines.

```python
import bpy

def verify_scene():
    # 1. Check for single armature
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
    if len(armatures) != 1:
        print("WARNING: Scene should have exactly one armature.")

    # 2. Check scale (Apply transforms)
    for obj in bpy.context.scene.objects:
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        obj.select_set(False)

def export_for_unity(filepath):
    # Unity uses Y-Up, Z-Forward usually handled by exporter settings
    bpy.ops.export_scene.fbx(
        filepath=filepath,
        use_selection=False,
        axis_forward='-Z',
        axis_up='Y',
        bake_anim=True,
        object_types={'ARMATURE', 'MESH'},
        apply_scale_options='FBX_SCALE_UNITS'
    )

def export_for_unreal(filepath):
    # Unreal typically expects X-Forward, Z-Up or standard FBX with specific axis settings
    bpy.ops.export_scene.fbx(
        filepath=filepath,
        use_selection=False,
        axis_forward='-Z',
        axis_up='Y', # Blender exporter handles conversion
        bake_anim=True,
        add_leaf_bones=False, # Important for UE
        object_types={'ARMATURE', 'MESH'}
    )

def export_for_godot(filepath):
    # Godot loves GLTF
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format='GLB',
        use_selection=False,
        export_yup=True
    )

# --- Execution ---
verify_scene()

# Example: Export for all
export_for_unity("output_unity.fbx")
export_for_unreal("output_unreal.fbx")
export_for_godot("output_godot.glb")
```

**Run Command:**

```bash
blender -b input_scene.blend -P export_script.py
```
