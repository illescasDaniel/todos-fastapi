#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=scripts/container/common.sh
source "$SCRIPT_DIR/common.sh"

cd "$PROJECT_ROOT"

image_name="${1:-todos-api}"

require_podman
podman build --format docker -t "$image_name" .

echo "Built: $image_name"
echo "Run: podman run --rm -p 8000:8000 -e JWT_SECRET_KEY=... -e DATABASE_URL=... $image_name"
