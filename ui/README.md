# Asset Creator Studio UI

The **Studio UI** is not just a prompt box; it is a **Structured Creativity Engine**. Its purpose is to guide game developers through the process of defining their game's unique identity—Style, Lore, and Mechanics—and using that structured context to generate consistent, production-ready assets.

## 🎯 Mission: Beyond "Text-to-Image"

Standard AI tools rely on chaotic prompting. The Studio UI relies on **Project Context**.
Instead of typing _"A knight"_ 50 times, you define the _"Kingdom of Aeloria"_ once, and the AI understands the armor style, color palette, and mood for every asset generated within that project.

---

## 🧩 Core Modules

### 1. Style DNA (The "Art Director")

This module defines the visual rules of the universe.

- **Visual Style Selector**: Not just keywords, but visual examples.
  - _Options_: Pixel Art (16/32 bit), Low Poly, Cel Shaded, Hyper-Realistic, Watercolor, Cyberpunk.
- **Color Palette Enforcer**: Define primary/secondary colors. The AI will bias generation towards these hex codes.
- **Mood Board**: Users upload 3-5 reference images. The AI extracts style embeddings (via IP-Adapter/ControlNet) to ensure consistency.

### 2. World Builder (The "Writer")

Context for the AI to understand _why_ an asset exists.

- **Setting**: "Post-Apocalyptic Tokyo", "High Fantasy Forest".
- **Time Period**: "1800s Steam Age", "Year 3000".
- **Atmosphere**: "Foggy", "Cheerful", "Oppressive".

### 3. Asset Wizards (The "Designer")

Structured forms to create specific asset types.

#### 👤 Character Wizard

- **Identity**: Name, Age, Role (Protagonist, Vendor, Enemy).
- **Backstory**: "A retired veteran looking for peace." (AI infers: Scars, weary expression, worn clothes).
- **Archetype**: Tank (Bulky), Rogue (Slim), Mage (Robes).
- **Output**: Concept Art → 3D Model → Rig.

#### ⚔️ Game Event Wizard

- **Scenario**: "Boss battle at the lava bridge."
- **Output**: Generates a set of assets:
  - Background (Lava environment).
  - Props (Broken bridge pieces, magma rocks).
  - VFX (Fire particles, smoke sprites).

---

## 🎨 User Experience Flow

1.  **Project Initialization**:
    - User creates "Project Alpha".
    - Selects **Style**: "Low Poly", **Palette**: "Neon".
    - _Result_: `project_context.json` is created.

2.  **Definition Phase**:
    - User defines "Hero Character".
    - User inputs story: "Orphan raised by wolves."
    - _Result_: AI suggests visual traits (Fur cloak, wild hair).

3.  **Generation Phase**:
    - User clicks "Generate 3D Model".
    - **System Action**: The UI sends a structured payload to the [Pipeline](../pipeline/README.md) combining:
      - User Input ("Hero")
      - - Project Style ("Low Poly")
      - - World Context ("Forest")
4.  **Review & Refine**:
    - User sees 4 variations.
    - Selects one -> "Make it more muscular" (Refinement Loop).
    - Approves -> Sends to [Export Service](../export-service/README.md).

---

## 🛠 Tech Stack

- **Framework**: Next.js (React) / Electron (for local file system access).
- **State Management**: Redux/Zustand (to hold Project Context).
- **Visuals**: Three.js / React-Three-Fiber (to preview 3D models directly in the browser).
- **API Client**: Axios (communicating with the [Server](../server/README.md) API Gateway).

## 📄 Data Structure (The "Context")

The UI manages a `ProjectContext` object that is passed to every AI generation request.

```json
{
  "project_id": "prj_001",
  "style_profile": {
    "engine": "UNITY_URP",
    "art_style": "STYLISED_PBR",
    "reference_images": ["s3://.../ref1.png"],
    "negative_prompt": "photorealistic, noise, grime"
  },
  "narrative_context": {
    "genre": "SCI_FI",
    "mood": "HOPEFUL"
  }
}
```
