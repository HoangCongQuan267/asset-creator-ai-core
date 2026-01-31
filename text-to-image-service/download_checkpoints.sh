#!/bin/bash

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECKPOINTS_DIR="$BASE_DIR/models/checkpoints"

mkdir -p "$CHECKPOINTS_DIR"

echo "📂 Checkpoints directory checked/created at $CHECKPOINTS_DIR"

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

CIVITAI_MODEL_IDS=(
    "128078" #SDXL
    # Add more Civitai model ids here, one per line.
    # Example:
    # "123456"
)

index=1
for id in "${CIVITAI_MODEL_IDS[@]}"; do
    url="https://civitai.com/api/download/models/$id"

    if [ "$index" -eq 1 ]; then
        filename="base_checkpoint.safetensors"
        pattern="base_checkpoint*.safetensors"
    else
        filename="checkpoint_${id}.safetensors"
        pattern="checkpoint_${id}*.safetensors"
    fi

    echo "Checkpoint $index from Civitai (model id: $id): $url"
    download_file \
        "$url" \
        "$CHECKPOINTS_DIR" \
        "$filename" \
        "$pattern"

    index=$((index + 1))
done
