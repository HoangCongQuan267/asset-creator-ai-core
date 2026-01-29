import torch
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
        # Load SDXL Base
        print(
            "⏳ Loading Stable Diffusion XL model... (This may take a while for the first download)"
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
