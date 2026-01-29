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

The pipeline operates as a directed acyclic graph (DAG), starting from the **Studio UI** and flowing through the **Backend Orchestrator** which retrieves project data from the database and applies business logic. It includes **Safety Checks** and **Human-in-the-Loop** checkpoints. All requests generate new assets; previously created assets are retrieved from the **Asset Library** and do not re-enter the pipeline. Every major step persists status and metadata to the user's database.

```mermaid
graph TD
    subgraph "Frontend Layer"
        UI[Studio UI (Next.js)] -->|Project Context + User Input| API[API Gateway]
    end

    API --> Backend[Backend Orchestrator]
    Backend --> DB[(User Database)]
    Backend --> Auth[Auth & Quota Check]
    Auth --> Safety[NSFW / Safety Filter]

    Safety --> Service1[Text-to-Image Service]

    subgraph "Quality Enhancement Loop"
        Service1 --> Upscale[Upscaler (RealESRGAN)]
        Upscale --> Refine[Detail Refiner (Img2Img)]
    end

    Refine --> Review1{User Review?}
    Review1 -->|Approve| Branching
    Review1 -->|Reject| Service1
    Backend -->|Persist Step| DB
    Service1 -->|Status + Artifacts| DB
    Refine -->|Status + Artifacts| DB
    Review1 -->|Decision| DB

    subgraph "Branching Logic"
        Branching -->|2D| Service2[Image-to-2D-Assets]
        Branching -->|3D| Service3[Image-to-3D-Model]
    end

    subgraph "3D Pipeline"
        Service3 --> Service4[Retopology & Remeshing]
        Service4 --> Review2{Approve Retopo?}
        Review2 -->|Approve| Service5[Rigging Service]
        Review2 -->|Edit| Service4
        Service5 --> Review3{Approve Rig?}
        Review3 -->|Approve| Service6[3D Animation Generation]
        Review3 -->|Edit| Service5
        Service6 --> Review4{Approve Anim?}
        Review4 -->|Approve| Export3D[Export (FBX/GLTF)]
        Review4 -->|Edit| Service6
    end

    Service2 --> Export2D[Export (Sprite/JSON)]

    Export2D --> Library[Asset Library (Versioned)]
    Export3D --> Library
    Library --> CDN[CloudFront CDN]
    CDN --> UI
    UI -->|Browse / Re-use| Library
    Service3 -->|Status + Artifacts| DB
    Service4 -->|Status + Mesh| DB
    Service5 -->|Status + Rig| DB
    Service6 -->|Status + Anim| DB
    Export2D -->|Index + Metadata| DB
    Export3D -->|Index + Metadata| DB
```

---

## 🛡 Production-Grade Enhancements

To make this system robust for thousands of users, we integrate the following layers:

### 1. Reliability & Safety Layer

- **Content Moderation**: Before any generation, prompts are checked against a safety list. Generated images are scanned for NSFW content using a lightweight classifier.
- **Circuit Breakers**: If a service (e.g., TripoSR) fails > 5 times in 1 minute, the system temporarily switches to a fallback model (e.g., Zero123++) or queues requests.

### Asset Library & Versioning

- **Always-Generate Policy**: Each pipeline request produces a new asset version; no generation is skipped.
- **Library Retrieval**: Old assets are browsed and reused directly from the library; they do not re-enter the pipeline.
- **Version Key**: `project_id + asset_type + timestamp + model_version + pipeline_flags`.
- **Access & Delivery**: Private per-project namespaces; delivered via signed URLs and CDN.

### 2. Human-in-the-Loop (HITL)

AI is not perfect. The pipeline supports **"Pause & Edit"** states:

- **Checkpoint A (Image)**: User can paint over the generated 2D image before it goes to 3D.
- **Checkpoint B (Mesh)**: User can download the `.obj`, fix topology in Blender manually, and re-upload to continue Rigging.

### 4. State Model & Transitions

- **Job Status**: pending → running → paused → approved/rejected → done/failed.
- **Step Status**: pending → running → paused → approved/rejected → done/failed.
- **Transitions**:
  - Backend sets step=pending → running on dispatch.
  - On completion, worker emits done/failed; backend persists and advances.
  - User reviews set approved/rejected; approved advances, rejected rewinds/edits.
- **Idempotency**: Steps use idempotency keys to avoid duplicate execution on retries.

### 5. Events & Idempotency

- **Events**: StepStarted, StepCompleted, StepFailed, UserReviewUpdated, AssetIndexed.
- **Outbox Pattern**: Backend writes DB + event atomically; event bus (e.g., EventBridge) delivers to subscribers.
- **Correlation IDs**: job_id and step_id propagate across services for tracing.
- **Idempotency Keys**: hash(project_id, asset_type, step_name, inputs, seed, model_version).

### 6. Error Handling & Retry

- **Retries**: Exponential backoff with jitter; cap attempts; annotate error causes.
- **DLQ**: Unrecoverable jobs routed to Dead Letter Queue for manual inspection.
- **Circuit Breakers**: Trip on consecutive failures; route to fallback model or pause pipeline.
- **Resume/Rewind**: Resume failed step or rewind to previous approved step based on user decision.

### 7. Observability

- **Metrics**: per-step latency, GPU utilization, cost estimate, success rate.
- **Tracing**: distributed traces across Backend → Workers → Storage.
- **Logs**: structured logs with correlation IDs; searchable by job_id.
- **Audit Trail**: user decisions and asset lineage recorded in DB.

### 8. Access Control & Privacy

- **Namespaces**: per-project isolation for storage and DB records.
- **RBAC**: roles for viewer/editor/admin; enforce on endpoints and assets.
- **Signed URLs**: time-limited access for private artifacts.
- **PII Minimization**: store only necessary user metadata.

### 9. Multi-Tenancy & Quotas

- **Per-Project Quotas**: concurrent jobs, GPU hours, storage caps.
- **Fair Scheduling**: queue prioritization to prevent starvation.
- **Burst Control**: throttle spikes; inform users with ETA.

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
