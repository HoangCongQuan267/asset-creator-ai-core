# Text-to-Text Service (LLM Prompt Engineering)

This service uses a local Large Language Model (LLM) to act as a professional "Prompt Engineer" for your game assets.
It converts simple raw ideas into sophisticated, highly detailed prompts optimized for Stable Diffusion XL.

## 🚀 Usage

You can run the interactive CLI tool to test the prompt generation:

```bash
python3 llm_prompt_enhancer.py
```

## 🧠 How it Works

We use **TinyLlama-1.1B-Chat** (or other lightweight open-source models) to intelligently expand your ideas.

1.  **Input**: User provides a basic idea (e.g., "a sword") and a style (e.g., "fantasy").
2.  **LLM Processing**: The model acts as an expert system, applying knowledge of art styles, lighting, and composition.
3.  **Output**:
    - **Positive Prompt**: Adds details like "intricate runic engravings, glowing hilt, 8k resolution, unreal engine 5 render".
    - **Negative Prompt**: Context-aware exclusions (e.g., for a sword: "bent, rusty, blunt" instead of just generic "bad anatomy").

## 🛠 Dependencies

Ensure you have the necessary AI libraries installed:

```bash
python3 -m pip install transformers accelerate torch
```

## 📦 Integration

```python
from text_to_text_service.llm_prompt_enhancer import LLMPromptEnhancer

# Initialize the model (loads once)
enhancer = LLMPromptEnhancer()

# Generate optimized prompts
prompts = enhancer.enhance_prompt("a futuristic soldier", style="cyberpunk")

print(prompts['positive'])
# "Cyberpunk soldier, neon armor, visor HUD, rain-slicked streets..."

print(prompts['negative'])
# "organic cloth, rusty metal, medieval armor, low resolution..."
```
