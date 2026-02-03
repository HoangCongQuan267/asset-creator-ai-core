#!/bin/bash

# Asset Creator AI Core - Model Downloader
# Usage: ./download_models.sh

echo "---------------------------------------------------"
echo "🚀 Starting Model Downloads"
echo "---------------------------------------------------"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Note: Post-processing now uses rembg (U2Net) which auto-downloads to models/u2net
# No need to manually download SAM or YOLO checkpoints anymore.

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
