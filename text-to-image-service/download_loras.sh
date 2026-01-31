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
    "160130" #StickersRedmond
    # Add more Civitai LoRA model ids here, one per line.
    # Example:
    # "123456"
)

index=1
for id in "${CIVITAI_LORA_IDS[@]}"; do
    url="https://civitai.com/api/download/models/$id"

    if [ "$index" -eq 1 ]; then
        filename="StickersRedmond.safetensors"
        pattern="StickersRedmond*.safetensors"
    else
        filename="lora_${id}.safetensors"
        pattern="lora_${id}*.safetensors"
    fi

    echo "LoRA $index from Civitai (model id: $id): $url"
    download_file \
        "$url" \
        "$LORAS_DIR" \
        "$filename" \
        "$pattern"

    index=$((index + 1))
done
