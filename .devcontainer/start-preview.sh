#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

log_file=/tmp/opennebula-docs-preview.log
preview_url=http://127.0.0.1:1313/

preview_ready() {
    curl --fail --silent --output /dev/null --max-time 2 "$preview_url"
}

show_error() {
    echo "$1 Check $log_file for details." >&2
    if [[ -f "$log_file" ]]; then
        tail -n 60 "$log_file" >&2
    fi
}

if preview_ready; then
    echo "The documentation preview is already ready on port 1313."
    exit 0
fi

echo "Starting the documentation preview. The first build may take several minutes."
echo "Hugo output: $log_file"
nohup bash .devcontainer/serve.sh >> "$log_file" 2>&1 < /dev/null &
server_pid=$!
deadline=$((SECONDS + 30))

until preview_ready; do
    if [[ -n "$server_pid" ]] && ! kill -0 "$server_pid" 2>/dev/null; then
        if wait "$server_pid"; then
            # Another launcher may already hold serve.sh's watcher lock.
            server_pid=""
        else
            show_error "The documentation preview failed to start."
            exit 1
        fi
    fi
    if (( SECONDS >= deadline )); then
        echo "Hugo is still starting in the background. The editor is ready to use."
        echo "Follow progress with: tail -f $log_file"
        echo "Open or refresh port 1313 after the first build finishes."
        exit 0
    fi
    sleep 1
done

echo "The documentation preview is ready. Open port 1313 from the Ports tab."
