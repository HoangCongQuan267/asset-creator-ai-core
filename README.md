# Asset Creator AI Core

**Asset Creator AI Core** is a modular, end-to-end generative AI pipeline designed to transform simple text prompts into production-ready game assets.

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
