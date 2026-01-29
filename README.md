# Asset Creator AI Core

**Asset Creator AI Core** is more than just an asset generator—it is a **Game Project Creator**.

Instead of asking for a single asset ("a sword"), the user describes a **Game Idea** ("a dark fantasy RPG set in a cursed forest"). The system analyzes the idea, breaks it down into required assets, structures the game project folders (Unity/Unreal), and orchestrates the creation of every element needed to build the game.

## 🧠 Core Workflow: Idea to Project

### 1. Game Design Analysis (LLM Agent)

**Input**: User Prompt (e.g., _"Make a 2D side-scroller about a cyber-ninja fighting robots in Neo-Tokyo"_).
**Process**:

- **Decomposition**: Identifies necessary components (Player Character, Enemy Types, Bosses, Tilesets, Backgrounds, UI Elements, Audio).
- **Style Definition**: Establishes a visual consistency guide (Palette, Lighting, Art Style) to ensure all assets look like they belong in the same game.
- **Output**: `GameDesignSpec.json`

### 2. Project Scaffolding

**Action**: Creates the directory structure for the target engine (Unity, Unreal, Godot).
**Structure Example (Unity)**:

```text
MyGameProject/
├── Assets/
│   ├── _Project/
│   │   ├── Characters/
│   │   │   ├── Player_Ninja/      <-- Target for Asset Pipeline
│   │   │   ├── Enemy_RobotGrunt/
│   │   ├── Environment/
│   │   │   ├── NeoTokyo_Streets/
│   │   ├── Props/
│   │   ├── UI/
│   ├── Scenes/
│   │   ├── Level1.unity
```

### 3. Asset Batch Orchestration

**Action**: Generates a bulk job list for the [Pipeline Orchestrator](./pipeline/README.md).

- Instead of 1 job, it dispatches 50 parallel jobs (1 Player, 5 Enemies, 20 Props, 3 Backgrounds).
- Passes the **Style Guide** context to every job to maintain consistency.

---

## 🏆 Key Market Advantages

Why this solution is positioned to lead the market:

1.  **True "Game-Ready" Output**: Unlike competitors that stop at raw meshes, this pipeline handles **Retopology, UV Unwrapping, LOD Generation, and Rigging** automatically. Assets drop directly into Unity/Unreal without manual cleanup.
2.  **Unbeatable Economics**:
    - **98%+ Gross Margins**: Optimized AWS Spot architecture and Vietnam-based operations keep COGS near zero (~$0.03 per 3D character).
    - **Competitive Pricing**: Offers indie-friendly rates ($1.50/character) that undercut manual outsourcing (hundreds of dollars) and expensive enterprise tools.
3.  **Global Scale from Day 1**:
    - **Multi-Region Delivery**: Architected for low-latency access in USA, EU, and China (via cross-border optimization).
    - **Enterprise & Indie Ready**: From single-asset pay-as-you-go to high-volume Studio subscriptions.

It supports two primary workflows:

1.  **2D Pipeline**: Text → Image → Sprites / Spine Animations.
2.  **3D Pipeline**: Text → Image → 3D Mesh → Retopology → Rigging → Animation.

The system is architected to run efficiently on both **Local Mac Silicon (M2/M3)** for development and **AWS GPU Clusters** for scalable production.

---

## 📂 Services Overview

The repository is organized into specialized micro-services, each handling a specific stage of the pipeline:

### 1. Foundation

- **[Text → Image Service](./text-to-image-service/README.md)**
  - _Core_: SDXL, Kandinsky, ControlNet.
  - _Goal_: Generate high-quality concept art and base textures.

### 2. 2D Asset Pipeline

- **[Image → 2D Assets & Animation](./image-to-2d-assets-animation-service/README.md)**
  - _Core_: SAM (Segmentation), Spine, AnimateDiff.
  - _Goal_: Create clean sprites, background layers, and 2D skeletal animations.

### 3. 3D Asset Pipeline

- **[Image → 3D Generation](./image-to-3d-model-generation-service/README.md)**
  - _Core_: TripoSR, Zero123++.
  - _Goal_: Convert 2D images into raw 3D meshes.
- **[Retopology & Remeshing](./retopology-service/README.md)**
  - _Core_: Blender (Python API), Instant Meshes.
  - _Goal_: Clean up raw meshes into game-ready topology with UVs.
- **[Rigging Service](./rigging-service/README.md)**
  - _Core_: RigNet, Blender Rigify.
  - _Goal_: Auto-rig humanoid and creature characters.
- **[3D Animation Generation](./animation-3d-service/README.md)**
  - _Core_: MDM (Motion Diffusion Model), MoDi.
  - _Goal_: Generate and retarget 3D motion clips from text descriptions.

### 4. Integration & Delivery

- **[Export Service](./export-service/README.md)**
  - _Core_: Blender CLI.
  - _Goal_: Final verification and export to Unity (FBX), Unreal (FBX), and Godot (GLTF).
- **[Pipeline Orchestrator](./pipeline/README.md)**
  - _Core_: DAG Architecture.
  - _Goal_: Connects all services into a unified workflow.

### 5. Infrastructure

- **[Server & Deployment](./server/README.md)**
  - _Core_: AWS (Lambda, SQS, Auto-Scaling GPU), Docker.
  - _Goal_: Production-grade architecture with auto-scaling and global delivery (CDN).

---

## 💻 Supported Environments

| Environment                   | Role                          | Setup Notes                                                      |
| ----------------------------- | ----------------------------- | ---------------------------------------------------------------- |
| **Mac M2/M3 (Apple Silicon)** | Development / Local Inference | Uses `MPS` (Metal Performance Shaders) for PyTorch acceleration. |
| **AWS G4dn (NVIDIA T4)**      | Production / Cloud Inference  | Uses standard `CUDA` acceleration with Auto-Scaling.             |

## 🚀 Getting Started

1.  **Pick a Service**: Navigate to a service folder (e.g., `text-to-image-service`).
2.  **Install Dependencies**: Follow the `README.md` inside that folder for environment-specific setup.
3.  **Run Pipeline**: See `pipeline/README.md` for how to chain services together.

---

## 💵 Pricing & Margin

### Assumptions (COGS Inputs)

- **GPU (Spot) G4dn.xlarge**: ~$0.0026/min
- **GPU (On-Demand) G4dn.xlarge**: ~$0.0088/min
- **CDN Egress**: ~$0.09/GB (typical CloudFront)
- **Asset Sizes**:
  - 2D Sprite/Sheet: 5–20 MB
  - 3D Character (GLB + Textures): 100–300 MB
  - Background/VFX Pack: 20–100 MB

### COGS Per Asset (Spot)

- **2D Sprite**:
  - Compute: SDXL + Refine ~ 13 s → ~$0.0006
  - Egress: 10 MB → ~$0.0009
  - Total COGS: ~$0.0015–$0.003
- **3D Character (Full Pipeline)**:
  - Compute (GPU): SDXL + TripoSR + RigNet ~ 70 s → ~$0.003–$0.004
  - CPU (Retopo/Export): negligible at scale
  - Egress: 200 MB → ~$0.018
  - Total COGS: ~$0.022–$0.030
- **Background / VFX Pack**:
  - Compute: ~20–30 s → ~$0.001–$0.002
  - Egress: 50 MB → ~$0.0045
  - Total COGS: ~$0.006–$0.010

### Suggested Retail Pricing (Pay‑As‑You‑Go)

- **2D Sprite / Sheet**: $0.25
- **3D Character (Model + Rig)**: $1.50
- **Background / Environment**: $0.75
- **VFX Pack (Sprites/Clips)**: $0.75

### Target Gross Margins (Spot)

- **2D**: ~99% margin ($0.25 price vs ~$0.003 COGS)
- **3D Character**: ~98% margin ($1.50 price vs ~$0.030 COGS)
- **Background/VFX**: ~98–99% margin
- On-Demand GPUs reduce margins by ~1–2% on busy periods; egress remains dominant cost for large assets.

### Subscription Tiers

- **Starter**: $29/month, 100 assets (effective ~$0.29/asset)
- **Studio**: $199/month, 1,000 assets (effective ~$0.20/asset)
- **Pro**: $499/month, 3,000 assets (effective ~$0.17/asset)
- **Enterprise**: Custom; dedicated GPUs, data residency, SSO, SLA

### Pricing Formula

- **COGS** = GPU_minutes × GPU_rate + Egress_GB × Egress_rate + Storage/Requests (minor)
- **Margin %** = (Price − COGS) ÷ Price
- **Recommended**: Price = COGS × 10–50× depending on asset type and SLA

### Notes

- Egress is often the largest driver for big 3D assets; prefer KTX2 textures and Draco compression.
- Spot GPUs keep compute costs low; maintain small On‑Demand baseline to minimize cold starts.
