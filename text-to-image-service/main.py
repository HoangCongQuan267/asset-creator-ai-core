import argparse
import json
import os
import time
from pathlib import Path

import torch
from diffusers import DPMSolverMultistepScheduler, StableDiffusionXLPipeline


ROOT_DIR = Path(__file__).resolve().parent
MODELS_DIR = ROOT_DIR / "models"
CHECKPOINTS_DIR = MODELS_DIR / "checkpoints"
OUTPUTS_DIR = ROOT_DIR / "outputs"


def load_config(config_path: str | None) -> dict[str, object]:
    if config_path:
        path = Path(config_path)
    else:
        path = ROOT_DIR / "pipeline.json"
    if not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        return {}
    return {}


def apply_config(args: argparse.Namespace, config: dict[str, object]) -> None:
    mapping = {
        "base_model": "base_model",
        "lora": "lora",
        "lora_weight": "lora_weight",
        "device": "device",
        "height": "height",
        "width": "width",
        "steps": "steps",
        "guidance_scale": "guidance_scale",
        "seed": "seed",
        "output_dir": "output_dir",
        "filename_prefix": "filename_prefix",
        "positive_prompt": "positive_prompt",
        "negative_prompt": "negative_prompt",
    }
    for key, attr in mapping.items():
        if key in config:
            value = config[key]
            if attr in {"height", "width", "steps"} and value is not None:
                try:
                    value = int(value)
                except Exception:
                    continue
            if attr == "guidance_scale" and value is not None:
                try:
                    value = float(value)
                except Exception:
                    continue
            if attr == "seed" and value is not None:
                try:
                    value = int(value)
                except Exception:
                    continue
            setattr(args, attr, value)
    if "loras" in config:
        value = config["loras"]
        setattr(args, "loras", value)


def apply_comfy_nodes(args: argparse.Namespace, config: dict[str, object]) -> None:
    nodes = config.get("nodes")
    if not isinstance(nodes, list):
        return

    positive_prompt = getattr(args, "positive_prompt", None)
    negative_prompt = getattr(args, "negative_prompt", None)

    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_type = node.get("type")
        if node_type != "PrimitiveNode":
            continue
        widgets = node.get("widgets_values")
        if not isinstance(widgets, list) or not widgets:
            continue
        text_value = widgets[0]
        if not isinstance(text_value, str) or not text_value.strip():
            continue
        title = node.get("title", "")
        if isinstance(title, str):
            lower_title = title.lower()
            if positive_prompt is None and "positive" in lower_title:
                positive_prompt = text_value
            elif negative_prompt is None and "negative" in lower_title:
                negative_prompt = text_value

    if positive_prompt is None or negative_prompt is None:
        clip_nodes: list[dict[str, object]] = []
        for node in nodes:
            if isinstance(node, dict) and node.get("type") == "CLIPTextEncode":
                clip_nodes.append(node)
        clip_nodes.sort(key=lambda n: n.get("id", 0))
        for index, node in enumerate(clip_nodes):
            widgets = node.get("widgets_values")
            if not isinstance(widgets, list) or not widgets:
                continue
            text_value = widgets[0]
            if not isinstance(text_value, str) or not text_value.strip():
                continue
            if positive_prompt is None and index == 0:
                positive_prompt = text_value
            elif negative_prompt is None and index == 1:
                negative_prompt = text_value

    if positive_prompt is not None:
        setattr(args, "positive_prompt", positive_prompt)
    if negative_prompt is not None:
        setattr(args, "negative_prompt", negative_prompt)


def select_device(preferred: str | None = None) -> tuple[str, torch.dtype]:
    if preferred and preferred != "auto":
        if preferred == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but not available")
        if preferred == "mps" and not torch.backends.mps.is_available():
            raise RuntimeError("MPS requested but not available")
        if preferred in {"cuda", "mps"}:
            return preferred, torch.float16
        return preferred, torch.float32

    if torch.cuda.is_available():
        return "cuda", torch.float16
    if torch.backends.mps.is_available():
        return "mps", torch.float16
    return "cpu", torch.float32


def resolve_base_model(base_model_arg: str | None) -> str:
    def resolve_path(candidate: Path) -> str | None:
        if candidate.is_dir() or candidate.is_file():
            return str(candidate)
        return None

    if not base_model_arg:
        env_value = os.getenv("ASSET_TTI_BASE_MODEL")
        if env_value:
            env_path = Path(env_value)
            resolved = resolve_path(env_path)
            if resolved:
                return resolved
            raise RuntimeError(
                f"ASSET_TTI_BASE_MODEL points to '{env_value}', but no file or directory was found"
            )

        default_file = CHECKPOINTS_DIR / "base_checkpoint.safetensors"
        default_dir = CHECKPOINTS_DIR / "sdxl-base-example"
        resolved_default = resolve_path(default_file) or resolve_path(default_dir)
        if resolved_default:
            return resolved_default

        raise RuntimeError(
            "No base model configured and no local models found under models/checkpoints/. "
            "Run download_checkpoints.sh or set --base-model/ASSET_TTI_BASE_MODEL to an existing path."
        )

    if base_model_arg == "default":
        return resolve_base_model(None)

    path = Path(base_model_arg)
    resolved_direct = resolve_path(path)
    if resolved_direct:
        return resolved_direct

    candidate_file = CHECKPOINTS_DIR / base_model_arg
    candidate_dir = CHECKPOINTS_DIR / base_model_arg
    resolved_candidate = resolve_path(candidate_file) or resolve_path(candidate_dir)
    if resolved_candidate:
        return resolved_candidate

    raise RuntimeError(
        f"Base model '{base_model_arg}' not found as a local file or directory. "
        "Remote downloads are disabled. Place the model under models/checkpoints/ "
        "or provide a valid local path."
    )


def resolve_lora_values(lora_value: str, weight_value: str | None) -> tuple[str, str]:
    path = Path(lora_value)
    if path.suffix == ".safetensors":
        if path.is_file():
            return str(path.parent), path.name
        root_candidate = ROOT_DIR / path
        if root_candidate.is_file():
            return str(root_candidate.parent), root_candidate.name
        loras_candidate = MODELS_DIR / "loras" / path.name
        if loras_candidate.is_file():
            return str(loras_candidate.parent), loras_candidate.name
        raise RuntimeError(f"LoRA file '{lora_value}' not found")
    candidate = MODELS_DIR / "loras" / lora_value
    if candidate.is_file():
        return str(candidate.parent), candidate.name
    candidate_with_suffix = candidate.with_suffix(".safetensors")
    if candidate_with_suffix.is_file():
        return str(candidate_with_suffix.parent), candidate_with_suffix.name
    if weight_value is None or not weight_value.strip():
        raise RuntimeError(
            "LoRA weight name must be provided when using a repo or directory"
        )
    return lora_value, weight_value


def resolve_lora(
    lora_arg: str | None, lora_weight_arg: str | None
) -> tuple[str | None, str | None]:
    if lora_arg is not None:
        value = lora_arg.strip()
        if not value:
            lora_arg = None
        else:
            if value.lower() in {"none", "off", "disable"}:
                return None, None
            repo_or_dir, weight_name = resolve_lora_values(value, lora_weight_arg)
            return repo_or_dir, weight_name

    env_lora = os.getenv("ASSET_TTI_LORA")
    env_weight = os.getenv("ASSET_TTI_LORA_WEIGHT")
    if env_lora:
        value = env_lora.strip()
        if not value:
            return None, None
        if value.lower() in {"none", "off", "disable"}:
            return None, None
        repo_or_dir, weight_name = resolve_lora_values(value, env_weight)
        return repo_or_dir, weight_name

    return None, None


def resolve_lora_list(entries: list[object]) -> list[tuple[str, str]]:
    resolved: list[tuple[str, str]] = []
    for item in entries:
        if isinstance(item, str):
            repo_or_dir, weight_name = resolve_lora_values(item, None)
            resolved.append((repo_or_dir, weight_name))
        elif isinstance(item, dict):
            raw_lora = item.get("lora")
            raw_weight = item.get("lora_weight")
            if not isinstance(raw_lora, str) or not raw_lora.strip():
                raise RuntimeError("Each LoRA entry must have a non-empty 'lora' value")
            repo_or_dir, weight_name = resolve_lora_values(raw_lora, raw_weight)
            resolved.append((repo_or_dir, weight_name))
        else:
            raise RuntimeError("Each LoRA entry must be a string or an object")
    return resolved


def build_pipeline(
    base_model: str,
    device: str,
    dtype: torch.dtype,
    lora_repo_or_dir: str | None,
    lora_weight_name: str | None,
    loras: list[tuple[str, str]] | None = None,
) -> StableDiffusionXLPipeline:
    kwargs: dict[str, object] = {
        "torch_dtype": dtype,
        "use_safetensors": True,
    }
    if dtype == torch.float16:
        kwargs["variant"] = "fp16"

    base_path = Path(base_model)
    if base_path.is_file():
        pipe = StableDiffusionXLPipeline.from_single_file(str(base_path), **kwargs)
    elif base_path.is_dir():
        pipe = StableDiffusionXLPipeline.from_pretrained(str(base_path), **kwargs)
    else:
        raise RuntimeError(
            f"Base model path '{base_model}' does not exist. Remote downloads are disabled."
        )

    if loras:
        for repo_or_dir, weight_name in loras:
            pipe.load_lora_weights(repo_or_dir, weight_name=weight_name)
        pipe.fuse_lora()
    elif lora_repo_or_dir and lora_weight_name:
        pipe.load_lora_weights(lora_repo_or_dir, weight_name=lora_weight_name)
        pipe.fuse_lora()

    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

    if device == "mps":
        pipe.enable_model_cpu_offload()
    else:
        pipe.to(device)
        if device == "cuda":
            try:
                pipe.enable_xformers_memory_efficient_attention()
            except Exception:
                pass

    return pipe


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Asset Creator AI Core - Text to Image (SDXL pipeline)"
    )
    parser.add_argument(
        "--base-model",
        type=str,
        default=None,
        help=(
            "Base SDXL checkpoint to use. Can be a Hugging Face model id, "
            "a local directory, or a name inside models/checkpoints/. "
            "Use 'default' for stabilityai/stable-diffusion-xl-base-1.0."
        ),
    )
    parser.add_argument(
        "--lora",
        type=str,
        default=None,
        help=(
            "LoRA to apply on top of the base model. Accepts a Hugging Face repo id, "
            "a directory path, or a .safetensors file under models/loras/. "
            "Use 'none' to disable LoRA."
        ),
    )
    parser.add_argument(
        "--lora-weight",
        type=str,
        default=None,
        help=(
            "LoRA weight filename when using a repo id or directory. "
            "Defaults to SDXL-Lightning 4-step weight when omitted."
        ),
    )
    parser.add_argument(
        "--device",
        type=str,
        choices=["auto", "mps", "cuda", "cpu"],
        default="auto",
        help="Execution device. Defaults to 'auto' (prefers CUDA, then MPS, then CPU).",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=int(os.getenv("ASSET_TTI_HEIGHT", "1024")),
        help="Output image height in pixels.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=int(os.getenv("ASSET_TTI_WIDTH", "1024")),
        help="Output image width in pixels.",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=int(os.getenv("ASSET_TTI_STEPS", "4")),
        help="Number of diffusion steps. SDXL-Lightning recommends 4 or 8.",
    )
    parser.add_argument(
        "--guidance-scale",
        type=float,
        default=float(os.getenv("ASSET_TTI_GUIDANCE", "0.0")),
        help="Classifier-free guidance scale. 0.0 is common for SDXL-Lightning.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible generations.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUTS_DIR),
        help="Directory where generated images will be written.",
    )
    parser.add_argument(
        "--filename-prefix",
        type=str,
        default="asset",
        help="Prefix for the generated image filename.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Optional JSON config file. If omitted, tries pipeline.json in this folder.",
    )
    return parser.parse_args()


def run(args: argparse.Namespace) -> None:
    config = load_config(getattr(args, "config", None))
    if config:
        apply_config(args, config)
        apply_comfy_nodes(args, config)

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    device, dtype = select_device(args.device)
    base_model = resolve_base_model(args.base_model)
    loras: list[tuple[str, str]] | None = None
    if hasattr(args, "loras") and getattr(args, "loras") is not None:
        raw_loras = getattr(args, "loras")
        if not isinstance(raw_loras, list):
            raise RuntimeError("Config field 'loras' must be a list")
        loras = resolve_lora_list(raw_loras)
        lora_repo_or_dir, lora_weight_name = None, None
    else:
        lora_repo_or_dir, lora_weight_name = resolve_lora(args.lora, args.lora_weight)

    print("Pipeline configuration:")
    print(f"  Device: {device} ({dtype})")
    print(f"  Base model path: {base_model}")
    if loras:
        print("  LoRAs:")
        for repo_or_dir, weight_name in loras:
            print(f"    - {repo_or_dir} :: {weight_name}")
    elif lora_repo_or_dir and lora_weight_name:
        print(f"  LoRA path: {lora_repo_or_dir}")
        print(f"  LoRA weight file: {lora_weight_name}")
    else:
        print("  LoRA: disabled")
    print(f"  Height x Width: {args.height} x {args.width}")
    print(f"  Steps: {args.steps}")
    print(f"  Guidance scale: {args.guidance_scale}")
    if args.seed is not None:
        print(f"  Seed: {args.seed}")
    print(f"  Output directory: {args.output_dir}")
    print(f"  Filename prefix: {args.filename_prefix}")

    pipe = build_pipeline(
        base_model=base_model,
        device=device,
        dtype=dtype,
        lora_repo_or_dir=lora_repo_or_dir,
        lora_weight_name=lora_weight_name,
        loras=loras,
    )

    positive_attr = getattr(args, "positive_prompt", None)
    if isinstance(positive_attr, str):
        positive = positive_attr.strip()
    else:
        positive = ""
    if not positive:
        positive = input("Positive prompt (describe your asset): ").strip()
        if not positive:
            positive = (
                "High quality game asset, concept art, detailed, sharp focus, 4k, "
                "trending on artstation"
            )

    negative_attr = getattr(args, "negative_prompt", None)
    if isinstance(negative_attr, str):
        negative = negative_attr.strip()
    else:
        negative = ""
    if not negative:
        negative = input("Negative prompt (press Enter for defaults): ").strip()
        if not negative:
            negative = "low quality, blurry, distorted, extra limbs, bad anatomy, watermark, text"

    generator_device = device if device in {"cuda", "cpu"} else "cpu"
    generator = torch.Generator(generator_device)
    if args.seed is not None:
        generator = generator.manual_seed(args.seed)

    result = pipe(
        prompt=positive,
        negative_prompt=negative,
        num_inference_steps=args.steps,
        guidance_scale=args.guidance_scale,
        height=args.height,
        width=args.width,
        generator=generator,
    )
    image = result.images[0]

    timestamp = int(time.time())
    filename = f"{args.filename_prefix}_{timestamp}.png"
    output_path = out_dir / filename
    image.save(output_path)

    print(f"Image saved to {output_path}")


def main() -> None:
    args = parse_args()
    run(args)


if __name__ == "__main__":
    main()
