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
        print("⏳ Loading Stable Diffusion XL Base...")
        base = DiffusionPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0",
            torch_dtype=dtype,
            variant="fp16",
            use_safetensors=True,
        )

        # Optimization
        if device == "mps":
            base.enable_model_cpu_offload()
        else:
            base.to(device)

        # 1. Get User Input
        user_prompt = input("Enter your POSITIVE prompt: ").strip()
        prompt = (
            user_prompt
            if user_prompt
            else "A warrior holding a sword, detailed hands, 8k"
        )

        # 2. Negative Prompt (The "Secret Sauce" for hands)
        default_negative = "deformed, distorted, disfigured, poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, mutated hands and fingers, disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation"

        user_negative = input(
            f"Enter your NEGATIVE prompt (Press Enter for default): "
        ).strip()
        negative_prompt = user_negative if user_negative else default_negative

        print(f"🎨 Generating with:")
        print(f"   Positive: {prompt}")
        print(f"   Negative: {negative_prompt}")

        # 3. Generate with High Guidance Scale (Follows prompt strictly)
        image = base(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=50,  # More steps = cleaner details
            guidance_scale=7.5,  # Standard strictness
        ).images[0]

        output_file = "enhanced_asset.png"
        image.save(output_file)
        print(f"✅ Success! Improved image saved to {output_file}")
        print(
            "💡 Tip: If hands are still bad, try using ControlNet (Depth/OpenPose) for structure."
        )

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
