#!/bin/bash

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LORAS_DIR="$BASE_DIR/models/loras"

mkdir -p "$LORAS_DIR"

echo "📂 LoRA directory checked/created at $LORAS_DIR"

download_file() {
    local url="$1"
    local dest_dir="$2"
    local filename="$3"
    local pattern="${4:-}"
    local dest_path="$dest_dir/$filename"

    if [ -n "$pattern" ] && compgen -G "$dest_dir/$pattern" > /dev/null; then
        echo "✅ Existing match ($pattern) found in $dest_dir. Skipping."
        return
    fi

    if [ -f "$dest_path" ]; then
        echo "✅ $filename already exists. Skipping."
    else
        echo "⬇️  Downloading $filename..."
        curl -L --fail -o "$dest_path" "$url"
        if [ $? -eq 0 ]; then
            echo "✅ Successfully downloaded $filename"
        else
            echo "❌ Failed to download $filename"
            rm -f "$dest_path"
        fi
    fi
}

CIVITAI_LORA_IDS=(
    "160130:stickers_redmond"
    # Add more Civitai LoRA model ids here, one per line.
    # Example:
    # "123456:MyLoraName"
    "198105:picture_books_children_cartoon"
    "135931:pixel_art"
    "128609:voxel_xl"
    "156373:game_icon"
    "183638:detail_enhance"
    "134147:game_icon_institute_kuijia"
)

index=1
for entry in "${CIVITAI_LORA_IDS[@]}"; do
    id="${entry%%:*}"
    name="${entry#*:}"
    url="https://civitai.com/api/download/models/$id"

    if [ "$id" = "$name" ]; then
        filename="lora_${id}.safetensors"
        pattern="lora_${id}*.safetensors"
    else
        filename="${name}_${id}.safetensors"
        pattern="${name}_${id}*.safetensors"
    fi

    echo "LoRA $index from Civitai (model id: $id): $url"
    download_file \
        "$url" \
        "$LORAS_DIR" \
        "$filename" \
        "$pattern"

    index=$((index + 1))
done
