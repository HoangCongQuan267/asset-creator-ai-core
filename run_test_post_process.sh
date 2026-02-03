#!/bin/bash
# Script to test post-processing on a specific image

# Ensure we are in the project root
cd "$(dirname "$0")"

# Path to the image
IMAGE_PATH="/Users/hoangcongquan/Documents/asset-creator-ai-core/text-to-image-service/outputs/asset_1769931949.png"

# Prompt for the object detection (assuming 'sword' based on the image content)
PROMPT="sword"

echo "Running post-processing test..."
echo "Image: $IMAGE_PATH"
echo "Prompt: $PROMPT"

python3 text-to-image-service/test_post_process.py --image "$IMAGE_PATH" --prompt "$PROMPT"
