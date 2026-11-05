#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

# Keep reconnects or repeated starts from launching a second watcher.
exec 9>/tmp/opennebula-docs-preview.lock
if ! flock --nonblock 9; then
    echo "The documentation preview is already running on port 1313."
    exit 0
fi

base_url="http://localhost:1313/"
args=(server --bind 0.0.0.0 --port 1313 --disableFastRender --appendPort=false)

if [[ -n "${CODESPACE_NAME:-}" ]]; then
    forwarding_domain="${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
    base_url="https://${CODESPACE_NAME}-1313.${forwarding_domain}/"
    # Codespaces terminates HTTPS while forwarding HTTP to Hugo.
    args+=(--liveReloadPort 443)
fi

exec hugo "${args[@]}" --baseURL "$base_url"
