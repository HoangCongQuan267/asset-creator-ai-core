# End-to-End Asset Generation Pipeline

This document outlines the master architecture that connects all individual micro-services into a unified solution for converting **Text → Game Assets**.

The system is designed to handle multiple asset types:
- **3D Characters & Creatures** (Text → Image → 3D → Rig → Anim)
- **2D Sprites & UI** (Text → Image → Cleanup → Anim)
- **Backgrounds & Effects** (Text → Image → Cleanup)

---

## 🏗 Architecture Overview

The pipeline operates as a directed acyclic graph (DAG), where the output of one service feeds into the next.

```mermaid
graph TD
    User[User Input (Text/Prompt)] --> Service1[Text-to-Image Service]
    
    subgraph "2D Pipeline"
        Service1 --> Service2[Image-to-2D-Assets & Animation]
        Service2 --> Export2D[Export (Sprite/JSON)]
    end
    
    subgraph "3D Pipeline"
        Service1 --> Service3[Image-to-3D-Model]
        Service3 --> Service4[Retopology & Remeshing]
        Service4 --> Service5[Rigging Service]
        Service5 --> Service6[3D Animation Generation]
        Service6 --> Export3D[Export (FBX/GLTF)]
    end
    
    Export2D --> GameEngine[Game Engine (Unity/Unreal/Godot)]
    Export3D --> GameEngine
```

---

## 🔗 Service Integration

### 1. [Text-to-Image Service](../text-to-image-service/README.md)
*The Foundation*
- **Input**: Text Prompt
- **Output**: High-res 2D Image
- **Role**: Generates the visual concept for characters, props, or backgrounds.

### 2. Branching Logic

#### A. For 2D Assets
**Service**: [Image-to-2D-Assets & Animation](../image-to-2d-assets-animation-service/README.md)
- **Input**: Generated Image
- **Steps**: Segmentation (SAM) → Background Removal → Bone Placement → Animation.
- **Output**: Sprite Sheets, Spine JSON.

#### B. For 3D Assets
**Step 1: Generation**
**Service**: [Image-to-3D-Model](../image-to-3d-model-generation-service/README.md)
- **Input**: Generated Image (Single/Multi-view)
- **Output**: Raw Mesh (TripoSR/Zero123++).

**Step 2: Cleanup**
**Service**: [Retopology & Remeshing](../retopology-service/README.md)
- **Input**: Raw Mesh
- **Output**: Clean Topology Mesh + UVs.

**Step 3: Rigging**
**Service**: [Rigging Service](../rigging-service/README.md)
- **Input**: Clean Mesh
- **Output**: Rigged Character (Skeleton + Weights).

**Step 4: Animation**
**Service**: [Animation Generation (3D)](../animation-3d-service/README.md)
- **Input**: Rigged Character + Motion Prompt
- **Output**: Animated Character.

### 3. Final Delivery
**Service**: [Export to Real Game Engines](../export-service/README.md)
- **Input**: Final 2D or 3D Asset
- **Output**: Engine-ready files (FBX, GLTF, PBR Textures).

---

## 🚀 Orchestration (Example)

A master Python script (`pipeline_orchestrator.py`) would manage data flow between services.

```python
# Conceptual Orchestrator
class AssetPipeline:
    def create_3d_character(self, prompt):
        # 1. Generate Concept
        image_path = text_to_image.generate(prompt)
        
        # 2. Generate 3D Base
        raw_mesh = image_to_3d.generate(image_path)
        
        # 3. Clean & Retopo
        clean_mesh = retopology.process(raw_mesh)
        
        # 4. Rig
        rigged_char = rigging.auto_rig(clean_mesh)
        
        # 5. Animate (Optional)
        final_asset = animation.apply_motion(rigged_char, "idle_breath")
        
        # 6. Export
        export.save(final_asset, format="fbx")
        
        return final_asset
```

## 🛠 Infrastructure Requirements

- **Orchestrator**: Python (Local or Serverless Lambda/Queue worker).
- **Storage**: Shared volume or S3 bucket to pass intermediate files (images, obj, fbx) between steps.
- **Compute**:
    - **GPU Nodes**: Text-to-Image, Image-to-3D, RigNet, Animation Gen.
    - **CPU Nodes**: Blender Automation (Retopo, Export), File I/O.
