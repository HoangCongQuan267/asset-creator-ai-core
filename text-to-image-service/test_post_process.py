import argparse
from pathlib import Path
from PIL import Image
from post_processing import center_object_postprocess

ROOT_DIR = Path(__file__).resolve().parent
MODELS_DIR = ROOT_DIR / "models"


def main():
    parser = argparse.ArgumentParser(description="Test Post-Processing Module")
    parser.add_argument(
        "--image", type=str, required=True, help="Path to the input image"
    )
    parser.add_argument(
        "--prompt", type=str, required=True, help="Text prompt describing the object"
    )
    args = parser.parse_args()

    input_path = Path(args.image)
    if not input_path.is_file():
        print(f"Error: Image not found at {input_path}")
        return

    try:
        image = Image.open(input_path).convert("RGB")
    except Exception as e:
        print(f"Error opening image: {e}")
        return

    print(f"Processing image: {input_path}")
    print(f"Prompt: {args.prompt}")

    output_path = center_object_postprocess(image, input_path, args.prompt, MODELS_DIR)

    if output_path:
        print(f"✅ Success! Output saved to: {output_path}")
    else:
        print("❌ Post-processing failed.")


if __name__ == "__main__":
    main()
