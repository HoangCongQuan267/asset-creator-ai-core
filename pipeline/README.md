# End-to-End Asset Generation Pipeline

This document outlines the master architecture that connects all individual micro-services into a unified solution for converting **Text → Game Assets**.

The system is designed to handle multiple asset types:

- **3D Characters & Creatures** (Text → Image → 3D → Rig → Anim)
- **2D Sprites & UI** (Text → Image → Cleanup → Anim)
- **Backgrounds & Effects** (Text → Image → Cleanup)

---

## 📝 Standardized User Input Schema (JSON)

To ensure high-quality results, the system expects structured input rather than just a raw text string.

```json
{
  "project_id": "uuid-1234",
  "asset_type": "3D_CHARACTER", // Options: 3D_CHARACTER, 2D_SPRITE, BACKGROUND, PROP
  "prompt": {
    "core_concept": "A cyberpunk street samurai",
    "style": "Stylized, Overwatch-like, vibrant colors",
    "details": "Neon katana, robotic left arm, wearing a trench coat"
  },
  "constraints": {
    "poly_count_budget": 15000,
    "platform": "MOBILE", // Options: MOBILE, PC, CONSOLE
    "rig_type": "HUMANOID" // Options: HUMANOID, QUADRUPED, STATIC
  },
  "reference_image_url": "optional_url_to_match_style.png"
}
```

---

## 🏗 Architecture Overview

The pipeline operates as a directed acyclic graph (DAG), starting from the **Studio UI** which injects creative context.

```mermaid
graph TD
    subgraph "Frontend Layer"
        UI[Studio UI (Next.js)] -->|Project Context + User Input| API[API Gateway]
    end

    API --> Validation[Input Validator]
    Validation --> Service1[Text-to-Image Service]

    subgraph "Quality Enhancement Loop"
        Service1 --> Upscale[Upscaler (RealESRGAN)]
        Upscale --> Refine[Detail Refiner (Img2Img)]
    end

    subgraph "2D Pipeline"
        Refine --> Service2[Image-to-2D-Assets & Animation]
        Service2 --> Export2D[Export (Sprite/JSON)]
    end

    subgraph "3D Pipeline"
        Refine --> Service3[Image-to-3D-Model]
        Service3 --> Service4[Retopology & Remeshing]
        Service4 --> Service5[Rigging Service]
        Service5 --> Service6[3D Animation Generation]
        Service6 --> Export3D[Export (FBX/GLTF)]
    end

    Export2D --> CDN[CloudFront CDN]
    Export3D --> CDN
    CDN --> UI
```

---

## 💎 Quality Enhancement Steps (Intermediary Processes)

To bridge the gap between "AI generated" and "Production Ready", we inject specific enhancement steps between major services.

### 1. Pre-Processing (Prompt Engineering)

- **Automatic Expansion**: Convert simple user prompts ("cool robot") into engineer-tuned prompts ("A high-fidelity sci-fi robot, metallic texture, octane render, 8k, unreal engine 5 style") using an LLM (GPT-4o/Claude).
- **Negative Prompt Injection**: Automatically inject anti-artifacts terms ("bad anatomy, blurred, watermark, extra limbs").

### 2. Image Refinement (Post-Generation)

- **Upscaling**: Apply **RealESRGAN** to the initial 512x512 or 1024x1024 generation to reach 2048x2048 or 4k textures.
- **Inpainting/Outpainting**: Fix common issues (e.g., cut-off feet or heads) before passing to 3D.
- **Normal Map Generation**: Generate a high-quality normal map from the diffuse texture to add surface detail without extra geometry.

### 3. 3D Geometry Cleanup

- **Manifold Check**: Before rigging, run a "watertight" check. If holes exist, use **OpenVDB** to voxelize and re-mesh automatically.
- **Symmetry Enforcer**: For characters, force X-axis symmetry on the mesh to ensure rigging works correctly.

---

## 🔗 Service Integration

### 0. [Studio UI (Creative Context)](../ui/README.md)

_The Driver_

- **Role**: Captures "Style DNA" and "World Context" to guide generation.
- **Output**: JSON Payload with prompt + style embeddings + constraints.

### 1. [Text-to-Image Service](../text-to-image-service/README.md)

_The Foundation_

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
