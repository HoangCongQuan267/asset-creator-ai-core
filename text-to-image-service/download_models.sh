#!/bin/bash

# Asset Creator AI Core - Model Downloader
# Usage: ./download_models.sh

echo "---------------------------------------------------"
echo "🚀 Starting Model Downloads"
echo "---------------------------------------------------"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SAM_DIR="$SCRIPT_DIR/models/sam"
mkdir -p "$SAM_DIR"
SAM_URL="https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth"
SAM_PATH="$SAM_DIR/sam_vit_h.pth"

if [ -f "$SAM_PATH" ]; then
    echo "✅ SAM checkpoint already exists at $SAM_PATH"
else
    echo "⬇️  Downloading SAM checkpoint to $SAM_PATH..."
    if curl -L --fail -o "$SAM_PATH" "$SAM_URL"; then
        echo "✅ Successfully downloaded SAM checkpoint"
    else
        echo "❌ Failed to download SAM checkpoint"
        rm -f "$SAM_PATH"
    fi
fi

if [ -f "$YOLO_PATH" ]; then
    echo "✅ YOLO checkpoint already exists at $YOLO_PATH"
else
    echo "⬇️  Downloading YOLO checkpoint to $YOLO_PATH..."
    # Using -k to skip SSL verification if needed, similar to the python fix
    if curl -L -k --fail -o "$YOLO_PATH" "$YOLO_URL"; then
        echo "✅ Successfully downloaded YOLO checkpoint"
    else
        echo "❌ Failed to download YOLO checkpoint"
        rm -f "$YOLO_PATH"
    fi
fi

bash "$SCRIPT_DIR/download_checkpoints.sh"
bash "$SCRIPT_DIR/download_vae.sh"
bash "$SCRIPT_DIR/download_loras.sh"

echo "---------------------------------------------------"
echo "🎉 Download process complete!"
echo "---------------------------------------------------"
echo "To download additional LoRAs from Civitai on AWS:"
echo "1. Go to Civitai.com on your PC"
echo "2. Right-click 'Download' -> 'Copy Link Address'"
echo "3. Run: wget --content-disposition \"PASTED_LINK\" -P models/loras"
