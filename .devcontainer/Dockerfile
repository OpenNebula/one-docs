FROM golang:1.26-bookworm AS go
FROM mcr.microsoft.com/devcontainers/javascript-node:5-22-bookworm

# Hugo uses Go to fetch the theme and other modules.
COPY --from=go /usr/local/go /usr/local/go
ENV PATH="/usr/local/go/bin:${PATH}"

# Keep Hugo aligned with setup.sh and the GitHub Actions workflows.
ARG HUGO_VERSION=0.155.3
ARG DART_SASS_VERSION=1.105.1

RUN set -eux; \
    arch="$(dpkg --print-architecture)"; \
    case "$arch" in \
        amd64) sass_arch=x64 ;; \
        arm64) sass_arch=arm64 ;; \
        *) echo "Unsupported architecture: $arch" >&2; exit 1 ;; \
    esac; \
    download_dir="$(mktemp -d)"; \
    hugo_archive="hugo_extended_${HUGO_VERSION}_linux-${arch}.tar.gz"; \
    curl -fsSL --retry 3 "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/${hugo_archive}" -o "${download_dir}/${hugo_archive}"; \
    curl -fsSL --retry 3 "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_${HUGO_VERSION}_checksums.txt" -o "${download_dir}/checksums.txt"; \
    (cd "$download_dir" && sha256sum --check --ignore-missing checksums.txt); \
    tar -xzf "${download_dir}/${hugo_archive}" -C /usr/local/bin hugo; \
    curl -fsSL --retry 3 "https://github.com/sass/dart-sass/releases/download/${DART_SASS_VERSION}/dart-sass-${DART_SASS_VERSION}-linux-${sass_arch}.tar.gz" -o "${download_dir}/dart-sass.tar.gz"; \
    tar -xzf "${download_dir}/dart-sass.tar.gz" -C /opt; \
    ln -s /opt/dart-sass/sass /usr/local/bin/sass; \
    rm -rf "$download_dir"
