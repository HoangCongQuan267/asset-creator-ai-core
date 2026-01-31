import torch
from pathlib import Path
from diffusers import DiffusionPipeline


def main():
    # Device selection
    if torch.backends.mps.is_available():
        device = "mps"
        dtype = torch.float16
    elif torch.cuda.is_available():
        device = "cuda"
        dtype = torch.float16
    else:
        device = "cpu"
        dtype = torch.float32

    print(f"🚀 Running on device: {device} with precision: {dtype}")

    try:
        root_dir = Path(__file__).resolve().parent
        local_checkpoint = (
            root_dir / "models" / "checkpoints" / "base_checkpoint.safetensors"
        )
        if local_checkpoint.is_file():
            print(f"⏳ Loading local checkpoint from {local_checkpoint}...")
            base = DiffusionPipeline.from_single_file(
                str(local_checkpoint),
                torch_dtype=dtype,
                variant="fp16",
                use_safetensors=True,
            )
        else:
            print(
                "⏳ Local checkpoint not found, loading Stable Diffusion XL model from Hugging Face..."
            )
            base = DiffusionPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-base-1.0",
                torch_dtype=dtype,
                variant="fp16",
                use_safetensors=True,
            )

        # Optimization: Offload to CPU when not in use (Crucial for Mac M2 16GB)
        if device == "mps":
            print("🔧 Optimization: Enabling Model CPU Offload for Mac M2")
            base.enable_model_cpu_offload()
        else:
            base.to(device)

        # Generate
        user_prompt = input(
            "Enter your prompt (default: cyberpunk street food vendor): "
        ).strip()
        prompt = (
            user_prompt
            if user_prompt
            else "A cinematic shot of a cyberpunk street food vendor, neon lights, highly detailed, 8k"
        )

        print(f"🎨 Generating image for prompt: '{prompt}'")

        image = base(prompt=prompt).images[0]

        output_file = "generated_asset.png"
        image.save(output_file)
        print(f"✅ Success! Image saved to {output_file}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
