#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

# Codespaces includes updateContentCommand in its prebuild snapshots.
echo "Installing documentation dependencies..."
npm ci --include=dev

# Resolve and cache modules without rendering the site or starting a server.
echo "Preparing Hugo modules..."
hugo mod graph
